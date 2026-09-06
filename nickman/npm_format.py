"""NPM (Nick Pack Master) package format for Vision Linux.

Structure of a .npm file (tar.zst):
    app-1.0.npm
    ├── app/
    │   ├── bin/          - executables
    │   ├── share/        - data, icons, .desktop
    │   └── ...           - application files
    ├── manifest.json     - metadata
    └── signature         - Ed25519 signature of sha256(manifest + app-archives)
"""

from __future__ import annotations

import hashlib
import json
import tarfile
import tempfile
from pathlib import Path


class NPMError(Exception):
    pass


class NPMPackage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.manifest: dict = {}
        self._payload: bytes | None = None
        self._signature: bytes | None = None

    def name(self) -> str:
        return self.manifest.get("name", "unknown")

    def version(self) -> str:
        return self.manifest.get("version", "0.0.0")


def load(pkg_path: Path) -> NPMPackage:
    if not pkg_path.exists():
        raise NPMError(f"File not found: {pkg_path}")
    if not pkg_path.name.endswith(".npm"):
        raise NPMError(f"Not an NPM package: {pkg_path.name}")

    pkg = NPMPackage(pkg_path)
    try:
        with tarfile.open(pkg_path, "r:*") as tar:
            members = {m.name: m for m in tar.getmembers()}

            # Read manifest
            if "manifest.json" not in members:
                raise NPMError("No manifest.json in package")
            manifest_file = tar.extractfile("manifest.json")
            if manifest_file is None:
                raise NPMError("Cannot read manifest.json")
            pkg.manifest = json.loads(manifest_file.read())

            # Read signature
            if "signature" not in members:
                raise NPMError("No signature in package (unsigned packages rejected)")
            sig_file = tar.extractfile("signature")
            if sig_file is None:
                raise NPMError("Cannot read signature")
            pkg._signature = sig_file.read()

            # Read app payload hash
            app_members = [m for m in tar.getmembers() if m.name.startswith("app/")]
            if not app_members:
                raise NPMError("No app/ directory in package")

            # Compute payload hash for verification
            h = hashlib.sha256()
            for m in sorted(app_members, key=lambda x: x.name):
                f = tar.extractfile(m)
                if f:
                    h.update(f.read())
            pkg._payload = h.digest()

    except tarfile.TarError as exc:
        raise NPMError(f"Corrupt package: {exc}")

    return pkg


def get_signature(pkg: NPMPackage) -> bytes | None:
    return pkg._signature


def get_payload_hash(pkg: NPMPackage) -> bytes | None:
    return pkg._payload


def create(payload_dir: Path, manifest: dict, output: Path,
           private_key_pem: bytes | None = None) -> None:
    """Create a .npm package from a directory."""
    if not payload_dir.is_dir():
        raise NPMError(f"Payload directory not found: {payload_dir}")

    # Try zstd first (Python 3.12+), fall back to gz
    try:
        _tar = tarfile.open(output, "w:zst")
    except (ValueError, TypeError):
        _tar = tarfile.open(output, "w:gz")
    with _tar as tar:
        # Add app/ contents
        for item in sorted(payload_dir.rglob("*")):
            if item.is_file():
                arcname = f"app/{item.relative_to(payload_dir)}"
                tar.add(item, arcname=arcname)

        # Write manifest
        manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode()
        import io
        manifest_info = tarfile.TarInfo(name="manifest.json")
        manifest_info.size = len(manifest_bytes)
        tar.addfile(manifest_info, io.BytesIO(manifest_bytes))

        # Sign if key provided
        if private_key_pem:
            from .signing import sign_file
            payload_hash = hashlib.sha256()
            for m in sorted(tar.getmembers(), key=lambda x: x.name):
                if m.name.startswith("app/"):
                    f = tar.extractfile(m)
                    if f:
                        payload_hash.update(f.read())

            sig = sign_file(payload_hash.digest(), manifest_bytes, private_key_pem)
            sig_info = tarfile.TarInfo(name="signature")
            sig_info.size = len(sig)
            tar.addfile(sig_info, io.BytesIO(sig))
        else:
            raise NPMError("Cannot create unsigned package — signing is mandatory")

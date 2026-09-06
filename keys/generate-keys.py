#!/usr/bin/env python3
"""Generate 10 Ed25519 key pairs for Vision Linux package signing.

Usage:
    python3 generate-keys.py [--out-dir ./keys]

Each key pair: <name>.priv (private) + <name>.pub (public).
Public keys are copied to rootfs/etc/visionlinux/keys/ for trusted storage.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        PublicFormat,
    )
except ImportError:
    raise SystemExit("Install cryptography: pip install cryptography")

KEY_NAMES = [
    "vision-main",
    "vision-core",
    "vision-apps",
    "vision-drivers",
    "vision-shell",
    "vision-net",
    "vision-gui",
    "vision-utils",
    "vision-media",
    "vision-backup",
]

ROOTFS_TRUSTED = Path(__file__).resolve().parent.parent / "rootfs" / "etc" / "visionlinux" / "keys"


def generate_key(name: str, out_dir: Path) -> tuple[Path, Path]:
    private_key = Ed25519PrivateKey.generate()
    priv_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    priv_path = out_dir / f"{name}.priv"
    pub_path = out_dir / f"{name}.pub"
    priv_path.write_bytes(priv_pem)
    pub_path.write_bytes(pub_pem)
    os.chmod(priv_path, 0o600)
    os.chmod(pub_path, 0o644)
    return priv_path, pub_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Vision Linux signing keys")
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent),
                        help="Output directory for keys")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ROOTFS_TRUSTED.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(KEY_NAMES)} key pairs in {out_dir}/\n")
    for i, name in enumerate(KEY_NAMES, 1):
        priv, pub = generate_key(name, out_dir)
        # Copy public key to rootfs trusted dir
        trusted_pub = ROOTFS_TRUSTED / f"{name}.pub"
        trusted_pub.write_bytes(pub.read_bytes())
        fp = pub.read_bytes()
        import hashlib
        fingerprint = hashlib.sha256(fp).hexdigest()
        print(f"  [{i:2d}/{len(KEY_NAMES)}] {name}")
        print(f"         priv: {priv.name}")
        print(f"         pub:  {pub.name}")
        print(f"         fingerprint: {' '.join(fingerprint[j:j+4] for j in range(0, 64, 4))}")
        print()

    print(f"Done. {len(KEY_NAMES)} key pairs generated.")
    print(f"Public keys copied to {ROOTFS_TRUSTED}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

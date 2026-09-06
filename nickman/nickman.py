#!/usr/bin/env python3
"""Nickman — Nick Pack Master for Vision Linux.

Commands:
    nickman install  <file.npm>   Verify signature, ask root, install
    nickman remove   <name>       Remove installed application (root)
    nickman list                  List installed applications
    nickman verify   <file.npm>   Verify signature only
    nickman pack    <dir> -o out.npm --key key.pem
    nickman keys                 Show trusted keys / fingerprints

Signature check is mandatory: unsigned packages are rejected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB))

from npm_format import NPMPackage, load, create, NPMError, get_signature, get_payload_hash
from signing import (
    verify_signature,
    trusted_keys,
    key_fingerprint,
    is_trusted,
    KEYS_DIR,
)

OPT_APPS = Path("/opt/visionlinux/apps")
REGISTRY = Path("/var/lib/visionlinux/npm/registry.json")
LOG_FILE = Path("/var/log/visionlinux/nickman.log")
SYMLINKS = Path("/usr/bin")


def _log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[nickman] {msg}\n")


def _read_registry() -> list[dict]:
    try:
        return json.loads(REGISTRY.read_text())
    except (OSError, json.JSONDecodeError):
        return []


def _write_registry(data: list[dict]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _as_root(args: list[str]) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            ["pkexec"] + args,
            capture_output=True, text=True, timeout=300,
        )
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        # Fallback: try sudo
        r = subprocess.run(
            ["sudo"] + args,
            capture_output=True, text=True, timeout=300,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"


def _is_live() -> bool:
    return sys.platform != "win32" and Path("/etc/visionlinux").exists()


def _extract_app(pkg_path: Path, dest: Path) -> None:
    with tarfile.open(pkg_path, "r:*") as tar:
        members = []
        for m in tar.getmembers():
            if m.name.startswith("app/"):
                fn = m.name[len("app/"):]
                m.name = fn
                members.append(m)
        tar.extractall(dest, members=members)


def _install_desktop_icon(manifest: dict, app_dir: Path) -> None:
    desktop_file = manifest.get("desktop")
    # Support both Russian and English desktop paths
    desktop_dir = Path.home() / "Desktop"
    if not desktop_dir.exists():
        desktop_dir = Path.home() / "Рабочий стол"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    target = desktop_dir / f"{manifest['name']}.desktop"
    if desktop_file:
        src = app_dir / desktop_file
        if src.exists():
            shutil.copy2(src, target)
            return
    target.write_text(
        "[Desktop Entry]\nType=Application\n"
        f"Name={manifest.get('display_name', manifest['name'])}\n"
        f"Exec={manifest.get('entry') or manifest['name']}\n"
        "Terminal=false\nCategories=Application;\n",
        encoding="utf-8",
    )


# ------------------------------------------------------------------ install
def install(pkg_path: Path) -> int:
    if not pkg_path.exists():
        print(f"File not found: {pkg_path}")
        return 2

    print(f"[1/4] Reading package {pkg_path.name}")
    try:
        pkg = load(pkg_path)
    except NPMError as exc:
        print(f"Rejected: {exc}")
        return 1

    print(f"[2/4] Verifying signature")
    sig = get_signature(pkg)
    payload_hash = get_payload_hash(pkg)
    manifest_bytes = json.dumps(pkg.manifest, indent=2, ensure_ascii=False).encode()

    if sig is None:
        print("Package rejected: no signature (NPM_UNSIGNED)")
        _log(f"REJECTED unsigned: {pkg_path.name}")
        return 3

    ok = False
    for key_path in trusted_keys():
        pub = key_path.read_bytes()
        if verify_signature(payload_hash, manifest_bytes, sig, pub):
            ok = True
            fp = key_fingerprint(pub)
            print(f"  Trusted key: {key_path.name} [{fp}]")
            break

    if not ok:
        print("Package rejected: signature not verified (NPM_UNTRUSTED)")
        _log(f"REJECTED untrusted: {pkg_path.name}")
        return 3

    print(f"[3/4] Requesting root access")
    if _is_live():
        code, _, err = _as_root(["mkdir", "-p", str(OPT_APPS)])
        if code != 0:
            print(f"Failed to create directory: {err}")
            return 4
    else:
        print("  (demo mode — no root needed)")

    name = pkg.name()
    dest = OPT_APPS / name
    registry = _read_registry()
    registry = [r for r in registry if r.get("name") != name]

    if _is_live():
        _as_root(["rm", "-rf", str(dest)])
        _as_root(["mkdir", "-p", str(dest)])
        _extract_app(pkg_path, dest)

        entry = pkg.manifest.get("entry")
        if entry:
            _as_root(["ln", "-sf", str(dest / entry), str(SYMLINKS / name)])

        registry.append({
            "name": name,
            "version": pkg.version(),
            "display_name": pkg.manifest.get("display_name", name),
            "entry": pkg.manifest.get("entry"),
            "source": str(pkg_path),
        })
        _write_registry(registry)
        _install_desktop_icon(pkg.manifest, dest)
    else:
        demo = Path(tempfile.gettempdir()) / "visionlinux-demo" / name
        demo.mkdir(parents=True, exist_ok=True)
        _extract_app(pkg_path, demo)
        print(f"  (demo) installed to {demo}")

    print(f"[4/4] Installed: {name} v{pkg.version()}")
    _log(f"INSTALLED: {name} v{pkg.version()} from {pkg_path.name}")
    return 0


# ------------------------------------------------------------------ remove
def remove(name: str) -> int:
    if _is_live():
        _as_root(["rm", "-rf", str(OPT_APPS / name)])
        _as_root(["rm", "-f", str(SYMLINKS / name)])
        registry = _read_registry()
        registry = [r for r in registry if r.get("name") != name]
        _write_registry(registry)
    print(f"Removed: {name}")
    _log(f"REMOVED: {name}")
    return 0


# ------------------------------------------------------------------ list
def list_apps() -> int:
    if _is_live():
        registry = _read_registry()
    else:
        demo = Path(tempfile.gettempdir()) / "visionlinux-demo"
        registry = [{"name": d.name, "version": "demo", "display_name": d.name}
                    for d in demo.iterdir()] if demo.exists() else []

    if not registry:
        print("No installed NPM packages.")
    else:
        print(f"Installed packages ({len(registry)}):")
        for app in registry:
            print(f"  {app.get('display_name', app['name'])}  v{app.get('version', '?')}")
    return 0


# ------------------------------------------------------------------ verify
def verify_only(pkg_path: Path) -> int:
    try:
        pkg = load(pkg_path)
    except NPMError as exc:
        print(f"Rejected: {exc}")
        return 1

    sig = get_signature(pkg)
    payload_hash = get_payload_hash(pkg)
    manifest_bytes = json.dumps(pkg.manifest, indent=2, ensure_ascii=False).encode()

    if sig is None:
        print("UNSIGNED — package rejected")
        return 3

    for key_path in trusted_keys():
        pub = key_path.read_bytes()
        if verify_signature(payload_hash, manifest_bytes, sig, pub):
            fp = key_fingerprint(pub)
            print(f"SIGNED — trusted key: {key_path.name} [{fp}]")
            return 0

    print("UNTRUSTED — signature not verified")
    return 3


# ------------------------------------------------------------------ keys
def keys() -> int:
    if not KEYS_DIR.exists():
        print("No trusted keys installed.")
        return 0
    klist = trusted_keys()
    if not klist:
        print("No trusted keys found.")
        return 0
    print(f"Trusted keys ({len(klist)}):")
    for p in klist:
        fp = key_fingerprint(p.read_bytes())
        print(f"  {p.name}  {fp}")
    return 0


# ------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nickman", description="Vision Linux NPM manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("install", help="Install NPM package")
    p.add_argument("file")
    p.set_defaults(func=lambda a: install(Path(a.file)))

    p = sub.add_parser("remove", help="Remove installed application")
    p.add_argument("name")
    p.set_defaults(func=lambda a: remove(a.name))

    p = sub.add_parser("list", help="List installed packages")
    p.set_defaults(func=lambda a: list_apps())

    p = sub.add_parser("verify", help="Verify package signature")
    p.add_argument("file")
    p.set_defaults(func=lambda a: verify_only(Path(a.file)))

    p = sub.add_parser("keys", help="Show trusted keys")
    p.set_defaults(func=lambda a: keys())

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

"""Ed25519 signing and verification for NPM packages.

Uses the `cryptography` library if present, otherwise falls back to the
`nacl` binding. Signing must never silently fail into an unsigned package.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
    _BACKEND = "cryptography"
except ImportError:
    try:
        import nacl.signing  # noqa: F401
        _BACKEND = "nacl"
    except ImportError:
        _BACKEND = None

KEYS_DIR = Path("/etc/visionlinux/keys")


def _build_message(payload: bytes, manifest: bytes) -> bytes:
    return hashlib.sha256(manifest + b"\x00" + payload).digest()


def sign_file(payload: bytes, manifest: bytes, private_key_pem: bytes) -> bytes:
    if _BACKEND is None:
        raise RuntimeError("No crypto backend (install cryptography or pynacl)")
    if _BACKEND == "cryptography":
        key = load_pem_private_key(private_key_pem, password=None)
        return key.sign(_build_message(payload, manifest))
    import nacl.signing
    key = nacl.signing.SigningKey(private_key_pem)
    return bytes(key.sign(_build_message(payload, manifest)).signature)


def verify_signature(payload: bytes, manifest: bytes, signature: bytes,
                     public_key_pem: bytes) -> bool:
    if _BACKEND is None:
        raise RuntimeError("No crypto backend (install cryptography or pynacl)")
    try:
        if _BACKEND == "cryptography":
            key = load_pem_public_key(public_key_pem)
            key.verify(signature, _build_message(payload, manifest))
            return True
        import nacl.signing
        key = nacl.signing.VerifyKey(public_key_pem)
        key.verify(_build_message(payload, manifest), signature)
        return True
    except Exception:
        return False


def key_fingerprint(public_key_pem: bytes) -> str:
    h = hashlib.sha256(public_key_pem).hexdigest()
    return " ".join(h[i:i + 4] for i in range(0, 64, 4))


def trusted_keys() -> list[Path]:
    if not KEYS_DIR.exists():
        return []
    return sorted(KEYS_DIR.glob("*.pub"))


def is_trusted(public_key_pem: bytes) -> bool:
    for key_path in trusted_keys():
        if key_path.read_bytes() == public_key_pem:
            return True
    return False

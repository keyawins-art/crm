"""
Symmetric encryption for sensitive fields stored at rest (e.g. integration
credentials, API keys).

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the ``cryptography`` package,
which is already a project dependency.

The encryption key is read from the ``ENCRYPTION_KEY`` environment variable.
Generate one with:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

import json
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    """Return a Fernet instance, raising early if the key is missing."""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. Integration credential encryption "
            "requires this env var. Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode())


def encrypt_json(data: Dict[str, Any]) -> str:
    """Serialize ``data`` to JSON and return a Fernet-encrypted string."""
    plaintext = json.dumps(data).encode("utf-8")
    return _get_fernet().encrypt(plaintext).decode("utf-8")


def decrypt_json(ciphertext: str) -> Dict[str, Any]:
    """Decrypt a Fernet ciphertext and return the parsed JSON dict."""
    try:
        plaintext = _get_fernet().decrypt(ciphertext.encode("utf-8"))
        return json.loads(plaintext)
    except InvalidToken:
        raise ValueError(
            "Failed to decrypt integration credentials. "
            "The ENCRYPTION_KEY may have changed or the data is corrupted."
        )


def encrypt_json_safe(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """Encrypt if data is non-empty, else return None."""
    if not data:
        return None
    return encrypt_json(data)


def decrypt_json_safe(ciphertext: Optional[str]) -> Dict[str, Any]:
    """Decrypt if ciphertext is non-empty, else return empty dict."""
    if not ciphertext:
        return {}
    return decrypt_json(ciphertext)

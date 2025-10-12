"""Security helpers for the accounts app."""
from __future__ import annotations

import base64
import os
from functools import lru_cache
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


ENCRYPTED_EMAIL_NONCE_SIZE = 12  # AES-GCM recommended nonce length


class EmailCipherError(RuntimeError):
    """Raised when an email cannot be encrypted or decrypted."""


@lru_cache(maxsize=1)
def _load_email_encryption_key() -> bytes:
    """Return the AES-256 key used for email encryption."""
    raw_key = getattr(settings, "ACCOUNT_EMAIL_ENCRYPTION_KEY", None)
    if not raw_key:
        raise EmailCipherError("ACCOUNT_EMAIL_ENCRYPTION_KEY is not configured")

    if isinstance(raw_key, bytes):
        key_bytes = raw_key
    else:
        try:
            key_bytes = base64.urlsafe_b64decode(raw_key)
        except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
            raise EmailCipherError("ACCOUNT_EMAIL_ENCRYPTION_KEY must be base64 encoded") from exc

    if len(key_bytes) != 32:
        raise EmailCipherError("ACCOUNT_EMAIL_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key_bytes


def encrypt_email(value: str) -> bytes:
    """Encrypt an email address using AES-256-GCM."""
    if value == "":
        return b""

    key = _load_email_encryption_key()
    nonce = os.urandom(ENCRYPTED_EMAIL_NONCE_SIZE)
    aes = AESGCM(key)
    ciphertext = aes.encrypt(nonce, value.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_email(encrypted: Optional[bytes]) -> str:
    """Decrypt an email address encrypted with :func:`encrypt_email`."""
    if not encrypted:
        return ""

    key = _load_email_encryption_key()
    nonce = encrypted[:ENCRYPTED_EMAIL_NONCE_SIZE]
    ciphertext = encrypted[ENCRYPTED_EMAIL_NONCE_SIZE:]
    aes = AESGCM(key)
    try:
        plaintext = aes.decrypt(nonce, ciphertext, None)
    except Exception as exc:  # pragma: no cover - tampering/invalid data guard
        raise EmailCipherError("Encrypted email payload could not be decrypted") from exc
    return plaintext.decode("utf-8")
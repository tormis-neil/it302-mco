"""
Email Encryption Utilities for MCO 1 Academic Project

This module implements AES-256-GCM encryption for user email addresses to demonstrate
secure data storage techniques. It provides encryption, decryption, and digest generation
for email addresses stored in the database.

Security Features:
- AES-256-GCM: Authenticated encryption with 256-bit keys
- Unique nonce/IV for each encryption operation (12 bytes)
- SHA-256 digest for email lookups and uniqueness checks
- Base64 encoding for database storage

Academic Purpose:
This implementation demonstrates encryption/decryption concepts for MCO 1.
For production systems, consider:
- Hardware Security Modules (HSM) for key storage
- Key rotation mechanisms
- External key management services (AWS KMS, HashiCorp Vault)
- Database-level encryption
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailEncryptionError(Exception):
    """Base exception for email encryption/decryption errors."""
    pass


class MissingEncryptionKeyError(EmailEncryptionError):
    """Raised when encryption key is not configured."""
    pass


class DecryptionFailedError(EmailEncryptionError):
    """Raised when email decryption fails (corrupted data, wrong key, etc.)."""
    pass


def get_encryption_key() -> bytes:
    """
    Retrieve and validate the encryption key from settings.

    Returns:
        bytes: 32-byte encryption key for AES-256

    Raises:
        MissingEncryptionKeyError: If key is not configured or invalid

    Note:
        The key must be base64-encoded in settings and decode to exactly 32 bytes.
    """
    key_b64 = getattr(settings, 'ACCOUNT_EMAIL_ENCRYPTION_KEY', None)

    if not key_b64:
        logger.error("ACCOUNT_EMAIL_ENCRYPTION_KEY not found in settings")
        raise MissingEncryptionKeyError(
            "Email encryption key not configured. "
            "Set ACCOUNT_EMAIL_ENCRYPTION_KEY in settings or .env file."
        )

    try:
        key = base64.b64decode(key_b64)
    except Exception as e:
        logger.error(f"Failed to decode encryption key: {e}")
        raise MissingEncryptionKeyError(
            f"Invalid encryption key format (must be base64): {e}"
        )

    if len(key) != 32:
        logger.error(f"Invalid key length: {len(key)} bytes (expected 32)")
        raise MissingEncryptionKeyError(
            f"Encryption key must be 32 bytes (256 bits), got {len(key)} bytes"
        )

    return key


def encrypt_email(email: str) -> bytes:
    """
    Encrypt an email address using AES-256-GCM.

    This function:
    1. Normalizes email to lowercase for case-insensitive handling
    2. Generates a unique 12-byte nonce (IV) for this encryption
    3. Encrypts the email using AES-256-GCM (authenticated encryption)
    4. Prepends the nonce to the ciphertext for storage

    Why AES-256-GCM?
    - AES-256: Industry-standard symmetric encryption with 256-bit keys
    - GCM mode: Provides both confidentiality AND authenticity
    - Authentication tag prevents tampering with encrypted data
    - NIST approved and widely supported

    Args:
        email: Plaintext email address to encrypt

    Returns:
        bytes: Encrypted email (nonce + ciphertext + auth_tag)
               Format: [12 bytes nonce][variable length ciphertext+tag]

    Raises:
        EmailEncryptionError: If encryption fails
        MissingEncryptionKeyError: If encryption key not configured

    Example:
        >>> encrypted = encrypt_email("user@example.com")
        >>> len(encrypted) > 12  # At least nonce + ciphertext
        True
    """
    try:
        # Normalize email to lowercase for consistent encryption/lookups
        normalized_email = email.lower().strip()

        # Get the encryption key
        key = get_encryption_key()

        # Create AESGCM cipher with 256-bit key
        aesgcm = AESGCM(key)

        # Generate a unique nonce (IV) for this encryption
        # CRITICAL: Never reuse a nonce with the same key!
        # 96 bits (12 bytes) is standard for GCM mode
        import os
        nonce = os.urandom(12)  # 96 bits = 12 bytes

        # Encrypt the email
        # GCM automatically adds authentication tag to ciphertext
        ciphertext = aesgcm.encrypt(
            nonce,
            normalized_email.encode('utf-8'),
            None  # No additional authenticated data (AAD)
        )

        # Store nonce with ciphertext (needed for decryption)
        # Format: [nonce][ciphertext+tag]
        encrypted_data = nonce + ciphertext

        logger.debug(f"Successfully encrypted email (length: {len(encrypted_data)} bytes)")
        return encrypted_data

    except MissingEncryptionKeyError:
        raise  # Re-raise key errors as-is
    except Exception as e:
        logger.error(f"Email encryption failed: {e}")
        raise EmailEncryptionError(f"Failed to encrypt email: {e}")


def decrypt_email(encrypted_data: bytes) -> str:
    """
    Decrypt an email address encrypted with AES-256-GCM.

    This function:
    1. Extracts the nonce from the first 12 bytes
    2. Extracts the ciphertext+tag from remaining bytes
    3. Decrypts using AES-256-GCM
    4. Verifies authentication tag (prevents tampering)
    5. Returns the plaintext email

    Args:
        encrypted_data: Encrypted email bytes (nonce + ciphertext + tag)

    Returns:
        str: Decrypted email address

    Raises:
        DecryptionFailedError: If decryption fails (wrong key, corrupted data, etc.)
        MissingEncryptionKeyError: If encryption key not configured

    Example:
        >>> encrypted = encrypt_email("user@example.com")
        >>> decrypt_email(encrypted)
        'user@example.com'
    """
    try:
        # Validate input
        if not encrypted_data or len(encrypted_data) < 13:
            # Minimum: 12 bytes nonce + 1 byte data
            raise DecryptionFailedError(
                f"Invalid encrypted data: too short ({len(encrypted_data)} bytes)"
            )

        # Get the encryption key
        key = get_encryption_key()

        # Create AESGCM cipher
        aesgcm = AESGCM(key)

        # Extract nonce and ciphertext
        nonce = encrypted_data[:12]  # First 12 bytes
        ciphertext = encrypted_data[12:]  # Remaining bytes (ciphertext + tag)

        # Decrypt and verify authentication tag
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        # Convert bytes back to string
        email = plaintext_bytes.decode('utf-8')

        logger.debug(f"Successfully decrypted email")
        return email

    except MissingEncryptionKeyError:
        raise  # Re-raise key errors as-is
    except Exception as e:
        logger.error(f"Email decryption failed: {e}")
        raise DecryptionFailedError(
            f"Failed to decrypt email (corrupted data or wrong key): {e}"
        )


def generate_email_digest(email: str) -> str:
    """
    Generate a SHA-256 digest of an email for lookups and uniqueness checks.

    Why use a digest?
    - Encrypted emails can't be directly searched or compared
    - Digest provides a deterministic fingerprint for each email
    - SHA-256 is one-way: can't reverse to get original email
    - Allows fast database lookups via indexed digest column
    - Maintains uniqueness constraint on emails

    The digest is NOT for security (emails aren't secret).
    It's for practical database operations with encrypted data.

    Args:
        email: Email address to hash

    Returns:
        str: 64-character hexadecimal SHA-256 digest

    Example:
        >>> generate_email_digest("user@example.com")
        'b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514'
        >>> generate_email_digest("USER@example.com")  # Case-insensitive
        'b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514'
    """
    # Normalize to lowercase for case-insensitive matching
    normalized_email = email.lower().strip()

    # Generate SHA-256 hash
    digest = hashlib.sha256(normalized_email.encode('utf-8')).hexdigest()

    logger.debug(f"Generated email digest: {digest[:16]}...")
    return digest


def generate_encryption_key() -> str:
    """
    Generate a cryptographically secure 32-byte key for AES-256-GCM.

    Returns:
        str: Base64-encoded 256-bit encryption key

    Example:
        >>> key = generate_encryption_key()
        >>> len(base64.b64decode(key))
        32

    Note:
        This key should be stored securely in .env file and NEVER committed to git.
        Back up this key safely - if lost, encrypted emails cannot be recovered!
    """
    import os

    # Generate 32 random bytes (256 bits)
    key_bytes = os.urandom(32)

    # Encode to base64 for storage in environment variable
    key_b64 = base64.b64encode(key_bytes).decode('ascii')

    return key_b64


# Convenience function for testing/demonstration
def test_encryption_roundtrip(email: str = "test@example.com") -> bool:
    """
    Test encryption and decryption with a sample email.

    This is useful for:
    - Verifying encryption key is correctly configured
    - Demonstrating encryption/decryption for MCO 1
    - Debugging encryption issues

    Args:
        email: Test email address (default: test@example.com)

    Returns:
        bool: True if roundtrip successful, False otherwise
    """
    try:
        print(f"\n=== Email Encryption Test ===")
        print(f"Original email: {email}")

        # Encrypt
        encrypted = encrypt_email(email)
        print(f"Encrypted (base64): {base64.b64encode(encrypted).decode()[:50]}...")
        print(f"Encrypted size: {len(encrypted)} bytes")

        # Generate digest
        digest = generate_email_digest(email)
        print(f"SHA-256 digest: {digest}")

        # Decrypt
        decrypted = decrypt_email(encrypted)
        print(f"Decrypted email: {decrypted}")

        # Verify
        success = decrypted.lower() == email.lower()
        print(f"Roundtrip successful: {success}")

        return success

    except Exception as e:
        print(f"Encryption test failed: {e}")
        return False

"""Password obscuring utilities for vaultconfig.

This is NOT encryption! It's designed to prevent casual "shoulder surfing"
of passwords in config files. Anyone with access to this code can decrypt
the passwords.

Uses AES-CTR encryption with a fixed key (similar to rclone's approach).
Note: We use our own unique key, not rclone's key.
"""

from __future__ import annotations

import base64
import os
from typing import Final

try:
    import cryptography  # noqa: F401

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Unique AES key for vaultconfig - provides obfuscation, not security
# This key is unique to vaultconfig (not shared with rclone or pywebdavserver)
_CIPHER_KEY: Final[bytes] = bytes(
    [
        0xA7,
        0x3B,
        0x9F,
        0x2C,
        0xE1,
        0x5D,
        0x4A,
        0x8E,
        0xB6,
        0xF4,
        0xC9,
        0x7A,
        0x3E,
        0x91,
        0x5C,
        0xD2,
        0x8B,
        0x4F,
        0xA3,
        0x6E,
        0x1B,
        0xC5,
        0x7D,
        0x9A,
        0x2F,
        0xE8,
        0x4B,
        0xA6,
        0x3C,
        0xD1,
        0x5E,
        0x92,
    ]
)

# AES block size
_AES_BLOCK_SIZE: Final[int] = 16


def _crypt(data: bytes, iv: bytes) -> bytes:
    """AES-CTR encryption/decryption (same operation for both).

    Args:
        data: Data to encrypt/decrypt
        iv: Initialization vector (16 bytes)

    Returns:
        Encrypted/decrypted data

    Raises:
        ImportError: If cryptography library not available
    """
    if not HAS_CRYPTOGRAPHY:
        raise ImportError(
            "Password obscuring requires 'cryptography' library. "
            "Install it with: pip install cryptography"
        )

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    cipher = Cipher(
        algorithms.AES(_CIPHER_KEY), modes.CTR(iv), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()


def obscure(password: str) -> str:
    """Obscure a password using AES-CTR + base64 encoding.

    Args:
        password: Plain text password to obscure

    Returns:
        Base64-encoded obscured password (URL-safe, no padding)

    Examples:
        >>> obscure("mypassword123")
        'FZq5EuI...'  # Random IV makes output different each time
    """
    if not password:
        return ""

    plaintext = password.encode("utf-8")

    # Create random IV (initialization vector)
    iv = os.urandom(_AES_BLOCK_SIZE)

    # Encrypt with AES-CTR
    ciphertext = _crypt(plaintext, iv)

    # Prepend IV to ciphertext
    result = iv + ciphertext

    # Encode to base64 (URL-safe, no padding)
    return base64.urlsafe_b64encode(result).decode("ascii").rstrip("=")


def reveal(obscured_password: str) -> str:
    """Reveal an obscured password.

    Args:
        obscured_password: Base64-encoded obscured password

    Returns:
        Plain text password

    Raises:
        ValueError: If the obscured password is invalid
    """
    if not obscured_password:
        return ""

    try:
        # Add padding if needed for base64 decoding
        padding = (4 - len(obscured_password) % 4) % 4
        obscured_password_padded = obscured_password + "=" * padding

        # Decode from base64
        ciphertext = base64.urlsafe_b64decode(obscured_password_padded.encode("ascii"))

        # Check minimum length (IV + at least 1 byte)
        if len(ciphertext) < _AES_BLOCK_SIZE:
            raise ValueError("Input too short - is it obscured?")

        # Extract IV and encrypted data
        iv = ciphertext[:_AES_BLOCK_SIZE]
        encrypted = ciphertext[_AES_BLOCK_SIZE:]

        # Decrypt with AES-CTR
        plaintext = _crypt(encrypted, iv)

        return plaintext.decode("utf-8")
    except ImportError as e:
        raise ImportError(str(e)) from e
    except Exception as e:
        raise ValueError(f"Failed to reveal password - is it obscured? {e}") from e


def is_obscured(value: str) -> bool:
    """Check if a string appears to be an obscured password.

    This is a heuristic check - it tries to decode and reveal the value.
    If it succeeds and produces reasonable output, it's likely obscured.

    Args:
        value: String to check

    Returns:
        True if the value appears to be obscured
    """
    if not value or not HAS_CRYPTOGRAPHY:
        return False

    try:
        revealed = reveal(value)
        # If we can reveal it and it's printable, it's likely obscured
        return revealed.isprintable()
    except Exception:
        return False

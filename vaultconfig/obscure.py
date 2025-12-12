"""Password obscuring utilities for vaultconfig.

SECURITY WARNING: This is NOT encryption!

This module provides OBFUSCATION ONLY to prevent casual "shoulder surfing"
of passwords in config files. Anyone with access to this code can decrypt
the passwords.

DO NOT USE THIS FOR SECURITY:
- The encryption key is hardcoded in this module
- Anyone with access to vaultconfig can decrypt obscured passwords
- This provides NO protection against anyone who can read your config files
- For real security, use the encrypt/decrypt functionality in crypt.py

This is similar to rclone's password obscuring approach.
Note: We use our own unique key, not rclone's key.

Use cases for obscuring:
- Prevent casual viewing of passwords in config files
- Avoid passwords appearing in plain text in logs/screenshots
- Basic protection in shared development environments

For production security requirements, use proper encryption instead.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Final

logger = logging.getLogger(__name__)

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

# Track if security warning has been shown (to avoid spamming)
_SECURITY_WARNING_SHOWN: bool = False


class Obscurer:
    """Obscurer instance with configurable cipher key.

    This class allows applications to use their own cipher key instead of the
    default hardcoded key, providing better protection against casual revelation.

    SECURITY WARNING: This is still obfuscation, NOT encryption!
    Even with a custom key, anyone with access to your application code and the
    custom key can decrypt the passwords. For real security, use the encrypt/decrypt
    functionality in vaultconfig.crypt instead.

    Attributes:
        _cipher_key: The AES key used for obscuring/revealing
        _security_warning_shown: Track if warning has been shown for this instance

    Examples:
        >>> # Use custom key
        >>> import secrets
        >>> custom_key = secrets.token_bytes(32)
        >>> obscurer = Obscurer(cipher_key=custom_key)
        >>> obscured = obscurer.obscure("mypassword")
        >>> revealed = obscurer.reveal(obscured)
        >>> revealed == "mypassword"
        True

        >>> # Use default key
        >>> obscurer = Obscurer()
        >>> obscured = obscurer.obscure("mypassword")
    """

    def __init__(self, cipher_key: bytes | None = None) -> None:
        """Initialize with custom or default cipher key.

        Args:
            cipher_key: 32-byte AES key (if None, uses default hardcoded key)

        Raises:
            ValueError: If cipher_key is not exactly 32 bytes
        """
        if cipher_key is not None:
            if not isinstance(cipher_key, bytes):
                raise TypeError("cipher_key must be bytes")
            if len(cipher_key) != 32:
                raise ValueError(
                    f"Cipher key must be exactly 32 bytes, got {len(cipher_key)}"
                )
            self._cipher_key = cipher_key
        else:
            self._cipher_key = _CIPHER_KEY

        self._security_warning_shown = False

    def _crypt(self, data: bytes, iv: bytes) -> bytes:
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
            algorithms.AES(self._cipher_key), modes.CTR(iv), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()

    def obscure(self, password: str) -> str:
        """Obscure a password using AES-CTR + base64 encoding.

        SECURITY WARNING: This is obfuscation, NOT encryption!

        This function uses a cipher key (either custom or default) that anyone with
        access to your application can use to decrypt the password. For real security,
        use the encrypt/decrypt functionality in vaultconfig.crypt instead.

        Args:
            password: Plain text password to obscure

        Returns:
            Base64-encoded obscured password (URL-safe, no padding)

        Examples:
            >>> obscurer = Obscurer()
            >>> obscurer.obscure("mypassword123")
            'FZq5EuI...'  # Random IV makes output different each time
        """
        # Warn users on first use (only once per instance)
        if not self._security_warning_shown:
            logger.warning(
                "SECURITY: obscure() provides obfuscation only, not encryption. "
                "Anyone with access to vaultconfig and your cipher key can decrypt "
                "obscured passwords. For real security, "
                "use vaultconfig.crypt.encrypt() instead."
            )
            self._security_warning_shown = True

        if not password:
            return ""

        plaintext = password.encode("utf-8")

        # Create random IV (initialization vector)
        iv = os.urandom(_AES_BLOCK_SIZE)

        # Encrypt with AES-CTR
        ciphertext = self._crypt(plaintext, iv)

        # Prepend IV to ciphertext
        result = iv + ciphertext

        # Encode to base64 (URL-safe, no padding)
        return base64.urlsafe_b64encode(result).decode("ascii").rstrip("=")

    def reveal(self, obscured_password: str) -> str:
        """Reveal an obscured password.

        NOTE: This demonstrates that obscured passwords provide NO real security.
        Anyone with access to your application and cipher key can reveal
        obscured passwords.

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
            ciphertext = base64.urlsafe_b64decode(
                obscured_password_padded.encode("ascii")
            )

            # Check minimum length (IV + at least 1 byte)
            if len(ciphertext) < _AES_BLOCK_SIZE:
                raise ValueError("Input too short - is it obscured?")

            # Extract IV and encrypted data
            iv = ciphertext[:_AES_BLOCK_SIZE]
            encrypted = ciphertext[_AES_BLOCK_SIZE:]

            # Decrypt with AES-CTR
            plaintext = self._crypt(encrypted, iv)

            return plaintext.decode("utf-8")
        except ImportError as e:
            raise ImportError(str(e)) from e
        except Exception as e:
            raise ValueError(f"Failed to reveal password - is it obscured? {e}") from e

    def is_obscured(self, value: str) -> bool:
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
            revealed = self.reveal(value)
            # If we can reveal it and it's printable, it's likely obscured
            return revealed.isprintable()
        except Exception:
            return False


# Helper functions for creating Obscurer instances


def create_obscurer_from_hex(hex_key: str) -> Obscurer:
    """Create obscurer from hex-encoded cipher key.

    Args:
        hex_key: Hex-encoded 32-byte key (64 hex characters)

    Returns:
        Obscurer instance with the specified key

    Raises:
        ValueError: If hex_key is not valid or wrong length

    Examples:
        >>> hex_key = "a73b9f2ce15d4a8eb6f4c97a3e915cd28b4fa36e1bc57d9a2fe84ba63cd15e92"
        >>> obscurer = create_obscurer_from_hex(hex_key)
        >>> obscured = obscurer.obscure("password")
    """
    try:
        key_bytes = bytes.fromhex(hex_key)
    except ValueError as e:
        raise ValueError(f"Invalid hex key: {e}") from e

    if len(key_bytes) != 32:
        raise ValueError(
            f"Hex key must decode to exactly 32 bytes, got {len(key_bytes)} bytes"
        )

    return Obscurer(cipher_key=key_bytes)


def create_obscurer_from_passphrase(passphrase: str) -> Obscurer:
    """Create obscurer from a passphrase (hashed to 32 bytes using SHA-256).

    This allows you to use a memorable passphrase instead of managing raw bytes.
    The passphrase is hashed to produce a consistent 32-byte key.

    Args:
        passphrase: Passphrase to hash into a cipher key

    Returns:
        Obscurer instance with key derived from passphrase

    Examples:
        >>> obscurer = create_obscurer_from_passphrase("MyApp-Unique-Key-2024")
        >>> obscured = obscurer.obscure("password")
    """
    import hashlib

    if not passphrase:
        raise ValueError("Passphrase cannot be empty")

    key_bytes = hashlib.sha256(passphrase.encode("utf-8")).digest()
    return Obscurer(cipher_key=key_bytes)


def create_obscurer_from_bytes(key_bytes: bytes) -> Obscurer:
    """Create obscurer from raw bytes.

    Args:
        key_bytes: Raw 32-byte key

    Returns:
        Obscurer instance with the specified key

    Raises:
        ValueError: If key_bytes is not exactly 32 bytes

    Examples:
        >>> import secrets
        >>> key_bytes = secrets.token_bytes(32)
        >>> obscurer = create_obscurer_from_bytes(key_bytes)
        >>> obscured = obscurer.obscure("password")
    """
    return Obscurer(cipher_key=key_bytes)


# Default obscurer instance (singleton pattern for backward compatibility)
_DEFAULT_OBSCURER: Obscurer | None = None


def _get_default_obscurer() -> Obscurer:
    """Get or create the default obscurer instance.

    Returns:
        Default Obscurer instance using the hardcoded _CIPHER_KEY
    """
    global _DEFAULT_OBSCURER
    if _DEFAULT_OBSCURER is None:
        _DEFAULT_OBSCURER = Obscurer()  # Uses default _CIPHER_KEY
    return _DEFAULT_OBSCURER


# Module-level functions for backward compatibility
# These use the default obscurer instance internally


def obscure(password: str) -> str:
    """Obscure a password using the default cipher key (AES-CTR + base64 encoding).

    SECURITY WARNING: This is obfuscation, NOT encryption!

    This function uses a hardcoded key that anyone with access to this code
    can use to decrypt the password. For real security, use the encrypt/decrypt
    functionality in vaultconfig.crypt instead.

    For better protection, use the Obscurer class with a custom cipher key.

    Args:
        password: Plain text password to obscure

    Returns:
        Base64-encoded obscured password (URL-safe, no padding)

    Examples:
        >>> obscure("mypassword123")
        'FZq5EuI...'  # Random IV makes output different each time
    """
    return _get_default_obscurer().obscure(password)


def reveal(obscured_password: str) -> str:
    """Reveal an obscured password using the default cipher key.

    NOTE: This demonstrates that obscured passwords provide NO real security.
    Anyone with access to this code can reveal obscured passwords.

    Args:
        obscured_password: Base64-encoded obscured password

    Returns:
        Plain text password

    Raises:
        ValueError: If the obscured password is invalid
    """
    return _get_default_obscurer().reveal(obscured_password)


def is_obscured(value: str) -> bool:
    """Check if a string appears to be an obscured password.

    This is a heuristic check - it tries to decode and reveal the value
    using the default cipher key. If it succeeds and produces reasonable
    output, it's likely obscured.

    Args:
        value: String to check

    Returns:
        True if the value appears to be obscured
    """
    return _get_default_obscurer().is_obscured(value)

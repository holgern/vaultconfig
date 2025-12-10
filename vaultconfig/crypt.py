"""Config file encryption/decryption using NaCl secretbox.

This module provides authenticated encryption for entire configuration files
using the NaCl secretbox construction (XSalsa20 + Poly1305).

Security notes:
- Uses strong authenticated encryption (XSalsa20-Poly1305)
- Password is hashed with SHA-256 and a salt
- Random 24-byte nonce used for each encryption
- No password recovery - lost password means lost data
- Password strength is the user's responsibility
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import os
import subprocess
import sys
from typing import Final

from vaultconfig.exceptions import (
    DecryptionError,
    EncryptionError,
    InvalidPasswordError,
)

try:
    import nacl.secret
    import nacl.utils

    HAS_NACL = True
except ImportError:
    HAS_NACL = False

# Encryption format version marker
ENCRYPTION_HEADER: Final[str] = "VAULTCONFIG_ENCRYPT_V0:"

# NaCl secretbox nonce size (24 bytes for XSalsa20)
NONCE_SIZE: Final[int] = 24

# Salt for password hashing
PASSWORD_SALT: Final[str] = "[vaultconfig-secure]"

# Environment variable names
ENV_PASSWORD: Final[str] = "VAULTCONFIG_PASSWORD"
ENV_PASSWORD_COMMAND: Final[str] = "VAULTCONFIG_PASSWORD_COMMAND"
ENV_PASSWORD_CHANGE: Final[str] = "VAULTCONFIG_PASSWORD_CHANGE"


def _check_nacl_available() -> None:
    """Check if PyNaCl is available.

    Raises:
        ImportError: If PyNaCl is not installed
    """
    if not HAS_NACL:
        raise ImportError(
            "Config file encryption requires 'PyNaCl' library. "
            "Install it with: pip install pynacl"
        )


def derive_key(password: str) -> bytes:
    """Derive encryption key from password using SHA-256.

    Args:
        password: User password

    Returns:
        32-byte encryption key suitable for NaCl secretbox

    Raises:
        ValueError: If password is empty
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Hash password with salt (similar to rclone's approach)
    sha = hashlib.sha256()
    sha.update(f"[{password}]{PASSWORD_SALT}".encode())
    return sha.digest()  # 32 bytes


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt config data using NaCl secretbox.

    Args:
        data: Config data to encrypt
        password: Encryption password

    Returns:
        Encrypted data with header and base64 encoding

    Raises:
        EncryptionError: If encryption fails
        ImportError: If PyNaCl is not installed
    """
    _check_nacl_available()

    try:
        # Derive key from password
        key = derive_key(password)

        # Create NaCl secretbox
        box = nacl.secret.SecretBox(key)

        # Generate random nonce
        nonce = nacl.utils.random(NONCE_SIZE)

        # Encrypt data (secretbox.encrypt appends the nonce automatically)
        # But we want explicit control, so we use encrypt with explicit nonce
        encrypted = box.encrypt(data, nonce)

        # encrypted contains: nonce (24 bytes) + ciphertext + MAC (16 bytes)
        # Encode to base64
        encoded = base64.b64encode(encrypted).decode("ascii")

        # Add version header
        result = f"{ENCRYPTION_HEADER}\n{encoded}\n"

        return result.encode("utf-8")

    except Exception as e:
        raise EncryptionError(f"Failed to encrypt config: {e}") from e


def decrypt(data: bytes, password: str | None = None) -> bytes:
    """Decrypt config data using NaCl secretbox.

    Args:
        data: Encrypted config data (may include header)
        password: Decryption password (if None, will attempt to retrieve)

    Returns:
        Decrypted plaintext data

    Raises:
        DecryptionError: If decryption fails
        InvalidPasswordError: If password is incorrect
        ImportError: If PyNaCl is not installed
    """
    _check_nacl_available()

    try:
        # Decode bytes to string
        text = data.decode("utf-8")

        # Check for encryption header
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        if not lines:
            raise DecryptionError("Empty config data")

        # Check if encrypted
        if not lines[0].startswith("VAULTCONFIG_ENCRYPT_"):
            raise DecryptionError("Config is not encrypted (missing encryption header)")

        # Check version - header should match exactly
        if lines[0] != ENCRYPTION_HEADER.rstrip():
            version = lines[0].split(":")[0] if ":" in lines[0] else "unknown"
            raise DecryptionError(
                f"Unsupported encryption version: {version}. "
                f"Expected {ENCRYPTION_HEADER.rstrip()}"
            )

        # Get encrypted data (everything after header)
        if len(lines) < 2:
            raise DecryptionError("No encrypted data found after header")

        encrypted_b64 = lines[1]

        # Decode base64
        try:
            encrypted_data = base64.b64decode(encrypted_b64)
        except Exception as e:
            raise DecryptionError(f"Invalid base64 encoding: {e}") from e

        # Get password if not provided
        if password is None:
            password = get_password()

        # Derive key
        key = derive_key(password)

        # Create NaCl secretbox
        box = nacl.secret.SecretBox(key)

        # Decrypt (will verify MAC automatically)
        try:
            plaintext = box.decrypt(encrypted_data)
        except nacl.exceptions.CryptoError as e:
            raise InvalidPasswordError("Invalid password or corrupted data") from e

        return plaintext

    except (InvalidPasswordError, DecryptionError):
        raise
    except Exception as e:
        raise DecryptionError(f"Failed to decrypt config: {e}") from e


def is_encrypted(data: bytes) -> bool:
    """Check if config data is encrypted.

    Args:
        data: Config data to check

    Returns:
        True if data appears to be encrypted
    """
    try:
        text = data.decode("utf-8", errors="ignore")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return len(lines) > 0 and lines[0] == ENCRYPTION_HEADER.rstrip()
    except Exception:
        return False


def get_password(prompt: str = "Config password: ", changing: bool = False) -> str:
    """Get password from various sources.

    Tries in order:
    1. Environment variable (VAULTCONFIG_PASSWORD)
    2. Password command (VAULTCONFIG_PASSWORD_COMMAND)
    3. Interactive prompt

    Args:
        prompt: Prompt to show for interactive input
        changing: If True, sets VAULTCONFIG_PASSWORD_CHANGE=1 for password command

    Returns:
        Password string

    Raises:
        ValueError: If password cannot be obtained
    """
    # Try environment variable first
    password = os.environ.get(ENV_PASSWORD)
    if password:
        return password

    # Try password command
    password_cmd = os.environ.get(ENV_PASSWORD_COMMAND)
    if password_cmd:
        try:
            env = os.environ.copy()
            if changing:
                env[ENV_PASSWORD_CHANGE] = "1"

            result = subprocess.run(
                password_cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            password = result.stdout.strip()
            if password:
                return password
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Password command failed: {e}") from e

    # Interactive prompt (only if stdin is a TTY)
    if sys.stdin.isatty():
        password = getpass.getpass(prompt)
        if password:
            return password

    raise ValueError("No password provided and cannot prompt (not a TTY)")


def check_password(password: str) -> tuple[str, list[str]]:
    """Validate and normalize a password.

    Args:
        password: Password to check

    Returns:
        Tuple of (normalized_password, warnings)

    Raises:
        ValueError: If password is invalid
    """
    warnings = []

    # Check if password is valid UTF-8 (already is if we got here)
    if not password:
        raise ValueError("Password cannot be empty")

    # Check for whitespace
    stripped = password.strip()
    if password != stripped:
        warnings.append("Password has leading/trailing whitespace (preserved)")

    # Check for at least one non-whitespace character
    if not stripped:
        raise ValueError("Password must contain at least one non-whitespace character")

    # Unicode normalization (NFKC)
    import unicodedata

    normalized = unicodedata.normalize("NFKC", password)
    if normalized != password:
        warnings.append("Password was normalized using Unicode NFKC")
        password = normalized

    return password, warnings

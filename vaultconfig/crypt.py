"""Config file encryption/decryption using NaCl secretbox.

This module provides authenticated encryption for entire configuration files
using the NaCl secretbox construction (XSalsa20 + Poly1305).

Security notes:
- Uses strong authenticated encryption (XSalsa20-Poly1305)
- Password is derived using PBKDF2-HMAC-SHA256 with 600,000 iterations
- Random 16-byte salt generated for each password (stored with encrypted data)
- Random 24-byte nonce used for each encryption
- No password recovery - lost password means lost data
- Use strong passwords (12+ characters recommended)
"""

from __future__ import annotations

import base64
import getpass
import os
import shlex
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

# Encryption format version marker (V1 uses PBKDF2)
ENCRYPTION_HEADER_V1: Final[str] = "VAULTCONFIG_ENCRYPT_V1:"
# Current version
ENCRYPTION_HEADER: Final[str] = ENCRYPTION_HEADER_V1

# NaCl secretbox nonce size (24 bytes for XSalsa20)
NONCE_SIZE: Final[int] = 24

# PBKDF2 parameters (OWASP recommended 2023+)
PBKDF2_ITERATIONS: Final[int] = 600_000
PBKDF2_SALT_SIZE: Final[int] = 16  # 128 bits

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


def derive_key(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Derive encryption key from password using PBKDF2-HMAC-SHA256.

    Args:
        password: User password
        salt: Salt for key derivation (generates random if None)

    Returns:
        Tuple of (32-byte encryption key, salt used)

    Raises:
        ValueError: If password is empty
        ImportError: If cryptography library not available
    """
    if not password:
        raise ValueError("Password cannot be empty")

    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as e:
        raise ImportError(
            "PBKDF2 key derivation requires 'cryptography' library. "
            "Install it with: pip install cryptography"
        ) from e

    # Generate random salt if not provided
    if salt is None:
        salt = os.urandom(PBKDF2_SALT_SIZE)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes for NaCl
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password.encode("utf-8"))
    return key, salt


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt config data using NaCl secretbox with PBKDF2 key derivation.

    Args:
        data: Config data to encrypt
        password: Encryption password

    Returns:
        Encrypted data with header, salt, and base64 encoding

    Raises:
        EncryptionError: If encryption fails
        ImportError: If PyNaCl is not installed
    """
    _check_nacl_available()

    try:
        # Derive key from password (generates random salt)
        key, salt = derive_key(password)

        # Create NaCl secretbox
        box = nacl.secret.SecretBox(key)

        # Generate random nonce
        nonce = nacl.utils.random(NONCE_SIZE)

        # Encrypt data
        encrypted = box.encrypt(data, nonce)

        # Format: salt (16 bytes) + encrypted (nonce + ciphertext + MAC)
        result_bytes = salt + encrypted

        # Encode to base64
        encoded = base64.b64encode(result_bytes).decode("ascii")

        # Add version header
        result = f"{ENCRYPTION_HEADER}\n{encoded}\n"

        return result.encode("utf-8")

    except Exception as e:
        raise EncryptionError(f"Failed to encrypt config: {e}") from e


def decrypt(data: bytes, password: str | None = None) -> bytes:
    """Decrypt config data using NaCl secretbox with PBKDF2 key derivation.

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

        # Check version
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

        # Extract salt
        if len(encrypted_data) < PBKDF2_SALT_SIZE:
            raise DecryptionError("Encrypted data too short (missing salt)")

        salt = encrypted_data[:PBKDF2_SALT_SIZE]
        encrypted_data = encrypted_data[PBKDF2_SALT_SIZE:]

        # Get password if not provided
        if password is None:
            password = get_password()

        # Derive key using PBKDF2
        key, _ = derive_key(password, salt=salt)

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

            # SECURITY: Use shlex.split() to safely parse command
            # This prevents shell injection while still allowing complex commands
            # Note: Use posix=True on all platforms because:
            # - It properly handles quoted arguments and strips quotes
            # - Works correctly with subprocess.run(..., shell=False)
            # - Handles both Windows and Unix paths when properly quoted
            cmd_args = shlex.split(password_cmd, posix=True)

            result = subprocess.run(
                cmd_args,
                shell=False,  # SECURITY: Never use shell=True with user input
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
        except ValueError as e:
            raise ValueError(f"Invalid password command format: {e}") from e

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

    # Check if password is empty
    if not password:
        raise ValueError("Password cannot be empty")

    # Check for whitespace
    stripped = password.strip()
    if password != stripped:
        warnings.append("Password has leading/trailing whitespace (preserved)")

    # Check for at least one non-whitespace character
    if not stripped:
        raise ValueError("Password must contain at least one non-whitespace character")

    # SECURITY: Minimum password length is 4 characters (bare minimum)
    if len(stripped) < 4:
        raise ValueError(
            "Password must be at least 4 characters long. "
            "For better security, use 12+ characters."
        )

    # SECURITY: Warn about short passwords (recommended minimum is 12 characters)
    if len(stripped) < 12:
        warnings.append(
            "Password is shorter than recommended 12 characters. "
            "Consider using a longer passphrase or password manager."
        )

    # SECURITY: Warn about common weak passwords
    common_passwords = {
        "password",
        "123456",
        "123456789",
        "12345678",
        "12345",
        "1234567",
        "password123",
        "admin",
        "secret",
        "letmein",
        "welcome",
        "qwerty",
    }
    if stripped.lower() in common_passwords:
        warnings.append(
            "Password appears to be a common/weak password. "
            "Consider choosing a stronger, unique password."
        )

    # Unicode normalization (NFKC)
    import unicodedata

    normalized = unicodedata.normalize("NFKC", password)
    if normalized != password:
        warnings.append("Password was normalized using Unicode NFKC")
        password = normalized

    return password, warnings

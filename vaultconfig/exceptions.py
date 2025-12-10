"""Custom exceptions for vaultconfig."""

from __future__ import annotations


class VaultConfigError(Exception):
    """Base exception for all vaultconfig errors."""

    pass


class EncryptionError(VaultConfigError):
    """Raised when encryption fails."""

    pass


class DecryptionError(VaultConfigError):
    """Raised when decryption fails."""

    pass


class InvalidPasswordError(DecryptionError):
    """Raised when password is incorrect for decryption."""

    pass


class FormatError(VaultConfigError):
    """Raised when config format is invalid or unsupported."""

    pass


class SchemaValidationError(VaultConfigError):
    """Raised when config data fails schema validation."""

    pass


class ConfigNotFoundError(VaultConfigError):
    """Raised when requested config does not exist."""

    pass


class ConfigExistsError(VaultConfigError):
    """Raised when trying to create a config that already exists."""

    pass

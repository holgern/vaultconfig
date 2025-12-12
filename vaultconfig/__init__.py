"""VaultConfig - Secure configuration management library.

VaultConfig provides easy-to-use configuration management with support for:
- Multiple formats (TOML, INI, YAML)
- Password obscuring for sensitive fields
- Full config file encryption (NaCl secretbox)
- Schema validation with Pydantic
- CLI tool for config management
"""

from __future__ import annotations

from vaultconfig import crypt, obscure
from vaultconfig.config import ConfigEntry, ConfigManager
from vaultconfig.exceptions import (
    ConfigExistsError,
    ConfigNotFoundError,
    DecryptionError,
    EncryptionError,
    FormatError,
    InvalidPasswordError,
    SchemaValidationError,
    VaultConfigError,
)
from vaultconfig.obscure import (
    Obscurer,
    create_obscurer_from_bytes,
    create_obscurer_from_hex,
    create_obscurer_from_passphrase,
)
from vaultconfig.schema import ConfigSchema, FieldDef, create_simple_schema

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "ConfigManager",
    "ConfigEntry",
    "ConfigSchema",
    "FieldDef",
    # Obscurer classes and functions
    "Obscurer",
    "create_obscurer_from_hex",
    "create_obscurer_from_passphrase",
    "create_obscurer_from_bytes",
    # Functions
    "create_simple_schema",
    # Modules
    "crypt",
    "obscure",
    # Exceptions
    "VaultConfigError",
    "EncryptionError",
    "DecryptionError",
    "InvalidPasswordError",
    "FormatError",
    "SchemaValidationError",
    "ConfigNotFoundError",
    "ConfigExistsError",
]

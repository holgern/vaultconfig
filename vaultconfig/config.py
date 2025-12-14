"""Configuration management for vaultconfig."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from vaultconfig import crypt, obscure
from vaultconfig.exceptions import (
    ConfigNotFoundError,
    EncryptionError,
    FormatError,
)
from vaultconfig.formats import INIFormat, TOMLFormat, YAMLFormat
from vaultconfig.formats.base import ConfigFormat
from vaultconfig.schema import ConfigSchema

logger = logging.getLogger(__name__)

# Registry of available formats
_FORMAT_REGISTRY: dict[str, type[ConfigFormat]] = {
    "toml": TOMLFormat,
    "ini": INIFormat,
    "yaml": YAMLFormat,
}


def _secure_write_file(path: Path, data: bytes) -> None:
    """Write file atomically with secure permissions.

    This function:
    1. Creates temp file with secure permissions (0o600) from the start
    2. Writes data to temp file
    3. Atomically renames temp file to final path
    4. Securely deletes temp file on error

    Args:
        path: Target file path
        data: Data to write

    Raises:
        OSError: If write or rename fails
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory (for atomic rename on same filesystem)
    temp_fd = None
    temp_path = None

    try:
        # SECURITY: Create temp file with secure permissions (0o600) from the start
        # This prevents race condition where file is created with default perms
        temp_fd = tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,  # We'll handle deletion manually
        )
        temp_path = Path(temp_fd.name)

        # Set secure permissions immediately (defense in depth)
        os.chmod(temp_fd.name, 0o600)

        # Write data
        temp_fd.write(data)
        temp_fd.flush()
        os.fsync(temp_fd.fileno())  # Ensure data is written to disk
        temp_fd.close()

        # Atomic rename (overwrites existing file)
        # os.replace() works atomically on both Windows and POSIX
        os.replace(temp_fd.name, path)
        temp_path = None  # Successfully renamed, don't delete

    except Exception as e:
        # SECURITY: Attempt secure deletion of temp file on error
        if temp_path and temp_path.exists():
            try:
                # Overwrite with zeros before deleting (basic secure deletion)
                size = temp_path.stat().st_size
                with open(temp_path, "wb") as f:
                    f.write(b"\x00" * size)
                    f.flush()
                    os.fsync(f.fileno())
                temp_path.unlink()
            except Exception as del_error:
                logger.warning(
                    f"Failed to securely delete temp file {temp_path}: {del_error}"
                )
        raise OSError(f"Failed to write file {path}: {e}") from e
    finally:
        if temp_fd and not temp_fd.closed:
            temp_fd.close()


class ConfigEntry:
    """Configuration entry with metadata."""

    def __init__(
        self,
        name: str,
        data: dict[str, Any],
        sensitive_fields: set[str] | None = None,
        obscurer: obscure.Obscurer | None = None,
    ) -> None:
        """Initialize config entry.

        Args:
            name: Config entry name
            data: Configuration data
            sensitive_fields: Set of field names that are sensitive (will be obscured)
            obscurer: Obscurer instance for password obscuring/revealing
            (uses default if None)
        """
        self.name = name
        self._data = data
        self._sensitive_fields = sensitive_fields or set()
        self._obscurer = obscurer if obscurer is not None else obscure.Obscurer()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value, revealing obscured passwords if needed.

        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value (with passwords revealed if obscured)
        """
        # Support dot notation for nested keys
        keys = key.split(".")
        value: Any = self._data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        # Reveal obscured passwords for sensitive fields
        if isinstance(value, str) and key in self._sensitive_fields:
            try:
                return self._obscurer.reveal(value)
            except ValueError:
                # Not obscured, return as-is
                return value

        return value

    def get_all(self, reveal_secrets: bool = True) -> dict[str, Any]:
        """Get all configuration values.

        Args:
            reveal_secrets: If True, reveal obscured passwords

        Returns:
            Dictionary of all configuration values
        """
        if not reveal_secrets:
            return self._data.copy()

        result: dict[str, Any] = {}
        for key, value in self._data.items():
            if isinstance(value, dict):
                result[key] = self._reveal_nested(value, key)
            elif isinstance(value, str):
                # Try to reveal if it's a known sensitive field or looks obscured
                if key in self._sensitive_fields or self._obscurer.is_obscured(value):
                    try:
                        result[key] = self._obscurer.reveal(value)
                    except ValueError:
                        result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value

        return result

    def _reveal_nested(self, data: dict[str, Any], prefix: str) -> dict[str, Any]:
        """Reveal secrets in nested dictionaries.

        Args:
            data: Nested data
            prefix: Key prefix for tracking sensitive fields

        Returns:
            Data with revealed secrets
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            full_key = f"{prefix}.{key}"
            if isinstance(value, dict):
                result[key] = self._reveal_nested(value, full_key)
            elif isinstance(value, str):
                # Try to reveal if it's a known sensitive field or looks obscured
                if full_key in self._sensitive_fields or self._obscurer.is_obscured(
                    value
                ):
                    try:
                        result[key] = self._obscurer.reveal(value)
                    except ValueError:
                        result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value
        return result


class ConfigManager:
    """Manager for configuration files with encryption and format support."""

    def __init__(
        self,
        config_dir: Path | str,
        format: str = "toml",
        schema: ConfigSchema | None = None,
        password: str | None = None,
        obscurer: obscure.Obscurer | None = None,
        auto_load: bool = True,
    ) -> None:
        """Initialize configuration manager.

        Args:
            config_dir: Directory for config files
            format: Config file format ('toml', 'ini', 'yaml')
            schema: Optional schema for validation
            password: Encryption password for directory-level encryption
                (if None, configs are not encrypted by default)
            obscurer: Obscurer instance for password obscuring (uses default if None)
            auto_load: If True, automatically load all configs on initialization
                (set to False to avoid password prompts when just listing files)

        Raises:
            FormatError: If format is not supported
        """
        self.config_dir = Path(config_dir).expanduser()
        self.schema = schema
        self._password = password  # Directory-level default password
        self._config_passwords: dict[str, str] = {}  # Per-config passwords
        self._obscurer = obscurer if obscurer is not None else obscure.Obscurer()
        self._configs: dict[str, ConfigEntry] = {}

        # Get format handler
        if format not in _FORMAT_REGISTRY:
            raise FormatError(
                f"Unsupported format: {format}. "
                f"Supported formats: {', '.join(_FORMAT_REGISTRY.keys())}"
            )

        self.format = format
        self._format_handler = _FORMAT_REGISTRY[format]()

        # Load existing configs (unless disabled)
        if auto_load:
            self._load_all()

    def _get_config_file(self, name: str) -> Path:
        """Get path to config file.

        Args:
            name: Config name

        Returns:
            Path to config file
        """
        extension = self._format_handler.get_extension()
        return self.config_dir / f"{name}{extension}"

    def _load_all(self) -> None:
        """Load all configuration files from directory."""
        if not self.config_dir.exists():
            logger.debug(f"Config directory not found: {self.config_dir}")
            return

        extension = self._format_handler.get_extension()

        for config_file in self.config_dir.glob(f"*{extension}"):
            name = config_file.stem
            try:
                self._load_config(name)
            except Exception as e:
                logger.error(f"Failed to load config '{name}': {e}")

    def _load_config(self, name: str) -> None:
        """Load a single config file.

        Args:
            name: Config name

        Raises:
            ConfigNotFoundError: If config file doesn't exist
            DecryptionError: If decryption fails
            FormatError: If parsing fails
        """
        config_file = self._get_config_file(name)

        if not config_file.exists():
            raise ConfigNotFoundError(f"Config '{name}' not found")

        # Read file
        with open(config_file, "rb") as f:
            data = f.read()

        # Decrypt if encrypted
        if crypt.is_encrypted(data):
            # Try to get password in priority order:
            # 1. Per-config password (already in memory)
            # 2. Environment variable VAULTCONFIG_PASSWORD_<CONFIGNAME>
            # 3. Directory-level password
            # 4. Prompt user
            password = self._config_passwords.get(name)

            if password is None:
                # Try environment variable for this specific config
                env_var = f"VAULTCONFIG_PASSWORD_{name.upper()}"
                password = os.environ.get(env_var)
                if password:
                    self._config_passwords[name] = password

            if password is None:
                # Try directory-level password
                password = self._password

            if password is None:
                # Prompt user with config-specific message
                password = crypt.get_password(f"Password for config '{name}': ")
                # Store for this session
                self._config_passwords[name] = password

            data = crypt.decrypt(data, password)

        # Parse config
        config_str = data.decode("utf-8")
        config_data = self._format_handler.load(config_str)

        # Validate schema if provided
        if self.schema:
            config_data = self.schema.validate(config_data)

        # Get sensitive fields
        sensitive_fields = set()
        if self.schema:
            sensitive_fields = self.schema.get_sensitive_fields()

        self._configs[name] = ConfigEntry(
            name, config_data, sensitive_fields, self._obscurer
        )
        logger.debug(f"Loaded config '{name}' from {config_file}")

    def _save_config(self, name: str) -> None:
        """Save a single config file.

        Args:
            name: Config name

        Raises:
            EncryptionError: If encryption fails
            FormatError: If serialization fails
        """
        if name not in self._configs:
            raise ConfigNotFoundError(f"Config '{name}' not found")

        config_file = self._get_config_file(name)
        config_entry = self._configs[name]

        # Serialize config
        config_str = self._format_handler.dump(config_entry._data)
        data = config_str.encode("utf-8")

        # Encrypt if password is set (check per-config first, then directory-level)
        password = self._config_passwords.get(name, self._password)
        if password is not None:
            data = crypt.encrypt(data, password)

        # Write file atomically with secure permissions
        _secure_write_file(config_file, data)

        logger.debug(f"Saved config '{name}' to {config_file}")

    def list_configs(self) -> list[str]:
        """List all configured names (only loaded configs).

        Returns:
            List of config names that have been successfully loaded
        """
        return list(self._configs.keys())

    def list_config_files(self) -> list[str]:
        """List all config file names without loading them.

        Returns:
            List of all config file names found in the directory
        """
        if not self.config_dir.exists():
            return []

        extension = self._format_handler.get_extension()
        config_files = []

        for config_file in self.config_dir.glob(f"*{extension}"):
            config_files.append(config_file.stem)

        return config_files

    def get_config(self, name: str) -> ConfigEntry | None:
        """Get a configuration by name.

        Args:
            name: Config name

        Returns:
            ConfigEntry or None if not found
        """
        return self._configs.get(name)

    def has_config(self, name: str) -> bool:
        """Check if a config exists.

        Args:
            name: Config name

        Returns:
            True if config exists
        """
        return name in self._configs

    def add_config(
        self,
        name: str,
        config: dict[str, Any],
        obscure_passwords: bool = True,
    ) -> None:
        """Add or update a configuration.

        Args:
            name: Config name
            config: Configuration dictionary
            obscure_passwords: Whether to obscure sensitive fields

        Raises:
            ConfigExistsError: If config exists and you want to prevent overwrite
            FormatError: If config format is invalid
        """
        if not name:
            raise ValueError("Config name cannot be empty")

        # Validate schema if provided
        if self.schema:
            config = self.schema.validate(config)

        # Get sensitive fields
        sensitive_fields = set()
        if self.schema:
            sensitive_fields = self.schema.get_sensitive_fields()

        # Obscure sensitive fields
        if obscure_passwords and sensitive_fields:
            config = config.copy()
            for field in sensitive_fields:
                if field in config and isinstance(config[field], str):
                    # Check if already obscured
                    if not self._obscurer.is_obscured(config[field]):
                        config[field] = self._obscurer.obscure(config[field])

        self._configs[name] = ConfigEntry(
            name, config, sensitive_fields, self._obscurer
        )
        self._save_config(name)

        logger.info(f"Added config '{name}'")

    def remove_config(self, name: str) -> bool:
        """Remove a configuration.

        Args:
            name: Config name

        Returns:
            True if config was removed, False if not found
        """
        if name not in self._configs:
            return False

        # Delete file
        config_file = self._get_config_file(name)
        if config_file.exists():
            config_file.unlink()

        del self._configs[name]
        logger.info(f"Removed config '{name}'")
        return True

    def set_encryption_password(self, password: str) -> None:
        """Set or change the encryption password.

        This will re-encrypt all configs with the new password.

        Args:
            password: New encryption password
        """
        old_password = self._password
        self._password = password

        # Re-save all configs with new password
        for name in self.list_configs():
            try:
                self._save_config(name)
            except Exception as e:
                # Rollback password on error
                self._password = old_password
                raise EncryptionError(
                    f"Failed to re-encrypt config '{name}': {e}"
                ) from e

        logger.info("Updated encryption password for all configs")

    def remove_encryption(self) -> None:
        """Remove encryption from all configs."""
        self._password = None

        # Re-save all configs without encryption
        for name in self.list_configs():
            self._save_config(name)

        logger.info("Removed encryption from all configs")

    def is_encrypted(self) -> bool:
        """Check if configs are encrypted (directory-level).

        Returns:
            True if directory-level encryption is enabled
        """
        return self._password is not None

    def encrypt_config(self, name: str, password: str) -> None:
        """Encrypt a specific config with its own password.

        Args:
            name: Config name
            password: Encryption password for this config

        Raises:
            ConfigNotFoundError: If config doesn't exist
            EncryptionError: If encryption fails
        """
        if name not in self._configs:
            raise ConfigNotFoundError(f"Config '{name}' not found")

        # Store password for this config
        self._config_passwords[name] = password

        # Re-save config (will be encrypted with new password)
        self._save_config(name)

        logger.info(f"Encrypted config '{name}'")

    def decrypt_config(self, name: str) -> None:
        """Remove encryption from a specific config.

        Args:
            name: Config name

        Raises:
            ConfigNotFoundError: If config doesn't exist
        """
        if name not in self._configs:
            raise ConfigNotFoundError(f"Config '{name}' not found")

        # Remove per-config password
        if name in self._config_passwords:
            del self._config_passwords[name]

        # Re-save config (will be saved unencrypted)
        self._save_config(name)

        logger.info(f"Decrypted config '{name}'")

    def is_config_encrypted(self, name: str) -> bool:
        """Check if a specific config file is encrypted.

        Args:
            name: Config name

        Returns:
            True if config file is encrypted

        Raises:
            ConfigNotFoundError: If config file doesn't exist
        """
        config_file = self._get_config_file(name)

        if not config_file.exists():
            raise ConfigNotFoundError(f"Config '{name}' not found")

        with open(config_file, "rb") as f:
            data = f.read()

        return crypt.is_encrypted(data)

    def get_encryption_status(self) -> dict[str, bool]:
        """Get encryption status for all configs.

        Returns:
            Dictionary mapping config name to encryption status
        """
        status = {}
        extension = self._format_handler.get_extension()

        for config_file in self.config_dir.glob(f"*{extension}"):
            name = config_file.stem
            try:
                with open(config_file, "rb") as f:
                    data = f.read()
                status[name] = crypt.is_encrypted(data)
            except Exception as e:
                logger.error(f"Failed to check encryption for '{name}': {e}")
                status[name] = False

        return status

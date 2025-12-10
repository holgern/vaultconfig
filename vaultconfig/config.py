"""Configuration management for vaultconfig."""

from __future__ import annotations

import logging
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


class ConfigEntry:
    """Configuration entry with metadata."""

    def __init__(
        self,
        name: str,
        data: dict[str, Any],
        sensitive_fields: set[str] | None = None,
    ) -> None:
        """Initialize config entry.

        Args:
            name: Config entry name
            data: Configuration data
            sensitive_fields: Set of field names that are sensitive (will be obscured)
        """
        self.name = name
        self._data = data
        self._sensitive_fields = sensitive_fields or set()

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
        value = self._data

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
                return obscure.reveal(value)
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

        result = {}
        for key, value in self._data.items():
            if isinstance(value, dict):
                result[key] = self._reveal_nested(value, key)
            elif isinstance(value, str):
                # Try to reveal if it's a known sensitive field or looks obscured
                if key in self._sensitive_fields or obscure.is_obscured(value):
                    try:
                        result[key] = obscure.reveal(value)
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
        result = {}
        for key, value in data.items():
            full_key = f"{prefix}.{key}"
            if isinstance(value, dict):
                result[key] = self._reveal_nested(value, full_key)
            elif isinstance(value, str):
                # Try to reveal if it's a known sensitive field or looks obscured
                if full_key in self._sensitive_fields or obscure.is_obscured(value):
                    try:
                        result[key] = obscure.reveal(value)
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
    ) -> None:
        """Initialize configuration manager.

        Args:
            config_dir: Directory for config files
            format: Config file format ('toml', 'ini', 'yaml')
            schema: Optional schema for validation
            password: Encryption password (if None, configs are not encrypted)

        Raises:
            FormatError: If format is not supported
        """
        self.config_dir = Path(config_dir).expanduser()
        self.schema = schema
        self._password = password
        self._configs: dict[str, ConfigEntry] = {}

        # Get format handler
        if format not in _FORMAT_REGISTRY:
            raise FormatError(
                f"Unsupported format: {format}. "
                f"Supported formats: {', '.join(_FORMAT_REGISTRY.keys())}"
            )

        self.format = format
        self._format_handler = _FORMAT_REGISTRY[format]()

        # Load existing configs
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
            if self._password is None:
                self._password = crypt.get_password()
            data = crypt.decrypt(data, self._password)

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

        self._configs[name] = ConfigEntry(name, config_data, sensitive_fields)
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

        # Create directory if needed
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Serialize config
        config_str = self._format_handler.dump(config_entry._data)
        data = config_str.encode("utf-8")

        # Encrypt if password is set
        if self._password is not None:
            data = crypt.encrypt(data, self._password)

        # Write file
        with open(config_file, "wb") as f:
            f.write(data)

        # Set secure permissions (owner read/write only)
        config_file.chmod(0o600)

        logger.debug(f"Saved config '{name}' to {config_file}")

    def list_configs(self) -> list[str]:
        """List all configured names.

        Returns:
            List of config names
        """
        return list(self._configs.keys())

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
                    if not obscure.is_obscured(config[field]):
                        config[field] = obscure.obscure(config[field])

        self._configs[name] = ConfigEntry(name, config, sensitive_fields)
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
        """Check if configs are encrypted.

        Returns:
            True if configs are encrypted
        """
        return self._password is not None

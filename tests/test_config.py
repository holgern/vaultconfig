"""Tests for configuration management."""

import pytest

from vaultconfig import obscure
from vaultconfig.config import ConfigEntry, ConfigManager
from vaultconfig.exceptions import FormatError
from vaultconfig.schema import FieldDef, create_simple_schema


def test_config_entry_initialization():
    """Test ConfigEntry initialization."""
    entry = ConfigEntry("test", {"key": "value"})
    assert entry.name == "test"
    assert entry._data == {"key": "value"}
    assert entry._sensitive_fields == set()


def test_config_entry_get():
    """Test getting a configuration value."""
    entry = ConfigEntry("test", {"host": "localhost", "port": 8080})
    assert entry.get("host") == "localhost"
    assert entry.get("port") == 8080


def test_config_entry_get_default():
    """Test getting a configuration value with default."""
    entry = ConfigEntry("test", {"host": "localhost"})
    assert entry.get("missing", "default") == "default"


def test_config_entry_get_nested():
    """Test getting nested configuration values with dot notation."""
    entry = ConfigEntry("test", {"database": {"host": "localhost", "port": 5432}})
    assert entry.get("database.host") == "localhost"
    assert entry.get("database.port") == 5432
    assert entry.get("database.missing", "default") == "default"


def test_config_entry_get_nested_not_dict():
    """Test getting nested values when intermediate is not a dict."""
    entry = ConfigEntry("test", {"value": "string"})
    assert entry.get("value.nested", "default") == "default"


def test_config_entry_get_sensitive_revealed():
    """Test that sensitive fields are revealed when accessed."""
    obscured = obscure.obscure("secret")
    entry = ConfigEntry("test", {"password": obscured}, sensitive_fields={"password"})
    assert entry.get("password") == "secret"


def test_config_entry_get_sensitive_not_obscured():
    """Test that non-obscured sensitive fields are returned as-is."""
    entry = ConfigEntry("test", {"password": "plain"}, sensitive_fields={"password"})
    assert entry.get("password") == "plain"


def test_config_entry_get_all():
    """Test getting all configuration values."""
    data = {"host": "localhost", "port": 8080}
    entry = ConfigEntry("test", data)
    result = entry.get_all()
    assert result == data
    assert result is not data  # Should be a copy


def test_config_entry_get_all_reveal_secrets():
    """Test getting all values with secrets revealed."""
    obscured = obscure.obscure("secret")
    entry = ConfigEntry(
        "test", {"user": "admin", "password": obscured}, sensitive_fields={"password"}
    )
    result = entry.get_all(reveal_secrets=True)
    assert result["user"] == "admin"
    assert result["password"] == "secret"


def test_config_entry_get_all_keep_secrets():
    """Test getting all values without revealing secrets."""
    obscured = obscure.obscure("secret")
    entry = ConfigEntry(
        "test", {"user": "admin", "password": obscured}, sensitive_fields={"password"}
    )
    result = entry.get_all(reveal_secrets=False)
    assert result["password"] == obscured


def test_config_entry_get_all_nested_secrets():
    """Test getting all values with nested secrets."""
    obscured = obscure.obscure("secret")
    entry = ConfigEntry(
        "test",
        {"database": {"user": "admin", "password": obscured}},
        sensitive_fields={"database.password"},
    )
    result = entry.get_all(reveal_secrets=True)
    assert result["database"]["user"] == "admin"
    assert result["database"]["password"] == "secret"


def test_config_manager_init(config_dir):
    """Test ConfigManager initialization."""
    manager = ConfigManager(config_dir)
    assert manager.config_dir == config_dir
    assert manager.format == "toml"
    assert manager.schema is None
    assert manager._password is None


def test_config_manager_init_with_schema(config_dir, sample_schema):
    """Test ConfigManager initialization with schema."""
    manager = ConfigManager(config_dir, schema=sample_schema)
    assert manager.schema == sample_schema


def test_config_manager_init_invalid_format(config_dir):
    """Test ConfigManager initialization with invalid format."""
    with pytest.raises(FormatError) as exc_info:
        ConfigManager(config_dir, format="invalid")
    assert "unsupported format" in str(exc_info.value).lower()


def test_config_manager_add_config(config_dir):
    """Test adding a configuration."""
    manager = ConfigManager(config_dir)
    config = {"host": "localhost", "port": 8080}
    manager.add_config("test", config, obscure_passwords=False)

    assert manager.has_config("test")
    assert "test" in manager.list_configs()


def test_config_manager_add_config_with_schema(config_dir, sample_schema):
    """Test adding a configuration with schema validation."""
    manager = ConfigManager(config_dir, schema=sample_schema)
    config = {
        "host": "localhost",
        "port": 8080,
        "username": "user",
        "password": "secret",
    }
    manager.add_config("test", config)

    entry = manager.get_config("test")
    assert entry is not None
    assert entry.get("host") == "localhost"


def test_config_manager_add_config_obscures_passwords(config_dir, sample_schema):
    """Test that sensitive fields are obscured when adding config."""
    manager = ConfigManager(config_dir, schema=sample_schema)
    config = {
        "host": "localhost",
        "port": 8080,
        "username": "user",
        "password": "secret",
    }
    manager.add_config("test", config, obscure_passwords=True)

    entry = manager.get_config("test")
    # Get raw data to check it's obscured
    raw_password = entry._data["password"]
    assert obscure.is_obscured(raw_password)
    # But when getting through the API, it should be revealed
    assert entry.get("password") == "secret"


def test_config_manager_add_config_already_obscured(config_dir, sample_schema):
    """Test that already-obscured passwords are not double-obscured."""
    manager = ConfigManager(config_dir, schema=sample_schema)
    obscured = obscure.obscure("secret")
    config = {
        "host": "localhost",
        "port": 8080,
        "username": "user",
        "password": obscured,
    }
    manager.add_config("test", config, obscure_passwords=True)

    entry = manager.get_config("test")
    # Should still be able to reveal it correctly
    assert entry.get("password") == "secret"


def test_config_manager_add_config_empty_name(config_dir):
    """Test that empty config name raises error."""
    manager = ConfigManager(config_dir)
    with pytest.raises(ValueError) as exc_info:
        manager.add_config("", {})
    assert "cannot be empty" in str(exc_info.value).lower()


def test_config_manager_get_config(config_dir):
    """Test getting a configuration."""
    manager = ConfigManager(config_dir)
    config = {"host": "localhost", "port": 8080}
    manager.add_config("test", config, obscure_passwords=False)

    entry = manager.get_config("test")
    assert entry is not None
    assert entry.name == "test"
    assert entry.get("host") == "localhost"


def test_config_manager_get_config_not_found(config_dir):
    """Test getting a non-existent configuration."""
    manager = ConfigManager(config_dir)
    entry = manager.get_config("nonexistent")
    assert entry is None


def test_config_manager_has_config(config_dir):
    """Test checking if configuration exists."""
    manager = ConfigManager(config_dir)
    config = {"host": "localhost"}
    manager.add_config("test", config, obscure_passwords=False)

    assert manager.has_config("test")
    assert not manager.has_config("nonexistent")


def test_config_manager_list_configs(config_dir):
    """Test listing all configurations."""
    manager = ConfigManager(config_dir)
    manager.add_config("test1", {"key": "value1"}, obscure_passwords=False)
    manager.add_config("test2", {"key": "value2"}, obscure_passwords=False)

    configs = manager.list_configs()
    assert len(configs) == 2
    assert "test1" in configs
    assert "test2" in configs


def test_config_manager_remove_config(config_dir):
    """Test removing a configuration."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    assert manager.has_config("test")
    result = manager.remove_config("test")
    assert result is True
    assert not manager.has_config("test")


def test_config_manager_remove_config_not_found(config_dir):
    """Test removing a non-existent configuration."""
    manager = ConfigManager(config_dir)
    result = manager.remove_config("nonexistent")
    assert result is False


def test_config_manager_persistence(config_dir):
    """Test that configurations persist across manager instances."""
    # Create config with first manager
    manager1 = ConfigManager(config_dir)
    manager1.add_config("test", {"host": "localhost"}, obscure_passwords=False)

    # Load with second manager
    manager2 = ConfigManager(config_dir)
    assert manager2.has_config("test")
    entry = manager2.get_config("test")
    assert entry.get("host") == "localhost"


def test_config_manager_different_formats(config_dir):
    """Test that different format managers don't interfere."""
    manager_toml = ConfigManager(config_dir, format="toml")
    manager_ini = ConfigManager(config_dir, format="ini")

    manager_toml.add_config("test", {"key": "value"}, obscure_passwords=False)

    # INI manager shouldn't see TOML config
    assert not manager_ini.has_config("test")


def test_config_manager_encryption(config_dir):
    """Test encryption of configurations."""
    manager = ConfigManager(config_dir, password="mypassword")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    # Check file is encrypted
    config_file = config_dir / "test.toml"
    with open(config_file, "rb") as f:
        content = f.read()
    assert b"VAULTCONFIG_ENCRYPT_V1" in content

    # Load with new manager with same password
    manager2 = ConfigManager(config_dir, password="mypassword")
    assert manager2.has_config("test")
    entry = manager2.get_config("test")
    assert entry.get("key") == "value"


def test_config_manager_set_encryption_password(config_dir):
    """Test setting encryption password on existing configs."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    # Enable encryption
    manager.set_encryption_password("newpassword")

    # Check file is now encrypted
    config_file = config_dir / "test.toml"
    with open(config_file, "rb") as f:
        content = f.read()
    assert b"VAULTCONFIG_ENCRYPT_V1" in content

    # Load with new manager
    manager2 = ConfigManager(config_dir, password="newpassword")
    assert manager2.has_config("test")


def test_config_manager_remove_encryption(config_dir):
    """Test removing encryption from configs."""
    manager = ConfigManager(config_dir, password="mypassword")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    # Remove encryption
    manager.remove_encryption()

    # Check file is not encrypted
    config_file = config_dir / "test.toml"
    with open(config_file, "rb") as f:
        content = f.read()
    assert b"VAULTCONFIG_ENCRYPT_V1" not in content
    assert b"VAULTCONFIG_ENCRYPT_" not in content  # No encryption at all

    # Load with new manager without password
    manager2 = ConfigManager(config_dir)
    assert manager2.has_config("test")


def test_config_manager_is_encrypted(config_dir):
    """Test checking if manager uses encryption."""
    manager1 = ConfigManager(config_dir)
    assert not manager1.is_encrypted()

    manager2 = ConfigManager(config_dir, password="secret")
    assert manager2.is_encrypted()


def test_config_manager_file_permissions(config_dir):
    """Test that config files have secure permissions."""
    import platform
    import stat

    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    config_file = config_dir / "test.toml"
    assert config_file.exists()

    # Check permissions are 0o600 (owner read/write only) on Unix-like systems
    # Windows doesn't support Unix-style permissions, so skip this check
    if platform.system() != "Windows":
        mode = config_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


def test_config_manager_ini_format(config_dir):
    """Test ConfigManager with INI format."""
    manager = ConfigManager(config_dir, format="ini")
    manager.add_config("test", {"section": {"key": "value"}}, obscure_passwords=False)

    config_file = config_dir / "test.ini"
    assert config_file.exists()

    # Reload
    manager2 = ConfigManager(config_dir, format="ini")
    entry = manager2.get_config("test")
    assert entry.get("section.key") == "value"


def test_config_manager_yaml_format(config_dir):
    """Test ConfigManager with YAML format."""
    pytest.importorskip("yaml")

    manager = ConfigManager(config_dir, format="yaml")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    config_file = config_dir / "test.yaml"
    assert config_file.exists()

    # Reload
    manager2 = ConfigManager(config_dir, format="yaml")
    entry = manager2.get_config("test")
    assert entry.get("key") == "value"


def test_config_manager_with_schema_validation_error(config_dir):
    """Test that schema validation errors are raised."""
    schema = create_simple_schema({"required_field": FieldDef(str)})

    manager = ConfigManager(config_dir, schema=schema)
    # Missing required field should raise error
    from vaultconfig.exceptions import SchemaValidationError

    with pytest.raises(SchemaValidationError):
        manager.add_config("test", {})


def test_config_manager_update_config(config_dir):
    """Test updating an existing configuration."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value1"}, obscure_passwords=False)
    manager.add_config("test", {"key": "value2"}, obscure_passwords=False)

    entry = manager.get_config("test")
    assert entry.get("key") == "value2"

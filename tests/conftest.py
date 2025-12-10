"""Pytest fixtures for vaultconfig tests."""

import pytest

from vaultconfig import ConfigManager, create_simple_schema
from vaultconfig.schema import FieldDef


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests.

    Args:
        tmp_path: pytest temporary directory fixture

    Yields:
        Path to temporary directory
    """
    return tmp_path


@pytest.fixture
def config_dir(temp_dir):
    """Create a temporary config directory.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to config directory
    """
    config_path = temp_dir / "config"
    config_path.mkdir()
    return config_path


@pytest.fixture
def sample_config():
    """Sample configuration data.

    Returns:
        Dictionary with sample config data
    """
    return {
        "host": "localhost",
        "port": 5432,
        "username": "testuser",
        "password": "testpass123",
    }


@pytest.fixture
def sample_schema():
    """Sample configuration schema.

    Returns:
        ConfigSchema instance
    """
    return create_simple_schema(
        {
            "host": FieldDef(str, default="localhost"),
            "port": FieldDef(int, default=5432),
            "username": FieldDef(str),
            "password": FieldDef(str, sensitive=True),
        }
    )


@pytest.fixture
def config_manager(config_dir):
    """Create a ConfigManager instance.

    Args:
        config_dir: Config directory fixture

    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_dir=config_dir, format="toml")


@pytest.fixture
def encrypted_config_manager(config_dir):
    """Create an encrypted ConfigManager instance.

    Args:
        config_dir: Config directory fixture

    Returns:
        ConfigManager instance with encryption
    """
    return ConfigManager(
        config_dir=config_dir,
        format="toml",
        password="test-password-123",
    )


@pytest.fixture
def toml_data():
    """Sample TOML data.

    Returns:
        TOML string
    """
    return """
host = "localhost"
port = 5432
username = "testuser"
password = "testpass123"

[database]
name = "testdb"
pool_size = 10
"""


@pytest.fixture
def ini_data():
    """Sample INI data.

    Returns:
        INI string
    """
    return """
[main]
host = localhost
port = 5432
username = testuser

[database]
name = testdb
pool_size = 10
"""


@pytest.fixture
def yaml_data():
    """Sample YAML data.

    Returns:
        YAML string
    """
    return """
host: localhost
port: 5432
username: testuser
password: testpass123

database:
  name: testdb
  pool_size: 10
"""

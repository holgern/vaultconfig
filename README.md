[![PyPI - Version](https://img.shields.io/pypi/v/vaultconfig)](https://pypi.org/project/vaultconfig/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vaultconfig)
![PyPI - Downloads](https://img.shields.io/pypi/dm/vaultconfig)
[![codecov](https://codecov.io/gh/holgern/vaultconfig/graph/badge.svg?token=iCHXwbjAXG)](https://codecov.io/gh/holgern/vaultconfig)

# VaultConfig

**Secure configuration management library with encryption support for Python**

VaultConfig provides an easy way to manage application configurations with support for
multiple formats (TOML, INI, YAML), password obscuring, and full config file encryption.

## Features

- **Multiple Format Support**: TOML, INI, and YAML (optional)
- **Password Obscuring**: Hide sensitive fields from casual viewing (AES-CTR based)
- **Config File Encryption**: Strong authenticated encryption using NaCl secretbox
  (XSalsa20 + Poly1305)
- **Schema Validation**: Pydantic-based schema system for type validation
- **CLI Tool**: Command-line interface for config management
- **Project-Specific**: Each project can have its own config directory
- **Easy Integration**: Simple API for embedding into Python applications

## Installation

```bash
# Basic installation
pip install vaultconfig

# With YAML support
pip install vaultconfig[yaml]

# For development
pip install vaultconfig[dev]
```

## Quick Start

### Command Line Usage

```bash
# Initialize a new config directory
vaultconfig init ./myapp-config --format toml

# Initialize with encryption
vaultconfig init ./myapp-config --format toml --encrypt

# List all configurations
vaultconfig list ./myapp-config

# Show a configuration
vaultconfig show ./myapp-config myconfig

# Show with revealed passwords
vaultconfig show ./myapp-config myconfig --reveal

# Delete a configuration
vaultconfig delete ./myapp-config myconfig

# Manage encryption
vaultconfig encrypt set ./myapp-config        # Set/change password
vaultconfig encrypt remove ./myapp-config     # Remove encryption
vaultconfig encrypt check ./myapp-config      # Check encryption status
```

### Python API Usage

#### Basic Usage

```python
from pathlib import Path
from vaultconfig import ConfigManager

# Create manager
manager = ConfigManager(
    config_dir=Path("./myapp-config"),
    format="toml",  # or "ini", "yaml"
)

# Add a configuration
manager.add_config(
    name="database",
    config={
        "host": "localhost",
        "port": 5432,
        "username": "myuser",
        "password": "secret123",  # Will be obscured
    },
)

# Get configuration
config = manager.get_config("database")
if config:
    host = config.get("host")
    password = config.get("password")  # Automatically revealed

# List all configs
configs = manager.list_configs()

# Remove a config
manager.remove_config("database")
```

#### With Encryption

```python
from vaultconfig import ConfigManager

# Create encrypted manager
manager = ConfigManager(
    config_dir=Path("./secure-config"),
    format="toml",
    password="my-secure-password",  # Or use env var VAULTCONFIG_PASSWORD
)

# Add configs - they'll be encrypted automatically
manager.add_config("secrets", {"api_key": "12345", "token": "abcde"})

# Change encryption password
manager.set_encryption_password("new-password")

# Remove encryption
manager.remove_encryption()
```

#### With Schema Validation

```python
from vaultconfig import ConfigManager, ConfigSchema, FieldDef, create_simple_schema

# Define schema
schema = create_simple_schema({
    "host": FieldDef(str, default="localhost"),
    "port": FieldDef(int, default=5432),
    "username": FieldDef(str, default="postgres"),
    "password": FieldDef(str, sensitive=True),  # Will be auto-obscured
})

# Create manager with schema
manager = ConfigManager(
    config_dir=Path("./myapp-config"),
    schema=schema,
)

# Schema validation happens automatically
manager.add_config("db", {
    "host": "db.example.com",
    "port": 5432,
    "password": "secret",
})
```

#### Using Pydantic Models

```python
from pydantic import BaseModel, Field
from vaultconfig import ConfigManager, ConfigSchema

# Define Pydantic model
class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    username: str
    password: str = Field(json_schema_extra={"sensitive": True})

# Create schema from model
schema = ConfigSchema(DatabaseConfig)

# Use with manager
manager = ConfigManager(
    config_dir=Path("./myapp-config"),
    schema=schema,
)
```

## Password Obscuring vs Encryption

VaultConfig provides two levels of security:

### Password Obscuring

- **Purpose**: Hide passwords from casual viewing (shoulder surfing)
- **Method**: AES-CTR with a fixed key + base64 encoding
- **Security**: NOT secure encryption - anyone with access to the code can decrypt
- **Use Case**: Prevent accidental exposure in config files, logs, or screens
- **Automatic**: Sensitive fields are automatically obscured when `sensitive=True`

```python
from vaultconfig import obscure

# Obscure a password
obscured = obscure.obscure("my_password")  # Returns base64 string

# Reveal it later
revealed = obscure.reveal(obscured)  # Returns "my_password"
```

### Config File Encryption

- **Purpose**: Secure encryption of entire config files
- **Method**: NaCl secretbox (XSalsa20-Poly1305) with password-derived key
- **Security**: Strong authenticated encryption - lost password = lost data
- **Use Case**: Protect sensitive configs at rest
- **Format**: `VAULTCONFIG_ENCRYPT_V0:<base64-encrypted-data>`

```python
# Encrypt all configs
manager = ConfigManager(
    config_dir=Path("./config"),
    password="strong-password",
)

# Or set password later
manager.set_encryption_password("strong-password")

# Password can also come from:
# - Environment variable: VAULTCONFIG_PASSWORD
# - External command: VAULTCONFIG_PASSWORD_COMMAND
# - Interactive prompt (if TTY available)
```

## Configuration Formats

### TOML (Default)

```toml
# config.toml
host = "localhost"
port = 5432
password = "obscured-password-here"

[nested]
key = "value"
```

### INI

```ini
# config.ini
[database]
host = localhost
port = 5432
password = obscured-password-here
```

### YAML (Optional)

```yaml
# config.yaml
host: localhost
port: 5432
password: obscured-password-here
nested:
  key: value
```

## Environment Variables

- `VAULTCONFIG_PASSWORD`: Password for encrypted configs
- `VAULTCONFIG_PASSWORD_COMMAND`: Command to retrieve password (e.g., from password
  manager)
- `VAULTCONFIG_PASSWORD_CHANGE`: Set to "1" when changing password (used by password
  command)

## Security Considerations

1. **Password Obscuring**:

   - NOT secure encryption - only prevents casual viewing
   - Anyone with code access can reveal passwords
   - Use for convenience, not security

2. **Config File Encryption**:

   - Uses strong authenticated encryption (NaCl secretbox)
   - Password is hashed with SHA-256 + salt
   - No password recovery - lost password = lost data
   - Password strength is user's responsibility

3. **Best Practices**:
   - Use config file encryption for production
   - Store encryption passwords in system keychain/password manager
   - Use `VAULTCONFIG_PASSWORD_COMMAND` for automation
   - Set config files to 0600 permissions (owner read/write only)
   - Never commit encrypted configs with weak passwords

## Integration Examples

### Flask Application

```python
from flask import Flask
from pathlib import Path
from vaultconfig import ConfigManager

app = Flask(__name__)

# Load config on startup
config_manager = ConfigManager(
    config_dir=Path.home() / ".config" / "myapp",
    password=os.environ.get("MYAPP_CONFIG_PASSWORD"),
)

db_config = config_manager.get_config("database")
if db_config:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{db_config.get('username')}:{db_config.get('password')}"
        f"@{db_config.get('host')}:{db_config.get('port')}/{db_config.get('database')}"
    )
```

### CLI Application

```python
import click
from vaultconfig import ConfigManager

@click.group()
@click.pass_context
def cli(ctx):
    """My CLI application."""
    ctx.obj = ConfigManager(
        config_dir=Path.home() / ".config" / "myapp",
    )

@cli.command()
@click.pass_obj
def connect(manager):
    """Connect to service."""
    config = manager.get_config("service")
    # Use config...
```

## Migrating from pywebdavserver

If you're migrating from the old `pywebdavserver` config system:

```python
# Old way
from pywebdavserver.config import get_config_manager

manager = get_config_manager()

# New way (vaultconfig is now used internally)
from pywebdavserver.config import get_config_manager

manager = get_config_manager()  # Same API, now powered by vaultconfig
```

The API remains the same for backward compatibility.

## Development

```bash
# Clone repository
git clone https://github.com/your-org/vaultconfig.git
cd vaultconfig

# Install in development mode
pip install -e ".[dev,yaml]"

# Run tests
pytest

# Format code
ruff check --fix .
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Acknowledgments

- Inspired by [rclone](https://rclone.org/)'s config encryption system
- Uses [PyNaCl](https://pynacl.readthedocs.io/) for strong encryption
- Built with [Pydantic](https://pydantic.dev/) for schema validation

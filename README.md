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
  (XSalsa20-Poly1305) with PBKDF2 key derivation
- **Schema Validation**: Pydantic-based schema system for type validation
- **CLI Tool**: Command-line interface for config management
- **Project-Specific**: Each project can have its own config directory
- **Easy Integration**: Simple API for embedding into Python applications
- **Security Features**: Atomic file writes, secure file permissions, password
  validation

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
- **Warning**: A security warning is logged on first use to remind users this is
  obfuscation only

```python
from vaultconfig import obscure

# Obscure a password
obscured = obscure.obscure("my_password")  # Returns base64 string

# Reveal it later
revealed = obscure.reveal(obscured)  # Returns "my_password"
```

**IMPORTANT**: This is obfuscation, not encryption! Anyone with access to vaultconfig
can decrypt obscured passwords. Use config file encryption for real security.

### Using Custom Cipher Keys

By default, vaultconfig uses a hardcoded cipher key for password obscuring. While this
prevents casual viewing, anyone with access to the vaultconfig library can reveal these
passwords. For better protection, you can use your own custom cipher key:

#### Python API

```python
from vaultconfig import ConfigManager, create_obscurer_from_passphrase
import secrets

# Option 1: Generate a random key (most secure)
cipher_key = secrets.token_bytes(32)
from vaultconfig import Obscurer
obscurer = Obscurer(cipher_key=cipher_key)

# Option 2: Use a passphrase (easiest - recommended for most apps)
obscurer = create_obscurer_from_passphrase("MyApp-Unique-Secret-2024")

# Option 3: Use a hex string (good for storing in env vars/files)
from vaultconfig import create_obscurer_from_hex
obscurer = create_obscurer_from_hex("a73b9f2c...")  # 64 hex chars

# Use with ConfigManager
manager = ConfigManager(
    config_dir=Path("./myapp-config"),
    obscurer=obscurer,  # All password obscuring uses YOUR key
)

# Everything else works the same
manager.add_config("db", {"password": "secret"})
config = manager.get_config("db")
password = config.get("password")  # Revealed automatically
```

#### CLI Usage

```bash
# Generate a cipher key
vaultconfig obscure generate-key > ~/.myapp_cipher_key

# Generate from passphrase (reproducible)
vaultconfig obscure generate-key --from-passphrase

# Use with environment variable
export VAULTCONFIG_CIPHER_KEY=$(cat ~/.myapp_cipher_key)
vaultconfig list ./myapp-config

# Or point to key file
export VAULTCONFIG_CIPHER_KEY_FILE=~/.myapp_cipher_key
vaultconfig show ./myapp-config database --reveal
```

#### Key Management Best Practices

1. **Generate Once**: Create your key once and store it securely
2. **Secure Storage**: Keep the key in a secure location (not in git!)
3. **Environment Variables**: Use env vars or key files for deployment
4. **Backup**: Keep a backup of your key - without it, passwords cannot be revealed
5. **App-Specific**: Use different keys for different applications
6. **Still Not Encryption**: Custom keys improve security but this is still obfuscation

**Benefits of Custom Keys**:

- Other apps/users cannot reveal your obscured passwords without your specific key
- Adds an application-specific layer of protection
- Easy to implement with passphrases or random keys

**Limitations**:

- Still not real encryption - anyone with your key can reveal passwords
- Lost key = lost ability to reveal passwords
- For real security, use config file encryption (see below)

### Config File Encryption

- **Purpose**: Secure encryption of entire config files
- **Method**: NaCl secretbox (XSalsa20-Poly1305) with PBKDF2-HMAC-SHA256 key derivation
- **Key Derivation**: 600,000 iterations of PBKDF2 with random salt (OWASP 2023
  recommended)
- **Security**: Strong authenticated encryption - lost password = lost data
- **Use Case**: Protect sensitive configs at rest
- **Format**: `VAULTCONFIG_ENCRYPT_V1:<base64-encrypted-data>`
- **Password Requirements**: Minimum 4 characters (12+ recommended)

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
- `VAULTCONFIG_CIPHER_KEY`: Hex-encoded custom cipher key (64 hex characters)
- `VAULTCONFIG_CIPHER_KEY_FILE`: Path to file containing hex-encoded cipher key

## Security Considerations

1. **Password Obscuring**:

   - NOT secure encryption - only prevents casual viewing
   - Anyone with code access can reveal passwords
   - Use for convenience, not security
   - A warning is logged on first use
   - **Custom Cipher Keys**: Using custom keys improves security but is still
     obfuscation
   - Custom keys prevent other apps from revealing your passwords
   - Lost custom key = lost ability to reveal passwords

2. **Config File Encryption**:

   - Uses strong authenticated encryption (NaCl secretbox)
   - Password is derived using PBKDF2-HMAC-SHA256 with 600,000 iterations
   - Random salt generated per encryption
   - No password recovery - lost password = lost data
   - Minimum password length: 4 characters (12+ strongly recommended)
   - Warnings shown for weak or short passwords

3. **File Security**:

   - Config files automatically set to 0600 permissions (owner read/write only)
   - Atomic file writes prevent partial/corrupted files
   - Secure deletion of temporary files on error
   - No race conditions in file permission setting

4. **Best Practices**:
   - Use config file encryption for production
   - Use strong passwords (12+ characters recommended)
   - Store encryption passwords in system keychain/password manager
   - Use `VAULTCONFIG_PASSWORD_COMMAND` for automation
   - Never commit encrypted configs with weak passwords
   - Keep PyYAML updated (>= 6.0 for security fixes)
   - Avoid using shell=True with password commands (use proper escaping)
   - **Use custom cipher keys** for password obscuring (better than default)
   - Generate cipher keys with `vaultconfig obscure generate-key`
   - Store cipher keys securely (env vars, key files, not in code/git)

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

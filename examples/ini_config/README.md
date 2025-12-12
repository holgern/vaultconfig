# INI Configuration Examples

This directory contains complete examples demonstrating the use of `vaultconfig` with
INI format configuration files.

## Overview

The examples show:

1. ✅ **Valid Configuration** - Loading and reading a properly formatted INI config
2. ❌ **Invalid Configuration** - Handling validation errors when config doesn't meet
   schema requirements
3. 🔐 **Obscured Passwords** - Using password obscuring for sensitive fields
4. 🌐 **DEFAULT Section** - SSH-style configuration with inherited values
5. 🏢 **Multi-Environment** - Managing dev/staging/prod configurations

## Files

### Configuration Files

- **valid_database.ini** - A valid configuration that passes schema validation
- **invalid_database.ini** - A configuration with validation errors (invalid port,
  missing password)
- **obscured_database.ini** - A configuration with an obscured password field
- **hosts_config.ini** - SSH-style configuration demonstrating DEFAULT section
  inheritance
- **environments.ini** - Multi-environment configuration (auto-generated)

### Example Scripts

- **example.py** - Main demonstration script showing validation and password obscuring
- **example_default_section.py** - Enhanced examples showing DEFAULT section usage
  patterns

## Requirements

```bash
pip install vaultconfig pydantic cryptography
```

## Running the Examples

### Basic Example (Validation & Obscuring)

```bash
cd examples/ini_config
python example.py
```

This demonstrates:

- Loading valid configurations
- Catching validation errors
- Working with obscured passwords

### DEFAULT Section Example (SSH-Style Config)

```bash
python example_default_section.py
```

This demonstrates:

- SSH-style configuration with DEFAULT section
- Value inheritance and overriding
- Multi-environment setup
- Practical usage patterns

## Example Output

### Example 1: Valid Configuration

```
✓ Successfully loaded 'valid_database' configuration

Configuration values:
  Host:         localhost
  Port:         5432
  Username:     admin
  Database:     myapp_db
  SSL Enabled:  True
  Password:     mysecretpassword123
```

### Example 2: Invalid Configuration

```
✓ Validation correctly detected errors:
  - Field 'port': Input should be less than or equal to 65535
  - Field 'password': Field required
```

The invalid configuration demonstrates:

- Port number out of range (99999 > 65535)
- Missing required field (password)

### Example 3: Obscured Password

```
✓ Successfully loaded 'obscured_database' configuration

Raw configuration (password obscured in INI file):
  host: db.example.com
  port: 5432
  username: dbuser
  password: k4BtDIYeAKEGkqmPPoIJFxqlcF8SmCLFfOrAXwi6_RsW79U1QtrJph8 (obscured)
  database: production_db
  ssl_enabled: true

Revealed password: super_secret_password_456

Obscuring a new password:
  Original:  new_secret_password_123
  Obscured:  z9PhfuSp230mINyqPJd0MSOGuP_1wuNK26_Pu7-KahKTMF77Vo4r
  Revealed:  new_secret_password_123
  Match:     True
```

### Example 4: DEFAULT Section (SSH-Style)

```
[forge.example]
  Specific settings:
    User = hg
  Inherited from DEFAULT:
    ServerAliveInterval = 45
    Compression = yes
    ForwardX11 = yes

[topsecret.server.example]
  Specific settings:
    Port = 50022
  Overridden settings:
    ForwardX11 = no (was: yes)
  Inherited from DEFAULT:
    ServerAliveInterval = 45
    Compression = yes
```

### Example 5: Multi-Environment Configuration

```
[DEVELOPMENT]
  Endpoint: https://localhost:8080
  Timeout: 30s
  Log Level: DEBUG

[STAGING]
  Endpoint: https://staging.example.com:443
  Timeout: 30s
  Log Level: INFO

[PRODUCTION]
  Endpoint: https://prod.example.com:443
  Timeout: 60s (overrides DEFAULT)
  Retry Count: 5 (overrides DEFAULT)
  Log Level: INFO
```

## Schema Definition

The examples use a Pydantic schema for validation:

```python
class DatabaseConfig(BaseModel):
    """Database configuration schema."""

    host: str = Field(description="Database host")
    port: int = Field(ge=1, le=65535, description="Database port (1-65535)")
    username: str = Field(description="Database username")
    password: str = Field(json_schema_extra={"sensitive": True})
    database: str = Field(description="Database name")
    ssl_enabled: bool = Field(default=False, description="Enable SSL")
```

The schema enforces:

- **Type validation** - All fields must be correct types
- **Range validation** - Port must be between 1-65535
- **Required fields** - All fields except `ssl_enabled` are required
- **Sensitive fields** - `password` is marked as sensitive for obscuring

## Password Obscuring vs Encryption

⚠️ **Important Security Note**

The examples demonstrate **password obscuring**, which is **NOT encryption**:

- **Obscuring** prevents casual viewing of passwords in config files
- Anyone with access to `vaultconfig` can reveal obscured passwords
- The encryption key is hardcoded in the library
- Use for development environments or preventing "shoulder surfing"

For **real security**, use the encryption features:

```python
manager = ConfigManager(
    config_dir="configs",
    format="ini",
    password="your-encryption-password"  # Real encryption
)
```

## Creating Obscured Passwords

To create your own obscured passwords:

```python
from vaultconfig.obscure import obscure, reveal

# Obscure a password
obscured = obscure("my_password")
print(f"Obscured: {obscured}")

# Reveal it
revealed = reveal(obscured)
print(f"Revealed: {revealed}")
```

Or use the CLI:

```bash
vaultconfig obscure "my_password"
```

## INI Format Notes

The INI format uses the standard Python `configparser` format with sections:

```ini
[DEFAULT]
ServerAliveInterval = 45
Compression = yes

[forge.example]
User = hg

[topsecret.server.example]
Port = 50022
ForwardX11 = no
```

**Key Features**:

- **DEFAULT section**: Values in `[DEFAULT]` are inherited by all other sections
- **Section names**: Support dots (e.g., `forge.example`) and spaces
- **Value inheritance**: Sections automatically inherit DEFAULT values
- **Value override**: Sections can override DEFAULT values
- **Case preservation**: Option names preserve their case (e.g., `User` stays `User`,
  not `user`)

**Example** - Section inheritance from DEFAULT:

```ini
[DEFAULT]
lh_server = 192.168.0.1

[host 1]
vh_root = PloneSite1
# lh_server is automatically inherited from DEFAULT
```

When you access `host 1`, it will have both `vh_root` and `lh_server` keys.

For flat configurations, use TOML or YAML format instead.

## Additional Examples

For more advanced usage, see:

- **Encryption examples** - Using real encryption for sensitive data
- **YAML/TOML formats** - Alternative configuration formats
- **Nested configurations** - Complex hierarchical configs
- **Multiple environments** - Managing dev/staging/prod configs

## Learn More

- [VaultConfig Documentation](../../README.md)
- [API Reference](../../docs/api.rst)
- [Security Guidelines](../../docs/security.rst)

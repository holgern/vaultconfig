# TOML Configuration Examples

This directory contains complete examples demonstrating the use of `vaultconfig` with
TOML format configuration files.

## Overview

The examples show:

1. ✅ **Valid Configuration** - Loading and reading a properly formatted TOML config
2. ❌ **Invalid Configuration** - Handling validation errors when config doesn't meet
   schema requirements
3. 🔐 **Obscured Passwords** - Using password obscuring for sensitive fields
4. 📦 **Nested Configuration** - Working with complex nested structures
5. 🌍 **Multi-Environment** - Managing dev/staging/prod configurations
6. 🎯 **Type Preservation** - Automatic type handling (integers, booleans, arrays, etc.)

## Files

### Configuration Files

- **valid_database.toml** - A valid configuration that passes schema validation
- **invalid_database.toml** - A configuration with validation errors (invalid port,
  missing password)
- **obscured_database.toml** - A configuration with an obscured password field
- **nested_config.toml** - Complex nested configuration with tables and sub-tables
- **environments.toml** - Multi-environment configuration (auto-generated)
- **app_config.toml** - Complete application configuration (auto-generated)
- **types_demo.toml** - Demonstration of type handling (auto-generated)

### Example Scripts

- **example.py** - Main demonstration script showing validation and password obscuring
- **example_advanced.py** - Advanced examples showing multi-environment and practical
  patterns

## Requirements

```bash
pip install vaultconfig pydantic cryptography
```

## Running the Examples

### Basic Example (Validation & Obscuring)

```bash
cd examples/toml_config
python example.py
```

This demonstrates:

- Loading valid configurations
- Catching validation errors
- Working with obscured passwords
- Accessing nested configuration values

### Advanced Examples

```bash
python example_advanced.py
```

This demonstrates:

- Multi-environment setup (dev/staging/prod)
- Complete application configuration
- Type preservation and handling
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
  Schema validation failed: 2 validation errors
  - port: Input should be less than or equal to 65535
  - password: Field required
```

### Example 3: Obscured Password

```
✓ Successfully loaded 'obscured_database' configuration

Raw configuration (passwords obscured):
  password: 647MdyXIW80RzH66xwqVxVQ7sFIeRyTK5_qU0ZiBEbkfqbjRVQ

Revealed configuration:
  password: toml_super_secret_456 (revealed)
```

### Example 4: Nested Configuration

```
✓ Successfully loaded 'nested_config' configuration

Full configuration structure:
database:
  host = localhost
  port = 5432
  database = myapp
  pool:
    max_connections = 20
    min_connections = 5
    timeout = 30
  ssl:
    enabled = True

Accessing nested values with dot notation:
  database.host: localhost
  database.pool.max_connections: 20
  api.rate_limit.requests_per_minute: 100
```

### Example 5: Multi-Environment Configuration

```
[DEVELOPMENT]
  Application: http://localhost:8080
  Debug: True
  Log Level: DEBUG
  Database: localhost:5432/myapp_dev

[STAGING]
  Application: http://staging.example.com:443
  Debug: False
  Log Level: INFO
  Database: staging-db.example.com:5432/myapp_staging

[PRODUCTION]
  Application: http://prod.example.com:443
  Debug: False
  Log Level: WARNING
  Database: prod-db.example.com:5432/myapp_prod
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

## TOML Format Features

### Nested Tables

TOML supports nested tables for organized configuration:

```toml
[database]
host = "localhost"
port = 5432

[database.pool]
max_connections = 20
min_connections = 5

[database.ssl]
enabled = true
cert_path = "/path/to/cert.pem"
```

### Type Preservation

Unlike INI, TOML preserves data types:

```toml
# Types are preserved automatically
string_value = "Hello"
integer_value = 42
float_value = 3.14
boolean_value = true
array_value = [1, 2, 3, 4, 5]
```

### Arrays

TOML supports arrays of any type:

```toml
# Simple arrays
numbers = [1, 2, 3, 4, 5]
strings = ["apple", "banana", "cherry"]

# Arrays of tables
[[servers]]
host = "server1.example.com"
port = 8080

[[servers]]
host = "server2.example.com"
port = 8081
```

## Accessing Nested Values

Use dot notation to access nested configuration:

```python
config = manager.get_config("nested_config")

# Access nested values
host = config.get("database.host")
max_conn = config.get("database.pool.max_connections")
ssl_enabled = config.get("database.ssl.enabled")

# With default values
timeout = config.get("database.pool.timeout", 30)
```

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
    format="toml",
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

## Multi-Environment Setup

### Environment-Based Configuration

```python
import os
from vaultconfig import ConfigManager

# Get current environment
env = os.getenv("APP_ENV", "development")

# Load environment-specific config
manager = ConfigManager(config_dir="./config", format="toml")
config = manager.get_config("environments")

# Get settings for current environment
env_config = config.get_all()[env]
```

### Environment Variable

```bash
# Set environment
export APP_ENV=production

# Run application
python app.py
```

## TOML vs INI

| Feature           | TOML      | INI                  |
| ----------------- | --------- | -------------------- |
| Type preservation | ✅ Yes    | ❌ No (all strings)  |
| Nested structures | ✅ Tables | ⚠️ Sections only     |
| Arrays            | ✅ Yes    | ❌ No                |
| DEFAULT section   | ❌ No     | ✅ Yes (inheritance) |
| Comments          | ✅ `#`    | ✅ `;` or `#`        |
| Case sensitivity  | ✅ Yes    | ⚠️ Optional          |

**Use TOML when:**

- You need type preservation (integers, booleans, etc.)
- You have complex nested structures
- You want arrays or lists
- Configuration is application-specific

**Use INI when:**

- You need DEFAULT section inheritance
- Configuration is SSH/systemd-style
- You want simple, flat key-value pairs
- Compatibility with legacy systems

## Additional Examples

For more advanced usage, see:

- **Encryption examples** - Using real encryption for sensitive data
- **YAML format** - Alternative configuration format
- **Schema validation** - Complex validation rules
- **CLI usage** - Managing configs from command line

## Learn More

- [VaultConfig Documentation](../../README.md)
- [API Reference](../../docs/api.rst)
- [Security Guidelines](../../docs/security.rst)
- [INI Examples](../ini_config/README.md)

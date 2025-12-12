# YAML Configuration Examples

This directory contains complete examples demonstrating the use of `vaultconfig` with
YAML format configuration files.

## Overview

The examples show:

1. ✅ **Valid Configuration** - Loading and reading a properly formatted YAML config
2. ❌ **Invalid Configuration** - Handling validation errors when config doesn't meet
   schema requirements
3. 🔐 **Obscured Passwords** - Using password obscuring for sensitive fields
4. 📦 **Nested Configuration** - Working with complex nested structures
5. 🌍 **Multi-Environment** - Managing dev/staging/prod configurations
6. 🎯 **Type Preservation** - Automatic type handling (integers, booleans, arrays, null,
   etc.)

## Files

### Configuration Files

- **valid_database.yaml** - A valid configuration that passes schema validation
- **invalid_database.yaml** - A configuration with validation errors (invalid port,
  missing password)
- **obscured_database.yaml** - A configuration with an obscured password field
- **nested_config.yaml** - Complex nested configuration with hierarchical structures
- **environments.yaml** - Multi-environment configuration (auto-generated)
- **app_config.yaml** - Complete application configuration (auto-generated)
- **types_demo.yaml** - Demonstration of type handling (auto-generated)

### Example Scripts

- **example.py** - Main demonstration script showing validation and password obscuring
- **example_advanced.py** - Advanced examples showing multi-environment and practical
  patterns

## Requirements

```bash
pip install vaultconfig pydantic cryptography PyYAML
```

**Note**: YAML support requires PyYAML to be installed separately.

## Running the Examples

### Basic Example (Validation & Obscuring)

```bash
cd examples/yaml_config
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

## YAML Format Features

### Nested Structures

YAML uses indentation for nested structures:

```yaml
database:
  host: localhost
  port: 5432
  pool:
    max_connections: 20
    min_connections: 5
  ssl:
    enabled: true
    cert_path: /path/to/cert.pem
```

### Type Preservation

YAML automatically preserves data types:

```yaml
# Types are preserved automatically
string_value: Hello, World!
integer_value: 42
float_value: 3.14
boolean_value: true
null_value: null
```

### Arrays (Lists)

YAML supports arrays with two syntaxes:

```yaml
# Block style (recommended for readability)
array_block:
  - item1
  - item2
  - item3

# Flow style (compact)
array_flow: [item1, item2, item3]

# Nested arrays
servers:
  - name: server1
    host: server1.example.com
    port: 8080
  - name: server2
    host: server2.example.com
    port: 8081
```

### Comments

YAML uses `#` for comments:

```yaml
# This is a comment
host: localhost # Inline comment
port: 5432
```

### Multi-line Strings

YAML has several ways to handle multi-line strings:

```yaml
# Literal block (preserves newlines)
description: |
  This is a multi-line
  description that preserves
  line breaks.

# Folded block (folds newlines into spaces)
summary: >
  This is a long text that will be folded into a single line.

# Single line with escapes
inline: "Line 1\nLine 2\nLine 3"
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
    format="yaml",
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
manager = ConfigManager(config_dir="./config", format="yaml")
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

## YAML vs TOML vs INI

| Feature            | YAML              | TOML      | INI                 |
| ------------------ | ----------------- | --------- | ------------------- | ----- |
| Type preservation  | ✅ Yes            | ✅ Yes    | ❌ No (all strings) |
| Nested structures  | ✅ Indentation    | ✅ Tables | ⚠️ Sections only    |
| Arrays             | ✅ Yes            | ✅ Yes    | ❌ No               |
| Null values        | ✅ `null`         | ❌ No     | ❌ No               |
| Multi-line strings | ✅ `              | `and`>`   | ✅ `"""`            | ❌ No |
| Comments           | ✅ `#`            | ✅ `#`    | ✅ `;` or `#`       |
| Readability        | ✅ Clean          | ✅ Clear  | ✅ Simple           |
| Complexity         | ⚠️ Can be complex | ✅ Simple | ✅ Very simple      |

**Use YAML when:**

- You need human-readable, clean configuration
- You have deeply nested structures
- You want advanced features (anchors, references, multi-line)
- Configuration is complex or hierarchical

**Use TOML when:**

- You need type preservation with clear syntax
- You want something between INI and YAML complexity
- You prefer explicit table definitions
- Configuration is application-specific

**Use INI when:**

- You need DEFAULT section inheritance
- Configuration is SSH/systemd-style
- You want simple, flat key-value pairs
- Compatibility with legacy systems

## YAML Best Practices

### 1. Use Consistent Indentation

```yaml
# Good - 2 spaces
database:
  host: localhost
  pool:
    size: 10

# Also good - 4 spaces (but be consistent)
database:
    host: localhost
    pool:
        size: 10
```

### 2. Quote Strings When Necessary

```yaml
# Quote when value could be misinterpreted
version: "1.0" # Without quotes, becomes float 1.0
country: "NO" # Without quotes, becomes boolean false
octal: "0755" # Without quotes, becomes octal number

# No quotes needed for simple strings
name: MyApp
description: A simple application
```

### 3. Use Block Style for Arrays

```yaml
# Good - easier to read and maintain
servers:
  - host: server1.example.com
    port: 8080
  - host: server2.example.com
    port: 8081

# Less readable for complex items
servers: [{host: server1.example.com, port: 8080}, {host: server2.example.com, port: 8081}]
```

### 4. Use `---` Document Separator

```yaml
---
# Document starts here
app:
  name: MyApp
  version: 1.0.0
```

### 5. Avoid Complex YAML Features in Config

Avoid these in configuration files (they're for templates):

- Anchors and aliases (`&anchor`, `*alias`)
- Merge keys (`<<: *default`)
- Tags (`!!python/object`)
- Multiple documents

Keep configuration simple and explicit.

## Common YAML Pitfalls

### 1. Norway Problem

```yaml
# Wrong - "NO" becomes boolean false
country: NO

# Right - quote it
country: "NO"
```

### 2. Version Numbers

```yaml
# Wrong - becomes float 1.1
version: 1.1

# Right - quote it
version: "1.1"
```

### 3. Octal Numbers

```yaml
# Wrong - becomes octal (493 in decimal)
port: 0755

# Right - don't use leading zeros for decimals
port: 755
```

### 4. Empty Values

```yaml
# These are all different:
key1: # null (None in Python)
key2: "" # empty string
key3: null # explicit null
key4: "null" # string "null"
```

## Additional Examples

For more advanced usage, see:

- **Encryption examples** - Using real encryption for sensitive data
- **TOML format** - Alternative configuration format
- **INI format** - Legacy configuration format
- **Schema validation** - Complex validation rules
- **CLI usage** - Managing configs from command line

## Learn More

- [VaultConfig Documentation](../../README.md)
- [API Reference](../../docs/api.rst)
- [Security Guidelines](../../docs/security.rst)
- [TOML Examples](../toml_config/README.md)
- [INI Examples](../ini_config/README.md)
- [YAML Specification](https://yaml.org/spec/1.2.2/)

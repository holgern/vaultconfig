# VaultConfig Examples

This directory contains comprehensive examples demonstrating various features of
`vaultconfig`.

## Available Examples

### 📄 [INI Configuration Examples](ini_config/)

Demonstrates INI format configuration with:

- ✅ Valid and invalid configuration handling
- 🔐 Password obscuring for sensitive fields
- 🌐 **DEFAULT section** support (SSH-style config)
- 🏢 Multi-environment setup (dev/staging/prod)
- 🔑 Case-sensitive option names
- 🎯 Section names with dots (e.g., `forge.example`)

**Key Features:**

- DEFAULT section inheritance (like SSH config)
- Value overrides per section
- Practical SSH-style and multi-host examples

```bash
cd ini_config
python example.py                    # Basic examples
python example_default_section.py   # DEFAULT section examples
```

### 📦 [TOML Configuration Examples](toml_config/)

Demonstrates TOML format configuration with:

- ✅ Valid and invalid configuration handling
- 🔐 Password obscuring for sensitive fields
- 📊 **Type preservation** (integers, booleans, arrays)
- 📦 **Nested structures** (tables and sub-tables)
- 🌍 Multi-environment configuration
- 🎯 Complete application config patterns

**Key Features:**

- Automatic type handling (no string conversion needed)
- Rich nested table support
- Arrays and complex data structures
- Dot notation for nested value access

```bash
cd toml_config
python example.py          # Basic examples
python example_advanced.py # Advanced patterns
```

### 🌐 [YAML Configuration Examples](yaml_config/)

Demonstrates YAML format configuration with:

- ✅ Valid and invalid configuration handling
- 🔐 Password obscuring for sensitive fields
- 📊 **Type preservation** (integers, booleans, arrays, null)
- 📦 **Nested structures** (clean indentation-based)
- 🌍 Multi-environment configuration
- 🎯 Complete application config patterns
- 📝 **Multi-line strings** (literal and folded)

**Key Features:**

- Human-readable indentation-based syntax
- Full type support including null values
- Multiple array syntax options (block and flow)
- Multi-line string support
- Most readable format for complex configs

```bash
cd yaml_config
python example.py          # Basic examples
python example_advanced.py # Advanced patterns
```

## Format Comparison

| Feature                | INI                 | TOML                       | YAML                    |
| ---------------------- | ------------------- | -------------------------- | ----------------------- |
| **Type preservation**  | ❌ All strings      | ✅ Auto (int, bool, float) | ✅ Auto + null          |
| **Nested structures**  | ⚠️ Sections only    | ✅ Tables & sub-tables     | ✅ Indentation          |
| **Arrays/Lists**       | ❌ Not supported    | ✅ Full support            | ✅ Full support         |
| **Null values**        | ❌ Not supported    | ❌ Not supported           | ✅ `null`               |
| **Multi-line strings** | ❌ Not supported    | ✅ `"""` delimiters        | ✅ `\|` and `>`         |
| **DEFAULT section**    | ✅ With inheritance | ❌ Not supported           | ❌ Not supported        |
| **Comments**           | ✅ `;` or `#`       | ✅ `#` only                | ✅ `#` only             |
| **Case sensitivity**   | ⚠️ Optional         | ✅ Always                  | ✅ Always               |
| **Readability**        | ⭐⭐⭐              | ⭐⭐⭐⭐                   | ⭐⭐⭐⭐⭐              |
| **Complexity**         | ⭐ (Simple)         | ⭐⭐ (Medium)              | ⭐⭐⭐ (Can be complex) |
| **Best for**           | SSH/systemd config  | App configuration          | Complex hierarchies     |

## Quick Start

### INI Example (SSH-Style)

```ini
[DEFAULT]
ServerAliveInterval = 45
Compression = yes

[forge.example]
User = hg
# Inherits ServerAliveInterval and Compression from DEFAULT
```

```python
from vaultconfig import ConfigManager
from pathlib import Path

manager = ConfigManager(config_dir=Path("./config"), format="ini")
config = manager.get_config("hosts")
forge = config.get_all()["forge.example"]
# forge has User='hg', ServerAliveInterval='45', Compression='yes'
```

### TOML Example (Application Config)

```toml
[database]
host = "localhost"
port = 5432
ssl_enabled = true

[database.pool]
max_connections = 20
timeout = 30
```

```python
from vaultconfig import ConfigManager
from pathlib import Path

manager = ConfigManager(config_dir=Path("./config"), format="toml")
config = manager.get_config("app")

# Access with dot notation
host = config.get("database.host")           # "localhost"
max_conn = config.get("database.pool.max_connections")  # 20 (integer preserved!)
```

### YAML Example (Clean Hierarchy)

```yaml
database:
  host: localhost
  port: 5432
  ssl_enabled: true
  pool:
    max_connections: 20
    timeout: 30
```

```python
from vaultconfig import ConfigManager
from pathlib import Path

manager = ConfigManager(config_dir=Path("./config"), format="yaml")
config = manager.get_config("app")

# Access with dot notation (same as TOML!)
host = config.get("database.host")           # "localhost"
max_conn = config.get("database.pool.max_connections")  # 20 (integer preserved!)
```

## Common Features (Both Formats)

All examples demonstrate:

- ✅ **Schema validation** with Pydantic
- 🔐 **Password obscuring** (not encryption!)
- ❌ **Error handling** and validation
- 📝 **Nested value access** with dot notation
- 🔒 **Optional encryption** support

## Requirements

### Basic (INI and TOML)

```bash
pip install vaultconfig pydantic cryptography
```

### With YAML Support

```bash
pip install vaultconfig[yaml]
# or
pip install vaultconfig pydantic cryptography PyYAML
```

## Security Notes

### Password Obscuring (Used in Examples)

- ⚠️ **NOT real encryption**
- Prevents casual viewing ("shoulder surfing")
- Anyone with vaultconfig can reveal passwords
- Good for development environments

### Real Encryption (Production)

```python
# Use encryption for production
manager = ConfigManager(
    config_dir="./config",
    format="toml",
    password="your-secure-password"  # Real encryption
)
```

## When to Use Each Format

### Use INI When:

- You need DEFAULT section inheritance
- Working with SSH/systemd-style configs
- Want simple flat key-value configuration
- All values can be strings
- Need compatibility with legacy systems

### Use TOML When:

- You need type preservation (integers, booleans)
- Working with complex nested structures
- Need arrays or lists
- Building modern application configuration
- Want clear, explicit table definitions

### Use YAML When:

- You need the most readable format
- Working with deeply nested hierarchies
- Need null value support
- Want multi-line string support
- Configuration is complex but must be human-editable
- Need maximum flexibility in data structures

## Learn More

- [VaultConfig Documentation](../docs/)
- [API Reference](../docs/api.rst)
- [Security Guide](../docs/security.rst)
- [GitHub Repository](https://github.com/holgern/vaultconfig)

## Contributing Examples

Have a useful example? Contributions are welcome!

1. Create a new directory with your example
2. Include a README.md with clear documentation
3. Add example config files and Python scripts
4. Submit a pull request

## License

All examples are part of the VaultConfig project and follow the same license.

---
title: "Architecture Documentation"
date: "1980-01-01"
generator: "archledger 0.1.1.dev13+g9edca5498"
arc42_template_version: "9.0-EN"
---

# Architecture Documentation

Generated from archledger records. Do not edit this generated file directly.

# Introduction and Goals

## System Overview

VaultConfig is a Python library that provides secure configuration management with
encryption support. It offers a CLI tool and a Python API for managing application
configurations in multiple file formats (TOML, INI, YAML) with password obscuring and
authenticated encryption.

## Stakeholders

| Role                   | Interest                                                                         |
| ---------------------- | -------------------------------------------------------------------------------- |
| Application developers | Simple Python API for loading/saving configs from Python applications            |
| DevOps/SRE engineers   | CLI tooling for secure config management in CI/CD, shell scripts, and deployment |
| Library consumers      | Embeddable config management; used internally by packages like `pywebdavserver`  |

## Goals

1. **Multiple format support**: Read and write TOML (default), INI, and YAML configs in
   a unified API.
2. **Password obfuscation**: Obscure sensitive values in config files via AES-CTR with
   base64 encoding to prevent casual viewing (shoulder-surfing).
3. **Config file encryption**: Strong authenticated encryption of entire config files
   using NaCl secretbox (XSalsa20-Poly1305) with PBKDF2 key derivation.
4. **Schema validation**: Optional Pydantic-based schema system for type validation and
   sensitive-field detection.
5. **CLI-first**: Full-featured CLI tool (`vaultconfig`) for shell-based operations,
   environment variable export (bash/zsh/fish/nushell/powershell), and running commands
   with config values.
6. **Secure by design**: Atomic file writes, 0600 file permissions, secure temp-file
   handling, and password validation.

## Requirements Overview

<!-- archledger: no accepted records for this section yet -->

## Quality Goals

<!-- archledger: no accepted records for this section yet -->

## Stakeholders

<!-- archledger: no accepted records for this section yet -->

# Architecture Constraints

## Technical Constraints

| Constraint               | Details                                                   | Rationale                                                               |
| ------------------------ | --------------------------------------------------------- | ----------------------------------------------------------------------- |
| Python >= 3.10           | Minimum runtime version                                   | Required for modern typing, `tomllib` (3.11+), and setuptools packaging |
| PyNaCl                   | Required for config file encryption                       | NaCl secretbox provides authenticated encryption (XSalsa20-Poly1305)    |
| cryptography >= 41.0     | Required for PBKDF2 key derivation and password obscuring | PBKDF2-HMAC-SHA256 with 600k iterations per OWASP 2023                  |
| click >= 8.0             | CLI framework dependency                                  | Declarative command groups, option handling, shell completion           |
| rich >= 13.0             | Terminal output formatting                                | Tables, syntax highlighting, colored output in CLI                      |
| pydantic >= 2.0          | Schema validation engine                                  | Type-safe config models, field metadata for sensitive marking           |
| tomli / tomli-w          | TOML read/write for Python < 3.11                         | Python 3.11+ has `tomllib` built-in; older versions use `tomli`         |
| PyYAML >= 6.0 (optional) | YAML support in `[yaml]` extra                            | Version >= 6.0 required for security fixes; lazy-loaded                 |

## Organizational Constraints

- Single-maintainer open-source project under MIT license.
- Distributed via PyPI as `vaultconfig` package.
- Follows semantic versioning via `setuptools_scm`.
- Type-checking enforced with mypy (`disallow_untyped_defs`, `strict_equality`).
- Linting via ruff.
- Test coverage tracked via codecov.

<!-- archledger: no accepted records for this section yet -->

# Context and Scope

## External Interfaces

### File System

VaultConfig reads and writes config files to a config directory (defaults to
`~/.config/vaultconfig` on Linux/macOS, `%APPDATA%\vaultconfig` on Windows). Config
directories contain one file per named configuration with a format-specific extension
(`.toml`, `.ini`, `.yaml`).

### Environment Variables

| Variable                       | Purpose                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------ |
| `VAULTCONFIG_DIR`              | Override the default config directory path                                     |
| `VAULTCONFIG_PASSWORD`         | Provide encryption password non-interactively                                  |
| `VAULTCONFIG_PASSWORD_COMMAND` | External command to retrieve encryption password (e.g., from password manager) |
| `VAULTCONFIG_PASSWORD_CHANGE`  | Set to `1` when changing password via external command                         |
| `VAULTCONFIG_PASSWORD_<NAME>`  | Per-config encryption password override                                        |
| `VAULTCONFIG_CIPHER_KEY`       | Custom 64-char hex cipher key for password obscuring                           |
| `VAULTCONFIG_CIPHER_KEY_FILE`  | Path to file containing hex cipher key                                         |

### Python API

Exposed via `vaultconfig.ConfigManager` and related classes. The public API surface
includes:

- `ConfigManager`: primary entry point for creating, reading, updating, and deleting
  configurations
- `ConfigEntry`: represents a single loaded configuration with getter/obscured-value
  handling
- `ConfigSchema`: Pydantic-based schema class for type validation
- `Obscurer`: configurable AES-CTR obscurer with custom key support
- `vaultconfig.crypt`: standalone encryption/decryption functions

### CLI

The `vaultconfig` CLI tool provides a Click-based command hierarchy:

- Config management: `init`, `list`, `show`, `get`, `set`, `unset`, `create`, `delete`,
  `copy`, `rename`
- Import/export: `export`, `import`, `export-env`
- Encryption: `encrypt set/remove/check`, `encrypt-file`, `decrypt-file`, `encrypt-dir`,
  `decrypt-dir`
- Execution: `run` (loads config as env vars and executes a subprocess)
- Validation: `validate` (against schema file)
- Key management: `obscure generate-key`

## System Context Diagram

```textdiagram
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Application  │────▶│   ConfigManager  │────▶│ File System   │
│  (Python API) │     │   (vaultconfig)  │     │ (.toml/.ini/  │
└──────────────┘     └────────┬─────────┘     │  .yaml files) │
                              │                └──────────────┘
                              │
                     ┌────────▼─────────┐
                     │   vaultconfig    │
                     │   CLI (click)    │
                     └────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼───┐  ┌───────▼──────┐  ┌─────▼──────┐
     │  Shell      │  │  CI/CD       │  │  Password  │
     │  (bash/zsh/ │  │  Pipelines   │  │  Manager   │
     │   fish/nu/  │  │              │  │  (via env) │
     │   powershell)│  │              │  │            │
     └────────────┘  └──────────────┘  └────────────┘
```

## Business Context

<!-- archledger: no accepted records for this section yet -->

## Technical Context

<!-- archledger: no accepted records for this section yet -->

# Solution Strategy

## Key Architectural Decisions

### 1. Format Handler Plugin Pattern

Configuration formats (TOML, INI, YAML) are abstracted behind the `ConfigFormat` ABC.
Each format implements `load()`, `dump()`, `get_extension()`, `detect()`, and
`get_name()`. This allows `ConfigManager` to operate format-agnostically. Formats are
discovered via a manual registry (`_FORMAT_REGISTRY`) rather than plugin auto-discovery
for simplicity.

### 2. Dual-Security Model: Obscuring + Encryption

VaultConfig provides two distinct security levels:

- **Password obscuring** (`vaultconfig.obscure`): AES-CTR with configurable key +
  base64. Purely cosmetic.
- **Config encryption** (`vaultconfig.crypt`): NaCl secretbox with PBKDF2-HMAC-SHA256
  (600k iterations). Cryptographically strong, suitable for protecting configs at rest.

This separation acknowledges that different use cases need different tradeoffs between
convenience and security.

### 3. Atomic File Writes with Secure Permissions

`_secure_write_file()` in `config.py` writes to a temporary file first, sets 0600
permissions, then atomically renames via `os.replace()`. On error, the temp file is
zeroed before deletion. This prevents partial/corrupted configs and race conditions in
permission setting.

### 4. Pydantic Schema as Optional Layer

Schema validation is optional and layered on top of the core config engine. The
`ConfigSchema` class wraps a Pydantic model, providing `validate()`,
`get_sensitive_fields()`, and `get_defaults()`. Sensitive fields (marked with
`json_schema_extra={"sensitive": True}`) are auto-obscured and auto-revealed.

### 5. Environment-Driven Password Sources

Encryption passwords can come from multiple sources, checked in priority order:

1. Per-config password in memory (`_config_passwords`)
2. Environment variable `VAULTCONFIG_PASSWORD_<NAME>`
3. Directory-level password (`_password`)
4. Interactive prompt (TTY only)

The password command mechanism (`VAULTCONFIG_PASSWORD_COMMAND`) uses `shlex.split()` and
`subprocess.run(shell=False)` for safe command execution.

### 6. Dotted Key Notation Throughout

Nested configuration keys are uniformly expressed with dot notation (`database.host`,
`nested.deep.key`). This convention is supported in `ConfigEntry.get()`,
`_set_nested_value()`, `_unset_nested_value()`, and `_obscure_nested_value()`. The CLI
maps dotted command arguments to nested dict structures.

## Strategy Items

<!-- archledger: no accepted records for this section yet -->

# Building Block View

## Level 1: System Context

VaultConfig is a monolithic Python package with no external service dependencies at
runtime. It operates purely on the local filesystem.

## Level 2: Package Decomposition

```textdiagram
┌───────────────────────────────────────────────────────────────┐
│                       vaultconfig                            │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   cli.py     │  │  config.py   │  │   formats/        │  │
│  │  (Click CLI) │──│ ConfigManager│──│  ├─ base.py       │  │
│  │              │  │ ConfigEntry  │  │  ├─ toml_format.py│  │
│  └──────────────┘  └──────┬───────┘  │  ├─ ini_format.py │  │
│                           │          │  └─ yaml_format.py│  │
│              ┌────────────┼──────────────┐                │  │
│              │            │              │                │  │
│  ┌───────────▼──┐ ┌───────▼──────┐ ┌────▼──────────┐    │  │
│  │  crypt.py   │ │ obscure.py  │ │  schema.py    │    │  │
│  │ NaCl        │ │ AES-CTR     │ │  ConfigSchema │    │  │
│  │ secretbox   │ │ Obscurer    │ │  FieldDef     │    │  │
│  │ PBKDF2      │ │             │ │               │    │  │
│  └──────────────┘ └──────────────┘ └───────────────┘    │  │
│                                                           │  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │  │
│  │   io.py      │  │ env_export.  │  │ exceptions.py │   │  │
│  │ load/dump    │  │  py          │  │ VaultConfig   │   │  │
│  │ mappings     │  │ shell export │  │  Error tree   │   │  │
│  └──────────────┘  └──────────────┘  └───────────────┘   │  │
└───────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

| Module          | Responsibility                                              | Key Classes/Functions                                                          |
| --------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `config.py`     | Core config manager, file I/O, encryption/orchestration     | `ConfigManager`, `ConfigEntry`, `_secure_write_file`                           |
| `cli.py`        | Click-based command-line interface                          | `main()`, all `@main.command()` subcommands                                    |
| `crypt.py`      | NaCl secretbox encryption/decryption, PBKDF2 key derivation | `encrypt()`, `decrypt()`, `derive_key()`, `get_password()`                     |
| `obscure.py`    | AES-CTR password obscuring with configurable keys           | `Obscurer`, `obscure()`, `reveal()`                                            |
| `schema.py`     | Pydantic-based schema validation                            | `ConfigSchema`, `FieldDef`, `create_simple_schema()`                           |
| `formats/`      | Format abstraction layer (TOML, INI, YAML)                  | `ConfigFormat` (ABC), `TOMLFormat`, `INIFormat`, `YAMLFormat`                  |
| `io.py`         | Shared file read/parse helpers for CLI                      | `load_mapping()`, `dump_mapping()`, `load_mapping_file()`                      |
| `env_export.py` | Shell environment variable export formatting                | `flatten_dict()`, `filter_dict()`, `format_env_export()`, `detect_shell()`     |
| `exceptions.py` | Exception hierarchy                                         | `VaultConfigError` → `EncryptionError`, `DecryptionError`, `FormatError`, etc. |

## Dependency Graph (internal)

```textdiagram
config.py ──▶ crypt.py
           ──▶ obscure.py
           ──▶ schema.py
           ──▶ formats/
           ──▶ exceptions.py

cli.py    ──▶ config.py
           ──▶ io.py
           ──▶ env_export.py
           ──▶ exceptions.py

io.py     ──▶ formats/

__init__.py ──▶ config.py, crypt.py, obscure.py, schema.py, exceptions.py
```

<!-- archledger: no accepted records for this section yet -->

# Runtime View

## Scenario 1: Loading Encrypted Config

```textdiagram
User/CLI                  ConfigManager              crypt.py              File System
   │                          │                         │                      │
   │  load config "db"        │                         │                      │
   ├─────────────────────────▶│                         │                      │
   │                          │  read config file       │                      │
   │                          ├─────────────────────────┼─────────────────────▶│
   │                          │                         │       bytes          │
   │                          │◀────────────────────────┼──────────────────────│
   │                          │                         │                      │
   │                          │  is_encrypted(data)?    │                      │
   │                          ├────────────────────────▶│                      │
   │                          │      True              │                      │
   │                          │◀────────────────────────│                      │
   │                          │                         │                      │
   │                          │  get_password()         │                      │
   │                          │  (env -> command -> TTY) │                      │
   │                          ├────────────────────────▶│                      │
   │                          │      password           │                      │
   │                          │◀────────────────────────│                      │
   │                          │                         │                      │
   │                          │  decrypt(data, pw)      │                      │
   │                          ├────────────────────────▶│                      │
   │                          │  plaintext bytes        │                      │
   │                          │◀────────────────────────│                      │
   │                          │                         │                      │
   │                          │  format_handler.load()  │                      │
   │                          │  ConfigSchema.validate()│                      │
   │                          │                         │                      │
   │  ConfigEntry returned    │                         │                      │
   │◀─────────────────────────│                         │                      │
```

## Scenario 2: CLI `set` with --obscure

```textdiagram
CLI                      ConfigManager              obscure.py              File System
 │                          │                         │                      │
 │  vaultconfig set db      │                         │                      │
 │  password=secret         │                         │                      │
 │  --obscure               │                         │                      │
 ├─────────────────────────▶│                         │                      │
 │                          │                         │                      │
 │                          │  _obscurer.obscure()    │                      │
 │                          ├────────────────────────▶│                      │
 │                          │  AES-CTR base64 string  │                      │
 │                          │◀────────────────────────│                      │
 │                          │                         │                      │
 │                          │  _save_config(name)     │                      │
 │                          │  _secure_write_file()   │─────────────────────▶│
 │                          │                         │      atomic write    │
 │                          │                         │◀─────────────────────│
 │  ✓ Updated config: db   │                         │                      │
 │◀─────────────────────────│                         │                      │
```

## Scenario 3: `vaultconfig run` Subprocess

```textdiagram
CLI               ConfigManager    env_export.py    OS
 │                     │                │              │
 │  vaultconfig run    │                │              │
 │  database --reveal  │                │              │
 │  python script.py   │                │              │
 ├────────────────────▶│                │              │
 │                     │  get_config() + get_all()     │
 │                     │  flatten_dict()│              │
 │                     ├───────────────▶│              │
 │                     │  flat keys     │              │
 │                     │◀───────────────│              │
 │                     │                │              │
 │                     │  build env vars (uppercase,   │
 │                     │  prefix), subprocess.Popen()  │
 │                     ├──────────────────────────────▶│
 │                     │              exit code         │
 │                     │◀──────────────────────────────│
 │  exit code          │                │              │
 │◀────────────────────│                │              │
```

<!-- archledger: no accepted records for this section yet -->

# Deployment View

## Deployment Context

VaultConfig is a library deployed alongside Python applications, not a standalone
service. It has no network interfaces, no daemon process, and no database.

## Distribution Channels

| Channel | Artifact                                                                                   |
| ------- | ------------------------------------------------------------------------------------------ |
| PyPI    | `vaultconfig` package (sdist + wheel)                                                      |
| pip     | `pip install vaultconfig`, `pip install vaultconfig[yaml]`, `pip install vaultconfig[dev]` |
| Source  | GitHub repository, `git clone` + `pip install -e .`                                        |

## Installation Topology

```textdiagram
┌─────────────────────────────────────────────────────────┐
│                   Developer Machine                      │
│                                                          │
│  pip install vaultconfig                                 │
│  vaultconfig init --format toml                          │
│  vaultconfig set database host=localhost --create        │
│  vaultconfig run database python app.py                  │
│                                                          │
│  Config Directory: ~/.config/vaultconfig/                │
│    database.toml                                         │
│    secrets.toml  (encrypted)                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   CI/CD Pipeline / Server                │
│                                                          │
│  export VAULTCONFIG_PASSWORD=$(get-secret db-pass)       │
│  vaultconfig export-env database --prefix DB_ --reveal | │
│  eval $(vaultconfig export-env database --reveal)        │
│  vaultconfig run production-db ./deploy.sh               │
│                                                          │
│  Password from: env var, external command, or keychain   │
└─────────────────────────────────────────────────────────┘
```

## File Layout

```
vaultconfig/
├── vaultconfig/
│   ├── __init__.py          # Public API exports
│   ├── _version.py          # Auto-generated by setuptools_scm
│   ├── cli.py               # Click CLI (2175 lines)
│   ├── config.py            # ConfigManager, ConfigEntry, file I/O
│   ├── crypt.py             # NaCl secretbox + PBKDF2
│   ├── obscure.py           # AES-CTR obscurer
│   ├── schema.py            # Pydantic schema
│   ├── io.py                # File read/parse helpers
│   ├── env_export.py        # Shell env var export
│   ├── exceptions.py        # Exception hierarchy
│   ├── py.typed             # PEP 561 marker
│   └── formats/
│       ├── __init__.py
│       ├── base.py          # ConfigFormat ABC
│       ├── toml_format.py
│       ├── ini_format.py
│       └── yaml_format.py
├── pyproject.toml           # Build config, dependencies, tool settings
├── LICENSE                  # MIT
├── README.md
└── .archledger/             # Architecture documentation
```

<!-- archledger: no accepted records for this section yet -->

# Cross-cutting Concepts

## Security Model

### Password Observability

VaultConfig implements a layered security model with clear boundaries:

| Layer      | Mechanism               | Algorithm                                                            | Key Management                                                       | Reversible?                 |
| ---------- | ----------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- | --------------------------- |
| Obscuring  | `Obscurer`              | AES-CTR (16-byte IV per operation)                                   | 32-byte key: default hardcoded or custom via env/key file/passphrase | Yes (by design)             |
| Encryption | `crypt.encrypt/decrypt` | NaCl secretbox (XSalsa20-Poly1305) + PBKDF2-HMAC-SHA256 (600k iters) | 32-byte key from PBKDF2 + 16-byte salt per file                      | Yes (with correct password) |

The obscuring layer is deliberately weak. The `Obscurer` class logs a security warning
on first use, and the module docstring explicitly states this is obfuscation only.
Custom cipher keys improve the situation by preventing cross-application password
revelation, but do not constitute real encryption.

### File Security

- All config files are written with 0600 permissions (owner read/write only).
- Files are written atomically via temp file + `os.replace()`.
- On write failure, temp files are zeroed before deletion.
- `os.fsync()` ensures data is flushed to disk before rename.
- Config names are sanitized via `_validate_config_name()` to prevent path traversal.

### Password Handling

- Encryption passwords are never stored; they are derived per-session from env vars,
  external commands, or interactive prompts.
- `VAULTCONFIG_PASSWORD_COMMAND` uses `shlex.split()` + `subprocess.run(shell=False)` to
  prevent shell injection.
- Password validation (`check_password()`) enforces minimum length (4 chars), warns
  about strength (< 12 chars), and normalizes Unicode (NFKC).
- Weak/common password detection warns on values like "password", "123456", "admin",
  etc.

## Error Handling

Exception hierarchy rooted at `VaultConfigError`:

```textdiagram
VaultConfigError
├── EncryptionError
├── DecryptionError
│   └── InvalidPasswordError
├── FormatError
├── SchemaValidationError
├── ConfigNotFoundError
└── ConfigExistsError
```

All CLI commands catch `VaultConfigError` at the top level and exit with code 1,
printing the error message via Rich console.

## Format Abstraction

The `ConfigFormat` ABC enforces a uniform interface across TOML, INI, and YAML:

```python
class ConfigFormat(ABC):
    @abstractmethod
    def load(self, data: str) -> dict[str, Any]: ...

    @abstractmethod
    def dump(self, data: dict[str, Any]) -> str: ...

    @abstractmethod
    def get_extension(self) -> str: ...

    @classmethod
    @abstractmethod
    def detect(cls, data: str) -> bool: ...

    @classmethod
    @abstractmethod
    def get_name(cls) -> str: ...
```

Format handlers are registered in a plain dict (`_FORMAT_REGISTRY` in `config.py`). No
plugin auto-discovery is used; the registry is explicitly populated at module level.

Optional dependencies are lazy: `YAMLFormat` checks `HAS_YAML` at load/dump time and
raises `FormatError` with an installation hint if PyYAML is missing. Similarly,
`TOMLFormat` checks for `tomli` availability on Python < 3.11.

## Type Safety

- Full type annotations throughout the codebase.
- `from __future__ import annotations` in every module.
- mypy configured with strict settings: `disallow_untyped_defs`,
  `disallow_incomplete_defs`, `strict_equality`, `warn_unreachable`.
- PEP 561 marker file (`py.typed`) signals type information availability to downstream
  consumers.

## Logging

Uses Python's standard `logging` module. Key log points:

- `config.py`: config load/save events at DEBUG/INFO level
- `obscure.py`: security warning at WARNING level on first obscure() call per Obscurer
  instance
- `config.py`: temp file cleanup failures at WARNING level
- `config.py`: encryption status check failures at ERROR level

<!-- archledger: no accepted records for this section yet -->

# Architecture Decisions

## ADR-1: Use NaCl secretbox for Config Encryption

**Status**: Accepted

**Context**: Config files containing secrets (API keys, database passwords) need strong
at-rest encryption.

**Decision**: Use NaCl secretbox (XSalsa20-Poly1305) via PyNaCl, combined with
PBKDF2-HMAC-SHA256 key derivation at 600,000 iterations as recommended by OWASP 2023.

**Rationale**:

- NaCl secretbox is a well-audited, misuse-resistant authenticated encryption
  construction.
- PBKDF2 with high iteration count resists brute-force attacks on weak passwords.
- Random 16-byte salt per encryption prevents rainbow table attacks.
- Random 24-byte nonce per encryption ensures semantic security.

**Alternatives considered**:

- AES-GCM: Requires careful nonce management; secretbox is simpler to use correctly.
- Fernet (cryptography library): Time-limited tokens add unnecessary complexity for
  config files.

**Evidence**: `crypt.py` lines 110-151 (encrypt), 154-233 (decrypt), 70-107
(derive_key).

---

## ADR-2: Two-Tier Security (Obscuring + Encryption)

**Status**: Accepted

**Context**: Some users need basic "don't show passwords on screen" protection; others
need real at-rest encryption. A single security mechanism cannot serve both without
frustrating one group.

**Decision**: Provide two separate, clearly labeled mechanisms:

1. `Obscurer` class with AES-CTR + configurable key for casual password hiding.
2. `crypt.encrypt/decrypt` with NaCl secretbox for strong at-rest encryption.

**Rationale**:

- Obscuring is intentionally reversible without a password (the code/docstrings say so
  explicitly).
- Encryption is cryptographically strong and irreversible without the password.
- Users choose the right tool for their threat model.
- Inspired by rclone's config password obscuring approach but uses a
  vaultconfig-specific key.

**Evidence**: `obscure.py` lines 1-24 (module docstring warning), `Obscurer.obscure()`
lines 168-213 (security warning log).

---

## ADR-3: Format Abstraction via ABC + Manual Registry

**Status**: Accepted

**Context**: Need to support TOML, INI, and YAML without format-specific code in the
core config manager.

**Decision**: Define `ConfigFormat` ABC with `load/dump/get_extension/detect/get_name`,
implement per format, register in a plain dict rather than using plugin auto-discovery.

**Rationale**:

- Manual registry is simpler than entry-point-based plugin discovery for three formats.
- ABC enforces interface consistency.
- Each format handler can have format-specific logic (e.g., INI's DEFAULT section
  inheritance, YAML's lazy import, TOML's Python version branching).

**Evidence**: `formats/base.py`, `formats/toml_format.py`, `formats/ini_format.py`,
`formats/yaml_format.py`.

---

## ADR-4: Click-based CLI with Rich Output

**Status**: Accepted

**Context**: Need a CLI that is both interactive (TTY prompts) and scriptable (JSON
output, exit codes).

**Decision**: Use Click for command structure/option parsing and Rich for formatted
terminal output (tables, syntax highlighting, colored status).

**Rationale**:

- Click's decorator-based command groups map naturally to the config management command
  hierarchy.
- Click handles TTY detection (`click.prompt`, `click.confirm`, `hide_input`).
- Rich provides readable tables for `list` and `show`, syntax highlighting for shell
  commands in `export-env --dry-run`.
- Both are mature, well-maintained libraries.

**Evidence**: `cli.py` 76-80 (Click group), 27 (Rich Console), 200-209 (Rich Table in
`list`), 1057-1118 (Rich Panel/Syntax in `export-env --dry-run`).

---

## ADR-5: Atomic File Writes

**Status**: Accepted

**Context**: Config file corruption from partial writes or crashes is unacceptable.

**Decision**: Write all config data to a temp file, `fsync`, then `os.replace()`
atomically to the target path. Set 0600 permissions on the temp file before writing any
data.

**Rationale**:

- `os.replace()` is atomic on both POSIX and Windows.
- Setting permissions before writing prevents a race window where data exists with
  default permissions.
- On failure, zero the temp file before deletion to prevent data leakage.
- `os.fsync()` ensures data reaches disk before the rename.

**Evidence**: `config.py` lines 81-149 (`_secure_write_file`).

<!-- archledger: no accepted records for this section yet -->

# Quality Requirements

## Quality Goals

| Quality Attribute | Goal                                                                          | Implementation                                                                     |
| ----------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Security          | Config files must be protectable at rest with strong authenticated encryption | NaCl secretbox + PBKDF2 in `crypt.py`                                              |
| Data Integrity    | Config files must never be corrupted by partial writes                        | Atomic writes via temp file + `os.replace()` + `fsync()` in `_secure_write_file()` |
| Usability         | CLI must support both interactive (TTY) and scriptable (JSON, exit codes) use | Click prompts + `--output json` options                                            |
| Portability       | Must run on Linux, macOS, and Windows with consistent behavior                | pathlib, `os.replace()` (atomic on both), platform-specific default config dirs    |
| Correctness       | Strong type checking throughout codebase                                      | Full mypy strict mode, `py.typed` marker                                           |
| Interoperability  | Support TOML, INI, YAML formats                                               | `ConfigFormat` ABC with format-specific handlers                                   |
| Shell Integration | Native support for bash, zsh, fish, nushell, powershell                       | `env_export.py` with format_env_export() per shell                                 |

## Quality Scenarios

### Security Scenario 1: Encrypt Config

- **Stimulus**: User invokes `vaultconfig encrypt set`
- **Response**: All config files are re-encrypted with NaCl secretbox using a
  PBKDF2-derived key
- **Measure**: Encryption uses cryptographically random 16-byte salt + 24-byte nonce;
  write is atomic with 0600 permissions

### Security Scenario 2: Password from External Command

- **Stimulus**: `VAULTCONFIG_PASSWORD_COMMAND=pass show vaultconfig/db` is set
- **Response**: Password is retrieved via `subprocess.run(shell=False)` with
  `shlex.split()` parsing
- **Measure**: No shell injection possible; command output is stripped and validated

### Integrity Scenario: Crash During Write

- **Stimulus**: Process crashes or power fails during `_save_config()`
- **Response**: Temp file is abandoned; original file is untouched since `os.replace()`
  is atomic
- **Measure**: Config file is never left in a partial/corrupt state

### Usability Scenario: Non-TTY Environment

- **Stimulus**: `vaultconfig show database` in a CI pipeline without a TTY
- **Response**: Password is obtained from `VAULTCONFIG_PASSWORD` env var or
  `VAULTCONFIG_PASSWORD_COMMAND`
- **Measure**: No interactive prompt blocks execution; `getpass.getpass()` is guarded by
  `sys.stdin.isatty()`

## Quality Requirements Overview

<!-- archledger: no accepted records for this section yet -->

## Quality Scenarios

<!-- archledger: no accepted records for this section yet -->

# Risks and Technical Debt

## Risks

| Risk                               | Impact                                 | Likelihood                   | Mitigation                                                                                                                  |
| ---------------------------------- | -------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Lost encryption password           | Permanent data loss                    | Low (with password managers) | Clear warnings in docs; `VAULTCONFIG_PASSWORD_COMMAND` for automation                                                       |
| PyNaCl supply chain compromise     | All encrypted configs decryptable      | Very low                     | Pin dependency versions; PyNaCl is a widely audited C library wrapper                                                       |
| Weak user password for encryption  | Brute-force feasible                   | Medium                       | Password validation enforces >=4 chars, warns <12 chars, detects common passwords; PBKDF2 600k iterations slows brute-force |
| YAML deserialization vulnerability | Code execution via crafted YAML        | Low (PyYAML >=6.0 required)  | `yaml.safe_load()` used exclusively; PyYAML >=6.0 enforced in optional dependency                                           |
| Temp file data leakage on crash    | Sensitive data in uncleaned temp files | Low                          | Temp files zeroed before deletion on write failure; 0600 permissions set before writing                                     |
| Custom cipher key loss             | Cannot reveal obscured passwords       | Low                          | Key generation documented; users warned to back up keys                                                                     |

## Technical Debt

| Item                                                                 | Location                                        | Notes                                                                                                                                                                      |
| -------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ask_password` parameter in `_get_manager()`                         | `cli.py` line 1906                              | Marked as deprecated but still accepted; can be removed after CLI callers are audited                                                                                      |
| Module-level `obscure/reveal/is_obscured` functions                  | `obscure.py` lines 383-438                      | Singleton-pattern wrappers for backward compatibility; new code should use `Obscurer` instances directly                                                                   |
| Format detection by counting file extensions                         | `cli.py` lines 1966-1991 (`_detect_format`)     | Simple heuristic, no content-based detection; fails on mixed-format directories                                                                                            |
| No streaming read/write for large configs                            | `config.py` `_load_config`/`_save_config`       | Entire config file is read into memory; acceptable for config files (typically < 1MB)                                                                                      |
| Duplicate format handler helpers                                     | `cli.py` lines 2089-2109 vs `io.py` lines 14-25 | Both modules define `_get_format_handler()` with identical logic; should be consolidated into `formats/` or `io.py`                                                        |
| CLI `encrypt` command group and `encrypt-file`/`encrypt-dir` overlap | `cli.py`                                        | The `encrypt` group provides `set/remove/check`, while `encrypt-file`/`decrypt-file` and `encrypt-dir`/`decrypt-dir` are top-level commands with overlapping functionality |

## Known Limitations

- Password obscuring uses a hardcoded default key; while custom keys improve this, the
  mechanism is still obfuscation.
- No support for key rotation or re-keying encrypted configs without decrypt/encrypt
  cycles.
- No built-in integration with hardware security modules (HSMs) or cloud KMS.
- Config names are restricted to simple filenames (no path separators).

## Risk Overview

<!-- archledger: no accepted records for this section yet -->

# Glossary

| Term                   | Definition                                                                                                                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Config Directory**   | A directory on the filesystem where vaultconfig stores configuration files. Defaults to `~/.config/vaultconfig` (Linux/macOS) or `%APPDATA%\vaultconfig` (Windows). Overridable via `VAULTCONFIG_DIR` or `--config-dir`. |
| **ConfigManager**      | The central class (`vaultconfig.config.ConfigManager`) that orchestrates reading, writing, encrypting, and validating configs. Holds a format handler, optional schema, and a dict of `ConfigEntry` objects.             |
| **ConfigEntry**        | Represents a single named configuration loaded from a file. Provides `get()` (with dot notation), `get_all()` (with optional reveal), and tracks sensitive field names.                                                  |
| **Obscuring**          | AES-CTR encryption with a known key + base64 encoding. Provides casual privacy (shoulder-surfing protection), NOT real security. The `Obscurer` class supports custom keys.                                              |
| **Encryption**         | NaCl secretbox (XSalsa20-Poly1305) authenticated encryption with PBKDF2-HMAC-SHA256 key derivation. Provides cryptographically strong at-rest protection. Files are prefixed with `VAULTCONFIG_ENCRYPT_V1:`.             |
| **Sensitive Field**    | A config field marked with `sensitive=True` in a Pydantic schema (via `json_schema_extra`). Such fields are automatically obscured on write and auto-revealed on read when using `get_all(reveal_secrets=True)`.         |
| **Atomic Write**       | The pattern of writing to a temp file, calling `fsync`, then atomically renaming to the target path via `os.replace()`. Prevents partial/corrupt files.                                                                  |
| **ConfigFormat**       | Abstract base class (`vaultconfig.formats.base.ConfigFormat`) defining the interface for format handlers: `load()`, `dump()`, `get_extension()`, `detect()`, `get_name()`.                                               |
| **PBKDF2**             | Password-Based Key Derivation Function 2. Used with HMAC-SHA256 at 600,000 iterations to derive a 32-byte NaCl key from a user password, plus a random 16-byte salt.                                                     |
| **Dot Notation**       | Convention for nested config keys using dots as separators (e.g., `database.host`, `nested.deep.key`). Supported across `ConfigEntry.get()`, `_set_nested_value()`, and the CLI.                                         |
| **Environment Export** | The CLI feature (`vaultconfig export-env`) that flattens a config into shell environment variable assignments. Supports bash, zsh, fish, nushell, and powershell output formats.                                         |
| **`vaultconfig run`**  | CLI subcommand that loads a config, flattens it into environment variables, and executes a subprocess with those variables set. Similar to `dotenv run`.                                                                 |
| **Format Handler**     | A concrete implementation of `ConfigFormat` for a specific file format: `TOMLFormat`, `INIFormat`, or `YAMLFormat`.                                                                                                      |
| **ConfigSchema**       | A Pydantic-based wrapper (`vaultconfig.schema.ConfigSchema`) that validates config data against a model and discovers sensitive fields. Provides `validate()`, `get_sensitive_fields()`, `get_defaults()`.               |

<!-- archledger: no accepted records for this section yet -->

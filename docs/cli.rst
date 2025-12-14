Command Line Interface
======================

VaultConfig provides a powerful CLI for managing configurations from the command line.

Global Options
--------------

.. code-block:: bash

   vaultconfig --version  # Show version
   vaultconfig --help     # Show help

Commands Overview
-----------------

- ``init`` - Initialize a new config directory
- ``list`` - List all configurations
- ``show`` - Show a configuration
- ``create`` - Create a new configuration
- ``set`` - Set configuration values
- ``get`` - Get a configuration value
- ``unset`` - Remove configuration keys
- ``delete`` - Delete a configuration
- ``copy`` - Copy a configuration
- ``rename`` - Rename a configuration
- ``export`` - Export a configuration to a file
- ``import`` - Import a configuration from a file
- ``export-env`` - Export configuration as environment variables
- ``run`` - Run a command with config values as environment variables
- ``encrypt`` - Manage encryption (command group with set, remove, check subcommands)
- ``encrypt-file`` - Encrypt a specific config file
- ``decrypt-file`` - Decrypt a specific config file
- ``encrypt-dir`` - Encrypt all configs in directory
- ``decrypt-dir`` - Decrypt all configs in directory
- ``encryption`` - Manage encryption settings (command group)
- ``validate`` - Validate a configuration against a schema
- ``obscure`` - Manage password obscuring (command group)

Default Config Directory
------------------------

VaultConfig uses a platform-specific default config directory:

- **Linux/macOS**: ``~/.config/vaultconfig``
- **Windows**: ``%APPDATA%\vaultconfig``

You can override this with:

- ``-d, --config-dir`` option on any command
- ``VAULTCONFIG_DIR`` environment variable

Most commands accept either a positional ``CONFIG_DIR`` argument or the ``-d`` option.

init Command
------------

Initialize a new configuration directory.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig init [OPTIONS]

Options
~~~~~~~

- ``-d, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format: toml (default), ini, or yaml
- ``-e, --encrypt`` - Enable encryption (prompts for password)
- ``--help`` - Show help message

Examples
~~~~~~~~

Initialize default directory:

.. code-block:: bash

   vaultconfig init

Initialize custom directory:

.. code-block:: bash

   vaultconfig init -d ./myapp-config

With specific format:

.. code-block:: bash

   vaultconfig init --format yaml

With encryption:

.. code-block:: bash

   vaultconfig init --encrypt
   # Prompts for password

list Command
------------

List all configurations in a directory.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig list [CONFIG_DIR] [OPTIONS]

Arguments
~~~~~~~~~

- ``CONFIG_DIR`` - Path to config directory (optional, uses default if not specified)

Options
~~~~~~~

- ``-d, --dir PATH`` - Config directory (alternative to positional argument)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-o, --output TEXT`` - Output format: table (default), json, or plain
- ``--help`` - Show help message

Examples
~~~~~~~~

.. code-block:: bash

   # List all configs (uses default directory)
   vaultconfig list

   # List with positional argument
   vaultconfig list ./myapp-config

   # List with option
   vaultconfig list -d ./myapp-config

   # List with explicit format
   vaultconfig list ./myapp-config --format toml

   # List as JSON
   vaultconfig list --output json

   # List as plain names (one per line)
   vaultconfig list --output plain

Output Example
~~~~~~~~~~~~~~

.. code-block:: text

   Configurations
   ┌──────────┬───────────┐
   │ Name     │ Encrypted │
   ├──────────┼───────────┤
   │ database │ Yes       │
   │ api      │ Yes       │
   └──────────┴───────────┘

show Command
------------

Display a configuration's contents.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig show [OPTIONS] NAME

Arguments
~~~~~~~~~

- ``NAME`` - Name of the configuration to show

Options
~~~~~~~

- ``-d, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-r, --reveal`` - Reveal obscured passwords
- ``-o, --output TEXT`` - Output format: pretty (default), json, yaml, or toml
- ``--help`` - Show help message

Examples
~~~~~~~~

Show with obscured passwords (uses default directory):

.. code-block:: bash

   vaultconfig show database

Show with revealed passwords:

.. code-block:: bash

   vaultconfig show database --reveal

Show from custom directory:

.. code-block:: bash

   vaultconfig show -d ./myapp-config database

Show as JSON:

.. code-block:: bash

   vaultconfig show database --output json

Output Example
~~~~~~~~~~~~~~

.. code-block:: text

   Configuration: database

   host: localhost
   port: 5432
   username: myuser
   password: eCkF3jAC0hI7TEpStvKvWf64gocJJQ

   Note: Use --reveal to show obscured passwords

delete Command
--------------

Delete a configuration.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig delete [OPTIONS] NAME

Arguments
~~~~~~~~~

- ``NAME`` - Name of the configuration to delete

Options
~~~~~~~

- ``-d, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-y, --yes`` - Skip confirmation prompt
- ``--help`` - Show help message

Examples
~~~~~~~~

With confirmation (uses default directory):

.. code-block:: bash

   vaultconfig delete database
   # Prompts: "Are you sure you want to delete config 'database'? [y/N]:"

Skip confirmation:

.. code-block:: bash

   vaultconfig delete database --yes

With custom directory:

.. code-block:: bash

   vaultconfig delete -d ./myapp-config database

encrypt Command Group
---------------------

Manage encryption for configuration files.

encrypt set
~~~~~~~~~~~

Set or change the encryption password for all configs in a directory.

Syntax:

.. code-block:: bash

   vaultconfig encrypt set [OPTIONS]

Options:

- ``-d, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-p, --password TEXT`` - Encryption password (prompts if not provided)
- ``--help`` - Show help message

Examples:

.. code-block:: bash

   # Set password (uses default directory)
   vaultconfig encrypt set
   # Prompts for new password twice

   # Set password for custom directory
   vaultconfig encrypt set -d ./myapp-config

   # Set password non-interactively
   vaultconfig encrypt set --password "my-password"

   # Using environment variable
   export VAULTCONFIG_PASSWORD="my-password"
   vaultconfig encrypt set

encrypt remove
~~~~~~~~~~~~~~

Remove encryption from all configs (decrypt to plaintext).

Syntax:

.. code-block:: bash

   vaultconfig encrypt remove [OPTIONS]

Options:

- ``-d, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-y, --yes`` - Skip confirmation prompt
- ``--help`` - Show help message

Examples:

.. code-block:: bash

   # Remove encryption (prompts for confirmation)
   vaultconfig encrypt remove

   # Remove from custom directory
   vaultconfig encrypt remove -d ./myapp-config

   # Skip confirmation
   vaultconfig encrypt remove --yes

   # Using environment variable for password
   export VAULTCONFIG_PASSWORD="my-password"
   vaultconfig encrypt remove --yes

encrypt check
~~~~~~~~~~~~~

Check encryption status of all configs in a directory.

Syntax:

.. code-block:: bash

   vaultconfig encrypt check [OPTIONS]

Options:

- ``-d, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``--help`` - Show help message

Examples:

.. code-block:: bash

   # Check encryption status (uses default directory)
   vaultconfig encrypt check

   # Check custom directory
   vaultconfig encrypt check -d ./myapp-config

Output Examples:

.. code-block:: text

   # All encrypted
   All configs (3) are encrypted
    Encryption Status
   ┏━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ Name     ┃ Encrypted ┃
   ┡━━━━━━━━━━╇━━━━━━━━━━━┩
   │ database │ Yes       │
   │ api      │ Yes       │
   │ cache    │ Yes       │
   └──────────┴───────────┘

   # None encrypted
   All configs (2) are NOT encrypted
    Encryption Status
   ┏━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ Name     ┃ Encrypted ┃
   ┡━━━━━━━━━━╇━━━━━━━━━━━┩
   │ database │ No        │
   │ api      │ No        │
   └──────────┴───────────┘

   # Mixed
   2/3 configs are encrypted
    Encryption Status
   ┏━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ Name     ┃ Encrypted ┃
   ┡━━━━━━━━━━╇━━━━━━━━━━━┩
   │ database │ Yes       │
   │ api      │ Yes       │
   │ cache    │ No        │
   └──────────┴───────────┘

Environment Variables
---------------------

VAULTCONFIG_DIR
~~~~~~~~~~~~~~~

Set the default config directory:

.. code-block:: bash

   export VAULTCONFIG_DIR=./myapp-config
   vaultconfig list  # Uses ./myapp-config

This allows you to omit the ``-d`` option on all commands.

VAULTCONFIG_PASSWORD
~~~~~~~~~~~~~~~~~~~~

Set the password for encrypted configs:

.. code-block:: bash

   export VAULTCONFIG_PASSWORD="my-secure-password"
   vaultconfig list

This avoids interactive password prompts.

VAULTCONFIG_PASSWORD_COMMAND
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a command to retrieve the password (e.g., from a password manager):

.. code-block:: bash

   export VAULTCONFIG_PASSWORD_COMMAND="pass show vaultconfig/myapp"
   vaultconfig list ./myapp-config

The command should output the password to stdout.

VAULTCONFIG_PASSWORD_CHANGE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set to "1" when changing passwords:

.. code-block:: bash

   export VAULTCONFIG_PASSWORD_CHANGE=1
   export VAULTCONFIG_PASSWORD_COMMAND="pass show vaultconfig/myapp-new"
   vaultconfig encrypt set ./myapp-config

run Command
-----------

Run a command with configuration values loaded as environment variables. This is similar
to ``dotenv run`` but works with VaultConfig configurations.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig run [OPTIONS] NAME COMMAND [ARGS]...

Arguments
~~~~~~~~~

- ``NAME`` - Name of the configuration to load
- ``COMMAND`` - Command to execute with the config as environment variables
- ``ARGS`` - Arguments to pass to the command

Options
~~~~~~~

- ``-d, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``--prefix TEXT`` - Prefix for environment variable names (default: CONFIG_NAME + "_")
- ``--reveal`` - Reveal obscured passwords
- ``--uppercase / --no-uppercase`` - Convert keys to uppercase (default: true)
- ``--override / --no-override`` - Override existing environment variables (default: true)
- ``--help`` - Show help message

How It Works
~~~~~~~~~~~~

1. Loads the specified configuration
2. Flattens nested configs (e.g., ``database.host`` → ``DATABASE_HOST``)
3. Converts keys to uppercase by default (disable with ``--no-uppercase``)
4. Adds optional prefix to all variable names
5. Executes the command with the config as environment variables
6. Exits with the same exit code as the command

Examples
~~~~~~~~

Basic usage (uses default directory):

.. code-block:: bash

   vaultconfig run database python app.py

Run with custom prefix:

.. code-block:: bash

   vaultconfig run database --prefix DB_ python manage.py migrate

Reveal obscured passwords:

.. code-block:: bash

   vaultconfig run database --reveal python deploy.py

Keep lowercase keys:

.. code-block:: bash

   vaultconfig run database --no-uppercase node server.js

Don't override existing environment variables:

.. code-block:: bash

   vaultconfig run database --no-override python app.py

Use custom directory:

.. code-block:: bash

   vaultconfig run -d ./myapp-config prod-db python deploy.py

Run tests with test config:

.. code-block:: bash

   vaultconfig run test-env pytest tests/

Run Docker Compose with config:

.. code-block:: bash

   vaultconfig run docker-config docker-compose up

Use with command that has flags (use ``--`` to separate):

.. code-block:: bash

   vaultconfig run database -- python app.py --debug --port 8000

Practical Examples
~~~~~~~~~~~~~~~~~~

**Database migrations:**

.. code-block:: bash

   # Run Django migrations with database config
   vaultconfig run database --prefix DB_ python manage.py migrate

**Running applications:**

.. code-block:: bash

   # Start Flask app with config
   vaultconfig run app-config --reveal flask run

**CI/CD pipelines:**

.. code-block:: bash

   # Deploy with production config
   vaultconfig run production --reveal ./deploy.sh

**Testing:**

.. code-block:: bash

   # Run tests with test database config
   vaultconfig run test-db pytest tests/integration/

**Docker containers:**

.. code-block:: bash

   # Start container with config
   vaultconfig run redis-config docker run -e REDIS_PASSWORD redis:alpine

Environment Variable Naming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``run`` command transforms configuration keys into environment variable names:

- **Uppercase conversion**: ``host`` → ``HOST`` (default, disable with ``--no-uppercase``)
- **Nested keys**: ``database.host`` → ``DATABASE_HOST``
- **Prefix**: With ``--prefix DB_``: ``host`` → ``DB_HOST``
- **Special characters**: Dots and hyphens converted to underscores

Example with nested config:

.. code-block:: bash

   # Config: database.toml
   # host = "localhost"
   # port = 5432
   # credentials.username = "myuser"
   # credentials.password = "secret"

   vaultconfig run database --prefix DB_ env | grep DB_
   # DB_HOST=localhost
   # DB_PORT=5432
   # DB_CREDENTIALS_USERNAME=myuser
   # DB_CREDENTIALS_PASSWORD=secret

Exit Code
~~~~~~~~~

The ``run`` command exits with the same exit code as the executed command. This allows
it to be used in scripts and CI/CD pipelines:

.. code-block:: bash

   # If the command fails, the script stops
   vaultconfig run database python deploy.py || exit 1

export-env Command
------------------

Export configuration as environment variables in shell-specific format.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig export-env [OPTIONS] NAME

Arguments
~~~~~~~~~

- ``NAME`` - Name of the configuration to export

Options
~~~~~~~

- ``-C, --config-dir PATH`` - Config directory (uses default if not specified)
- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-p, --prefix TEXT`` - Prefix for environment variable names (default: "")
- ``-r, --reveal`` - Reveal obscured passwords
- ``-u, --uppercase`` - Convert keys to uppercase (default: true)
- ``-s, --shell TEXT`` - Shell type: bash, zsh, fish, nushell, powershell (auto-detected if not specified)
- ``--dry-run`` - Show preview with copyable commands instead of outputting for eval/source
- ``--help`` - Show help message

Supported Shells
~~~~~~~~~~~~~~~~

The ``export-env`` command supports multiple shell formats:

- **bash** - Bash shell (``export KEY='value'``)
- **zsh** - Zsh shell (``export KEY='value'``)
- **fish** - Fish shell (``set -gx KEY 'value'``)
- **nushell** - Nushell (``$env.KEY = 'value'``)
- **powershell** - PowerShell (``$env:KEY = 'value'``)

If no shell is specified, the command auto-detects your shell from the ``SHELL``
environment variable.

Examples
~~~~~~~~

Basic usage with auto-detection:

.. code-block:: bash

   vaultconfig export-env database

For Bash/Zsh:

.. code-block:: bash

   # Export and evaluate in current shell
   eval $(vaultconfig export-env database --prefix DB_)
   echo $DB_HOST

   # With revealed passwords
   eval $(vaultconfig export-env database --reveal)

For Fish:

.. code-block:: bash

   # Source directly
   vaultconfig export-env database --shell fish | source

   # With prefix
   vaultconfig export-env database --prefix DB_ --shell fish | source

For Nushell:

.. code-block:: bash

   # Save to file and source
   vaultconfig export-env database --shell nushell | save -f env.nu
   source env.nu

   # Or use directly
   vaultconfig export-env database --shell nushell | lines | each { |line| nu -c $line }

For PowerShell:

.. code-block:: bash

   # Invoke directly
   vaultconfig export-env database --shell powershell | Invoke-Expression

   # With prefix
   vaultconfig export-env database --prefix APP_ --shell powershell | Invoke-Expression

Practical Examples
~~~~~~~~~~~~~~~~~~

**Set database credentials in current shell:**

.. code-block:: bash

   # Bash/Zsh
   eval $(vaultconfig export-env production-db --prefix DB_ --reveal)
   psql -h $DB_HOST -U $DB_USERNAME

   # Fish
   vaultconfig export-env production-db --prefix DB_ --reveal --shell fish | source
   psql -h $DB_HOST -U $DB_USERNAME

**Export for CI/CD:**

.. code-block:: bash

   # GitHub Actions, GitLab CI (bash)
   eval $(vaultconfig export-env ci-secrets --reveal)

   # Azure Pipelines (PowerShell)
   vaultconfig export-env ci-secrets --reveal --shell powershell | Invoke-Expression

**Use with Docker:**

.. code-block:: bash

   # Create .env file for Docker Compose
   vaultconfig export-env docker-config --shell bash | sed 's/export //' > .env
   docker-compose up

Shell Auto-Detection
~~~~~~~~~~~~~~~~~~~~

The command detects your shell in the following order:

1. Check ``SHELL`` environment variable for bash, zsh, fish, nu/nushell
2. Check ``PSModulePath`` environment variable for PowerShell
3. Default to bash format if detection fails

You can always override auto-detection with the ``--shell`` option.

Dry-Run Mode
~~~~~~~~~~~~

Use ``--dry-run`` to preview environment variables before exporting them. This mode
displays:

1. A formatted table showing all variables and their values
2. Shell-specific copyable commands in a syntax-highlighted panel
3. Helpful notes and tips

This is useful for:

- Verifying what will be exported before using ``eval`` or ``source``
- Getting ready-to-copy commands for manual setup
- Checking variable names with different prefixes
- Reviewing obscured values before revealing them

Example:

.. code-block:: bash

   # Preview with bash format
   vaultconfig export-env database --dry-run

   # Preview with nushell format and prefix
   vaultconfig export-env database --shell nushell --prefix DB_ --dry-run

   # Preview and reveal passwords
   vaultconfig export-env database --dry-run --reveal

The dry-run output shows both a table view and copyable commands that you can paste
directly into your shell.

Format Autodetection
--------------------

VaultConfig can autodetect the format based on file extensions in the config directory:

- If ``.toml`` files are found, uses TOML format
- If ``.ini`` files are found, uses INI format
- If ``.yaml`` or ``.yml`` files are found, uses YAML format
- Defaults to TOML if directory is empty

Example:

.. code-block:: bash

   # Autodetects format
   vaultconfig list ./myapp-config

   # Explicit format (overrides autodetection)
   vaultconfig list ./myapp-config --format yaml

Exit Codes
----------

The CLI uses standard exit codes:

- ``0`` - Success
- ``1`` - Error (config not found, validation failed, etc.)
- ``2`` - Usage error (invalid arguments)

Examples:

.. code-block:: bash

   # Check if config exists
   if vaultconfig show ./myapp-config database > /dev/null 2>&1; then
       echo "Config exists"
   else
       echo "Config not found"
   fi

Shell Integration
-----------------

Bash Completion
~~~~~~~~~~~~~~~

Generate completion script:

.. code-block:: bash

   _VAULTCONFIG_COMPLETE=bash_source vaultconfig > ~/.vaultconfig-complete.bash

Add to your ``.bashrc``:

.. code-block:: bash

   . ~/.vaultconfig-complete.bash

Zsh Completion
~~~~~~~~~~~~~~

Generate completion script:

.. code-block:: bash

   _VAULTCONFIG_COMPLETE=zsh_source vaultconfig > ~/.vaultconfig-complete.zsh

Add to your ``.zshrc``:

.. code-block:: bash

   . ~/.vaultconfig-complete.zsh

Scripting Examples
------------------

Backup Configs
~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   CONFIG_DIR="./myapp-config"
   BACKUP_DIR="./backup-$(date +%Y%m%d)"

   mkdir -p "$BACKUP_DIR"
   cp -r "$CONFIG_DIR" "$BACKUP_DIR/"

   echo "Backed up configs to $BACKUP_DIR"

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   CONFIG_DIR="./myapp-config"

   # List all configs
   configs=$(vaultconfig list "$CONFIG_DIR" --format toml | tail -n +3 | awk '{print $1}')

   # Show each config
   for config in $configs; do
       echo "=== $config ==="
       vaultconfig show "$CONFIG_DIR" "$config"
       echo
   done

Migrate Formats
~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # Migrate from TOML to YAML
   OLD_DIR="./config-toml"
   NEW_DIR="./config-yaml"

   vaultconfig init "$NEW_DIR" --format yaml

   # Export configs as JSON, then import to new format
   # (requires custom scripting with Python API)

CI/CD Integration
-----------------

GitHub Actions Example
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: Deploy
   on: [push]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2

         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.11'

         - name: Install VaultConfig
           run: pip install vaultconfig

         - name: Decrypt configs
           env:
             VAULTCONFIG_PASSWORD: ${{ secrets.CONFIG_PASSWORD }}
           run: |
             vaultconfig show ./config database > database.json

GitLab CI Example
~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   deploy:
     script:
       - pip install vaultconfig
       - export VAULTCONFIG_PASSWORD=$CONFIG_PASSWORD
       - vaultconfig list ./config

Troubleshooting
---------------

Password Not Accepted
~~~~~~~~~~~~~~~~~~~~~

If your password is not accepted for encrypted configs:

1. Check for typos (passwords are case-sensitive)
2. Verify the environment variable is set correctly
3. Try setting the password explicitly with ``encrypt set``

Format Detection Issues
~~~~~~~~~~~~~~~~~~~~~~~

If format autodetection fails:

1. Use the ``--format`` option explicitly
2. Ensure config files have correct extensions
3. Check that the config directory is not empty

Permission Denied
~~~~~~~~~~~~~~~~~

If you get permission errors:

.. code-block:: bash

   chmod 700 ./myapp-config    # Directory
   chmod 600 ./myapp-config/*  # Files

Interactive Mode Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If password prompts don't appear:

1. Ensure you're running in a TTY
2. Use environment variables for non-interactive environments
3. Check that stdin is not redirected

For more information, see :doc:`security` and :doc:`examples`.

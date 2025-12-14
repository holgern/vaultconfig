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

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
- ``delete`` - Delete a configuration
- ``encrypt`` - Manage encryption

init Command
------------

Initialize a new configuration directory.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig init [OPTIONS] CONFIG_DIR

Options
~~~~~~~

- ``-f, --format TEXT`` - Config format: toml (default), ini, or yaml
- ``-e, --encrypt`` - Enable encryption (prompts for password)
- ``--help`` - Show help message

Examples
~~~~~~~~

Basic initialization:

.. code-block:: bash

   vaultconfig init ./myapp-config

With specific format:

.. code-block:: bash

   vaultconfig init ./myapp-config --format yaml

With encryption:

.. code-block:: bash

   vaultconfig init ./myapp-config --encrypt
   # Prompts for password

list Command
------------

List all configurations in a directory.

Syntax
~~~~~~

.. code-block:: bash

   vaultconfig list [OPTIONS] CONFIG_DIR

Options
~~~~~~~

- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``--help`` - Show help message

Examples
~~~~~~~~

.. code-block:: bash

   # List all configs
   vaultconfig list ./myapp-config

   # List with explicit format
   vaultconfig list ./myapp-config --format toml

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

   vaultconfig show [OPTIONS] CONFIG_DIR NAME

Arguments
~~~~~~~~~

- ``CONFIG_DIR`` - Path to config directory
- ``NAME`` - Name of the configuration to show

Options
~~~~~~~

- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-r, --reveal`` - Reveal obscured passwords
- ``--help`` - Show help message

Examples
~~~~~~~~

Show with obscured passwords:

.. code-block:: bash

   vaultconfig show ./myapp-config database

Show with revealed passwords:

.. code-block:: bash

   vaultconfig show ./myapp-config database --reveal

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

   vaultconfig delete [OPTIONS] CONFIG_DIR NAME

Arguments
~~~~~~~~~

- ``CONFIG_DIR`` - Path to config directory
- ``NAME`` - Name of the configuration to delete

Options
~~~~~~~

- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-y, --yes`` - Skip confirmation prompt
- ``--help`` - Show help message

Examples
~~~~~~~~

With confirmation:

.. code-block:: bash

   vaultconfig delete ./myapp-config database
   # Prompts: "Are you sure you want to delete this config? [y/N]:"

Skip confirmation:

.. code-block:: bash

   vaultconfig delete ./myapp-config database --yes

encrypt Command Group
---------------------

Manage encryption for configuration files.

encrypt set
~~~~~~~~~~~

Set or change the encryption password.

Syntax:

.. code-block:: bash

   vaultconfig encrypt set [OPTIONS] CONFIG_DIR

Options:

- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``--help`` - Show help message

Example:

.. code-block:: bash

   vaultconfig encrypt set ./myapp-config
   # Prompts for new password twice

encrypt remove
~~~~~~~~~~~~~~

Remove encryption from all configs (decrypt to plaintext).

Syntax:

.. code-block:: bash

   vaultconfig encrypt remove [OPTIONS] CONFIG_DIR

Options:

- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``-y, --yes`` - Skip confirmation prompt
- ``--help`` - Show help message

Example:

.. code-block:: bash

   vaultconfig encrypt remove ./myapp-config
   # Prompts for confirmation

encrypt check
~~~~~~~~~~~~~

Check if configs are encrypted.

Syntax:

.. code-block:: bash

   vaultconfig encrypt check [OPTIONS] CONFIG_DIR

Options:

- ``-f, --format TEXT`` - Config format (autodetected if not specified)
- ``--help`` - Show help message

Example:

.. code-block:: bash

   vaultconfig encrypt check ./myapp-config
   # Output: "✓ Configs are encrypted" or "! Configs are NOT encrypted"

Environment Variables
---------------------

VAULTCONFIG_PASSWORD
~~~~~~~~~~~~~~~~~~~~

Set the password for encrypted configs:

.. code-block:: bash

   export VAULTCONFIG_PASSWORD="my-secure-password"
   vaultconfig list ./myapp-config

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

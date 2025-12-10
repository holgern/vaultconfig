Installation
============

Basic Installation
------------------

Install VaultConfig using pip:

.. code-block:: bash

   pip install vaultconfig

This installs the core library with support for TOML and INI formats.

Optional Dependencies
---------------------

YAML Support
~~~~~~~~~~~~

To enable YAML format support:

.. code-block:: bash

   pip install vaultconfig[yaml]

This installs PyYAML as an optional dependency.

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

For development, testing, and contributing:

.. code-block:: bash

   pip install vaultconfig[dev]

This installs:

- pytest and pytest-cov for testing
- ruff for linting and formatting
- pre-commit for git hooks
- sphinx for documentation
- All optional dependencies

All Dependencies
~~~~~~~~~~~~~~~~

Install everything:

.. code-block:: bash

   pip install vaultconfig[yaml,dev]

Requirements
------------

- Python 3.10 or higher
- cryptography >= 41.0.0 (for password obscuring)
- PyNaCl >= 1.5.0 (for config encryption)
- pydantic >= 2.0.0 (for schema validation)
- click >= 8.0.0 (for CLI)
- rich >= 13.0.0 (for CLI output)

Installing from Source
----------------------

Clone the repository and install in development mode:

.. code-block:: bash

   git clone https://github.com/holgern/vaultconfig.git
   cd vaultconfig
   pip install -e ".[dev,yaml]"

Verifying Installation
----------------------

Check that vaultconfig is installed correctly:

.. code-block:: bash

   # Check CLI
   vaultconfig --version

   # Check Python import
   python -c "from vaultconfig import ConfigManager; print('OK')"

Upgrading
---------

To upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade vaultconfig

To upgrade with all optional dependencies:

.. code-block:: bash

   pip install --upgrade vaultconfig[yaml,dev]

Uninstalling
------------

To remove vaultconfig:

.. code-block:: bash

   pip uninstall vaultconfig

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

If you encounter import errors, ensure all dependencies are installed:

.. code-block:: bash

   pip install --upgrade pip
   pip install --force-reinstall vaultconfig

YAML Not Available
~~~~~~~~~~~~~~~~~~

If YAML format is not working:

.. code-block:: bash

   pip install PyYAML

Cryptography Issues
~~~~~~~~~~~~~~~~~~~

On some systems, installing cryptography may require additional system packages:

**Ubuntu/Debian:**

.. code-block:: bash

   sudo apt-get install build-essential libssl-dev libffi-dev python3-dev

**macOS:**

.. code-block:: bash

   xcode-select --install

**Windows:**

Install Visual C++ Build Tools from Microsoft.

Platform-Specific Notes
-----------------------

Linux
~~~~~

VaultConfig works on all major Linux distributions. Ensure you have Python 3.10+.

macOS
~~~~~

VaultConfig works on macOS 10.15 (Catalina) and later with Python 3.10+.

Windows
~~~~~~~

VaultConfig works on Windows 10 and later with Python 3.10+. Use PowerShell or
Command Prompt for CLI commands.

Docker
~~~~~~

Example Dockerfile:

.. code-block:: dockerfile

   FROM python:3.11-slim

   RUN pip install vaultconfig[yaml]

   # Copy your config
   COPY ./config /app/config

   # Your application
   COPY ./app /app

   WORKDIR /app
   CMD ["python", "main.py"]

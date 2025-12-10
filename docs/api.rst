API Reference
=============

This page provides detailed API documentation for VaultConfig.

Core Classes
------------

ConfigManager
~~~~~~~~~~~~~

.. autoclass:: vaultconfig.ConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

ConfigEntry
~~~~~~~~~~~

.. autoclass:: vaultconfig.config.ConfigEntry
   :members:
   :undoc-members:
   :show-inheritance:

Schema System
-------------

ConfigSchema
~~~~~~~~~~~~

.. autoclass:: vaultconfig.ConfigSchema
   :members:
   :undoc-members:
   :show-inheritance:

FieldDef
~~~~~~~~

.. autoclass:: vaultconfig.FieldDef
   :members:
   :undoc-members:
   :show-inheritance:

Helper Functions
~~~~~~~~~~~~~~~~

.. autofunction:: vaultconfig.create_simple_schema

Encryption & Obscuring
----------------------

Encryption Module
~~~~~~~~~~~~~~~~~

.. automodule:: vaultconfig.crypt
   :members:
   :undoc-members:

Obscuring Module
~~~~~~~~~~~~~~~~

.. automodule:: vaultconfig.obscure
   :members:
   :undoc-members:

Format Handlers
---------------

Base Format
~~~~~~~~~~~

.. autoclass:: vaultconfig.formats.base.ConfigFormat
   :members:
   :undoc-members:
   :show-inheritance:

TOML Format
~~~~~~~~~~~

.. autoclass:: vaultconfig.formats.TOMLFormat
   :members:
   :undoc-members:
   :show-inheritance:

INI Format
~~~~~~~~~~

.. autoclass:: vaultconfig.formats.INIFormat
   :members:
   :undoc-members:
   :show-inheritance:

YAML Format
~~~~~~~~~~~

.. autoclass:: vaultconfig.formats.YAMLFormat
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. automodule:: vaultconfig.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Constants and Configuration
---------------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

VaultConfig recognizes the following environment variables:

.. py:data:: VAULTCONFIG_PASSWORD
   :type: str

   Password for encrypted configuration files.

   Example::

      export VAULTCONFIG_PASSWORD="my-secure-password"

.. py:data:: VAULTCONFIG_PASSWORD_COMMAND
   :type: str

   Command to retrieve the password (stdout is used as password).

   Example::

      export VAULTCONFIG_PASSWORD_COMMAND="pass show vaultconfig/myapp"

.. py:data:: VAULTCONFIG_PASSWORD_CHANGE
   :type: str

   Set to "1" when changing the password (used by password command).

   Example::

      export VAULTCONFIG_PASSWORD_CHANGE=1

File Formats
~~~~~~~~~~~~

Encryption Header
^^^^^^^^^^^^^^^^^

Encrypted files start with this header::

   VAULTCONFIG_ENCRYPT_V0:

Format: ``VAULTCONFIG_ENCRYPT_V0:<base64-encoded-encrypted-data>``

File Extensions
^^^^^^^^^^^^^^^

- TOML: ``.toml``
- INI: ``.ini``
- YAML: ``.yaml`` or ``.yml``

Type Hints
----------

Common type aliases used throughout the codebase:

.. code-block:: python

   from pathlib import Path
   from typing import Any, Optional

   # Config data type
   ConfigDict = dict[str, Any]

   # Config directory path
   ConfigDir = Path | str

   # Password type
   Password = Optional[str]

   # Config name
   ConfigName = str

Module Overview
---------------

vaultconfig
~~~~~~~~~~~

Main package providing configuration management.

**Key exports:**

- ``ConfigManager`` - Main configuration manager class
- ``ConfigEntry`` - Individual configuration entry
- ``ConfigSchema`` - Schema validation class
- ``FieldDef`` - Field definition for schemas
- ``create_simple_schema`` - Helper to create schemas

vaultconfig.config
~~~~~~~~~~~~~~~~~~

Core configuration management functionality.

vaultconfig.crypt
~~~~~~~~~~~~~~~~~

Strong encryption for configuration files using NaCl.

vaultconfig.obscure
~~~~~~~~~~~~~~~~~~~

Password obscuring (not secure encryption).

vaultconfig.schema
~~~~~~~~~~~~~~~~~~

Schema validation using Pydantic.

vaultconfig.formats
~~~~~~~~~~~~~~~~~~~

Format handlers for TOML, INI, and YAML.

vaultconfig.cli
~~~~~~~~~~~~~~~

Command-line interface implementation.

vaultconfig.exceptions
~~~~~~~~~~~~~~~~~~~~~~

Custom exception classes.

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager

   # Create manager
   manager = ConfigManager(
       config_dir=Path("./config"),
       format="toml",
   )

   # Add config
   manager.add_config("myapp", {
       "host": "localhost",
       "port": 8080,
   })

   # Get config
   config = manager.get_config("myapp")
   if config:
       host = config.get("host")

With Encryption
~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager

   # Encrypted manager
   manager = ConfigManager(
       config_dir=Path("./config"),
       password="secure-password",
   )

   # Configs are encrypted automatically
   manager.add_config("secrets", {
       "api_key": "12345",
   })

With Schema
~~~~~~~~~~~

.. code-block:: python

   from vaultconfig import ConfigManager, create_simple_schema, FieldDef
   from pathlib import Path

   # Define schema
   schema = create_simple_schema({
       "host": FieldDef(str, default="localhost"),
       "port": FieldDef(int, default=8080),
       "password": FieldDef(str, sensitive=True),
   })

   # Manager with schema
   manager = ConfigManager(
       config_dir=Path("./config"),
       schema=schema,
   )

Direct Encryption/Obscuring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from vaultconfig import crypt, obscure

   # Encrypt data
   encrypted = crypt.encrypt(b"sensitive data", "password")
   decrypted = crypt.decrypt(encrypted, "password")

   # Obscure password
   obscured = obscure.obscure("my_password")
   revealed = obscure.reveal(obscured)

Migration Guide
---------------

From Version 0.x to 1.x
~~~~~~~~~~~~~~~~~~~~~~~

No breaking changes. All APIs are backward compatible.

From Plain Config Files
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import json
   from vaultconfig import ConfigManager

   # Load old config
   with open("old-config.json") as f:
       old_config = json.load(f)

   # Migrate to VaultConfig
   manager = ConfigManager(config_dir="./new-config")
   for name, config in old_config.items():
       manager.add_config(name, config)

Performance Considerations
--------------------------

Caching
~~~~~~~

ConfigManager caches loaded configurations in memory. Modifications are
persisted immediately but reads use the cache.

File I/O
~~~~~~~~

Each config is stored in a separate file. For large numbers of configs,
consider using a database-backed solution instead.

Encryption Overhead
~~~~~~~~~~~~~~~~~~~

- Password obscuring: ~1ms per operation
- File encryption: ~5-10ms per file (depends on size)
- Key derivation: ~50ms (done once per manager instance)

Thread Safety
~~~~~~~~~~~~~

ConfigManager is **not** thread-safe. Use separate instances per thread or
add external locking.

Best Practices
--------------

1. **Use schemas** for type safety and validation
2. **Enable encryption** for production environments
3. **Use password commands** instead of environment variables
4. **Set file permissions** to 600/700
5. **Separate configs** by environment
6. **Cache ConfigManager** instances where possible
7. **Handle exceptions** appropriately

See Also
--------

- :doc:`quickstart` - Getting started guide
- :doc:`examples` - Integration examples
- :doc:`security` - Security best practices
- :doc:`cli` - Command-line interface

Quick Start Guide
=================

This guide will help you get started with VaultConfig in 5 minutes.

Basic Usage
-----------

Creating a Configuration Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager

   # Create a config manager
   manager = ConfigManager(
       config_dir=Path("./myapp-config"),
       format="toml",  # Options: "toml", "ini", "yaml"
   )

Adding Configurations
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Add a simple configuration
   manager.add_config(
       name="database",
       config={
           "host": "localhost",
           "port": 5432,
           "username": "myuser",
           "password": "secret123",
       },
   )

   # Passwords are automatically obscured in the file
   # but accessible via the API

Reading Configurations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get a configuration
   config = manager.get_config("database")

   if config:
       # Access individual values
       host = config.get("host")              # "localhost"
       port = config.get("port")              # 5432
       password = config.get("password")      # "secret123" (revealed)

       # Get all values
       all_values = config.get_all()
       print(all_values)
       # {'host': 'localhost', 'port': 5432, 'username': 'myuser', 'password': 'secret123'}

Listing Configurations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # List all configuration names
   configs = manager.list_configs()
   print(configs)  # ['database']

Updating Configurations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Update an existing configuration
   manager.update_config(
       name="database",
       updates={"port": 5433, "host": "db.example.com"},
   )

Removing Configurations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Remove a configuration
   manager.remove_config("database")

Using Encryption
----------------

Encrypted configurations provide strong security for sensitive data.

Creating Encrypted Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager

   # Create manager with encryption
   manager = ConfigManager(
       config_dir=Path("./secure-config"),
       format="toml",
       password="my-secure-password",
   )

   # All configs are encrypted automatically
   manager.add_config("secrets", {
       "api_key": "12345",
       "token": "abcde",
   })

Using Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the password via environment variable:

.. code-block:: bash

   export VAULTCONFIG_PASSWORD="my-secure-password"

.. code-block:: python

   # Password is read from environment
   manager = ConfigManager(
       config_dir=Path("./secure-config"),
       format="toml",
   )

Managing Encryption
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Set or change encryption password
   manager.set_encryption_password("new-password")

   # Remove encryption
   manager.remove_encryption()

   # Check if configs are encrypted
   is_encrypted = manager.is_encrypted()

Using Schemas
-------------

Schemas provide type validation and automatic password obscuring.

Simple Schema
~~~~~~~~~~~~~

.. code-block:: python

   from vaultconfig import ConfigManager, create_simple_schema, FieldDef

   # Define a schema
   schema = create_simple_schema({
       "host": FieldDef(str, default="localhost"),
       "port": FieldDef(int, default=5432),
       "username": FieldDef(str),
       "password": FieldDef(str, sensitive=True),
   })

   # Create manager with schema
   manager = ConfigManager(
       config_dir=Path("./myapp-config"),
       schema=schema,
   )

   # Schema validates and obscures sensitive fields automatically
   manager.add_config("db", {
       "host": "db.example.com",
       "username": "admin",
       "password": "secret",  # Will be auto-obscured
   })
   # port will use default value (5432)

Pydantic Schema
~~~~~~~~~~~~~~~

.. code-block:: python

   from pydantic import BaseModel, Field
   from vaultconfig import ConfigManager, ConfigSchema

   # Define a Pydantic model
   class DatabaseConfig(BaseModel):
       host: str = "localhost"
       port: int = 5432
       username: str
       password: str = Field(json_schema_extra={"sensitive": True})

   # Create schema from model
   schema = ConfigSchema(DatabaseConfig)

   # Use with manager
   manager = ConfigManager(
       config_dir=Path("./myapp-config"),
       schema=schema,
   )

Command Line Usage
------------------

Initialize a Config Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Initialize default directory
   vaultconfig init

   # Initialize custom directory
   vaultconfig init -d ./myapp-config

   # With specific format
   vaultconfig init --format yaml

   # With encryption
   vaultconfig init --encrypt

List Configurations
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List using default directory
   vaultconfig list

   # List specific directory
   vaultconfig list ./myapp-config

   # or with option
   vaultconfig list -d ./myapp-config

Show a Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show with obscured passwords (uses default directory)
   vaultconfig show database

   # Show with revealed passwords
   vaultconfig show database --reveal

   # Show from custom directory
   vaultconfig show -d ./myapp-config database

Delete a Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Delete with confirmation
   vaultconfig delete database

   # Delete without confirmation
   vaultconfig delete database --yes

   # Delete from custom directory
   vaultconfig delete -d ./myapp-config database

Manage Encryption
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set encryption password (uses default directory)
   vaultconfig encrypt set

   # Set for custom directory
   vaultconfig encrypt set -d ./myapp-config

   # Remove encryption
   vaultconfig encrypt remove

   # Remove from custom directory
   vaultconfig encrypt remove -d ./myapp-config

   # Check encryption status
   vaultconfig encrypt check

   # Check custom directory
   vaultconfig encrypt check -d ./myapp-config

Run Commands with Config
~~~~~~~~~~~~~~~~~~~~~~~~~

Load a configuration and run a command with config values as environment variables:

.. code-block:: bash

   # Run a Python script with database config (uses default directory)
   vaultconfig run database python app.py

   # Run with custom prefix
   vaultconfig run database --prefix DB_ python manage.py migrate

   # Run with revealed passwords
   vaultconfig run database --reveal python deploy.py

   # Run from custom directory
   vaultconfig run -d ./myapp-config prod-db python app.py

   # Run tests with test environment
   vaultconfig run test-env pytest tests/

This is useful for running applications that expect configuration in environment
variables without needing to manually export them.

Export Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Export configuration as shell-specific environment variables:

.. code-block:: bash

   # Auto-detect shell and export variables
   eval $(vaultconfig export-env database)

   # Fish shell
   vaultconfig export-env database --shell fish | source

   # Nushell
   vaultconfig export-env database --shell nushell | save -f env.nu

   # PowerShell
   vaultconfig export-env database --shell powershell | Invoke-Expression

Supports bash, zsh, fish, nushell, and powershell with automatic shell detection.

Configuration Formats
---------------------

TOML (Default)
~~~~~~~~~~~~~~

.. code-block:: toml

   # database.toml
   host = "localhost"
   port = 5432
   username = "myuser"
   password = "obscured-value-here"

   [nested]
   key = "value"

INI
~~~

INI format supports the DEFAULT section for shared values:

.. code-block:: ini

   # database.ini
   [DEFAULT]
   ServerAliveInterval = 45
   Compression = yes
   ForwardX11 = yes

   [forge.example]
   User = hg
   # Inherits ServerAliveInterval, Compression, ForwardX11 from DEFAULT

   [topsecret.server.example]
   Port = 50022
   ForwardX11 = no  # Overrides DEFAULT value
   # Inherits ServerAliveInterval, Compression from DEFAULT

**Key Features**:

- Section names can contain dots (e.g., ``forge.example``)
- Values in ``[DEFAULT]`` are inherited by all sections
- Sections can override DEFAULT values
- Option names preserve case by default

YAML
~~~~

.. code-block:: yaml

   # database.yaml
   host: localhost
   port: 5432
   username: myuser
   password: obscured-value-here
   nested:
     key: value

Nested Configuration Access
----------------------------

.. code-block:: python

   # Add nested configuration
   manager.add_config("app", {
       "database": {
           "host": "localhost",
           "port": 5432,
       },
       "cache": {
           "enabled": True,
           "ttl": 300,
       },
   })

   # Access nested values using dot notation
   config = manager.get_config("app")
   db_host = config.get("database.host")        # "localhost"
   cache_ttl = config.get("cache.ttl")          # 300
   invalid = config.get("cache.invalid", None)  # None (with default)

Password Obscuring vs Encryption
---------------------------------

Two Levels of Security
~~~~~~~~~~~~~~~~~~~~~~

**Password Obscuring** (Automatic):

- Hides passwords from casual viewing
- Uses AES-CTR + base64
- NOT secure encryption
- Automatic for ``sensitive=True`` fields

**Config File Encryption** (Optional):

- Strong authenticated encryption (NaCl)
- Protects entire config files
- Password-protected
- Lost password = lost data

When to Use Each
~~~~~~~~~~~~~~~~

Use **password obscuring** when:

- You want convenience over security
- Config files are in a secure location
- You need to prevent shoulder surfing

Use **config file encryption** when:

- Security is critical
- Config files might be exposed
- You have a secure password management system

Next Steps
----------

- Read the :doc:`cli` guide for more CLI examples
- Check the :doc:`security` guide for best practices
- See :doc:`examples` for integration patterns
- Explore the :doc:`api` reference for advanced usage

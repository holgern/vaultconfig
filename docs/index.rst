VaultConfig Documentation
=========================

**Secure configuration management library with encryption support for Python**

VaultConfig provides an easy way to manage application configurations with support for
multiple formats (TOML, INI, YAML), password obscuring, and full config file encryption.

Features
--------

- **Multiple Format Support**: TOML, INI, and YAML (optional)
- **Password Obscuring**: Hide sensitive fields from casual viewing (AES-CTR based)
- **Config File Encryption**: Strong authenticated encryption using NaCl secretbox (XSalsa20 + Poly1305)
- **Schema Validation**: Pydantic-based schema system for type validation
- **CLI Tool**: Command-line interface for config management
- **Project-Specific**: Each project can have its own config directory
- **Easy Integration**: Simple API for embedding into Python applications

Quick Example
-------------

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager

   # Create manager
   manager = ConfigManager(
       config_dir=Path("./myapp-config"),
       format="toml",
   )

   # Add a configuration
   manager.add_config(
       name="database",
       config={
           "host": "localhost",
           "port": 5432,
           "username": "myuser",
           "password": "secret123",  # Will be obscured
       },
   )

   # Get configuration
   config = manager.get_config("database")
   if config:
       host = config.get("host")
       password = config.get("password")  # Automatically revealed

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   cli
   security
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

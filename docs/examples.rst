Integration Examples
====================

This page provides real-world examples of integrating VaultConfig into various types of applications.

Web Applications
----------------

Flask Application
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flask import Flask
   from pathlib import Path
   import os
   from vaultconfig import ConfigManager

   app = Flask(__name__)

   # Initialize config manager
   config_manager = ConfigManager(
       config_dir=Path.home() / ".config" / "myapp",
       password=os.getenv("MYAPP_CONFIG_PASSWORD"),
   )

   # Load database config
   db_config = config_manager.get_config("database")
   if db_config:
       app.config["SQLALCHEMY_DATABASE_URI"] = (
           f"postgresql://{db_config.get('username')}:"
           f"{db_config.get('password')}@"
           f"{db_config.get('host')}:"
           f"{db_config.get('port')}/"
           f"{db_config.get('database')}"
       )

   # Load app config
   app_config = config_manager.get_config("app")
   if app_config:
       app.config["SECRET_KEY"] = app_config.get("secret_key")
       app.config["DEBUG"] = app_config.get("debug", False)

   @app.route("/")
   def index():
       return "Hello World!"

   if __name__ == "__main__":
       app.run()

FastAPI Application
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI
   from pathlib import Path
   from pydantic import BaseModel, Field
   from vaultconfig import ConfigManager, ConfigSchema
   import os

   # Define config schema
   class DatabaseConfig(BaseModel):
       host: str = "localhost"
       port: int = 5432
       database: str
       username: str
       password: str = Field(json_schema_extra={"sensitive": True})

   # Create config manager with schema
   schema = ConfigSchema(DatabaseConfig)
   config_manager = ConfigManager(
       config_dir=Path("./config"),
       schema=schema,
       password=os.getenv("CONFIG_PASSWORD"),
   )

   # Initialize app
   app = FastAPI()

   @app.on_event("startup")
   async def startup():
       db_config = config_manager.get_config("database")
       if db_config:
           # Initialize database connection
           app.state.db_host = db_config.get("host")
           app.state.db_port = db_config.get("port")

   @app.get("/")
   async def root():
       return {"message": "Hello World"}

Django Settings Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings.py
   from pathlib import Path
   import os
   from vaultconfig import ConfigManager

   BASE_DIR = Path(__file__).resolve().parent.parent

   # Load config
   config_manager = ConfigManager(
       config_dir=BASE_DIR / "config",
       password=os.getenv("DJANGO_CONFIG_PASSWORD"),
   )

   # Database config
   db_config = config_manager.get_config("database")
   if db_config:
       DATABASES = {
           "default": {
               "ENGINE": "django.db.backends.postgresql",
               "NAME": db_config.get("database"),
               "USER": db_config.get("username"),
               "PASSWORD": db_config.get("password"),
               "HOST": db_config.get("host"),
               "PORT": db_config.get("port"),
           }
       }

   # App config
   app_config = config_manager.get_config("app")
   if app_config:
       SECRET_KEY = app_config.get("secret_key")
       DEBUG = app_config.get("debug", False)
       ALLOWED_HOSTS = app_config.get("allowed_hosts", [])

CLI Applications
----------------

Click-Based CLI
~~~~~~~~~~~~~~~

.. code-block:: python

   import click
   from pathlib import Path
   from vaultconfig import ConfigManager

   @click.group()
   @click.pass_context
   def cli(ctx):
       """My awesome CLI application."""
       ctx.ensure_object(dict)
       ctx.obj["config"] = ConfigManager(
           config_dir=Path.home() / ".config" / "myapp",
       )

   @cli.command()
   @click.argument("service")
   @click.pass_context
   def connect(ctx, service):
       """Connect to a service."""
       manager = ctx.obj["config"]
       config = manager.get_config(service)

       if not config:
           click.echo(f"Service '{service}' not configured", err=True)
           ctx.exit(1)

       host = config.get("host")
       port = config.get("port")
       click.echo(f"Connecting to {host}:{port}...")

   @cli.command()
   @click.pass_context
   def list_services(ctx):
       """List all configured services."""
       manager = ctx.obj["config"]
       services = manager.list_configs()

       if not services:
           click.echo("No services configured")
           return

       click.echo("Configured services:")
       for service in services:
           click.echo(f"  - {service}")

   if __name__ == "__main__":
       cli()

Argparse-Based CLI
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import argparse
   from pathlib import Path
   from vaultconfig import ConfigManager

   def main():
       parser = argparse.ArgumentParser(description="My CLI application")
       parser.add_argument("--config-dir", type=Path,
                          default=Path.home() / ".config" / "myapp")

       subparsers = parser.add_subparsers(dest="command")

       # Connect command
       connect_parser = subparsers.add_parser("connect")
       connect_parser.add_argument("service")

       # List command
       subparsers.add_parser("list")

       args = parser.parse_args()

       # Initialize config manager
       manager = ConfigManager(config_dir=args.config_dir)

       if args.command == "connect":
           config = manager.get_config(args.service)
           if config:
               print(f"Connecting to {config.get('host')}...")
           else:
               print(f"Service not found: {args.service}")

       elif args.command == "list":
           services = manager.list_configs()
           print("Services:", ", ".join(services))

   if __name__ == "__main__":
       main()

Background Services
-------------------

Systemd Service
~~~~~~~~~~~~~~~

Service file (``/etc/systemd/system/myapp.service``):

.. code-block:: ini

   [Unit]
   Description=My Application
   After=network.target

   [Service]
   Type=simple
   User=myapp
   WorkingDirectory=/opt/myapp
   Environment="VAULTCONFIG_PASSWORD_COMMAND=cat /etc/myapp/password"
   ExecStart=/usr/bin/python3 /opt/myapp/main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target

Python code:

.. code-block:: python

   # main.py
   from pathlib import Path
   from vaultconfig import ConfigManager
   import time

   def main():
       manager = ConfigManager(
           config_dir=Path("/etc/myapp/config"),
       )

       config = manager.get_config("app")

       while True:
           # Your service logic here
           time.sleep(60)

   if __name__ == "__main__":
       main()

Docker Container
~~~~~~~~~~~~~~~~

Dockerfile:

.. code-block:: dockerfile

   FROM python:3.11-slim

   WORKDIR /app

   # Install VaultConfig
   RUN pip install vaultconfig[yaml]

   # Copy application
   COPY . /app

   # Create config directory
   RUN mkdir -p /app/config && chmod 700 /app/config

   # Run application
   CMD ["python", "main.py"]

Docker Compose:

.. code-block:: yaml

   version: '3.8'

   services:
     app:
       build: .
       environment:
         - VAULTCONFIG_PASSWORD=${CONFIG_PASSWORD}
       volumes:
         - ./config:/app/config:ro
       restart: unless-stopped

Run:

.. code-block:: bash

   export CONFIG_PASSWORD="my-secure-password"
   docker-compose up -d

Data Processing
---------------

ETL Pipeline
~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager
   import sqlalchemy
   import pandas as pd

   class ETLPipeline:
       def __init__(self, config_dir):
           self.manager = ConfigManager(config_dir=Path(config_dir))

       def get_database_engine(self, config_name):
           """Create SQLAlchemy engine from config."""
           config = self.manager.get_config(config_name)
           if not config:
               raise ValueError(f"Config not found: {config_name}")

           conn_str = (
               f"postgresql://{config.get('username')}:"
               f"{config.get('password')}@"
               f"{config.get('host')}:"
               f"{config.get('port')}/"
               f"{config.get('database')}"
           )
           return sqlalchemy.create_engine(conn_str)

       def extract(self):
           """Extract data from source."""
           engine = self.get_database_engine("source_db")
           return pd.read_sql("SELECT * FROM users", engine)

       def transform(self, df):
           """Transform data."""
           df["processed_at"] = pd.Timestamp.now()
           return df

       def load(self, df):
           """Load data to destination."""
           engine = self.get_database_engine("dest_db")
           df.to_sql("users", engine, if_exists="append", index=False)

       def run(self):
           """Run the ETL pipeline."""
           print("Extracting...")
           df = self.extract()

           print("Transforming...")
           df = self.transform(df)

           print("Loading...")
           self.load(df)

           print("Done!")

   if __name__ == "__main__":
       pipeline = ETLPipeline("./config")
       pipeline.run()

API Client
~~~~~~~~~~

.. code-block:: python

   import requests
   from pathlib import Path
   from vaultconfig import ConfigManager

   class APIClient:
       def __init__(self, config_dir, service_name):
           self.manager = ConfigManager(config_dir=Path(config_dir))
           self.config = self.manager.get_config(service_name)

           if not self.config:
               raise ValueError(f"Service not configured: {service_name}")

           self.base_url = self.config.get("base_url")
           self.api_key = self.config.get("api_key")
           self.session = requests.Session()
           self.session.headers.update({
               "Authorization": f"Bearer {self.api_key}",
               "User-Agent": "MyApp/1.0",
           })

       def get(self, endpoint, **kwargs):
           """Make GET request."""
           url = f"{self.base_url}/{endpoint}"
           return self.session.get(url, **kwargs)

       def post(self, endpoint, **kwargs):
           """Make POST request."""
           url = f"{self.base_url}/{endpoint}"
           return self.session.post(url, **kwargs)

   # Usage
   client = APIClient("./config", "api_service")
   response = client.get("users/123")
   print(response.json())

Testing
-------

Pytest Fixture
~~~~~~~~~~~~~~

.. code-block:: python

   # conftest.py
   import pytest
   from pathlib import Path
   from vaultconfig import ConfigManager
   import tempfile
   import shutil

   @pytest.fixture
   def config_manager(tmp_path):
       """Provide a test config manager."""
       manager = ConfigManager(
           config_dir=tmp_path / "config",
           format="toml",
       )

       # Add test configs
       manager.add_config("test_db", {
           "host": "localhost",
           "port": 5432,
           "username": "test",
           "password": "test",
       })

       yield manager

       # Cleanup
       shutil.rmtree(tmp_path, ignore_errors=True)

   # test_myapp.py
   def test_database_connection(config_manager):
       """Test database connection."""
       config = config_manager.get_config("test_db")
       assert config is not None
       assert config.get("host") == "localhost"

Mocking Configs
~~~~~~~~~~~~~~~

.. code-block:: python

   import unittest
   from unittest.mock import Mock, patch
   from vaultconfig import ConfigManager

   class TestMyApp(unittest.TestCase):
       def setUp(self):
           """Set up test fixtures."""
           self.mock_config = Mock()
           self.mock_config.get.side_effect = lambda key, default=None: {
               "host": "test-host",
               "port": 5432,
               "username": "test-user",
               "password": "test-pass",
           }.get(key, default)

       @patch.object(ConfigManager, "get_config")
       def test_app_initialization(self, mock_get_config):
           """Test app initialization with mocked config."""
           mock_get_config.return_value = self.mock_config

           manager = ConfigManager(config_dir="./config")
           config = manager.get_config("database")

           self.assertEqual(config.get("host"), "test-host")
           self.assertEqual(config.get("port"), 5432)

Multi-Tenancy
-------------

Per-Tenant Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager
   from typing import Dict

   class TenantConfigManager:
       def __init__(self, base_config_dir: Path):
           self.base_dir = base_config_dir
           self.managers: Dict[str, ConfigManager] = {}

       def get_manager(self, tenant_id: str) -> ConfigManager:
           """Get or create config manager for tenant."""
           if tenant_id not in self.managers:
               tenant_dir = self.base_dir / tenant_id
               self.managers[tenant_id] = ConfigManager(
                   config_dir=tenant_dir,
                   password=self._get_tenant_password(tenant_id),
               )
           return self.managers[tenant_id]

       def _get_tenant_password(self, tenant_id: str) -> str:
           """Get encryption password for tenant."""
           # Implement your password retrieval logic
           # e.g., from key management service
           pass

       def get_tenant_config(self, tenant_id: str, config_name: str):
           """Get config for specific tenant."""
           manager = self.get_manager(tenant_id)
           return manager.get_config(config_name)

   # Usage
   tenant_manager = TenantConfigManager(Path("./tenants"))

   # Get config for tenant A
   tenant_a_db = tenant_manager.get_tenant_config("tenant-a", "database")

   # Get config for tenant B
   tenant_b_db = tenant_manager.get_tenant_config("tenant-b", "database")

Microservices
-------------

Service Registry Pattern
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager
   from typing import List, Dict, Optional

   class ServiceRegistry:
       def __init__(self, config_dir: Path):
           self.manager = ConfigManager(config_dir=config_dir)
           self._cache: Dict[str, dict] = {}

       def register_service(self, name: str, host: str, port: int,
                          metadata: Optional[dict] = None):
           """Register a service."""
           config = {
               "host": host,
               "port": port,
               "metadata": metadata or {},
           }
           self.manager.add_config(name, config)
           self._cache[name] = config

       def discover_service(self, name: str) -> Optional[dict]:
           """Discover a service by name."""
           if name in self._cache:
               return self._cache[name]

           config = self.manager.get_config(name)
           if config:
               service = {
                   "host": config.get("host"),
                   "port": config.get("port"),
                   "metadata": config.get("metadata", {}),
               }
               self._cache[name] = service
               return service

           return None

       def list_services(self) -> List[str]:
           """List all registered services."""
           return self.manager.list_configs()

   # Usage
   registry = ServiceRegistry(Path("./services"))

   # Register services
   registry.register_service("auth", "auth.internal", 8080)
   registry.register_service("users", "users.internal", 8081)

   # Discover service
   auth_service = registry.discover_service("auth")
   print(f"Auth service: {auth_service['host']}:{auth_service['port']}")

Configuration Migration
-----------------------

Migrate from JSON
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import json
   from pathlib import Path
   from vaultconfig import ConfigManager

   def migrate_from_json(json_file: Path, vaultconfig_dir: Path):
       """Migrate configs from JSON to VaultConfig."""
       # Load JSON
       with open(json_file) as f:
           data = json.load(f)

       # Create VaultConfig manager
       manager = ConfigManager(
           config_dir=vaultconfig_dir,
           format="toml",
       )

       # Migrate each config
       for name, config in data.items():
           print(f"Migrating {name}...")
           manager.add_config(name, config)

       print(f"Migrated {len(data)} configs")

   # Usage
   migrate_from_json(
       json_file=Path("./old-config.json"),
       vaultconfig_dir=Path("./new-config"),
   )

Migrate Between Formats
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager
   import shutil

   def migrate_format(source_dir: Path, dest_dir: Path,
                     source_format: str, dest_format: str):
       """Migrate configs between formats."""
       # Load from source
       source_manager = ConfigManager(
           config_dir=source_dir,
           format=source_format,
       )

       # Create destination
       dest_manager = ConfigManager(
           config_dir=dest_dir,
           format=dest_format,
       )

       # Migrate each config
       for name in source_manager.list_configs():
           print(f"Migrating {name} from {source_format} to {dest_format}...")
           config = source_manager.get_config(name)
           if config:
               dest_manager.add_config(name, config.get_all())

       print(f"Migration complete!")

   # Usage
   migrate_format(
       source_dir=Path("./config-toml"),
       dest_dir=Path("./config-yaml"),
       source_format="toml",
       dest_format="yaml",
   )

For more examples, see the project repository: https://github.com/holgern/vaultconfig

INI Format with DEFAULT Section
--------------------------------

SSH-Style Configuration
~~~~~~~~~~~~~~~~~~~~~~~

INI format supports DEFAULT sections, similar to SSH config files:

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager

   # Create manager for INI files
   manager = ConfigManager(
       config_dir=Path("./config"),
       format="ini",
   )

   # Add SSH-style configuration
   manager.add_config("ssh_hosts", {
       "DEFAULT": {
           "ServerAliveInterval": "45",
           "Compression": "yes",
           "ForwardX11": "yes",
       },
       "forge.example": {
           "User": "hg",
       },
       "topsecret.server.example": {
           "Port": "50022",
           "ForwardX11": "no",  # Override DEFAULT
       },
   })

   # Access configuration
   config = manager.get_config("ssh_hosts")

   # Get host configuration (includes inherited DEFAULT values)
   forge = config.get_all()["forge.example"]
   print(f"User: {forge['User']}")
   print(f"ServerAliveInterval: {forge['ServerAliveInterval']}")  # From DEFAULT
   print(f"Compression: {forge['Compression']}")  # From DEFAULT

   # topsecret host with overridden value
   secret = config.get_all()["topsecret.server.example"]
   print(f"Port: {secret['Port']}")
   print(f"ForwardX11: {secret['ForwardX11']}")  # Overridden to 'no'

Multi-Environment Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from vaultconfig import ConfigManager

   manager = ConfigManager(
       config_dir=Path("./config"),
       format="ini",
   )

   # Create multi-environment config with shared defaults
   manager.add_config("environments", {
       "DEFAULT": {
           "timeout": "30",
           "retry_count": "3",
           "log_level": "INFO",
           "protocol": "https",
       },
       "development": {
           "host": "localhost",
           "port": "8080",
           "log_level": "DEBUG",  # Override for dev
       },
       "staging": {
           "host": "staging.example.com",
           "port": "443",
       },
       "production": {
           "host": "prod.example.com",
           "port": "443",
           "timeout": "60",  # Override for production
           "retry_count": "5",  # Override for production
       },
   })

   # Access environment-specific configuration
   config = manager.get_config("environments")

   # Get production config (with overrides and inherited defaults)
   prod = config.get_all()["production"]
   print(f"Production: {prod['protocol']}://{prod['host']}:{prod['port']}")
   print(f"Timeout: {prod['timeout']}s")  # 60 (overridden)
   print(f"Retry: {prod['retry_count']}")  # 5 (overridden)
   print(f"Log Level: {prod['log_level']}")  # INFO (from DEFAULT)

The generated INI file:

.. code-block:: ini

   [DEFAULT]
   timeout = 30
   retry_count = 3
   log_level = INFO
   protocol = https

   [development]
   host = localhost
   port = 8080
   log_level = DEBUG

   [production]
   host = prod.example.com
   port = 443
   timeout = 60
   retry_count = 5

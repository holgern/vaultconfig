#!/usr/bin/env python3
"""Complete example demonstrating vaultconfig with TOML format.

This example demonstrates:
1. Loading and reading valid TOML configuration
2. Handling configuration with validation errors
3. Using obscured passwords for sensitive fields
4. Using custom cipher keys for better security
"""

import sys
from pathlib import Path

from pydantic import BaseModel, Field

from vaultconfig import create_obscurer_from_passphrase
from vaultconfig.config import ConfigManager
from vaultconfig.exceptions import SchemaValidationError
from vaultconfig.schema import ConfigSchema

# Create a unique cipher key for this example/application
# In production, you'd load this from secure storage (env var, key file, etc.)
TOML_EXAMPLE_OBSCURER = create_obscurer_from_passphrase("VaultConfig-TOML-Example-2024")


class DatabaseConfig(BaseModel):
    """Database configuration schema."""

    host: str = Field(description="Database host")
    port: int = Field(ge=1, le=65535, description="Database port (1-65535)")
    username: str = Field(description="Database username")
    password: str = Field(
        json_schema_extra={"sensitive": True}, description="Database password"
    )
    database: str = Field(description="Database name")
    ssl_enabled: bool = Field(default=False, description="Enable SSL connection")


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def example_valid_config():
    """Example 1: Load and read a valid configuration."""
    print_section("Example 1: Valid Configuration")

    # Create schema
    schema = ConfigSchema(DatabaseConfig)

    # Get the directory containing this script
    config_dir = Path(__file__).parent

    # Initialize config manager with TOML format
    manager = ConfigManager(
        config_dir=config_dir,
        format="toml",
        schema=schema,
        password=None,  # No encryption for this example
        obscurer=TOML_EXAMPLE_OBSCURER,  # Use custom cipher key
    )

    # Load the valid config
    try:
        config = manager.get_config("valid_database")

        if config:
            print("✓ Successfully loaded 'valid_database' configuration")
            print("\nConfiguration values:")
            print(f"  Host:         {config.get('host')}")
            print(f"  Port:         {config.get('port')}")
            print(f"  Username:     {config.get('username')}")
            print(f"  Database:     {config.get('database')}")
            print(f"  SSL Enabled:  {config.get('ssl_enabled')}")

            # Get password (will be revealed automatically if obscured)
            password = config.get("password")
            print(f"  Password:     {password}")

            print("\nAll values:")
            all_values = config.get_all(reveal_secrets=True)
            for key, value in all_values.items():
                print(f"  {key}: {value}")
        else:
            print("✗ Configuration 'valid_database' not found")

    except SchemaValidationError as e:
        print(f"✗ Validation error: {e}")
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")


def example_invalid_config():
    """Example 2: Try to load configuration with validation errors."""
    print_section("Example 2: Invalid Configuration (Schema Validation)")

    # Create schema
    schema = ConfigSchema(DatabaseConfig)

    # Get the directory containing this script
    config_dir = Path(__file__).parent

    # Initialize config manager WITHOUT schema first to load the file
    manager_no_schema = ConfigManager(
        config_dir=config_dir,
        format="toml",
        schema=None,
        password=None,
        obscurer=TOML_EXAMPLE_OBSCURER,  # Use custom cipher key
    )

    # Load the config without validation
    try:
        config = manager_no_schema.get_config("invalid_database")

        if config:
            print("✓ Loaded 'invalid_database' configuration (without validation)")
            print("\nRaw configuration values:")
            raw_data = config.get_all()
            for key, value in raw_data.items():
                print(f"  {key}: {value}")

            # Now try to validate it
            print("\nAttempting schema validation...")
            try:
                schema.validate(raw_data)
                print("✗ Validation passed (should have failed!)")
            except Exception as e:
                print("✓ Validation correctly detected errors:")
                # Parse the validation error
                if "validation error" in str(e):
                    print(f"  {e}")
        else:
            print("Configuration 'invalid_database' not found")

    except SchemaValidationError as e:
        print("✓ Validation correctly detected errors:")
        print(f"  {e}")
    except Exception as e:
        print(f"Error: {e}")


def example_obscured_password():
    """Example 3: Demonstrate password obscuring."""
    print_section("Example 3: Obscured Password")

    # Create schema
    schema = ConfigSchema(DatabaseConfig)

    # Get the directory containing this script
    config_dir = Path(__file__).parent

    # Initialize config manager
    manager = ConfigManager(
        config_dir=config_dir,
        format="toml",
        schema=schema,
        password=None,
        obscurer=TOML_EXAMPLE_OBSCURER,  # Use custom cipher key
    )

    # Load config with obscured password
    try:
        config = manager.get_config("obscured_database")

        if config:
            print("✓ Successfully loaded 'obscured_database' configuration")
            print("\nRaw configuration (passwords obscured):")
            raw_values = config.get_all(reveal_secrets=False)
            for key, value in raw_values.items():
                print(f"  {key}: {value}")

            print("\nRevealed configuration (passwords revealed):")
            revealed_values = config.get_all(reveal_secrets=True)
            for key, value in revealed_values.items():
                if key == "password":
                    print(f"  {key}: {value} (revealed)")
                else:
                    print(f"  {key}: {value}")

            # Demonstrate obscuring a new password with custom key
            print("\nObscuring a new password with custom cipher key:")
            new_password = "new_secret_password_123"
            obscured = TOML_EXAMPLE_OBSCURER.obscure(new_password)
            revealed_again = TOML_EXAMPLE_OBSCURER.reveal(obscured)

            print(f"  Original:  {new_password}")
            print(f"  Obscured:  {obscured}")
            print(f"  Revealed:  {revealed_again}")
            print(f"  Match:     {new_password == revealed_again}")

            # Show that the default key won't work with custom obscured password
            print("\n  Note: This password was obscured with a custom cipher key.")
            print("  It cannot be revealed with the default key used by other apps.")
        else:
            print("✗ Configuration 'obscured_database' not found")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_nested_config():
    """Example 4: Demonstrate nested TOML configuration."""
    print_section("Example 4: Nested Configuration")

    config_dir = Path(__file__).parent
    manager = ConfigManager(
        config_dir=config_dir,
        format="toml",
        schema=None,
        password=None,
        obscurer=TOML_EXAMPLE_OBSCURER,  # Use custom cipher key
    )

    # Load nested config
    try:
        config = manager.get_config("nested_config")

        if config:
            print("✓ Successfully loaded 'nested_config' configuration")
            print("\nFull configuration structure:")
            all_values = config.get_all()

            # Display nested structure
            def print_nested(data, indent=0):
                for key, value in data.items():
                    if isinstance(value, dict):
                        print("  " * indent + f"{key}:")
                        print_nested(value, indent + 1)
                    else:
                        print("  " * indent + f"{key} = {value}")

            print_nested(all_values)

            print("\nAccessing nested values with dot notation:")
            print(f"  database.host: {config.get('database.host')}")
            max_conn = config.get("database.pool.max_connections")
            print(f"  database.pool.max_connections: {max_conn}")
            rpm = config.get("api.rate_limit.requests_per_minute")
            print(f"  api.rate_limit.requests_per_minute: {rpm}")
        else:
            print("✗ Configuration 'nested_config' not found")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("  VaultConfig TOML Format Examples")
    print("=" * 60)

    # Run examples
    example_valid_config()
    example_invalid_config()
    example_obscured_password()
    example_nested_config()

    print("\n" + "=" * 60)
    print("  Examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)

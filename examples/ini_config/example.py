#!/usr/bin/env python3
"""Complete example demonstrating vaultconfig with INI format.

This example demonstrates:
1. Loading and reading valid INI configuration
2. Handling configuration with validation errors
3. Using obscured passwords for sensitive fields
"""

import sys
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from vaultconfig.config import ConfigManager
from vaultconfig.exceptions import SchemaValidationError
from vaultconfig.obscure import obscure, reveal
from vaultconfig.schema import ConfigSchema


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

    # Initialize config manager with INI format
    # Note: For INI format, we don't use schema validation during load
    # because INI files are structured as sections->keys
    manager = ConfigManager(
        config_dir=config_dir,
        format="ini",
        schema=None,  # No schema during load
        password=None,  # No encryption for this example
    )

    # Load the valid config
    try:
        config = manager.get_config("valid_database")

        if config:
            # INI files have sections, get the 'database' section
            db_section = config.get("database", {})

            if db_section:
                # Manually validate with schema
                validated_data = schema.validate(db_section)

                print("✓ Successfully loaded 'valid_database' configuration")
                print("\nConfiguration values:")
                print(f"  Host:         {validated_data['host']}")
                print(f"  Port:         {validated_data['port']}")
                print(f"  Username:     {validated_data['username']}")
                print(f"  Database:     {validated_data['database']}")
                print(f"  SSL Enabled:  {validated_data['ssl_enabled']}")
                print(f"  Password:     {validated_data['password']}")

                print("\nAll values:")
                for key, value in validated_data.items():
                    print(f"  {key}: {value}")
            else:
                print("✗ No 'database' section found in configuration")
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

    # Initialize config manager with INI format
    manager = ConfigManager(
        config_dir=config_dir,
        format="ini",
        schema=None,
        password=None,
    )

    # Try to load the invalid config
    try:
        config = manager.get_config("invalid_database")

        if config:
            # Get the 'database' section
            db_section = config.get("database", {})

            if db_section:
                # Try to validate with schema - this should fail
                try:
                    validated_data = schema.validate(db_section)
                    print("✗ Configuration loaded (should have failed validation)")
                    print("Configuration values:")
                    for key, value in validated_data.items():
                        print(f"  {key}: {value}")
                except ValidationError as e:
                    print("✓ Validation correctly detected errors:")
                    # Extract error messages
                    for error in e.errors():
                        field = error["loc"][0] if error["loc"] else "unknown"
                        msg = error["msg"]
                        print(f"  - Field '{field}': {msg}")
            else:
                print("✗ No 'database' section found in configuration")
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

    # Get the directory containing this script
    config_dir = Path(__file__).parent

    # Initialize config manager
    manager = ConfigManager(
        config_dir=config_dir,
        format="ini",
        schema=None,
        password=None,
    )

    # Load config with obscured password
    try:
        config = manager.get_config("obscured_database")

        if config:
            print("✓ Successfully loaded 'obscured_database' configuration")

            # Get the database section
            db_section = config.get("database", {})

            if db_section:
                print("\nRaw configuration (password obscured in INI file):")
                for key, value in db_section.items():
                    if key == "password":
                        # Show the obscured password
                        print(f"  {key}: {value} (obscured)")
                    else:
                        print(f"  {key}: {value}")

                # Reveal the password
                obscured_password = db_section.get("password", "")
                if obscured_password:
                    try:
                        revealed_password = reveal(obscured_password)
                        print(f"\nRevealed password: {revealed_password}")
                    except Exception as e:
                        print(f"\nCouldn't reveal password: {e}")

                # Demonstrate obscuring a new password
                print("\nObscuring a new password:")
                new_password = "new_secret_password_123"
                obscured = obscure(new_password)
                revealed_again = reveal(obscured)

                print(f"  Original:  {new_password}")
                print(f"  Obscured:  {obscured}")
                print(f"  Revealed:  {revealed_again}")
                print(f"  Match:     {new_password == revealed_again}")
            else:
                print("✗ No 'database' section found in configuration")
        else:
            print("✗ Configuration 'obscured_database' not found")

    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("  VaultConfig INI Format Examples")
    print("=" * 60)

    # Run examples
    example_valid_config()
    example_invalid_config()
    example_obscured_password()

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

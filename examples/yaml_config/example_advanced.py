#!/usr/bin/env python3
"""Advanced YAML examples demonstrating complex configurations.

This example shows:
1. Multi-environment configuration (dev/staging/prod)
2. Array and nested structure handling
3. Type preservation (integers, booleans, null, etc.)
4. Practical application configuration
"""

import sys
from pathlib import Path

from vaultconfig.config import ConfigManager


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


def example_multi_environment():
    """Demonstrate multi-environment configuration with YAML."""
    print_section("Example 1: Multi-Environment Configuration")

    config_dir = Path(__file__).parent
    manager = ConfigManager(
        config_dir=config_dir,
        format="yaml",
        schema=None,
        password=None,
    )

    # Check if environments config exists, if not create it
    if not manager.has_config("environments"):
        print("Creating multi-environment configuration...")

        env_config = {
            "development": {
                "host": "localhost",
                "port": 8080,
                "debug": True,
                "log_level": "DEBUG",
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "myapp_dev",
                },
            },
            "staging": {
                "host": "staging.example.com",
                "port": 443,
                "debug": False,
                "log_level": "INFO",
                "database": {
                    "host": "staging-db.example.com",
                    "port": 5432,
                    "name": "myapp_staging",
                },
            },
            "production": {
                "host": "prod.example.com",
                "port": 443,
                "debug": False,
                "log_level": "WARNING",
                "database": {
                    "host": "prod-db.example.com",
                    "port": 5432,
                    "name": "myapp_prod",
                },
            },
        }

        manager.add_config("environments", env_config, obscure_passwords=False)
        print("✓ Created environments.yaml\n")

    # Load and display
    config = manager.get_config("environments")
    if config:
        print("✓ Successfully loaded environments configuration\n")

        all_envs = config.get_all()
        for env_name in ["development", "staging", "production"]:
            if env_name in all_envs:
                env = all_envs[env_name]
                db = env.get("database", {})

                print(f"[{env_name.upper()}]")
                print(f"  Application: http://{env.get('host')}:{env.get('port')}")
                print(f"  Debug: {env.get('debug')}")
                print(f"  Log Level: {env.get('log_level')}")
                print(f"  Database: {db.get('host')}:{db.get('port')}/{db.get('name')}")
                print()


def example_application_config():
    """Demonstrate complete application configuration."""
    print_section("Example 2: Complete Application Configuration")

    config_dir = Path(__file__).parent
    manager = ConfigManager(
        config_dir=config_dir,
        format="yaml",
        schema=None,
        password=None,
    )

    # Create application config if it doesn't exist
    if not manager.has_config("app_config"):
        print("Creating application configuration...")

        app_config = {
            "app": {
                "name": "MyAwesomeApp",
                "version": "1.0.0",
                "environment": "production",
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "workers": 4,
                "timeout": 30,
            },
            "database": {
                "url": "postgresql://user:pass@localhost:5432/mydb",
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
            },
            "cache": {
                "backend": "redis",
                "url": "redis://localhost:6379/0",
                "ttl": 3600,
            },
            "security": {
                "secret_key": "your-secret-key-here",
                "allowed_hosts": ["localhost", "*.example.com"],
                "cors_origins": ["https://example.com", "https://app.example.com"],
            },
            "features": {
                "registration": True,
                "email_verification": True,
                "two_factor_auth": False,
            },
        }

        manager.add_config("app_config", app_config, obscure_passwords=False)
        print("✓ Created app_config.yaml\n")

    # Load and display
    config = manager.get_config("app_config")
    if config:
        print("✓ Successfully loaded application configuration\n")

        # Display configuration
        app_info = config.get_all().get("app", {})
        print(f"Application: {app_info.get('name')} v{app_info.get('version')}")
        print(f"Environment: {app_info.get('environment')}\n")

        server = config.get_all().get("server", {})
        print("Server Configuration:")
        print(f"  Listening on: {server.get('host')}:{server.get('port')}")
        print(f"  Workers: {server.get('workers')}")
        print(f"  Timeout: {server.get('timeout')}s\n")

        features = config.get_all().get("features", {})
        print("Feature Flags:")
        for feature, enabled in features.items():
            status = "✓ enabled" if enabled else "✗ disabled"
            print(f"  {feature}: {status}")


def example_type_handling():
    """Demonstrate YAML type handling."""
    print_section("Example 3: Type Handling in YAML")

    config_dir = Path(__file__).parent
    manager = ConfigManager(
        config_dir=config_dir,
        format="yaml",
        schema=None,
        password=None,
    )

    print("YAML preserves data types automatically:\n")

    # Create config with various types
    if not manager.has_config("types_demo"):
        types_config = {
            "string_value": "Hello, World!",
            "integer_value": 42,
            "float_value": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "null_value": None,
            "array_integers": [1, 2, 3, 4, 5],
            "array_strings": ["apple", "banana", "cherry"],
            "array_mixed": [1, "two", 3.0, True],
            "nested": {
                "level1": {
                    "level2": {
                        "deep_value": "Found me!",
                    },
                },
            },
            "inline_array": [1, 2, 3, 4, 5],
            "inline_strings": ["red", "green", "blue"],
        }

        manager.add_config("types_demo", types_config, obscure_passwords=False)

    config = manager.get_config("types_demo")
    if config:
        all_data = config.get_all()

        str_val = all_data["string_value"]
        str_type = type(str_val).__name__
        print(f"String: {str_val} (type: {str_type})")

        int_val = all_data["integer_value"]
        int_type = type(int_val).__name__
        print(f"Integer: {int_val} (type: {int_type})")

        float_val = all_data["float_value"]
        float_type = type(float_val).__name__
        print(f"Float: {float_val} (type: {float_type})")

        bool_val = all_data["boolean_true"]
        bool_type = type(bool_val).__name__
        print(f"Boolean: {bool_val} (type: {bool_type})")

        null_val = all_data["null_value"]
        null_type = type(null_val).__name__
        print(f"Null: {null_val} (type: {null_type})")

        arr_val = all_data["array_integers"]
        arr_type = type(arr_val).__name__
        print(f"Array: {arr_val} (type: {arr_type})")

        print(f"\nNested access: {config.get('nested.level1.level2.deep_value')}")


def example_practical_usage():
    """Show practical usage pattern."""
    print_section("Example 4: Practical Usage - Loading Environment Config")

    config_dir = Path(__file__).parent
    manager = ConfigManager(
        config_dir=config_dir,
        format="yaml",
        schema=None,
        password=None,
    )

    # Simulate loading config based on environment
    import os

    current_env = os.getenv("APP_ENV", "development")

    print(f"Current environment: {current_env}\n")

    config = manager.get_config("environments")
    if config:
        all_envs = config.get_all()

        if current_env in all_envs:
            env_config = all_envs[current_env]

            print(f"Loading configuration for {current_env}:")
            print(f"  Host: {env_config['host']}")
            print(f"  Port: {env_config['port']}")
            print(f"  Debug: {env_config['debug']}")
            print(f"  Log Level: {env_config['log_level']}")

            # Build connection string
            db = env_config.get("database", {})
            conn_str = f"postgresql://{db['host']}:{db['port']}/{db['name']}"
            print(f"  Database: {conn_str}")

            print("\n✓ Configuration loaded successfully!")
        else:
            print(f"✗ Environment '{current_env}' not found in configuration")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  VaultConfig YAML Advanced Examples")
    print("=" * 70)

    example_multi_environment()
    example_application_config()
    example_type_handling()
    example_practical_usage()

    print("\n" + "=" * 70)
    print("  All examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

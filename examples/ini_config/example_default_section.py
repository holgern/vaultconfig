#!/usr/bin/env python3
"""Enhanced example demonstrating INI DEFAULT section support.

This example shows real-world usage patterns:
1. SSH-style configuration with DEFAULT section
2. Multiple hosts inheriting common settings
3. Individual hosts overriding specific values
4. Accessing inherited values programmatically
"""

import sys
from pathlib import Path

from vaultconfig.config import ConfigManager


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


def example_ssh_config():
    """Demonstrate SSH-style configuration with DEFAULT section."""
    print_section("Example 1: SSH-Style Configuration")

    # Get the directory containing this script
    config_dir = Path(__file__).parent

    # Initialize config manager
    manager = ConfigManager(
        config_dir=config_dir,
        format="ini",
        schema=None,
        password=None,
    )

    # Load the SSH-style config
    config = manager.get_config("hosts_config")

    if config:
        print("✓ Successfully loaded 'hosts_config.ini'\n")

        all_data = config.get_all()

        # Show DEFAULT section
        if "DEFAULT" in all_data:
            print("DEFAULT section (applied to all hosts):")
            for key, value in all_data["DEFAULT"].items():
                print(f"  {key} = {value}")

        # Show each host
        print("\n" + "-" * 70)
        for section_name in sorted(all_data.keys()):
            if section_name != "DEFAULT":
                print(f"\n[{section_name}]")
                section_data = all_data[section_name]

                # Separate inherited vs specific values
                inherited = []
                specific = []
                overridden = []

                for key, value in section_data.items():
                    if "DEFAULT" in all_data and key in all_data["DEFAULT"]:
                        if value == all_data["DEFAULT"][key]:
                            inherited.append((key, value))
                        else:
                            overridden.append((key, value, all_data["DEFAULT"][key]))
                    else:
                        specific.append((key, value))

                # Display specific values first
                if specific:
                    print("  Specific settings:")
                    for key, value in specific:
                        print(f"    {key} = {value}")

                # Display overridden values
                if overridden:
                    print("  Overridden settings:")
                    for key, value, default_val in overridden:
                        print(f"    {key} = {value} (was: {default_val})")

                # Display inherited values
                if inherited:
                    print("  Inherited from DEFAULT:")
                    for key, value in inherited:
                        print(f"    {key} = {value}")

        # Demonstrate programmatic access
        print("\n" + "=" * 70)
        print("Programmatic Access Example:")
        print("=" * 70)

        # Access forge.example settings
        forge = all_data.get("forge.example", {})
        print("\nConnecting to forge.example:")
        print(f"  User: {forge.get('User')}")
        print(
            f"  ServerAliveInterval: {forge.get('ServerAliveInterval')} (from DEFAULT)"
        )
        print(f"  Compression: {forge.get('Compression')} (from DEFAULT)")
        print(f"  ForwardX11: {forge.get('ForwardX11')} (from DEFAULT)")

        # Access topsecret.server.example settings
        topsecret = all_data.get("topsecret.server.example", {})
        print("\nConnecting to topsecret.server.example:")
        print(f"  Port: {topsecret.get('Port')}")
        print(f"  ForwardX11: {topsecret.get('ForwardX11')} (overrides DEFAULT)")
        interval = topsecret.get("ServerAliveInterval")
        print(f"  ServerAliveInterval: {interval} (from DEFAULT)")
        print(f"  Compression: {topsecret.get('Compression')} (from DEFAULT)")
    else:
        print("✗ Configuration 'hosts_config' not found")


def example_multi_environment():
    """Demonstrate multi-environment configuration."""
    print_section("Example 2: Multi-Environment Configuration")

    config_dir = Path(__file__).parent
    manager = ConfigManager(
        config_dir=config_dir,
        format="ini",
        schema=None,
        password=None,
    )

    # Create a multi-environment example
    print("Creating multi-environment configuration...")

    env_config = {
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
    }

    manager.add_config("environments", env_config, obscure_passwords=False)
    print("✓ Created environments.ini\n")

    # Load and display
    config = manager.get_config("environments")
    if config:
        all_data = config.get_all()

        for env_name in ["development", "staging", "production"]:
            if env_name in all_data:
                env = all_data[env_name]
                protocol = env.get("protocol", "https")
                host = env.get("host", "unknown")
                port = env.get("port", "443")
                timeout = env.get("timeout", "30")
                retry = env.get("retry_count", "3")
                log = env.get("log_level", "INFO")

                print(f"[{env_name.upper()}]")
                print(f"  Endpoint: {protocol}://{host}:{port}")
                print(f"  Timeout: {timeout}s")
                print(f"  Retry Count: {retry}")
                print(f"  Log Level: {log}")
                print()


def example_practical_use():
    """Show practical usage pattern."""
    print_section("Example 3: Practical Usage Pattern")

    config_dir = Path(__file__).parent
    manager = ConfigManager(
        config_dir=config_dir,
        format="ini",
        schema=None,
        password=None,
    )

    # Load hosts config
    config = manager.get_config("hosts_config")
    if not config:
        print("✗ hosts_config not found")
        return

    all_data = config.get_all()

    print("Simulating SSH connection logic:\n")

    # Simulate connecting to different hosts
    for host in ["forge.example", "topsecret.server.example"]:
        if host in all_data:
            settings = all_data[host]

            print(f"ssh {host}")

            # Build connection parameters
            params = []
            if "User" in settings:
                params.append(f"-l {settings['User']}")
            if "Port" in settings:
                params.append(f"-p {settings['Port']}")

            # Add options from configuration
            options = []
            if settings.get("Compression") == "yes":
                options.append("Compression yes")
            if settings.get("ForwardX11") == "yes":
                options.append("ForwardX11 yes")
            elif settings.get("ForwardX11") == "no":
                options.append("ForwardX11 no")
            if "ServerAliveInterval" in settings:
                options.append(f"ServerAliveInterval {settings['ServerAliveInterval']}")

            if params:
                print(f"  Parameters: {' '.join(params)}")
            if options:
                print(f"  Options: {', '.join(options)}")
            print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  VaultConfig INI DEFAULT Section - Enhanced Examples")
    print("=" * 70)

    example_ssh_config()
    example_multi_environment()
    example_practical_use()

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

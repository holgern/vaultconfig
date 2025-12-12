#!/usr/bin/env python3
"""Example demonstrating custom cipher keys for password obscuring.

This example shows how to use your own cipher key instead of the default
hardcoded key to better protect obscured passwords.

IMPORTANT: Custom cipher keys provide better protection but are still
obfuscation, NOT encryption. For real security, use config file encryption.
"""

import secrets
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from vaultconfig import (
    ConfigManager,
    Obscurer,
    create_obscurer_from_bytes,
    create_obscurer_from_hex,
    create_obscurer_from_passphrase,
)
from vaultconfig.schema import ConfigSchema


class DatabaseConfig(BaseModel):
    """Database configuration schema."""

    host: str = Field(description="Database host")
    port: int = Field(ge=1, le=65535, description="Database port")
    username: str = Field(description="Database username")
    password: str = Field(
        json_schema_extra={"sensitive": True}, description="Database password"
    )
    database: str = Field(description="Database name")


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


def example_passphrase_obscurer():
    """Example 1: Create obscurer from a passphrase."""
    print_section("Example 1: Obscurer from Passphrase")

    # Create obscurer from a memorable passphrase
    # This is the easiest method - just use a unique passphrase for your app
    obscurer = create_obscurer_from_passphrase("MyApp-Unique-Passphrase-2024")

    # Test it
    password = "my_secret_password"
    obscured = obscurer.obscure(password)
    revealed = obscurer.reveal(obscured)

    print(f"Original password:  {password}")
    print(f"Obscured password:  {obscured}")
    print(f"Revealed password:  {revealed}")
    print(f"Match:              {password == revealed}")

    print("\nKey features:")
    print("  - Easy to remember and reproduce")
    print("  - Same passphrase always produces same key")
    print("  - Perfect for hardcoding in your application")


def example_random_key_obscurer():
    """Example 2: Create obscurer from random bytes."""
    print_section("Example 2: Obscurer from Random Bytes")

    # Generate a completely random 32-byte key
    # This is the most secure option but you must save the key somewhere
    random_key = secrets.token_bytes(32)

    obscurer = create_obscurer_from_bytes(random_key)

    # Convert to hex for storage/display
    hex_key = random_key.hex()
    print(f"Generated random key (hex): {hex_key}")
    print(f"Key length: {len(random_key)} bytes")

    # Test it
    password = "super_secret_123"
    obscured = obscurer.obscure(password)
    revealed = obscurer.reveal(obscured)

    print(f"\nOriginal password:  {password}")
    print(f"Obscured password:  {obscured}")
    print(f"Revealed password:  {revealed}")
    print(f"Match:              {password == revealed}")

    print("\nKey features:")
    print("  - Maximum randomness")
    print("  - Must be saved securely (env var, key file, etc.)")
    print("  - Can be generated with: vaultconfig obscure generate-key")


def example_hex_key_obscurer():
    """Example 3: Create obscurer from hex string."""
    print_section("Example 3: Obscurer from Hex String")

    # This simulates loading a key from a file or environment variable
    # You'd typically generate this once with: vaultconfig obscure generate-key
    hex_key = "a73b9f2ce15d4a8eb6f4c97a3e915cd28b4fa36e1bc57d9a2fe84ba63cd15e92"

    print("Loading key from hex string...")
    print(f"Hex key: {hex_key}")

    obscurer = create_obscurer_from_hex(hex_key)

    # Test it
    password = "test_password_456"
    obscured = obscurer.obscure(password)
    revealed = obscurer.reveal(obscured)

    print(f"\nOriginal password:  {password}")
    print(f"Obscured password:  {obscured}")
    print(f"Revealed password:  {revealed}")
    print(f"Match:              {password == revealed}")

    print("\nKey features:")
    print("  - Easy to store in text files or env vars")
    print("  - 64 hex characters = 32 bytes")
    print("  - Can be loaded from VAULTCONFIG_CIPHER_KEY env var")


def example_config_manager_with_custom_key():
    """Example 4: Use custom obscurer with ConfigManager."""
    print_section("Example 4: ConfigManager with Custom Obscurer")

    # Create a custom obscurer for your application
    my_obscurer = create_obscurer_from_passphrase("ProductionApp-Secret-Key-2024")

    # Create schema
    schema = ConfigSchema(DatabaseConfig)

    # Create a temporary config directory
    config_dir = Path("/tmp/vaultconfig_custom_key_example")
    config_dir.mkdir(exist_ok=True)

    # Initialize ConfigManager with custom obscurer
    manager = ConfigManager(
        config_dir=config_dir,
        format="toml",
        schema=schema,
        password=None,  # No file encryption
        obscurer=my_obscurer,  # Use custom cipher key
    )

    print("Created ConfigManager with custom cipher key")

    # Add a configuration with sensitive fields
    config_data = {
        "host": "db.example.com",
        "port": 5432,
        "username": "admin",
        "password": "very_secret_password_123",  # Will be obscured with custom key
        "database": "production_db",
    }

    manager.add_config("production", config_data)
    print("\nAdded 'production' config with obscured password")

    # Read the config back
    config = manager.get_config("production")
    if config:
        print("\nConfiguration values (password auto-revealed):")
        all_values = config.get_all(reveal_secrets=True)
        for key, value in all_values.items():
            if key == "password":
                print(f"  {key}: {value} (was obscured, now revealed)")
            else:
                print(f"  {key}: {value}")

    # Show the raw file content
    config_file = config_dir / "production.toml"
    print(f"\nRaw config file content ({config_file}):")
    with open(config_file) as f:
        for line in f:
            print(f"  {line.rstrip()}")

    print("\nKey features:")
    print("  - All operations (obscure/reveal) use your custom key")
    print("  - Other apps can't reveal passwords without your key")
    print("  - Passwords in config files are obscured with YOUR key")

    # Cleanup
    config_file.unlink()
    config_dir.rmdir()


def example_cli_usage():
    """Example 5: CLI usage with custom cipher keys."""
    print_section("Example 5: CLI Usage with Custom Keys")

    print("To use custom cipher keys with the CLI:\n")

    print("1. Generate a cipher key:")
    print("   $ vaultconfig obscure generate-key > ~/.myapp_cipher_key\n")

    print("2. Set environment variable:")
    print("   $ export VAULTCONFIG_CIPHER_KEY_FILE=~/.myapp_cipher_key")
    print("   # or")
    print("   $ export VAULTCONFIG_CIPHER_KEY=$(cat ~/.myapp_cipher_key)\n")

    print("3. Use vaultconfig CLI normally:")
    print("   $ vaultconfig init ./myapp-config")
    print("   $ vaultconfig show ./myapp-config database --reveal\n")

    print("4. Generate from passphrase (reproducible):")
    print("   $ vaultconfig obscure generate-key --from-passphrase\n")

    print("All CLI operations will use your custom cipher key!")


def example_different_keys_comparison():
    """Example 6: Demonstrate that different keys produce different results."""
    print_section("Example 6: Different Keys = Different Obscured Passwords")

    password = "same_password"

    # Create three different obscurers
    obscurer1 = create_obscurer_from_passphrase("Key-1")
    obscurer2 = create_obscurer_from_passphrase("Key-2")
    obscurer3 = Obscurer()  # Default key

    # Obscure the same password with different keys
    obscured1 = obscurer1.obscure(password)
    obscured2 = obscurer2.obscure(password)
    obscured3 = obscurer3.obscure(password)

    print(f"Original password: {password}\n")
    print(f"Obscured with Key-1:     {obscured1}")
    print(f"Obscured with Key-2:     {obscured2}")
    print(f"Obscured with default:   {obscured3}")

    print("\nTrying to reveal with wrong keys:")
    try:
        # Try to reveal password obscured with Key-1 using Key-2
        wrong_reveal = obscurer2.reveal(obscured1)
        print(f"  Key-2 revealed Key-1's password: {wrong_reveal} (WRONG!)")
    except Exception:
        print("  ✓ Key-2 cannot reveal Key-1's password (as expected)")

    try:
        # Try to reveal password obscured with Key-1 using default key
        wrong_reveal = obscurer3.reveal(obscured1)
        print(f"  Default revealed Key-1's password: {wrong_reveal} (WRONG!)")
    except Exception:
        print("  ✓ Default key cannot reveal Key-1's password (as expected)")

    print("\nRevealing with correct keys:")
    print(f"  Key-1 reveals its own:   {obscurer1.reveal(obscured1)} ✓")
    print(f"  Key-2 reveals its own:   {obscurer2.reveal(obscured2)} ✓")
    print(f"  Default reveals its own: {obscurer3.reveal(obscured3)} ✓")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("  VaultConfig Custom Cipher Key Examples")
    print("=" * 70)

    example_passphrase_obscurer()
    example_random_key_obscurer()
    example_hex_key_obscurer()
    example_config_manager_with_custom_key()
    example_cli_usage()
    example_different_keys_comparison()

    print("\n" + "=" * 70)
    print("  All examples completed!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Use create_obscurer_from_passphrase() for easy app-specific keys")
    print("  2. Use generate-key command for random keys (most secure)")
    print("  3. Pass obscurer= to ConfigManager to use your custom key")
    print("  4. Set VAULTCONFIG_CIPHER_KEY env var for CLI usage")
    print("  5. Different keys = different obscured passwords (they don't mix!)")
    print("\n  Remember: This is still obfuscation, NOT encryption!")
    print("  For real security, use config file encryption (password= parameter)")
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

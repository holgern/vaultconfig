"""Tests for custom cipher key functionality."""

import secrets

import pytest

from vaultconfig.obscure import (
    Obscurer,
    create_obscurer_from_bytes,
    create_obscurer_from_hex,
    create_obscurer_from_passphrase,
    obscure,
    reveal,
)


class TestObscurerClass:
    """Test the Obscurer class with custom keys."""

    def test_obscurer_with_custom_key(self):
        """Test obscurer with a custom 32-byte key."""
        custom_key = secrets.token_bytes(32)
        obscurer = Obscurer(cipher_key=custom_key)

        password = "test_password_123"
        obscured = obscurer.obscure(password)
        revealed = obscurer.reveal(obscured)

        assert revealed == password
        assert obscured != password

    def test_obscurer_with_default_key(self):
        """Test obscurer with default key (None)."""
        obscurer = Obscurer(cipher_key=None)

        password = "default_key_password"
        obscured = obscurer.obscure(password)
        revealed = obscurer.reveal(obscured)

        assert revealed == password

    def test_different_keys_produce_different_results(self):
        """Test that different keys produce different obscured passwords."""
        password = "same_password"

        key1 = secrets.token_bytes(32)
        key2 = secrets.token_bytes(32)

        obscurer1 = Obscurer(cipher_key=key1)
        obscurer2 = Obscurer(cipher_key=key2)

        obscured1 = obscurer1.obscure(password)
        obscured2 = obscurer2.obscure(password)

        # Different keys should produce different obscured results
        # (even for the same password)
        assert obscured1 != obscured2

        # But each can reveal its own
        assert obscurer1.reveal(obscured1) == password
        assert obscurer2.reveal(obscured2) == password

    def test_wrong_key_cannot_reveal(self):
        """Test that wrong key cannot reveal password."""
        password = "secret"

        key1 = secrets.token_bytes(32)
        key2 = secrets.token_bytes(32)

        obscurer1 = Obscurer(cipher_key=key1)
        obscurer2 = Obscurer(cipher_key=key2)

        obscured = obscurer1.obscure(password)

        # Trying to reveal with wrong key should produce garbage or error
        try:
            revealed_wrong = obscurer2.reveal(obscured)
            # If it doesn't raise an error, it should at least not match
            assert revealed_wrong != password
        except (ValueError, UnicodeDecodeError):
            # This is expected - wrong key produces invalid data
            pass

    def test_obscurer_invalid_key_length(self):
        """Test that invalid key length raises error."""
        # Too short
        with pytest.raises(ValueError, match="exactly 32 bytes"):
            Obscurer(cipher_key=b"too_short")

        # Too long
        with pytest.raises(ValueError, match="exactly 32 bytes"):
            Obscurer(cipher_key=b"x" * 64)

    def test_obscurer_invalid_key_type(self):
        """Test that invalid key type raises error."""
        with pytest.raises(TypeError, match="must be bytes"):
            Obscurer(cipher_key="not_bytes")  # type: ignore

    def test_obscurer_is_obscured(self):
        """Test is_obscured method with custom key."""
        custom_key = secrets.token_bytes(32)
        obscurer = Obscurer(cipher_key=custom_key)

        password = "test"
        obscured = obscurer.obscure(password)

        assert obscurer.is_obscured(obscured) is True
        assert obscurer.is_obscured("plaintext") is False


class TestObscurerHelpers:
    """Test helper functions for creating obscurers."""

    def test_create_from_hex(self):
        """Test creating obscurer from hex string."""
        hex_key = "a73b9f2ce15d4a8eb6f4c97a3e915cd28b4fa36e1bc57d9a2fe84ba63cd15e92"
        obscurer = create_obscurer_from_hex(hex_key)

        password = "test"
        obscured = obscurer.obscure(password)
        revealed = obscurer.reveal(obscured)

        assert revealed == password

    def test_create_from_hex_invalid(self):
        """Test that invalid hex raises error."""
        with pytest.raises(ValueError, match="Invalid hex key"):
            create_obscurer_from_hex("not_valid_hex!!!")

        with pytest.raises(ValueError, match="exactly 32 bytes"):
            create_obscurer_from_hex("aabbcc")  # Too short

    def test_create_from_passphrase(self):
        """Test creating obscurer from passphrase."""
        passphrase = "MyApp-Secret-2024"
        obscurer = create_obscurer_from_passphrase(passphrase)

        password = "test"
        obscured = obscurer.obscure(password)
        revealed = obscurer.reveal(obscured)

        assert revealed == password

    def test_create_from_passphrase_deterministic(self):
        """Test that same passphrase produces same key."""
        passphrase = "MyPassphrase"

        obscurer1 = create_obscurer_from_passphrase(passphrase)
        obscurer2 = create_obscurer_from_passphrase(passphrase)

        password = "test"
        obscured1 = obscurer1.obscure(password)

        # obscurer2 should be able to reveal password obscured by obscurer1
        revealed = obscurer2.reveal(obscured1)
        assert revealed == password

    def test_create_from_passphrase_empty(self):
        """Test that empty passphrase raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            create_obscurer_from_passphrase("")

    def test_create_from_bytes(self):
        """Test creating obscurer from bytes."""
        key_bytes = secrets.token_bytes(32)
        obscurer = create_obscurer_from_bytes(key_bytes)

        password = "test"
        obscured = obscurer.obscure(password)
        revealed = obscurer.reveal(obscured)

        assert revealed == password

    def test_create_from_bytes_invalid_length(self):
        """Test that invalid length raises error."""
        with pytest.raises(ValueError, match="exactly 32 bytes"):
            create_obscurer_from_bytes(b"too_short")


class TestBackwardCompatibility:
    """Test that module-level functions still work (backward compatibility)."""

    def test_module_functions_still_work(self):
        """Test that obscure() and reveal() module functions work."""
        password = "test_password"
        obscured = obscure(password)
        revealed = reveal(obscured)

        assert revealed == password
        assert obscured != password

    def test_module_functions_use_same_key(self):
        """Test that multiple calls use consistent default key."""
        password = "test"

        obscured1 = obscure(password)
        obscured2 = obscure(password)

        # Both should be revealable with module function
        assert reveal(obscured1) == password
        assert reveal(obscured2) == password

    def test_default_obscurer_singleton(self):
        """Test that default obscurer is a singleton."""
        from vaultconfig.obscure import _get_default_obscurer

        obscurer1 = _get_default_obscurer()
        obscurer2 = _get_default_obscurer()

        # Should be the same instance
        assert obscurer1 is obscurer2


class TestCustomKeyInteroperability:
    """Test that custom keys don't interfere with each other."""

    def test_custom_and_default_keys_independent(self):
        """Test that custom and default keys are independent."""
        password = "test"

        # Obscure with default key
        obscured_default = obscure(password)

        # Obscure with custom key
        custom_obscurer = create_obscurer_from_passphrase("Custom")
        obscured_custom = custom_obscurer.obscure(password)

        # They should be different
        assert obscured_default != obscured_custom

        # Each can reveal its own
        assert reveal(obscured_default) == password
        assert custom_obscurer.reveal(obscured_custom) == password

        # But custom can't reveal default's password (or vice versa)
        try:
            wrong_reveal = custom_obscurer.reveal(obscured_default)
            assert wrong_reveal != password
        except (ValueError, UnicodeDecodeError):
            pass

    def test_multiple_custom_keys_independent(self):
        """Test that multiple custom keys are independent."""
        password = "test"

        obs1 = create_obscurer_from_passphrase("Key1")
        obs2 = create_obscurer_from_passphrase("Key2")
        obs3 = create_obscurer_from_passphrase("Key3")

        obscured1 = obs1.obscure(password)
        obscured2 = obs2.obscure(password)
        obscured3 = obs3.obscure(password)

        # All different
        assert obscured1 != obscured2 != obscured3

        # Each can reveal its own
        assert obs1.reveal(obscured1) == password
        assert obs2.reveal(obscured2) == password
        assert obs3.reveal(obscured3) == password


class TestObscurerEdgeCases:
    """Test edge cases for Obscurer class."""

    def test_empty_password(self):
        """Test obscuring empty password."""
        obscurer = Obscurer()

        obscured = obscurer.obscure("")
        assert obscured == ""

        revealed = obscurer.reveal("")
        assert revealed == ""

    def test_very_long_password(self):
        """Test obscuring very long password."""
        obscurer = create_obscurer_from_passphrase("Test")

        password = "x" * 10000
        obscured = obscurer.obscure(password)
        revealed = obscurer.reveal(obscured)

        assert revealed == password

    def test_unicode_password_custom_key(self):
        """Test obscuring unicode password with custom key."""
        obscurer = create_obscurer_from_passphrase("Unicode-Test")

        passwords = [
            "пароль123",  # Russian
            "密码123",  # Chinese
            "パスワード123",  # Japanese
            "🔒secure🔑",  # Emoji
        ]

        for password in passwords:
            obscured = obscurer.obscure(password)
            revealed = obscurer.reveal(obscured)
            assert revealed == password

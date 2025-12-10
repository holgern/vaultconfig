"""Tests for password obscuring functionality."""

import pytest

from vaultconfig import obscure


class TestObscure:
    """Test password obscuring functions."""

    def test_obscure_and_reveal(self):
        """Test basic obscure and reveal round-trip."""
        password = "my_secret_password_123"
        obscured = obscure.obscure(password)

        # Obscured should be different from original
        assert obscured != password
        # Obscured should be base64-like string
        assert isinstance(obscured, str)
        assert len(obscured) > 0

        # Reveal should return original
        revealed = obscure.reveal(obscured)
        assert revealed == password

    def test_obscure_empty_string(self):
        """Test obscuring empty string."""
        obscured = obscure.obscure("")
        assert obscured == ""

        revealed = obscure.reveal("")
        assert revealed == ""

    def test_obscure_unicode(self):
        """Test obscuring unicode passwords."""
        passwords = [
            "пароль123",  # Russian
            "密码123",  # Chinese
            "パスワード123",  # Japanese
            "🔒secure🔑",  # Emoji
        ]

        for password in passwords:
            obscured = obscure.obscure(password)
            revealed = obscure.reveal(obscured)
            assert revealed == password

    def test_obscure_different_each_time(self):
        """Test that obscuring same password produces different results."""
        password = "test_password"

        obscured1 = obscure.obscure(password)
        obscured2 = obscure.obscure(password)

        # Different obscured values (due to random IV)
        assert obscured1 != obscured2

        # Both reveal to same password
        assert obscure.reveal(obscured1) == password
        assert obscure.reveal(obscured2) == password

    def test_reveal_invalid_password(self):
        """Test revealing invalid obscured password."""
        invalid_passwords = [
            "not_obscured",
            "invalid!!!",
            "too_short",
            "x",
        ]

        for invalid in invalid_passwords:
            with pytest.raises(ValueError):
                obscure.reveal(invalid)

    def test_is_obscured(self):
        """Test is_obscured detection."""
        password = "my_password"
        obscured = obscure.obscure(password)

        # Should detect obscured password
        assert obscure.is_obscured(obscured) is True

        # Should not detect plain text
        assert obscure.is_obscured("plaintext") is False
        assert obscure.is_obscured("") is False

    def test_obscure_long_password(self):
        """Test obscuring very long passwords."""
        # 1000 character password
        password = "a" * 1000
        obscured = obscure.obscure(password)
        revealed = obscure.reveal(obscured)

        assert revealed == password

    def test_obscure_special_characters(self):
        """Test obscuring passwords with special characters."""
        passwords = [
            "pass@word#123$",
            "p@$$w0rd!",
            "test\nwith\nnewlines",
            "test\twith\ttabs",
            "test with spaces",
            "'quotes'",
            '"double quotes"',
            "back\\slash",
        ]

        for password in passwords:
            obscured = obscure.obscure(password)
            revealed = obscure.reveal(obscured)
            assert revealed == password


class TestObscureBase64:
    """Test base64 encoding specifics."""

    def test_obscured_is_url_safe_base64(self):
        """Test that obscured passwords are URL-safe base64."""
        password = "test_password"
        obscured = obscure.obscure(password)

        # Should not contain URL-unsafe characters
        assert "+" not in obscured
        assert "/" not in obscured
        assert "=" not in obscured  # No padding

        # Should only contain URL-safe base64 chars
        import re

        assert re.match(r"^[A-Za-z0-9_-]+$", obscured)

    def test_reveal_with_padding(self):
        """Test revealing passwords that need base64 padding."""
        password = "test"
        obscured = obscure.obscure(password)

        # Remove any existing padding
        obscured_no_padding = obscured.rstrip("=")

        # Should still reveal correctly (padding added automatically)
        revealed = obscure.reveal(obscured_no_padding)
        assert revealed == password


class TestObscureErrors:
    """Test error handling."""

    def test_reveal_corrupted_data(self):
        """Test revealing corrupted obscured data."""
        password = "test_password"
        obscured = obscure.obscure(password)

        # Corrupt the obscured data more severely - flip bits in the middle
        # This ensures we corrupt the actual encrypted data, not just the end
        mid = len(obscured) // 2
        corrupted = obscured[:mid] + "XXXXX" + obscured[mid + 5 :]

        with pytest.raises(ValueError):
            obscure.reveal(corrupted)

    def test_reveal_too_short(self):
        """Test revealing data that's too short to be valid."""
        # Less than 16 bytes (AES block size) after base64 decode
        too_short = "abc"

        with pytest.raises(ValueError):
            obscure.reveal(too_short)

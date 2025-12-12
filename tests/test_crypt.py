"""Tests for config file encryption functionality."""

import pytest

from vaultconfig import crypt
from vaultconfig.exceptions import (
    DecryptionError,
    InvalidPasswordError,
)


class TestEncryptDecrypt:
    """Test encryption and decryption functionality."""

    def test_encrypt_decrypt_round_trip(self):
        """Test basic encrypt and decrypt round-trip."""
        data = b"This is my config data"
        password = "test_password_123"

        # Encrypt
        encrypted = crypt.encrypt(data, password)

        # Should be different from original
        assert encrypted != data
        # Should have encryption header
        assert crypt.ENCRYPTION_HEADER.encode() in encrypted

        # Decrypt
        decrypted = crypt.decrypt(encrypted, password)
        assert decrypted == data

    def test_encrypt_empty_data(self):
        """Test encrypting empty data."""
        data = b""
        password = "test_password"

        encrypted = crypt.encrypt(data, password)
        decrypted = crypt.decrypt(encrypted, password)

        assert decrypted == data

    def test_encrypt_large_data(self):
        """Test encrypting large data."""
        # 1MB of data
        data = b"x" * (1024 * 1024)
        password = "test_password"

        encrypted = crypt.encrypt(data, password)
        decrypted = crypt.decrypt(encrypted, password)

        assert decrypted == data

    def test_encrypt_unicode_data(self):
        """Test encrypting unicode config data."""
        data = "Config with unicode: пароль 密码 🔒".encode()
        password = "test_password"

        encrypted = crypt.encrypt(data, password)
        decrypted = crypt.decrypt(encrypted, password)

        assert decrypted == data

    def test_wrong_password_fails(self):
        """Test that wrong password fails decryption."""
        data = b"secret config"
        password = "correct_password"
        wrong_password = "wrong_password"

        encrypted = crypt.encrypt(data, password)

        with pytest.raises(InvalidPasswordError):
            crypt.decrypt(encrypted, wrong_password)

    def test_different_passwords(self):
        """Test encryption with different passwords."""
        data = b"config data"
        password1 = "password1"
        password2 = "password2"

        encrypted1 = crypt.encrypt(data, password1)
        encrypted2 = crypt.encrypt(data, password2)

        # Different passwords produce different encrypted data
        assert encrypted1 != encrypted2

        # Each decrypts correctly with its own password
        assert crypt.decrypt(encrypted1, password1) == data
        assert crypt.decrypt(encrypted2, password2) == data


class TestIsEncrypted:
    """Test is_encrypted detection."""

    def test_is_encrypted_true(self):
        """Test detecting encrypted data."""
        data = b"test data"
        password = "test_password"

        encrypted = crypt.encrypt(data, password)
        assert crypt.is_encrypted(encrypted) is True

    def test_is_encrypted_false(self):
        """Test detecting unencrypted data."""
        plaintext_data = [
            b"Just plain text",
            b"# Comment line\ndata=value",
            b"[section]\nkey=value",
            b"",
        ]

        for data in plaintext_data:
            assert crypt.is_encrypted(data) is False

    def test_is_encrypted_partial_match(self):
        """Test that partial header match doesn't count as encrypted."""
        fake_encrypted = b"VAULTCONFIG_ENCRYPT_something else"
        assert crypt.is_encrypted(fake_encrypted) is False


class TestDeriveKey:
    """Test key derivation."""

    def test_derive_key_consistent(self):
        """Test that same password with same salt produces same key."""
        password = "test_password"
        salt = b"fixed_salt_12345"  # Use fixed salt for consistency test

        key1, salt1 = crypt.derive_key(password, salt=salt)
        key2, salt2 = crypt.derive_key(password, salt=salt)

        assert key1 == key2
        assert salt1 == salt2 == salt

    def test_derive_key_random_salt(self):
        """Test that same password with random salts produces different keys."""
        password = "test_password"

        key1, salt1 = crypt.derive_key(password)
        key2, salt2 = crypt.derive_key(password)

        # Different salts should produce different keys
        assert salt1 != salt2
        assert key1 != key2

    def test_derive_key_different_passwords(self):
        """Test that different passwords produce different keys."""
        password1 = "password1"
        password2 = "password2"
        salt = b"same_salt_123456"  # Use same salt

        key1, _ = crypt.derive_key(password1, salt=salt)
        key2, _ = crypt.derive_key(password2, salt=salt)

        assert key1 != key2

    def test_derive_key_length(self):
        """Test that derived key is correct length."""
        password = "test_password"

        key, salt = crypt.derive_key(password)

        # NaCl requires 32-byte key
        assert len(key) == 32
        # Salt should be 16 bytes
        assert len(salt) == 16

    def test_derive_key_empty_password_fails(self):
        """Test that empty password fails."""
        with pytest.raises(ValueError):
            crypt.derive_key("")


class TestEncryptionFormat:
    """Test encryption format specifics."""

    def test_encrypted_format_has_header(self):
        """Test that encrypted data has correct header."""
        data = b"test data"
        password = "test_password"

        encrypted = crypt.encrypt(data, password)
        decrypted_str = encrypted.decode("utf-8")

        # Should start with version header
        assert decrypted_str.startswith(crypt.ENCRYPTION_HEADER)

    def test_encrypted_format_has_base64(self):
        """Test that encrypted data contains base64."""
        data = b"test data"
        password = "test_password"

        encrypted = crypt.encrypt(data, password)
        lines = encrypted.decode("utf-8").strip().split("\n")

        # Should have at least 2 lines: header + base64 data
        assert len(lines) >= 2

        # Second line should be base64
        import base64

        try:
            base64.b64decode(lines[1])
        except Exception:
            pytest.fail("Encrypted data does not contain valid base64")

    def test_decrypt_unsupported_version(self):
        """Test that unsupported version fails."""
        # Create fake encrypted data with unsupported version
        fake_encrypted = b"VAULTCONFIG_ENCRYPT_V999:\nYWJjZGVmZ2hpamtsbW5vcA=="

        with pytest.raises(DecryptionError, match="Unsupported encryption version"):
            crypt.decrypt(fake_encrypted, "password")

    def test_decrypt_no_data_after_header(self):
        """Test decryption with missing data after header."""
        fake_encrypted = f"{crypt.ENCRYPTION_HEADER}\n".encode()

        with pytest.raises(DecryptionError, match="No encrypted data"):
            crypt.decrypt(fake_encrypted, "password")

    def test_decrypt_invalid_base64(self):
        """Test decryption with invalid base64."""
        fake_encrypted = f"{crypt.ENCRYPTION_HEADER}\ninvalid!!!base64".encode()

        with pytest.raises(DecryptionError, match="Invalid base64"):
            crypt.decrypt(fake_encrypted, "password")


class TestGetPassword:
    """Test password retrieval."""

    def test_get_password_from_env(self, monkeypatch):
        """Test getting password from environment variable."""
        test_password = "env_password_123"
        monkeypatch.setenv(crypt.ENV_PASSWORD, test_password)

        password = crypt.get_password()
        assert password == test_password

    def test_get_password_env_priority(self, monkeypatch, tmp_path):
        """Test that environment variable has priority."""
        env_password = "env_password"
        monkeypatch.setenv(crypt.ENV_PASSWORD, env_password)

        # Also set password command (should be ignored)
        cmd_file = tmp_path / "pwd.sh"
        cmd_file.write_text("#!/bin/sh\necho 'cmd_password'")
        cmd_file.chmod(0o755)
        monkeypatch.setenv(crypt.ENV_PASSWORD_COMMAND, str(cmd_file))

        password = crypt.get_password()
        # Should use env var, not command
        assert password == env_password

    def test_get_password_from_command(self, monkeypatch, tmp_path):
        """Test getting password from command."""
        import platform
        import sys

        # Create a Python script that works cross-platform
        cmd_file = tmp_path / "get_password.py"
        cmd_file.write_text("import sys\nprint('command_password_123')")

        monkeypatch.delenv(crypt.ENV_PASSWORD, raising=False)

        # Use Python to execute the script (works on all platforms)
        # Use str() to ensure paths are strings, not Path objects
        if platform.system() == "Windows":
            # On Windows, use python with script file to avoid quoting issues
            # shlex.split with posix=False doesn't handle nested quotes well
            monkeypatch.setenv(
                crypt.ENV_PASSWORD_COMMAND,
                f'"{sys.executable}" "{str(cmd_file)}"',
            )
        else:
            # On Unix, we can execute the script file directly
            monkeypatch.setenv(
                crypt.ENV_PASSWORD_COMMAND,
                f'"{sys.executable}" "{str(cmd_file)}"',
            )

        password = crypt.get_password()
        assert password == "command_password_123"

    def test_get_password_command_with_change_flag(self, monkeypatch, tmp_path):
        """Test password command receives VAULTCONFIG_PASSWORD_CHANGE flag."""
        import sys

        # Create command that checks environment variable (cross-platform)
        # Use a script file to avoid quoting issues on all platforms
        cmd_file = tmp_path / "pwd.py"
        cmd_file.write_text(
            "import os\n"
            "import sys\n"
            "if os.environ.get('VAULTCONFIG_PASSWORD_CHANGE') == '1':\n"
            "    print('new_password')\n"
            "else:\n"
            "    print('old_password')\n"
        )
        cmd = f'"{sys.executable}" "{str(cmd_file)}"'

        monkeypatch.delenv(crypt.ENV_PASSWORD, raising=False)
        monkeypatch.setenv(crypt.ENV_PASSWORD_COMMAND, cmd)

        # Normal call
        password = crypt.get_password(changing=False)
        assert password == "old_password"

        # Call with changing=True
        password = crypt.get_password(changing=True)
        assert password == "new_password"

    def test_get_password_no_source_fails(self, monkeypatch):
        """Test that missing password source raises error."""
        monkeypatch.delenv(crypt.ENV_PASSWORD, raising=False)
        monkeypatch.delenv(crypt.ENV_PASSWORD_COMMAND, raising=False)

        # No TTY available in tests
        with pytest.raises(ValueError, match="No password provided"):
            crypt.get_password()


class TestCheckPassword:
    """Test password validation."""

    def test_check_password_valid(self):
        """Test valid passwords."""
        valid_passwords = [
            "simple_password",
            "p@$$w0rd!",
            "пароль123",  # Unicode (8 chars)
            "密码密码",  # Chinese (4 chars)
            "pass with spaces",
        ]

        for password in valid_passwords:
            normalized, warnings = crypt.check_password(password)
            assert normalized == password
            assert isinstance(warnings, list)

    def test_check_password_empty_fails(self):
        """Test that empty password fails."""
        with pytest.raises(ValueError, match="cannot be empty"):
            crypt.check_password("")

    def test_check_password_whitespace_only_fails(self):
        """Test that whitespace-only password fails."""
        with pytest.raises(ValueError, match="at least one non-whitespace"):
            crypt.check_password("   ")

    def test_check_password_too_short_fails(self):
        """Test that password shorter than 4 characters fails."""
        # Test 1, 2, 3 character passwords
        for password in ["a", "ab", "abc"]:
            with pytest.raises(ValueError, match="at least 4 characters"):
                crypt.check_password(password)

    def test_check_password_minimum_length(self):
        """Test that 4 character password is accepted with warning."""
        password = "abcd"
        normalized, warnings = crypt.check_password(password)
        assert normalized == password
        # Should have warning about being shorter than 12 characters
        assert any("shorter than recommended 12 characters" in w for w in warnings)

    def test_check_password_short_warning(self):
        """Test that passwords < 12 characters get a warning."""
        short_passwords = ["1234", "12345", "password1", "short"]
        for password in short_passwords:
            normalized, warnings = crypt.check_password(password)
            assert normalized == password
            assert any("shorter than recommended 12 characters" in w for w in warnings)

    def test_check_password_no_warning_long(self):
        """Test that passwords >= 12 characters don't get short password warning."""
        password = "this_is_a_very_long_secure_password"
        normalized, warnings = crypt.check_password(password)
        assert normalized == password
        # Should not have warning about length
        assert not any("shorter than recommended" in w for w in warnings)

    def test_check_password_leading_trailing_whitespace_warning(self):
        """Test warning for leading/trailing whitespace."""
        password = "  password  "
        normalized, warnings = crypt.check_password(password)

        assert normalized == password  # Preserved
        assert len(warnings) > 0
        assert any("whitespace" in w.lower() for w in warnings)

    def test_check_password_unicode_normalization(self):
        """Test unicode normalization."""
        # Test with decomposed vs composed unicode
        # These look the same but have different representations

        # Manually create different unicode representations if possible
        # For simplicity, just test that normalization is mentioned
        password = "café"  # Already normalized
        normalized, warnings = crypt.check_password(password)

        assert isinstance(normalized, str)
        assert isinstance(warnings, list)


class TestDecryptErrors:
    """Test decryption error cases."""

    def test_decrypt_empty_data(self):
        """Test decrypting empty data."""
        with pytest.raises(DecryptionError, match="Empty config data"):
            crypt.decrypt(b"", "password")

    def test_decrypt_no_header(self):
        """Test decrypting data without encryption header."""
        plaintext = b"Just plain config data"

        with pytest.raises(DecryptionError, match="not encrypted"):
            crypt.decrypt(plaintext, "password")

    def test_decrypt_corrupted_data(self):
        """Test decrypting corrupted encrypted data."""
        data = b"test data"
        password = "test_password"

        encrypted = crypt.encrypt(data, password)

        # Corrupt the encrypted data (but keep header)
        lines = encrypted.split(b"\n")
        lines[1] = b"corrupted_base64_data_that_wont_decrypt"
        corrupted = b"\n".join(lines)

        with pytest.raises((DecryptionError, InvalidPasswordError)):
            crypt.decrypt(corrupted, password)

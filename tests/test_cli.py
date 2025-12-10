"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner

from vaultconfig.cli import main
from vaultconfig.config import ConfigManager


@pytest.fixture
def cli_runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


def test_cli_main_help(cli_runner):
    """Test main CLI help."""
    result = cli_runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "VaultConfig" in result.output


def test_cli_init(cli_runner, temp_dir):
    """Test init command."""
    config_dir = temp_dir / "test_config"
    result = cli_runner.invoke(main, ["init", str(config_dir)])
    assert result.exit_code == 0
    assert config_dir.exists()
    assert "Initialized" in result.output


def test_cli_init_with_format(cli_runner, temp_dir):
    """Test init command with specific format."""
    config_dir = temp_dir / "test_config"
    result = cli_runner.invoke(main, ["init", str(config_dir), "-f", "ini"])
    assert result.exit_code == 0
    assert "Format: ini" in result.output


def test_cli_init_with_encryption(cli_runner, temp_dir):
    """Test init command with encryption."""
    config_dir = temp_dir / "test_config"
    result = cli_runner.invoke(
        main, ["init", str(config_dir), "-e"], input="password123\npassword123\n"
    )
    assert result.exit_code == 0
    assert "Encrypted: Yes" in result.output


def test_cli_init_password_mismatch(cli_runner, temp_dir):
    """Test init with mismatched passwords."""
    config_dir = temp_dir / "test_config"
    result = cli_runner.invoke(
        main, ["init", str(config_dir), "-e"], input="password123\nwrong\n"
    )
    assert result.exit_code == 1
    assert "do not match" in result.output


def test_cli_init_existing_directory(cli_runner, config_dir):
    """Test init with existing non-empty directory."""
    # Add a config first
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    # Try to init again - should warn
    result = cli_runner.invoke(main, ["init", str(config_dir)], input="n\n")
    assert result.exit_code == 0
    # Check for warning message (may contain line breaks)
    assert "already" in result.output and "exists" in result.output
    assert "not empty" in result.output


def test_cli_list_empty(cli_runner, config_dir):
    """Test list command with no configs."""
    result = cli_runner.invoke(main, ["list", str(config_dir)])
    assert result.exit_code == 0
    assert "No configurations found" in result.output


def test_cli_list_with_configs(cli_runner, config_dir):
    """Test list command with configs."""
    manager = ConfigManager(config_dir)
    manager.add_config("test1", {"key": "value1"}, obscure_passwords=False)
    manager.add_config("test2", {"key": "value2"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["list", str(config_dir)])
    assert result.exit_code == 0
    assert "test1" in result.output
    assert "test2" in result.output


def test_cli_list_encrypted(cli_runner, config_dir):
    """Test list command with encrypted configs."""
    manager = ConfigManager(config_dir, password="secret")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main, ["list", str(config_dir)], env={"VAULTCONFIG_PASSWORD": "secret"}
    )
    assert result.exit_code == 0
    assert "test" in result.output


def test_cli_show_config(cli_runner, config_dir):
    """Test show command."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 8080}, obscure_passwords=False
    )

    result = cli_runner.invoke(main, ["show", str(config_dir), "test"])
    assert result.exit_code == 0
    assert "localhost" in result.output
    assert "8080" in result.output


def test_cli_show_config_not_found(cli_runner, config_dir):
    """Test show command with non-existent config."""
    result = cli_runner.invoke(main, ["show", str(config_dir), "nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_show_with_reveal(cli_runner, config_dir, sample_schema):
    """Test show command with --reveal flag."""
    manager = ConfigManager(config_dir, schema=sample_schema)
    manager.add_config(
        "test",
        {
            "host": "localhost",
            "port": 8080,
            "username": "testuser",
            "password": "secret",
        },
    )

    result = cli_runner.invoke(main, ["show", str(config_dir), "test", "-r"])
    assert result.exit_code == 0
    assert "secret" in result.output


def test_cli_show_without_reveal(cli_runner, config_dir, sample_schema):
    """Test show command without --reveal flag."""
    manager = ConfigManager(config_dir, schema=sample_schema)
    manager.add_config(
        "test",
        {
            "host": "localhost",
            "port": 8080,
            "username": "testuser",
            "password": "secret",
        },
    )

    result = cli_runner.invoke(main, ["show", str(config_dir), "test"])
    assert result.exit_code == 0
    # Should show a note about --reveal
    assert "--reveal" in result.output


def test_cli_delete_config(cli_runner, config_dir):
    """Test delete command."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["delete", str(config_dir), "test"], input="y\n")
    assert result.exit_code == 0
    assert "Deleted" in result.output

    # Verify it's gone
    manager2 = ConfigManager(config_dir)
    assert not manager2.has_config("test")


def test_cli_delete_config_not_found(cli_runner, config_dir):
    """Test delete command with non-existent config."""
    result = cli_runner.invoke(
        main, ["delete", str(config_dir), "nonexistent"], input="y\n"
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_delete_config_cancel(cli_runner, config_dir):
    """Test delete command cancellation."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["delete", str(config_dir), "test"], input="n\n")
    # Should abort
    assert result.exit_code == 1

    # Config should still exist
    manager2 = ConfigManager(config_dir)
    assert manager2.has_config("test")


def test_cli_encrypt_set(cli_runner, config_dir):
    """Test encrypt set command."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        ["encrypt", "set", str(config_dir)],
        input="newpassword\nnewpassword\n",
    )
    assert result.exit_code == 0
    assert "updated" in result.output.lower()

    # Verify configs are now encrypted
    config_file = config_dir / "test.toml"
    with open(config_file, "rb") as f:
        content = f.read()
    assert b"VAULTCONFIG_ENCRYPT_V1" in content


def test_cli_encrypt_set_password_mismatch(cli_runner, config_dir):
    """Test encrypt set with mismatched passwords."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        ["encrypt", "set", str(config_dir)],
        input="password1\npassword2\n",
    )
    assert result.exit_code == 1
    assert "do not match" in result.output


def test_cli_encrypt_remove(cli_runner, config_dir):
    """Test encrypt remove command."""
    manager = ConfigManager(config_dir, password="secret")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        ["encrypt", "remove", str(config_dir)],
        input="y\n",
        env={"VAULTCONFIG_PASSWORD": "secret"},
    )
    assert result.exit_code == 0
    assert "removed" in result.output.lower()

    # Verify configs are no longer encrypted
    config_file = config_dir / "test.toml"
    with open(config_file, "rb") as f:
        content = f.read()
    assert b"VAULTCONFIG_ENCRYPT_V1" not in content
    assert b"VAULTCONFIG_ENCRYPT_" not in content  # No encryption at all


def test_cli_encrypt_remove_cancel(cli_runner, config_dir):
    """Test encrypt remove cancellation."""
    manager = ConfigManager(config_dir, password="secret")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        ["encrypt", "remove", str(config_dir)],
        input="n\n",
        env={"VAULTCONFIG_PASSWORD": "secret"},
    )
    # Should abort
    assert result.exit_code == 1


def test_cli_encrypt_check_encrypted(cli_runner, config_dir):
    """Test encrypt check with encrypted configs."""
    manager = ConfigManager(config_dir, password="secret")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["encrypt", "check", str(config_dir)])
    assert result.exit_code == 0
    assert "NOT encrypted" in result.output  # Manager created without password


def test_cli_encrypt_check_not_encrypted(cli_runner, config_dir):
    """Test encrypt check with non-encrypted configs."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["encrypt", "check", str(config_dir)])
    assert result.exit_code == 0
    assert "NOT encrypted" in result.output


def test_cli_with_different_formats(cli_runner, temp_dir):
    """Test CLI with different config formats."""
    # Test with INI
    config_dir = temp_dir / "ini_config"
    config_dir.mkdir()
    manager = ConfigManager(config_dir, format="ini")
    manager.add_config("test", {"section": {"key": "value"}}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["list", str(config_dir), "-f", "ini"])
    assert result.exit_code == 0
    assert "test" in result.output


def test_cli_format_autodetect(cli_runner, temp_dir):
    """Test CLI format autodetection."""
    config_dir = temp_dir / "auto_config"
    config_dir.mkdir()
    manager = ConfigManager(config_dir, format="yaml")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    # Should autodetect yaml format
    result = cli_runner.invoke(main, ["list", str(config_dir)])
    assert result.exit_code == 0
    assert "test" in result.output


def test_cli_version(cli_runner):
    """Test --version flag."""
    result = cli_runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_cli_encrypt_help(cli_runner):
    """Test encrypt command help."""
    result = cli_runner.invoke(main, ["encrypt", "--help"])
    assert result.exit_code == 0
    assert "encryption" in result.output.lower()


def test_cli_nested_config_display(cli_runner, config_dir):
    """Test showing nested configuration."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {"database": {"host": "localhost", "port": 5432}},
        obscure_passwords=False,
    )

    result = cli_runner.invoke(main, ["show", str(config_dir), "test"])
    assert result.exit_code == 0
    assert "database" in result.output
    assert "localhost" in result.output
    assert "5432" in result.output

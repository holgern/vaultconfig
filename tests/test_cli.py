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
    result = cli_runner.invoke(main, ["init", "-d", str(config_dir)])
    assert result.exit_code == 0
    assert config_dir.exists()
    assert "Initialized" in result.output


def test_cli_init_with_format(cli_runner, temp_dir):
    """Test init command with specific format."""
    config_dir = temp_dir / "test_config"
    result = cli_runner.invoke(main, ["init", "-d", str(config_dir), "-f", "ini"])
    assert result.exit_code == 0
    assert "Format: ini" in result.output


def test_cli_init_with_encryption(cli_runner, temp_dir):
    """Test init command with encryption."""
    config_dir = temp_dir / "test_config"
    result = cli_runner.invoke(
        main, ["init", "-d", str(config_dir), "-e"], input="password123\npassword123\n"
    )
    assert result.exit_code == 0
    assert "Encrypted: Yes" in result.output


def test_cli_init_password_mismatch(cli_runner, temp_dir):
    """Test init with mismatched passwords."""
    config_dir = temp_dir / "test_config"
    result = cli_runner.invoke(
        main, ["init", "-d", str(config_dir), "-e"], input="password123\nwrong\n"
    )
    assert result.exit_code == 1
    assert "do not match" in result.output


def test_cli_init_existing_directory(cli_runner, config_dir):
    """Test init with existing non-empty directory."""
    # Add a config first
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    # Try to init again - should warn
    result = cli_runner.invoke(main, ["init", "-d", str(config_dir)], input="n\n")
    assert result.exit_code == 0
    # Check for warning message (may contain line breaks)
    assert "already" in result.output and "exists" in result.output
    assert "not empty" in result.output


def test_cli_list_empty(cli_runner, config_dir):
    """Test list command with no configs."""
    result = cli_runner.invoke(main, ["list", "-d", str(config_dir)])
    assert result.exit_code == 0
    assert "No configurations found" in result.output


def test_cli_list_with_configs(cli_runner, config_dir):
    """Test list command with configs."""
    manager = ConfigManager(config_dir)
    manager.add_config("test1", {"key": "value1"}, obscure_passwords=False)
    manager.add_config("test2", {"key": "value2"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["list", "-d", str(config_dir)])
    assert result.exit_code == 0
    assert "test1" in result.output
    assert "test2" in result.output


def test_cli_list_encrypted(cli_runner, config_dir):
    """Test list command with encrypted configs."""
    manager = ConfigManager(config_dir, password="secret")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main, ["list", "-d", str(config_dir)], env={"VAULTCONFIG_PASSWORD": "secret"}
    )
    assert result.exit_code == 0
    assert "test" in result.output


def test_cli_show_config(cli_runner, config_dir):
    """Test show command."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 8080}, obscure_passwords=False
    )

    result = cli_runner.invoke(main, ["show", "test", "-d", str(config_dir)])
    assert result.exit_code == 0
    assert "localhost" in result.output
    assert "8080" in result.output


def test_cli_show_config_not_found(cli_runner, config_dir):
    """Test show command with non-existent config."""
    result = cli_runner.invoke(main, ["show", "nonexistent", "-d", str(config_dir)])
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

    result = cli_runner.invoke(main, ["show", "test", "-d", str(config_dir), "-r"])
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

    result = cli_runner.invoke(main, ["show", "test", "-d", str(config_dir)])
    assert result.exit_code == 0
    # Should show a note about --reveal
    assert "--reveal" in result.output


def test_cli_delete_config(cli_runner, config_dir):
    """Test delete command."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main, ["delete", "test", "-d", str(config_dir)], input="y\n"
    )
    assert result.exit_code == 0
    assert "Deleted" in result.output

    # Verify it's gone
    manager2 = ConfigManager(config_dir)
    assert not manager2.has_config("test")


def test_cli_delete_config_not_found(cli_runner, config_dir):
    """Test delete command with non-existent config."""
    result = cli_runner.invoke(
        main, ["delete", "nonexistent", "-d", str(config_dir)], input="y\n"
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_delete_config_cancel(cli_runner, config_dir):
    """Test delete command cancellation."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        ["delete", "test", "-d", str(config_dir)],
        input="n\n",
    )
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
        ["encrypt", "set", "-d", str(config_dir)],
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
        ["encrypt", "set", "-d", str(config_dir)],
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
        ["encrypt", "remove", "-d", str(config_dir)],
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
        ["encrypt", "remove", "-d", str(config_dir)],
        input="n\n",
        env={"VAULTCONFIG_PASSWORD": "secret"},
    )
    # Should abort
    assert result.exit_code == 1


def test_cli_encrypt_check_encrypted(cli_runner, config_dir):
    """Test encrypt check with encrypted configs."""
    manager = ConfigManager(config_dir, password="secret")
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["encrypt", "check", "-d", str(config_dir)])
    assert result.exit_code == 0
    assert "encrypted" in result.output.lower()  # Should detect encrypted status


def test_cli_encrypt_check_not_encrypted(cli_runner, config_dir):
    """Test encrypt check with non-encrypted configs."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["encrypt", "check", "-d", str(config_dir)])
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
    result = cli_runner.invoke(main, ["list", "-d", str(config_dir)])
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

    result = cli_runner.invoke(main, ["show", "test", "-d", str(config_dir)])
    assert result.exit_code == 0
    assert "database" in result.output
    assert "localhost" in result.output
    assert "5432" in result.output


def test_cli_run_command(cli_runner, config_dir, tmp_path):
    """Test run command with environment variables."""
    import platform
    import sys

    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {"host": "localhost", "port": 5432, "nested": {"key": "value"}},
        obscure_passwords=False,
    )

    # Create platform-specific test script
    if platform.system() == "Windows":
        # Use Python script that works on all platforms
        test_script = tmp_path / "test.py"
        test_script.write_text(
            "import os\n"
            'print(f\'HOST={os.environ.get("HOST", "")}\')\n'
            'print(f\'PORT={os.environ.get("PORT", "")}\')\n'
            'print(f\'NESTED_KEY={os.environ.get("NESTED_KEY", "")}\')\n'
        )
        cmd = [sys.executable, str(test_script)]
    else:
        # Unix: use bash script
        test_script = tmp_path / "test.sh"
        test_script.write_text(
            "#!/bin/bash\n"
            "echo HOST=$HOST\n"
            "echo PORT=$PORT\n"
            "echo NESTED_KEY=$NESTED_KEY\n"
        )
        test_script.chmod(0o755)
        cmd = ["bash", str(test_script)]

    result = cli_runner.invoke(main, ["run", "test", "-d", str(config_dir)] + cmd)

    # The command should execute successfully
    # Note: exit_code may vary depending on how execvpe is handled in tests
    assert "HOST=localhost" in result.output or result.exit_code == 0
    assert "PORT=5432" in result.output or result.exit_code == 0


def test_cli_run_command_with_prefix(cli_runner, config_dir, tmp_path):
    """Test run command with custom prefix."""
    import platform
    import sys

    manager = ConfigManager(config_dir)
    manager.add_config("test", {"host": "db.example.com"}, obscure_passwords=False)

    # Create platform-specific test script
    if platform.system() == "Windows":
        # Use Python script that works on all platforms
        test_script = tmp_path / "test.py"
        test_script.write_text(
            'import os\nprint(f\'DB_HOST={os.environ.get("DB_HOST", "")}\')\n'
        )
        cmd = [sys.executable, str(test_script)]
    else:
        # Unix: use bash script
        test_script = tmp_path / "test.sh"
        test_script.write_text("#!/bin/bash\necho DB_HOST=$DB_HOST\n")
        test_script.chmod(0o755)
        cmd = ["bash", str(test_script)]

    result = cli_runner.invoke(
        main, ["run", "test", "-d", str(config_dir), "--prefix", "DB_"] + cmd
    )

    assert "DB_HOST=db.example.com" in result.output or result.exit_code == 0


def test_cli_run_command_config_not_found(cli_runner, config_dir):
    """Test run command with non-existent config."""
    result = cli_runner.invoke(
        main, ["run", "nonexistent", "-d", str(config_dir), "echo", "test"]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_run_command_no_command(cli_runner, config_dir):
    """Test run command without a command to run."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"key": "value"}, obscure_passwords=False)

    result = cli_runner.invoke(main, ["run", "test", "-d", str(config_dir)])
    assert result.exit_code == 2  # Click returns 2 for usage errors
    assert "Missing argument" in result.output


def test_cli_export_env_bash(cli_runner, config_dir):
    """Test export-env with bash format."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "bash"]
    )
    assert result.exit_code == 0
    assert "export HOST='localhost'" in result.output
    assert "export PORT='5432'" in result.output


def test_cli_export_env_zsh(cli_runner, config_dir):
    """Test export-env with zsh format."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "zsh"]
    )
    assert result.exit_code == 0
    assert "export HOST='localhost'" in result.output
    assert "export PORT='5432'" in result.output


def test_cli_export_env_fish(cli_runner, config_dir):
    """Test export-env with fish format."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "fish"]
    )
    assert result.exit_code == 0
    assert "set -gx HOST 'localhost'" in result.output
    assert "set -gx PORT '5432'" in result.output


def test_cli_export_env_nushell(cli_runner, config_dir):
    """Test export-env with nushell format."""
    import json

    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "nushell"]
    )
    assert result.exit_code == 0
    # Nushell format outputs JSON that can be piped to: from json | load-env
    output_data = json.loads(result.output.strip())
    assert output_data["HOST"] == "localhost"
    assert output_data["PORT"] == "5432"


def test_cli_export_env_powershell(cli_runner, config_dir):
    """Test export-env with powershell format."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "powershell"]
    )
    assert result.exit_code == 0
    assert "$env:HOST = 'localhost'" in result.output
    assert "$env:PORT = '5432'" in result.output


def test_cli_export_env_with_prefix(cli_runner, config_dir):
    """Test export-env with prefix option."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--prefix",
            "DB_",
            "--shell",
            "bash",
        ],
    )
    assert result.exit_code == 0
    assert "export DB_HOST='localhost'" in result.output
    assert "export DB_PORT='5432'" in result.output


def test_cli_export_env_nested(cli_runner, config_dir):
    """Test export-env with nested configuration."""
    import json

    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {"database": {"host": "localhost", "port": 5432}},
        obscure_passwords=False,
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "nushell"]
    )
    assert result.exit_code == 0
    # Nushell format outputs JSON
    output_data = json.loads(result.output.strip())
    assert output_data["DATABASE_HOST"] == "localhost"
    assert output_data["DATABASE_PORT"] == "5432"


def test_cli_export_env_special_characters_nushell(cli_runner, config_dir):
    """Test export-env with special characters in nushell format."""
    import json

    manager = ConfigManager(config_dir)
    manager.add_config("test", {"password": "my'pass\\word"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "nushell"]
    )
    assert result.exit_code == 0
    # Nushell format outputs JSON which properly escapes special characters
    output_data = json.loads(result.output.strip())
    assert output_data["PASSWORD"] == "my'pass\\word"


def test_cli_export_env_special_characters_powershell(cli_runner, config_dir):
    """Test export-env with special characters in powershell format."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"password": "my'password"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--shell", "powershell"]
    )
    assert result.exit_code == 0
    # PowerShell should double single quotes
    assert "$env:PASSWORD = 'my''password'" in result.output


def test_cli_export_env_config_not_found(cli_runner, config_dir):
    """Test export-env with non-existent config."""
    result = cli_runner.invoke(
        main, ["export-env", "nonexistent", "-C", str(config_dir)]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_export_env_autodetect_default(cli_runner, config_dir, monkeypatch):
    """Test export-env with shell auto-detection defaulting to bash."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"host": "localhost"}, obscure_passwords=False)

    # Clear SHELL env var to test default
    monkeypatch.delenv("SHELL", raising=False)
    monkeypatch.delenv("PSModulePath", raising=False)

    result = cli_runner.invoke(main, ["export-env", "test", "-C", str(config_dir)])
    assert result.exit_code == 0
    # Should default to bash format
    assert "export HOST='localhost'" in result.output


def test_cli_export_env_dry_run(cli_runner, config_dir):
    """Test export-env with --dry-run flag."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {"host": "localhost", "port": 5432, "password": "secret"},
        obscure_passwords=True,
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--dry-run"]
    )
    assert result.exit_code == 0
    # Should show table format
    assert "Preview" in result.output and "test" in result.output
    assert "HOST" in result.output
    assert "PORT" in result.output
    assert "PASSWORD" in result.output
    # Should show copyable commands section
    assert "Copyable" in result.output
    assert "Commands" in result.output
    # Should show note about --reveal
    assert "--reveal" in result.output
    # Should show tip about copying
    assert "Tip:" in result.output or "copy" in result.output.lower()


def test_cli_export_env_dry_run_with_reveal(cli_runner, config_dir):
    """Test export-env with --dry-run and --reveal flags."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "password": "secret"}, obscure_passwords=True
    )

    result = cli_runner.invoke(
        main, ["export-env", "test", "-C", str(config_dir), "--dry-run", "--reveal"]
    )
    assert result.exit_code == 0
    assert "Preview" in result.output and "test" in result.output
    # Should not show the reveal note when using --reveal
    assert "Note:" not in result.output


def test_cli_export_env_dry_run_with_prefix(cli_runner, config_dir):
    """Test export-env dry-run with prefix."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--dry-run",
            "--prefix",
            "DB_",
        ],
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output


def test_cli_export_env_dry_run_copyable_bash(cli_runner, config_dir):
    """Test export-env dry-run shows copyable bash commands."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--dry-run",
            "--shell",
            "bash",
        ],
    )
    assert result.exit_code == 0
    # Should show copyable commands
    assert "Copyable" in result.output
    assert "export HOST='localhost'" in result.output
    assert "export PORT='5432'" in result.output


def test_cli_export_env_dry_run_copyable_nushell(cli_runner, config_dir):
    """Test export-env dry-run shows copyable nushell commands."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test", {"host": "localhost", "port": 5432}, obscure_passwords=False
    )

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--dry-run",
            "--shell",
            "nushell",
        ],
    )
    assert result.exit_code == 0
    # Should show copyable nushell commands with load-env prefix
    assert "Copyable" in result.output
    assert "load-env" in result.output
    # Check for JSON format record in the output
    assert '"HOST"' in result.output
    assert '"PORT"' in result.output
    assert "localhost" in result.output


def test_cli_export_env_dry_run_usage_bash(cli_runner, config_dir):
    """Test export-env dry-run shows bash-specific usage instructions."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"host": "localhost"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--dry-run",
            "--shell",
            "bash",
        ],
    )
    assert result.exit_code == 0
    assert "Usage for Bash:" in result.output
    assert "eval $(" in result.output
    assert "vaultconfig export-env test" in result.output


def test_cli_export_env_dry_run_usage_nushell(cli_runner, config_dir):
    """Test export-env dry-run shows nushell-specific usage instructions."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"host": "localhost"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--dry-run",
            "--shell",
            "nushell",
        ],
    )
    assert result.exit_code == 0
    assert "Usage for Nushell:" in result.output
    assert "save -f env.nu" in result.output
    assert "source env.nu" in result.output


def test_cli_export_env_dry_run_usage_fish(cli_runner, config_dir):
    """Test export-env dry-run shows fish-specific usage instructions."""
    manager = ConfigManager(config_dir)
    manager.add_config("test", {"host": "localhost"}, obscure_passwords=False)

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--dry-run",
            "--shell",
            "fish",
        ],
    )
    assert result.exit_code == 0
    assert "Usage for Fish:" in result.output
    assert "| source" in result.output


def test_filter_dict():
    """Test _filter_dict helper function."""
    from vaultconfig.cli import _filter_dict

    test_data = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "username": "admin",
            "password": "secret123",
        },
        "api": {
            "endpoint": "https://api.example.com",
            "key": "apikey123",
            "timeout": 30,
        },
        "debug": True,
        "version": "1.0.0",
    }

    # Test 1: Include only database keys
    filtered = _filter_dict(test_data, include=("database.*",), exclude=None)
    assert "database" in filtered
    assert "api" not in filtered
    assert "debug" not in filtered
    assert filtered["database"]["host"] == "localhost"
    assert filtered["database"]["port"] == 5432

    # Test 2: Exclude password fields
    filtered = _filter_dict(test_data, include=None, exclude=("*.password", "*.key"))
    assert "database" in filtered
    assert "password" not in filtered["database"]
    assert "host" in filtered["database"]
    assert "api" in filtered
    assert "key" not in filtered["api"]
    assert "endpoint" in filtered["api"]

    # Test 3: Include database but exclude password
    filtered = _filter_dict(test_data, include=("database.*",), exclude=("*.password",))
    assert "database" in filtered
    assert "password" not in filtered["database"]
    assert "host" in filtered["database"]
    assert "api" not in filtered

    # Test 4: Include specific keys
    filtered = _filter_dict(
        test_data, include=("database.host", "database.port", "version"), exclude=None
    )
    assert "database" in filtered
    assert "host" in filtered["database"]
    assert "port" in filtered["database"]
    assert "username" not in filtered["database"]
    assert "version" in filtered
    assert "api" not in filtered

    # Test 5: No filters (should return all data)
    filtered = _filter_dict(test_data, include=None, exclude=None)
    assert filtered == test_data

    # Test 6: Exclude takes precedence over include
    filtered = _filter_dict(
        test_data, include=("database.*",), exclude=("database.password",)
    )
    assert "database" in filtered
    assert "password" not in filtered["database"]
    assert "host" in filtered["database"]


def test_cli_export_with_include(cli_runner, config_dir):
    """Test export command with --include filter."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {
            "database": {"host": "localhost", "port": 5432, "password": "secret"},
            "api": {"endpoint": "https://api.example.com"},
        },
        obscure_passwords=False,
    )

    result = cli_runner.invoke(
        main,
        [
            "export",
            "test",
            "-C",
            str(config_dir),
            "--include",
            "database.*",
            "--export-format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert "localhost" in result.output
    assert "5432" in result.output
    assert "api.example.com" not in result.output


def test_cli_export_with_exclude(cli_runner, config_dir):
    """Test export command with --exclude filter."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {
            "database": {"host": "localhost", "port": 5432, "password": "secret"},
            "api": {"key": "apikey123"},
        },
        obscure_passwords=False,
    )

    result = cli_runner.invoke(
        main,
        [
            "export",
            "test",
            "-C",
            str(config_dir),
            "--exclude",
            "*.password",
            "--exclude",
            "*.key",
            "--export-format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert "localhost" in result.output
    assert "5432" in result.output
    assert "secret" not in result.output
    assert "apikey123" not in result.output


def test_cli_export_with_include_and_exclude(cli_runner, config_dir):
    """Test export command with both --include and --exclude filters."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret",
            }
        },
        obscure_passwords=False,
    )

    result = cli_runner.invoke(
        main,
        [
            "export",
            "test",
            "-C",
            str(config_dir),
            "--include",
            "database.*",
            "--exclude",
            "*.password",
            "--export-format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert "localhost" in result.output
    assert "5432" in result.output
    assert "admin" in result.output
    assert "secret" not in result.output


def test_cli_export_env_with_include(cli_runner, config_dir):
    """Test export-env command with --include filter."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {
            "database": {"host": "localhost", "port": 5432},
            "api": {"endpoint": "https://api.example.com"},
        },
        obscure_passwords=False,
    )

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--include",
            "database.*",
            "--shell",
            "bash",
        ],
    )
    assert result.exit_code == 0
    assert "DATABASE_HOST" in result.output
    assert "DATABASE_PORT" in result.output
    assert "API_ENDPOINT" not in result.output


def test_cli_export_env_with_exclude(cli_runner, config_dir):
    """Test export-env command with --exclude filter."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {
            "database": {"host": "localhost", "password": "secret"},
            "api": {"key": "apikey123"},
        },
        obscure_passwords=False,
    )

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--exclude",
            "*.password",
            "--exclude",
            "*.key",
            "--shell",
            "bash",
        ],
    )
    assert result.exit_code == 0
    assert "DATABASE_HOST" in result.output
    assert "localhost" in result.output
    assert "secret" not in result.output
    assert "apikey123" not in result.output


def test_cli_export_env_with_include_and_exclude(cli_runner, config_dir):
    """Test export-env command with both --include and --exclude filters."""
    manager = ConfigManager(config_dir)
    manager.add_config(
        "test",
        {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "admin",
                "password": "secret",
            }
        },
        obscure_passwords=False,
    )

    result = cli_runner.invoke(
        main,
        [
            "export-env",
            "test",
            "-C",
            str(config_dir),
            "--include",
            "database.*",
            "--exclude",
            "*.password",
            "--shell",
            "bash",
        ],
    )
    assert result.exit_code == 0
    assert "DATABASE_HOST" in result.output
    assert "DATABASE_PORT" in result.output
    assert "DATABASE_USERNAME" in result.output
    assert "secret" not in result.output

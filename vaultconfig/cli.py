"""Command-line interface for vaultconfig."""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from vaultconfig.config import ConfigManager
from vaultconfig.exceptions import VaultConfigError

console = Console()


def _get_default_config_dir() -> Path:
    """Get the default config directory for the current platform.

    Returns:
        Path to default config directory
    """
    import platform

    system = platform.system()

    if system == "Windows":
        # Use %APPDATA%\vaultconfig on Windows
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "vaultconfig"
        # Fallback to user home
        return Path.home() / "vaultconfig"
    else:
        # Use XDG standard on Unix/Linux/macOS
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "vaultconfig"
        return Path.home() / ".config" / "vaultconfig"


def _get_config_dir(config_dir: str | None) -> Path:
    """Get config directory, using default if not specified.

    Args:
        config_dir: User-specified config dir, or None for default

    Returns:
        Path to config directory
    """
    if config_dir:
        return Path(config_dir)

    # Check environment variable first
    env_dir = os.environ.get("VAULTCONFIG_DIR")
    if env_dir:
        return Path(env_dir)

    # Use platform-specific default
    return _get_default_config_dir()


@click.group()
@click.version_option()
def main() -> None:
    """VaultConfig - Secure configuration management with encryption support."""
    pass


@main.command()
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", default="toml", help="Config format (toml/ini/yaml)")
@click.option("--encrypt", "-e", is_flag=True, help="Enable encryption")
def init(config_dir: str | None, format: str, encrypt: bool) -> None:
    """Initialize a new config directory.

    If no directory is specified, uses the default config directory:
    - Linux/macOS: ~/.config/vaultconfig
    - Windows: %APPDATA%\\vaultconfig

    Set VAULTCONFIG_DIR environment variable to override the default.
    """
    config_path = _get_config_dir(config_dir)

    if config_path.exists() and any(config_path.iterdir()):
        console.print(
            f"[yellow]Warning:[/yellow] Directory {config_dir} already exists "
            "and is not empty"
        )
        if not click.confirm("Continue?"):
            return

    config_path.mkdir(parents=True, exist_ok=True)

    password = None
    if encrypt:
        password = click.prompt("Enter encryption password", hide_input=True)
        confirm = click.prompt("Confirm password", hide_input=True)
        if password != confirm:
            console.print("[red]Error:[/red] Passwords do not match")
            sys.exit(1)

    # Initialize the ConfigManager to create the directory structure
    ConfigManager(config_path, format=format, password=password)

    console.print(f"[green]✓[/green] Initialized config directory: {config_path}")
    console.print(f"  Format: {format}")
    console.print(f"  Encrypted: {'Yes' if encrypt else 'No'}")


@main.command(name="list")
@click.argument("config_dir", required=False, type=click.Path())
@click.option(
    "-d",
    "--dir",
    "config_dir_option",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format (autodetect if not specified)")
@click.option(
    "--output", "-o", default="table", help="Output format (table/json/plain)"
)
def list_command(
    config_dir: str | None,
    config_dir_option: str | None,
    format: str | None,
    output: str,
) -> None:
    """List all configurations.

    Uses default config directory if not specified.

    Examples:
        vaultconfig list
        vaultconfig list /path/to/config
        vaultconfig list -d /path/to/config
    """
    # Use positional argument if provided, otherwise use option
    if config_dir is None:
        config_dir = config_dir_option
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            if output == "json":
                click.echo("[]")
            else:
                console.print("[yellow]No config directory found.[/yellow]")
                console.print(f"Run 'vaultconfig init' to create one at: {config_path}")
            return

        manager = _get_manager(
            str(config_path), format, ask_password=False, auto_load=False
        )
        # List config files without loading them (don't prompt for passwords)
        configs = manager.list_config_files()

        if not configs:
            if output == "json":
                click.echo("[]")
            else:
                console.print("No configurations found")
            return

        # Get encryption status without prompting for passwords
        encryption_status = manager.get_encryption_status()

        # Output based on format
        if output == "json":
            import json

            result = [
                {"name": name, "encrypted": encryption_status.get(name, False)}
                for name in sorted(configs)
            ]
            click.echo(json.dumps(result, indent=2))
        elif output == "plain":
            for name in sorted(configs):
                prefix = "[E] " if encryption_status.get(name, False) else ""
                click.echo(f"{prefix}{name}")
        else:  # table (default)
            table = Table(title="Configurations")
            table.add_column("Name", style="cyan")
            table.add_column("Encrypted", style="yellow")

            for name in sorted(configs):
                is_encrypted = encryption_status.get(name, False)
                encrypted = "Yes" if is_encrypted else "No"
                table.add_row(name, encrypted)

            console.print(table)

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="show")
@click.argument("name", required=True)
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--reveal", "-r", is_flag=True, help="Reveal obscured passwords")
@click.option(
    "--output", "-o", default="pretty", help="Output format (pretty/json/yaml/toml)"
)
def show_command(
    name: str, config_dir: str | None, format: str | None, reveal: bool, output: str
) -> None:
    """Show configuration.

    Uses default config directory if not specified.
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format)
        config = manager.get_config(name)

        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        data = config.get_all(reveal_secrets=reveal)

        # Output based on format
        if output == "json":
            import json

            click.echo(json.dumps(data, indent=2))
        elif output == "yaml":
            handler = _get_format_handler("yaml")
            click.echo(handler.dump(data))
        elif output == "toml":
            handler = _get_format_handler("toml")
            click.echo(handler.dump(data))
        else:  # pretty (default)
            console.print(f"[bold]Configuration:[/bold] {name}")
            console.print()
            _print_dict(data)

            if not reveal:
                console.print()
                console.print(
                    "[yellow]Note:[/yellow] Use --reveal to show obscured passwords"
                )

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="create")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("name", required=True)
@click.option("--format", "-f", help="Config format")
@click.option("--from-file", type=click.Path(exists=True), help="Import from file")
@click.option("--interactive/--no-interactive", default=True, help="Interactive mode")
@click.option("--encrypted", "-e", is_flag=True, help="Encrypt this config")
@click.option("--password", "-p", help="Encryption password")
def create_command(
    name: str,
    config_dir: str | None,
    format: str | None,
    from_file: str | None,
    interactive: bool,
    encrypted: bool,
    password: str | None,
) -> None:
    """Create a new configuration.

    Uses default config directory if not specified.

    Examples:
        vaultconfig create database --interactive
        vaultconfig create api --encrypted
        vaultconfig create secrets --encrypted --password "mypass"
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            console.print("Run 'vaultconfig init' first")
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)

        # Check if config already exists
        if manager.has_config(name):
            console.print(f"[red]Error:[/red] Config '{name}' already exists")
            console.print(
                "Use 'vaultconfig set' to modify it or "
                "'vaultconfig delete' to remove it first"
            )
            sys.exit(1)

        config_data = {}

        if from_file:
            # Import from file
            import json
            from pathlib import Path

            file_path = Path(from_file)
            content = file_path.read_text()

            # Detect format from extension or content
            if file_path.suffix == ".json":
                config_data = json.loads(content)
            elif file_path.suffix in [".yaml", ".yml"]:
                manager._format_handler = (
                    manager._format_handler or _get_format_handler("yaml")
                )
                config_data = manager._format_handler.load(content)
            elif file_path.suffix == ".toml":
                manager._format_handler = (
                    manager._format_handler or _get_format_handler("toml")
                )
                config_data = manager._format_handler.load(content)
            elif file_path.suffix == ".ini":
                manager._format_handler = (
                    manager._format_handler or _get_format_handler("ini")
                )
                config_data = manager._format_handler.load(content)
            else:
                # Try to parse as JSON by default
                try:
                    config_data = json.loads(content)
                except json.JSONDecodeError:
                    console.print(
                        "[red]Error:[/red] Could not detect file format. "
                        "Use .json, .yaml, .toml, or .ini extension"
                    )
                    sys.exit(1)

        elif interactive:
            # Interactive mode
            console.print(f"[bold]Creating configuration:[/bold] {name}")
            console.print(
                "Enter configuration values (press Ctrl+C or leave key empty to finish)"
            )
            console.print()

            while True:
                key = click.prompt("Key", default="", show_default=False)
                if not key:
                    break

                # Check if this should be obscured
                is_sensitive = click.confirm(
                    f"Is '{key}' a sensitive value (password)?", default=False
                )

                if is_sensitive:
                    value = click.prompt(f"Value for '{key}'", hide_input=True)
                else:
                    value = click.prompt(f"Value for '{key}'")

                # Try to parse as appropriate type
                parsed_value = _parse_value(value)
                config_data[key] = parsed_value

        else:
            console.print(
                "[yellow]Warning:[/yellow] Non-interactive mode with no "
                "--from-file specified"
            )
            console.print(
                "Creating empty configuration. Use 'vaultconfig set' to add values."
            )

        # Add configuration
        manager.add_config(name, config_data)

        # Encrypt if requested
        if encrypted:
            if password is None:
                password = click.prompt("Enter encryption password", hide_input=True)
                confirm = click.prompt("Confirm password", hide_input=True)
                if password != confirm:
                    console.print("[red]Error:[/red] Passwords do not match")
                    # Remove the config we just created
                    manager.remove_config(name)
                    sys.exit(1)

            assert password is not None
            manager.encrypt_config(name, password)
            console.print(f"[green]✓[/green] Created encrypted config: {name}")
        else:
            console.print(f"[green]✓[/green] Created config: {name}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        sys.exit(0)
    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="set")
@click.argument("name", required=True)
@click.argument("assignments", nargs=-1, required=True)
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--obscure", is_flag=True, help="Obscure the value (for passwords)")
@click.option("--create", "-c", is_flag=True, help="Create config if it doesn't exist")
def set_command(
    name: str,
    assignments: tuple,
    config_dir: str | None,
    format: str | None,
    obscure: bool,
    create: bool,
) -> None:
    """Set configuration values.

    Uses default config directory if not specified.

    Examples:
        vaultconfig set database host=localhost port=5432
        vaultconfig set database password=secret --obscure
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            console.print("Run 'vaultconfig init' first")
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)

        # Get or create config
        config = manager.get_config(name)
        if config is None:
            if create:
                config_data = {}
            else:
                console.print(f"[red]Error:[/red] Config '{name}' not found")
                console.print(
                    "Use --create to create it, or 'vaultconfig create' for "
                    "interactive creation"
                )
                sys.exit(1)
        else:
            config_data = config._data.copy()

        # Parse assignments (key=value format)
        for assignment in assignments:
            if "=" not in assignment:
                console.print(
                    f"[red]Error:[/red] Invalid assignment '{assignment}'. "
                    "Use key=value format"
                )
                sys.exit(1)

            key, value = assignment.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Parse value to appropriate type
            parsed_value = _parse_value(value)

            # Obscure if requested
            if obscure and isinstance(parsed_value, str):
                parsed_value = manager._obscurer.obscure(parsed_value)

            # Support nested keys with dot notation
            _set_nested_value(config_data, key, parsed_value)

        # Save configuration
        manager.add_config(
            name, config_data, obscure_passwords=False
        )  # Don't auto-obscure since we handle it
        console.print(f"[green]✓[/green] Updated config: {name}")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="get")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("name", required=True)
@click.argument("key", required=True)
@click.option("--format", "-f", help="Config format")
@click.option("--reveal", "-r", is_flag=True, help="Reveal obscured passwords")
@click.option("--default", "-D", help="Default value if key not found")
def get_command(
    name: str,
    key: str,
    config_dir: str | None,
    format: str | None,
    reveal: bool,
    default: str | None,
) -> None:
    """Get a configuration value.

    Uses default config directory if not specified.

    Examples:
        vaultconfig get database host
        vaultconfig get database password --reveal
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format)
        config = manager.get_config(name)

        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Get value (supports dot notation)
        if reveal:
            value = config.get(key)
        else:
            # Get without revealing
            data: Any = config._data
            keys = key.split(".")
            for k in keys:
                if isinstance(data, dict):
                    data = data.get(k)
                    if data is None:
                        break
                else:
                    data = None
                    break
            value = data

        if value is None:
            if default is not None:
                console.print(default)
            else:
                console.print(f"[red]Error:[/red] Key '{key}' not found")
                sys.exit(1)
        else:
            # Print value without formatting
            console.print(str(value))

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="unset")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("name", required=True)
@click.argument("keys", nargs=-1, required=True)
@click.option("--format", "-f", help="Config format")
def unset_command(
    config_dir: str | None, name: str, keys: tuple, format: str | None
) -> None:
    """Remove configuration keys.

    Uses default config directory if not specified.

    Examples:
        vaultconfig unset database old_key
        vaultconfig unset database key1 key2 key3
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)
        config = manager.get_config(name)

        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        config_data = config._data.copy()
        removed = []
        not_found = []

        for key in keys:
            if _unset_nested_value(config_data, key):
                removed.append(key)
            else:
                not_found.append(key)

        # Save configuration
        if removed:
            manager.add_config(name, config_data, obscure_passwords=False)
            console.print(
                f"[green]✓[/green] Removed keys from config '{name}': "
                f"{', '.join(removed)}"
            )

        if not_found:
            console.print(
                f"[yellow]Warning:[/yellow] Keys not found: {', '.join(not_found)}"
            )

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="delete")
@click.argument("name", required=True)
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def delete_command(
    config_dir: str | None, name: str, format: str | None, yes: bool
) -> None:
    """Delete a configuration.

    Uses default config directory if not specified.
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format)

        # Check if config exists
        if not manager.has_config(name):
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Confirm deletion
        if not yes:
            if not click.confirm(f"Are you sure you want to delete config '{name}'?"):
                console.print("[yellow]Cancelled[/yellow]")
                sys.exit(1)

        if manager.remove_config(name):
            console.print(f"[green]✓[/green] Deleted config: {name}")
        else:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="copy")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("source", required=True)
@click.argument("dest", required=True)
@click.option("--format", "-f", help="Config format")
def copy_command(
    config_dir: str | None, source: str, dest: str, format: str | None
) -> None:
    """Copy a configuration.

    Uses default config directory if not specified.

    Examples:
        vaultconfig copy database database-backup
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)

        # Check if source exists
        source_config = manager.get_config(source)
        if not source_config:
            console.print(f"[red]Error:[/red] Source config '{source}' not found")
            sys.exit(1)

        # Check if destination already exists
        if manager.has_config(dest):
            console.print(
                f"[red]Error:[/red] Destination config '{dest}' already exists"
            )
            sys.exit(1)

        # Copy the configuration
        config_data = source_config._data.copy()
        manager.add_config(dest, config_data, obscure_passwords=False)
        console.print(f"[green]✓[/green] Copied '{source}' to '{dest}'")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="rename")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("old_name", required=True)
@click.argument("new_name", required=True)
@click.option("--format", "-f", help="Config format")
def rename_command(
    config_dir: str | None, old_name: str, new_name: str, format: str | None
) -> None:
    """Rename a configuration.

    Uses default config directory if not specified.

    Examples:
        vaultconfig rename database database-prod
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)

        # Check if source exists
        source_config = manager.get_config(old_name)
        if not source_config:
            console.print(f"[red]Error:[/red] Config '{old_name}' not found")
            sys.exit(1)

        # Check if destination already exists
        if manager.has_config(new_name):
            console.print(f"[red]Error:[/red] Config '{new_name}' already exists")
            sys.exit(1)

        # Copy to new name and delete old
        config_data = source_config._data.copy()
        manager.add_config(new_name, config_data, obscure_passwords=False)
        manager.remove_config(old_name)
        console.print(f"[green]✓[/green] Renamed '{old_name}' to '{new_name}'")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="export")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("name", required=True)
@click.option("--format", "-f", help="Config format (toml/ini/yaml)")
@click.option(
    "--output", "-o", type=click.Path(), help="Output file (stdout if not specified)"
)
@click.option(
    "--export-format", "-e", default="json", help="Export format (json/yaml/toml)"
)
@click.option("--reveal", "-r", is_flag=True, help="Reveal obscured passwords")
@click.option(
    "--include",
    "-i",
    multiple=True,
    help=(
        "Include only keys matching pattern "
        "(supports wildcards, can be used multiple times)"
    ),
)
@click.option(
    "--exclude",
    "-x",
    multiple=True,
    help=(
        "Exclude keys matching pattern (supports wildcards, can be used multiple times)"
    ),
)
def export_command(
    name: str,
    config_dir: str | None,
    format: str | None,
    output: str | None,
    export_format: str,
    reveal: bool,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> None:
    """Export a configuration to a file or stdout.

    Uses default config directory if not specified.

    Examples:
        vaultconfig export database --export-format json
        vaultconfig export database -o database.json --reveal
        vaultconfig export database -e yaml -o database.yaml
        vaultconfig export database --include "database.*" --exclude "*.password"
        vaultconfig export database -i "host" -i "port" -o connection.json
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format)
        config = manager.get_config(name)

        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Get configuration data
        data = config.get_all(reveal_secrets=reveal)

        # Filter data based on include/exclude patterns
        data = _filter_dict(
            data, include if include else None, exclude if exclude else None
        )

        # Export in requested format
        if export_format == "json":
            import json

            output_str = json.dumps(data, indent=2)
        elif export_format == "yaml":
            handler = _get_format_handler("yaml")
            output_str = handler.dump(data)
        elif export_format == "toml":
            handler = _get_format_handler("toml")
            output_str = handler.dump(data)
        elif export_format == "ini":
            handler = _get_format_handler("ini")
            output_str = handler.dump(data)
        else:
            console.print(
                f"[red]Error:[/red] Unsupported export format: {export_format}"
            )
            sys.exit(1)

        # Output to file or stdout
        if output:
            output_path = Path(output)
            output_path.write_text(output_str)
            console.print(f"[green]✓[/green] Exported to: {output}")
        else:
            # Print to stdout (use click.echo to avoid rich formatting)
            click.echo(output_str)

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="import")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("name", required=True)
@click.option("--format", "-f", help="Config format")
@click.option(
    "--from-file",
    required=True,
    type=click.Path(exists=True),
    help="File to import from",
)
@click.option(
    "--import-format",
    "-i",
    help="Import format (json/yaml/toml/ini, autodetect if not specified)",
)
@click.option("--overwrite", is_flag=True, help="Overwrite if config already exists")
def import_command(
    name: str,
    config_dir: str | None,
    format: str | None,
    from_file: str,
    import_format: str | None,
    overwrite: bool,
) -> None:
    """Import a configuration from a file.

    Uses default config directory if not specified.

    Examples:
        vaultconfig import database --from-file database.json
        vaultconfig import database --from-file config.yaml -i yaml
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            console.print("Run 'vaultconfig init' first")
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)

        # Check if config already exists
        if manager.has_config(name) and not overwrite:
            console.print(f"[red]Error:[/red] Config '{name}' already exists")
            console.print("Use --overwrite to replace it")
            sys.exit(1)

        # Read file
        file_path = Path(from_file)
        content = file_path.read_text()

        # Detect format if not specified
        if import_format is None:
            ext = file_path.suffix.lower()
            if ext == ".json":
                import_format = "json"
            elif ext in [".yaml", ".yml"]:
                import_format = "yaml"
            elif ext == ".toml":
                import_format = "toml"
            elif ext == ".ini":
                import_format = "ini"
            else:
                # Try JSON by default
                import_format = "json"

        # Parse content
        if import_format == "json":
            import json

            config_data = json.loads(content)
        elif import_format == "yaml":
            handler = _get_format_handler("yaml")
            config_data = handler.load(content)
        elif import_format == "toml":
            handler = _get_format_handler("toml")
            config_data = handler.load(content)
        elif import_format == "ini":
            handler = _get_format_handler("ini")
            config_data = handler.load(content)
        else:
            console.print(
                f"[red]Error:[/red] Unsupported import format: {import_format}"
            )
            sys.exit(1)

        # Add configuration
        manager.add_config(name, config_data)
        console.print(f"[green]✓[/green] Imported config: {name}")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to import: {e}")
        sys.exit(1)


@main.command(name="export-env")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("name", required=True)
@click.option("--format", "-f", help="Config format")
@click.option("--prefix", "-p", default="", help="Environment variable prefix")
@click.option("--reveal", "-r", is_flag=True, help="Reveal obscured passwords")
@click.option(
    "--uppercase", "-u", is_flag=True, default=True, help="Convert keys to uppercase"
)
@click.option(
    "--shell",
    "-s",
    type=click.Choice(
        ["bash", "zsh", "fish", "nushell", "powershell"], case_sensitive=False
    ),
    help="Shell type (auto-detected if not specified)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show preview of variables without shell-specific formatting",
)
@click.option(
    "--include",
    "-i",
    multiple=True,
    help=(
        "Include only keys matching pattern "
        "(supports wildcards, can be used multiple times)"
    ),
)
@click.option(
    "--exclude",
    "-x",
    multiple=True,
    help=(
        "Exclude keys matching pattern (supports wildcards, can be used multiple times)"
    ),
)
def export_env_command(
    name: str,
    config_dir: str | None,
    format: str | None,
    prefix: str,
    reveal: bool,
    uppercase: bool,
    shell: str | None,
    dry_run: bool,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> None:
    """Export configuration as environment variables.

    Uses default config directory if not specified.
    Supports bash, zsh, fish, nushell, and powershell.

    Examples:
        vaultconfig export-env database --prefix DB_
        eval $(vaultconfig export-env database --prefix DB_ --reveal)
        vaultconfig export-env database --shell nushell | from json | load-env
        vaultconfig export-env database --shell fish | source
        vaultconfig export-env database --dry-run  # Preview only
        vaultconfig export-env database --include "host" --include "port"
        vaultconfig export-env database --exclude "*.password" --exclude "*.secret"
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format)
        config = manager.get_config(name)

        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Get configuration data
        data = config.get_all(reveal_secrets=reveal)

        # Filter data based on include/exclude patterns
        data = _filter_dict(
            data, include if include else None, exclude if exclude else None
        )

        # Flatten nested dictionaries
        flat_data = _flatten_dict(data)

        # Detect shell if not specified (only needed if not dry-run)
        if shell is None and not dry_run:
            shell = _detect_shell()

        # Show preview or export as environment variables
        if dry_run:
            # Dry-run: Show readable preview with Rich table
            from rich.panel import Panel
            from rich.syntax import Syntax
            from rich.table import Table

            table = Table(title=f"Environment Variables Preview: {name}")
            table.add_column("Variable", style="cyan")
            table.add_column("Value", style="green")

            # Detect shell for copyable format
            shell_type = shell if shell is not None else _detect_shell()

            # Build list of export commands for copyable format
            export_commands = []
            env_vars_dict = {}

            for key, value in flat_data.items():
                # Convert key to env var format
                env_key = key.replace(".", "_").replace("-", "_")
                if uppercase:
                    env_key = env_key.upper()
                env_key = prefix + env_key

                # Truncate long values for display in table
                value_str = str(value)
                display_value = value_str
                if len(value_str) > 50:
                    display_value = value_str[:47] + "..."

                table.add_row(env_key, display_value)

                # Store for nushell format
                env_vars_dict[env_key] = value_str

                # Add to export commands (for non-nushell shells)
                if shell_type != "nushell":
                    export_commands.append(
                        _format_env_export(env_key, value_str, shell_type)
                    )

            console.print(table)

            # Show copyable shell commands
            console.print(
                f"\n[bold]Copyable {shell_type.capitalize()} Commands:[/bold]"
            )

            # Create a syntax-highlighted code block
            if shell_type == "nushell":
                # For nushell, show the complete load-env command for copying
                record = _format_nushell_load_env(env_vars_dict)
                code = f"load-env {record}"
            else:
                code = "\n".join(export_commands)

            syntax = Syntax(
                code,
                shell_type if shell_type != "powershell" else "powershell",
                theme="monokai",
                line_numbers=False,
            )
            console.print(Panel(syntax, border_style="dim"))

            # Show shell-specific usage instructions
            console.print(
                f"\n[bold cyan]Usage for {shell_type.capitalize()}:[/bold cyan]"
            )

            # Build the actual command for usage example
            cmd_parts = ["vaultconfig", "export-env", name]
            # Only add config-dir if explicitly provided (not default)
            if config_dir and str(config_path) != str(_get_config_dir(None)):
                cmd_parts.extend(["-C", config_dir])
            if prefix:
                cmd_parts.extend(["--prefix", prefix])
            if reveal:
                cmd_parts.append("--reveal")
            # Only add --shell if explicitly specified (not auto-detected)
            if shell:
                cmd_parts.extend(["--shell", shell_type])
            base_cmd = " ".join(cmd_parts)

            if shell_type in ["bash", "zsh"]:
                usage_example = f"eval $({base_cmd})"
                console.print(f"  [green]{usage_example}[/green]")
                console.print(
                    "  [dim]This will set the environment variables in your current "
                    "shell session.[/dim]"
                )
            elif shell_type == "fish":
                usage_example = f"{base_cmd} | source"
                console.print(f"  [green]{usage_example}[/green]")
                console.print(
                    "  [dim]This will set the environment variables in your current "
                    "fish session.[/dim]"
                )
            elif shell_type == "nushell":
                console.print(f"  [green]{base_cmd} | from json | load-env[/green]")
                console.print(
                    "  [dim]This will load the environment variables into your "
                    "current nushell session.[/dim]"
                )
                console.print(f"  [green]{base_cmd} | save -f env.nu[/green]")
                console.print("  [dim]Then: [/dim][green]source env.nu[/green]")
                console.print(
                    "  [dim]This will save the variables to a file that you can "
                    "source later.[/dim]"
                )
            elif shell_type == "powershell":
                usage_example = f"{base_cmd} | Invoke-Expression"
                console.print(f"  [green]{usage_example}[/green]")
                console.print(
                    "  [dim]This will set the environment variables in your current "
                    "PowerShell session.[/dim]"
                )

            if not reveal:
                console.print(
                    "\n[yellow]Note:[/yellow] Use --reveal to show obscured passwords"
                )

            console.print(
                f"\n[dim]Tip: You can copy the commands above and paste "
                f"them into your {shell_type} shell, or use the usage example to load "
                "them automatically.[/dim]"
            )
        else:
            # Normal mode: Export as shell commands
            # Ensure shell is not None
            shell_type = shell if shell is not None else "bash"

            # Build environment variables dict
            env_vars = {}
            for key, value in flat_data.items():
                # Convert key to env var format
                env_key = key.replace(".", "_").replace("-", "_")
                if uppercase:
                    env_key = env_key.upper()
                env_key = prefix + env_key
                env_vars[env_key] = str(value)

            # For nushell, use load-env command format
            if shell_type == "nushell":
                click.echo(_format_nushell_load_env(env_vars))
            else:
                # For other shells, print individual export statements
                for env_key, value in env_vars.items():
                    click.echo(_format_env_export(env_key, value, shell_type))

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="run", context_settings={"ignore_unknown_options": True})
@click.argument("name", required=True)
@click.argument("commandline", nargs=-1, type=click.UNPROCESSED, required=True)
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--prefix", "-p", default="", help="Environment variable prefix")
@click.option("--reveal", "-r", is_flag=True, help="Reveal obscured passwords")
@click.option(
    "--uppercase", "-u", is_flag=True, default=True, help="Convert keys to uppercase"
)
@click.option(
    "--override/--no-override",
    default=True,
    help="Override existing environment variables",
)
def run_command(
    name: str,
    commandline: tuple[str, ...],
    config_dir: str | None,
    format: str | None,
    prefix: str,
    reveal: bool,
    uppercase: bool,
    override: bool,
) -> None:
    """Run a command with configuration loaded as environment variables.

    This loads a configuration and runs a command with the config values
    set as environment variables. Similar to 'dotenv run' but for vaultconfig.

    Uses default config directory if not specified.

    Examples:
        # Run a script with database config
        vaultconfig run database python manage.py migrate

        # Run with custom prefix
        vaultconfig run database --prefix DB_ ./start-server.sh

        # Run with revealed passwords
        vaultconfig run database --reveal env | grep PASSWORD

        # Don't override existing env vars
        vaultconfig run database --no-override python script.py
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format)
        config = manager.get_config(name)

        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Get configuration data
        data = config.get_all(reveal_secrets=reveal)

        # Flatten nested dictionaries
        flat_data = _flatten_dict(data)

        # Build environment variables dict
        env_vars = {}
        for key, value in flat_data.items():
            # Convert key to env var format
            env_key = key.replace(".", "_")
            if uppercase:
                env_key = env_key.upper()
            env_key = prefix + env_key

            # Only add if override is True or var doesn't exist
            if override or env_key not in os.environ:
                env_vars[env_key] = str(value)

        if not commandline:
            console.print("[red]Error:[/red] No command given")
            sys.exit(1)

        # Run the command with environment variables
        _run_command_with_env(list(commandline), env_vars)

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _run_command_with_env(command: list[str], env: dict[str, str]) -> None:
    """Execute a command with additional environment variables.

    Args:
        command: Command and arguments to execute
        env: Additional environment variables to add

    This function replaces the current process with the command.
    """
    import subprocess

    # Copy current environment and add new variables
    cmd_env = os.environ.copy()
    cmd_env.update(env)

    # Use subprocess instead of execvpe for better test compatibility
    # and consistent behavior across platforms
    p = subprocess.Popen(
        command, universal_newlines=True, bufsize=0, shell=False, env=cmd_env
    )
    p.communicate()
    sys.exit(p.returncode)


@main.command(name="encrypt-file")
@click.argument("name", required=True)
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--password", "-p", help="Encryption password")
def encrypt_single_command(
    name: str, config_dir: str | None, format: str | None, password: str | None
) -> None:
    """Encrypt a specific config file.

    Uses default config directory if not specified.

    Examples:
        vaultconfig encrypt-file database
        vaultconfig encrypt-file api --password "mypass"
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(
            str(config_path), format, ask_password=False, auto_load=False
        )

        # Check if config file exists
        config_file = manager._get_config_file(name)
        if not config_file.exists():
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Load only this specific config
        manager._load_config(name)

        # Get password
        if password is None:
            password = click.prompt("Enter encryption password", hide_input=True)
            confirm = click.prompt("Confirm password", hide_input=True)
            if password != confirm:
                console.print("[red]Error:[/red] Passwords do not match")
                sys.exit(1)

        # Validate password is not None after prompt
        assert password is not None

        # Encrypt config
        manager.encrypt_config(name, password)
        console.print(f"[green]✓[/green] Encrypted config: {name}")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="decrypt-file")
@click.argument("name", required=True)
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
def decrypt_command(name: str, config_dir: str | None, format: str | None) -> None:
    """Decrypt a specific config file.

    Uses default config directory if not specified.

    Examples:
        vaultconfig decrypt-file database
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(
            str(config_path), format, ask_password=False, auto_load=False
        )

        # Check if config file exists
        config_file = manager._get_config_file(name)
        if not config_file.exists():
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Load only this specific config
        manager._load_config(name)

        # Decrypt config
        manager.decrypt_config(name)
        console.print(f"[green]✓[/green] Decrypted config: {name}")
        console.print("[yellow]Note:[/yellow] Config is now stored as plaintext")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.group(name="encrypt")
def encrypt_group() -> None:
    """Manage encryption for configs."""
    pass


@encrypt_group.command(name="set")
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--password", "-p", help="Encryption password")
def encrypt_set_command(
    config_dir: str | None, format: str | None, password: str | None
) -> None:
    """Set encryption password for all configs in directory.

    Uses default config directory if not specified.

    Examples:
        vaultconfig encrypt set
        vaultconfig encrypt set --password "mypass"
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)

        if password is None:
            password = click.prompt("Enter encryption password", hide_input=True)
            confirm = click.prompt("Confirm password", hide_input=True)

            if password != confirm:
                console.print("[red]Error:[/red] Passwords do not match")
                sys.exit(1)

        assert password is not None
        manager.set_encryption_password(password)
        console.print("[green]✓[/green] Encryption password updated for all configs")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@encrypt_group.command(name="remove")
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def encrypt_remove_command(
    config_dir: str | None, format: str | None, yes: bool
) -> None:
    """Remove encryption from all configs in directory.

    Uses default config directory if not specified.

    Examples:
        vaultconfig encrypt remove
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        # Confirm removal
        if not yes:
            if not click.confirm(
                "Are you sure you want to remove encryption? "
                "Configs will be stored as plaintext."
            ):
                console.print("[yellow]Cancelled[/yellow]")
                sys.exit(1)

        manager = _get_manager(str(config_path), format)
        manager.remove_encryption()
        console.print("[green]✓[/green] Encryption removed from all configs")
        console.print("[yellow]Note:[/yellow] Configs are now stored as plaintext")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@encrypt_group.command(name="check")
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
def encrypt_check_command(config_dir: str | None, format: str | None) -> None:
    """Check encryption status for all configs.

    Uses default config directory if not specified.

    Examples:
        vaultconfig encrypt check
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(
            str(config_path), format, ask_password=False, auto_load=False
        )
        status = manager.get_encryption_status()

        if not status:
            console.print("No configurations found")
            return

        # Check if any are encrypted
        encrypted_count = sum(1 for is_encrypted in status.values() if is_encrypted)
        total_count = len(status)

        if encrypted_count == 0:
            console.print(
                f"[yellow]All configs ({total_count}) are NOT encrypted[/yellow]"
            )
        elif encrypted_count == total_count:
            console.print(f"[green]All configs ({total_count}) are encrypted[/green]")
        else:
            console.print(
                f"[yellow]{encrypted_count}/{total_count} configs "
                "are encrypted[/yellow]"
            )

        # Show status table
        table = Table(title="Encryption Status")
        table.add_column("Name", style="cyan")
        table.add_column("Encrypted", style="yellow")

        for name in sorted(status.keys()):
            encrypted_status = "Yes" if status[name] else "No"
            table.add_row(name, encrypted_status)

        console.print(table)

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.group()
def encryption() -> None:
    """Manage encryption settings."""
    pass


@main.command(name="encrypt-dir")
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.option("--password", "-p", help="Encryption password")
def encrypt_dir_command(
    config_dir: str | None, format: str | None, password: str | None
) -> None:
    """Encrypt all configs in directory with same password.

    Uses default config directory if not specified.

    Examples:
        vaultconfig encrypt-dir
        vaultconfig encrypt-dir --password "mypass"
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format, ask_password=False)

        if password is None:
            password = click.prompt("Enter encryption password", hide_input=True)
            confirm = click.prompt("Confirm password", hide_input=True)

            if password != confirm:
                console.print("[red]Error:[/red] Passwords do not match")
                sys.exit(1)

        assert password is not None
        manager.set_encryption_password(password)
        console.print("[green]✓[/green] All configs encrypted with directory password")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="decrypt-dir")
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
@click.confirmation_option(
    prompt=(
        "Are you sure you want to decrypt all configs? "
        "They will be stored as plaintext."
    )
)
def decrypt_dir_command(config_dir: str | None, format: str | None) -> None:
    """Remove encryption from all configs in directory.

    Uses default config directory if not specified.

    Examples:
        vaultconfig decrypt-dir
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(str(config_path), format)
        manager.remove_encryption()
        console.print("[green]✓[/green] All configs decrypted")
        console.print("[yellow]Note:[/yellow] Configs are now stored as plaintext")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@encryption.command(name="status")
@click.option(
    "--config-dir",
    "-d",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.option("--format", "-f", help="Config format")
def encryption_status_command(config_dir: str | None, format: str | None) -> None:
    """Show encryption status for all configs.

    Uses default config directory if not specified.

    Examples:
        vaultconfig encryption status
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        manager = _get_manager(
            str(config_path), format, ask_password=False, auto_load=False
        )
        status = manager.get_encryption_status()

        if not status:
            console.print("No configurations found")
            return

        # Show status table
        table = Table(title="Encryption Status")
        table.add_column("Name", style="cyan")
        table.add_column("Encrypted", style="yellow")

        for name in sorted(status.keys()):
            encrypted_status = "[E] Yes" if status[name] else "No"
            table.add_row(name, encrypted_status)

        console.print(table)

        # Show directory-level status
        if manager.is_encrypted():
            console.print(
                "\n[yellow]Note:[/yellow] Directory-level encryption is enabled"
            )

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="validate")
@click.option(
    "--config-dir",
    "-C",
    type=click.Path(),
    help="Config directory (uses default if not specified)",
)
@click.argument("name", required=True)
@click.option("--format", "-f", help="Config format")
@click.option(
    "--schema", "-s", type=click.Path(exists=True), help="Schema file (YAML or JSON)"
)
def validate_command(
    config_dir: str | None, name: str, format: str | None, schema: str | None
) -> None:
    """Validate a configuration against a schema.

    Uses default config directory if not specified.

    Examples:
        vaultconfig validate database --schema schema.yaml
    """
    try:
        config_path = _get_config_dir(config_dir)
        if not config_path.exists():
            console.print(
                f"[red]Error:[/red] Config directory not found: {config_path}"
            )
            sys.exit(1)

        # Load schema if provided
        config_schema = None
        if schema:
            config_schema = _load_schema_from_file(schema)

        # Get manager with schema
        manager = _get_manager(str(config_path), format, ask_password=False)
        if config_schema:
            manager.schema = config_schema

        # Get config
        config = manager.get_config(name)
        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        # Validate
        if config_schema:
            try:
                config_schema.validate(config._data)
                console.print(f"[green]✓[/green] Config '{name}' is valid")
            except Exception as e:
                console.print(f"[red]✗[/red] Validation failed: {e}")
                sys.exit(1)
        else:
            console.print(
                "[yellow]Warning:[/yellow] No schema provided, skipping validation"
            )
            console.print(f"[green]✓[/green] Config '{name}' exists and is readable")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.group()
def obscure() -> None:
    """Manage password obscuring."""
    pass


@obscure.command(name="generate-key")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (prints to stdout if not specified)",
)
@click.option(
    "--from-passphrase",
    "-p",
    is_flag=True,
    help="Generate key from passphrase instead of random bytes",
)
def obscure_generate_key(output: str | None, from_passphrase: bool) -> None:
    """Generate a new cipher key for password obscuring.

    This generates a 32-byte (256-bit) AES key that can be used with vaultconfig
    for custom password obscuring. The key is output as a 64-character hex string.

    Examples:
        # Generate random key and save to file
        vaultconfig obscure generate-key -o ~/.myapp_cipher_key

        # Generate from passphrase
        vaultconfig obscure generate-key --from-passphrase

        # Print to stdout
        vaultconfig obscure generate-key
    """
    import hashlib

    try:
        if from_passphrase:
            passphrase = click.prompt("Enter passphrase", hide_input=True)
            confirm = click.prompt("Confirm passphrase", hide_input=True)

            if passphrase != confirm:
                console.print("[red]Error:[/red] Passphrases do not match")
                sys.exit(1)

            # Generate key from passphrase using SHA-256
            key_bytes = hashlib.sha256(passphrase.encode("utf-8")).digest()
        else:
            # Generate random 32-byte key
            key_bytes = secrets.token_bytes(32)

        # Convert to hex string
        hex_key = key_bytes.hex()

        if output:
            output_path = Path(output).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                f.write(hex_key)

            # Set secure permissions (owner read/write only)
            os.chmod(output_path, 0o600)

            console.print(f"[green]✓[/green] Cipher key saved to: {output}")
            console.print("\nTo use this key, set the environment variable:")
            console.print(f"  export VAULTCONFIG_CIPHER_KEY_FILE={output}")
            console.print("\nOr:")
            console.print(f"  export VAULTCONFIG_CIPHER_KEY=$(cat {output})")
        else:
            # Print to stdout
            console.print(hex_key)
            # Print warning to stderr using click.echo
            click.echo(
                "\nNote: Save this key securely! "
                "You'll need it to reveal obscured passwords.",
                err=True,
            )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _get_manager(
    config_dir: str,
    format: str | None = None,
    ask_password: bool = True,
    auto_load: bool = True,
) -> ConfigManager:
    """Get ConfigManager instance with password handling.

    Args:
        config_dir: Config directory path
        format: Config format (autodetect if None)
        ask_password: If True, ask for password if needed
            (deprecated, kept for compatibility)
        auto_load: If True, automatically load all configs
            (set False for list operations)

    Returns:
        ConfigManager instance
    """
    from vaultconfig import obscure

    config_path = Path(config_dir)

    # Detect format if not specified
    if format is None:
        format = _detect_format(config_path)

    # Check for password in environment variable
    # Don't prompt interactively - let individual operations decide
    password = os.environ.get("VAULTCONFIG_PASSWORD")

    # Load custom cipher key if provided
    obscurer = None
    cipher_key_hex = os.environ.get("VAULTCONFIG_CIPHER_KEY")
    cipher_key_file = os.environ.get("VAULTCONFIG_CIPHER_KEY_FILE")

    if cipher_key_file:
        try:
            key_path = Path(cipher_key_file).expanduser()
            with open(key_path) as f:
                cipher_key_hex = f.read().strip()
        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Failed to read cipher key file: {e}"
            )

    if cipher_key_hex:
        try:
            obscurer = obscure.create_obscurer_from_hex(cipher_key_hex)
        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Invalid cipher key, using default: {e}"
            )

    return ConfigManager(
        config_path,
        format=format,
        password=password,
        obscurer=obscurer,
        auto_load=auto_load,
    )


def _detect_format(config_dir: Path) -> str:
    """Detect config format from existing files.

    Args:
        config_dir: Config directory

    Returns:
        Detected format name
    """
    # Count files by extension
    extensions = {".toml": 0, ".ini": 0, ".yaml": 0, ".yml": 0}

    for ext in extensions:
        extensions[ext] = len(list(config_dir.glob(f"*{ext}")))

    # Return most common format
    if extensions[".toml"] > 0:
        return "toml"
    elif extensions[".ini"] > 0:
        return "ini"
    elif extensions[".yaml"] > 0 or extensions[".yml"] > 0:
        return "yaml"

    # Default to toml
    return "toml"


def _print_dict(data: dict, indent: int = 0) -> None:
    """Pretty print dictionary.

    Args:
        data: Dictionary to print
        indent: Indentation level
    """
    for key, value in data.items():
        if isinstance(value, dict):
            console.print("  " * indent + f"[bold]{key}:[/bold]")
            _print_dict(value, indent + 1)
        else:
            console.print("  " * indent + f"{key}: {value}")


def _parse_value(value: str) -> Any:
    """Parse a string value to appropriate Python type.

    Args:
        value: String value to parse

    Returns:
        Parsed value (int, float, bool, or str)
    """
    # Try to parse as int
    try:
        return int(value)
    except ValueError:
        pass

    # Try to parse as float
    try:
        return float(value)
    except ValueError:
        pass

    # Parse booleans
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    # Return as string
    return value


def _set_nested_value(data: dict, key: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot notation.

    Args:
        data: Dictionary to modify
        key: Key (supports dot notation like "database.host")
        value: Value to set
    """
    keys = key.split(".")
    current = data

    # Navigate to the parent of the final key
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            # Can't navigate further, replace with dict
            current[k] = {}
        current = current[k]

    # Set the final value
    current[keys[-1]] = value


def _unset_nested_value(data: dict, key: str) -> bool:
    """Remove a value from a nested dictionary using dot notation.

    Args:
        data: Dictionary to modify
        key: Key to remove (supports dot notation)

    Returns:
        True if key was found and removed, False otherwise
    """
    keys = key.split(".")
    current = data

    # Navigate to the parent of the final key
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            return False
        current = current[k]

    # Remove the final key
    if keys[-1] in current:
        del current[keys[-1]]
        return True
    return False


def _get_format_handler(format_name: str) -> Any:
    """Get format handler by name.

    Args:
        format_name: Format name (toml, ini, yaml)

    Returns:
        Format handler instance
    """
    from vaultconfig.formats import INIFormat, TOMLFormat, YAMLFormat

    handlers = {
        "toml": TOMLFormat,
        "ini": INIFormat,
        "yaml": YAMLFormat,
    }

    if format_name not in handlers:
        raise ValueError(f"Unsupported format: {format_name}")

    return handlers[format_name]()


def _flatten_dict(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten a nested dictionary.

    Args:
        data: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items: list[tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(_flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def _filter_dict(
    data: dict, include: tuple[str, ...] | None, exclude: tuple[str, ...] | None
) -> dict:
    """Filter a dictionary based on include and exclude patterns.

    Args:
        data: Dictionary to filter (can be nested)
        include: Tuple of key patterns to include (supports dot notation and wildcards)
        exclude: Tuple of key patterns to exclude (supports dot notation and wildcards)

    Returns:
        Filtered dictionary

    Note:
        - If include is specified, only matching keys are included
        - If exclude is specified, matching keys are removed
        - Exclude takes precedence over include
        - Patterns support wildcards: "database.*" matches all keys starting
          with "database."
    """
    import fnmatch

    # If no filters, return as-is
    if not include and not exclude:
        return data

    # Flatten the dictionary to work with full key paths
    flat_data = _flatten_dict(data)
    filtered_flat: dict[str, Any] = {}

    for key, value in flat_data.items():
        # Check include patterns
        included = True
        if include:
            included = any(fnmatch.fnmatch(key, pattern) for pattern in include)

        # Check exclude patterns (takes precedence)
        excluded = False
        if exclude:
            excluded = any(fnmatch.fnmatch(key, pattern) for pattern in exclude)

        # Add if included and not excluded
        if included and not excluded:
            filtered_flat[key] = value

    # Reconstruct nested dictionary from filtered flat data
    result: dict[str, Any] = {}
    for key, value in filtered_flat.items():
        keys = key.split(".")
        current = result
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    return result


def _shell_quote(value: str) -> str:
    """Quote a string for safe use in shell export statements.

    Args:
        value: String to quote

    Returns:
        Quoted string safe for shell
    """
    # Simple quoting: use single quotes and escape any single quotes in the value
    return f"'{value.replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'"


def _detect_shell() -> str:
    """Detect the current shell from environment.

    Returns:
        Shell name: bash, zsh, fish, nushell, powershell, or bash (default)
    """
    import os

    # Check SHELL environment variable first
    shell_path = os.environ.get("SHELL", "")
    if shell_path:
        shell_name = Path(shell_path).name
        if shell_name in ["bash", "zsh", "fish", "nu", "nushell"]:
            if shell_name == "nu":
                return "nushell"
            return shell_name

    # Check for PowerShell
    if os.environ.get("PSModulePath"):
        return "powershell"

    # Default to bash
    return "bash"


def _format_env_export(key: str, value: str, shell: str) -> str:
    """Format an environment variable export for a specific shell.

    Args:
        key: Environment variable name
        value: Environment variable value
        shell: Shell type (bash, zsh, fish, nushell, powershell)

    Returns:
        Formatted export statement

    Note:
        For nushell with multiple variables, use _format_nushell_load_env instead.
    """
    if shell in ["bash", "zsh"]:
        # Bash/Zsh: export KEY='value'
        return f"export {key}={_shell_quote(value)}"
    elif shell == "fish":
        # Fish: set -gx KEY 'value'
        return f"set -gx {key} {_shell_quote(value)}"
    elif shell == "nushell":
        # Nushell: $env.KEY = 'value'
        # Nushell uses single quotes for strings, backslash for escaping
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"$env.{key} = '{escaped}'"
    elif shell == "powershell":
        # PowerShell: $env:KEY = 'value'
        # PowerShell uses single quotes, double single quote to escape
        escaped = value.replace("'", "''")
        return f"$env:{key} = '{escaped}'"
    else:
        # Default to bash format
        return f"export {key}={_shell_quote(value)}"


def _format_nushell_load_env(env_vars: dict[str, str]) -> str:
    """Format environment variables for nushell's load-env command.

    Args:
        env_vars: Dictionary of environment variable names and values

    Returns:
        Nushell record that can be piped directly to load-env
        Format: { "KEY1": "value1", "KEY2": "value2" }
    """
    import json

    if not env_vars:
        return "{}"

    # Output as a nushell record (which is JSON-like)
    # This can be used both ways:
    # 1. Piped: vaultconfig export-env name --shell nushell | load-env
    # 2. Copied: load-env { "KEY": "value" }
    return json.dumps(env_vars)


def _load_schema_from_file(schema_file: str) -> Any:
    """Load schema from YAML or JSON file.

    Args:
        schema_file: Path to schema file

    Returns:
        ConfigSchema instance

    Raises:
        Exception: If schema cannot be loaded
    """
    from vaultconfig.schema import FieldDef, create_simple_schema

    schema_path = Path(schema_file)
    content = schema_path.read_text()

    # Parse file based on extension
    if schema_path.suffix in [".yaml", ".yml"]:
        handler = _get_format_handler("yaml")
        schema_data = handler.load(content)
    elif schema_path.suffix == ".json":
        import json

        schema_data = json.loads(content)
    else:
        # Try JSON first, then YAML
        import json

        try:
            schema_data = json.loads(content)
        except json.JSONDecodeError:
            handler = _get_format_handler("yaml")
            schema_data = handler.load(content)

    # Convert schema data to FieldDef format
    # Expected format:
    # fields:
    #   host:
    #     type = "str"
    #     default = "localhost"
    #     sensitive = false
    #   password:
    #     type = "str"
    #     sensitive = true
    #     required = true

    if "fields" not in schema_data:
        raise ValueError("Schema file must contain a 'fields' key")

    fields = {}
    type_map = {
        "str": str,
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "bool": bool,
        "boolean": bool,
    }

    for field_name, field_spec in schema_data["fields"].items():
        field_type_str = field_spec.get("type", "str")
        field_type = type_map.get(field_type_str, str)

        required = field_spec.get("required", False)
        default = field_spec.get("default", ... if required else None)
        sensitive = field_spec.get("sensitive", False)
        description = field_spec.get("description", "")

        fields[field_name] = FieldDef(
            type=field_type,
            default=default,
            sensitive=sensitive,
            description=description,
        )

    return create_simple_schema(fields)


if __name__ == "__main__":
    main()

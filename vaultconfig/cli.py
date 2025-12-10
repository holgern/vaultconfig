"""Command-line interface for vaultconfig."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from vaultconfig.config import ConfigManager
from vaultconfig.exceptions import VaultConfigError

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """VaultConfig - Secure configuration management with encryption support."""
    pass


@main.command()
@click.argument("config_dir", type=click.Path())
@click.option("--format", "-f", default="toml", help="Config format (toml/ini/yaml)")
@click.option("--encrypt", "-e", is_flag=True, help="Enable encryption")
def init(config_dir: str, format: str, encrypt: bool) -> None:
    """Initialize a new config directory."""
    config_path = Path(config_dir)

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

    console.print(f"[green]✓[/green] Initialized config directory: {config_dir}")
    console.print(f"  Format: {format}")
    console.print(f"  Encrypted: {'Yes' if encrypt else 'No'}")


@main.command(name="list")
@click.argument("config_dir", type=click.Path(exists=True))
@click.option("--format", "-f", help="Config format (autodetect if not specified)")
def list_command(config_dir: str, format: str | None) -> None:
    """List all configurations."""
    try:
        manager = _get_manager(config_dir, format)
        configs = manager.list_configs()

        if not configs:
            console.print("No configurations found")
            return

        table = Table(title="Configurations")
        table.add_column("Name", style="cyan")
        table.add_column("Encrypted", style="yellow")

        for name in sorted(configs):
            encrypted = "Yes" if manager.is_encrypted() else "No"
            table.add_row(name, encrypted)

        console.print(table)

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="show")
@click.argument("config_dir", type=click.Path(exists=True))
@click.argument("name")
@click.option("--format", "-f", help="Config format")
@click.option("--reveal", "-r", is_flag=True, help="Reveal obscured passwords")
def show_command(config_dir: str, name: str, format: str | None, reveal: bool) -> None:
    """Show configuration."""
    try:
        manager = _get_manager(config_dir, format)
        config = manager.get_config(name)

        if not config:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

        console.print(f"[bold]Configuration:[/bold] {name}")
        console.print()

        data = config.get_all(reveal_secrets=reveal)
        _print_dict(data)

        if not reveal:
            console.print()
            console.print(
                "[yellow]Note:[/yellow] Use --reveal to show obscured passwords"
            )

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command(name="delete")
@click.argument("config_dir", type=click.Path(exists=True))
@click.argument("name")
@click.option("--format", "-f", help="Config format")
@click.confirmation_option(prompt="Are you sure you want to delete this config?")
def delete_command(config_dir: str, name: str, format: str | None) -> None:
    """Delete a configuration."""
    try:
        manager = _get_manager(config_dir, format)

        if manager.remove_config(name):
            console.print(f"[green]✓[/green] Deleted config: {name}")
        else:
            console.print(f"[red]Error:[/red] Config '{name}' not found")
            sys.exit(1)

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.group()
def encrypt() -> None:
    """Manage config encryption."""
    pass


@encrypt.command(name="set")
@click.argument("config_dir", type=click.Path(exists=True))
@click.option("--format", "-f", help="Config format")
def encrypt_set(config_dir: str, format: str | None) -> None:
    """Set or change encryption password."""
    try:
        manager = _get_manager(config_dir, format, ask_password=False)

        password = click.prompt("Enter new encryption password", hide_input=True)
        confirm = click.prompt("Confirm password", hide_input=True)

        if password != confirm:
            console.print("[red]Error:[/red] Passwords do not match")
            sys.exit(1)

        manager.set_encryption_password(password)
        console.print("[green]✓[/green] Encryption password updated")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@encrypt.command(name="remove")
@click.argument("config_dir", type=click.Path(exists=True))
@click.option("--format", "-f", help="Config format")
@click.confirmation_option(
    prompt=(
        "Are you sure you want to remove encryption? "
        "Configs will be stored in plaintext."
    )
)
def encrypt_remove(config_dir: str, format: str | None) -> None:
    """Remove encryption from all configs."""
    try:
        manager = _get_manager(config_dir, format)
        manager.remove_encryption()
        console.print("[green]✓[/green] Encryption removed")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@encrypt.command(name="check")
@click.argument("config_dir", type=click.Path(exists=True))
@click.option("--format", "-f", help="Config format")
def encrypt_check(config_dir: str, format: str | None) -> None:
    """Check if configs are encrypted."""
    try:
        manager = _get_manager(config_dir, format, ask_password=False)

        if manager.is_encrypted():
            console.print("[green]✓[/green] Configs are encrypted")
        else:
            console.print("[yellow]![/yellow] Configs are NOT encrypted")

    except VaultConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _get_manager(
    config_dir: str, format: str | None = None, ask_password: bool = True
) -> ConfigManager:
    """Get ConfigManager instance with password handling.

    Args:
        config_dir: Config directory path
        format: Config format (autodetect if None)
        ask_password: If True, ask for password if needed

    Returns:
        ConfigManager instance
    """
    from vaultconfig import crypt

    config_path = Path(config_dir)

    # Detect format if not specified
    if format is None:
        format = _detect_format(config_path)

    # Check if any config file is encrypted
    password = None
    if ask_password:
        extension = {"toml": ".toml", "ini": ".ini", "yaml": ".yaml"}.get(
            format, ".toml"
        )

        for config_file in config_path.glob(f"*{extension}"):
            with open(config_file, "rb") as f:
                if crypt.is_encrypted(f.read()):
                    password = crypt.get_password()
                    break

    return ConfigManager(config_path, format=format, password=password)


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


if __name__ == "__main__":
    main()

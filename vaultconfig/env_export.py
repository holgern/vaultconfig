"""Environment export helpers for vaultconfig.

Provides pure functions for filtering, flattening, and formatting configuration
data as shell environment variable exports.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def flatten_dict(
    data: dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> dict[str, str]:
    """Flatten a nested dictionary using a separator.

    Args:
        data: Dictionary to flatten (can be nested).
        parent_key: Key prefix for recursion.
        sep: Separator between nested key parts.

    Returns:
        Flattened dictionary with original value types preserved.
    """
    items: list[tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def filter_dict(
    data: dict[str, Any],
    include: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Filter a dictionary based on include and exclude key patterns.

    Patterns support wildcards using fnmatch (e.g., ``"database.*"``).
    Exclude takes precedence over include.

    Args:
        data: Dictionary to filter (can be nested).
        include: Key patterns to include. None means include all.
        exclude: Key patterns to exclude. None means exclude none.

    Returns:
        Filtered dictionary.
    """
    import fnmatch

    if not include and not exclude:
        return data
    flat_data = flatten_dict(data)
    filtered_flat: dict[str, Any] = {}

    for key, value in flat_data.items():
        included = True
        if include:
            included = any(fnmatch.fnmatch(key, pattern) for pattern in include)

        excluded = False
        if exclude:
            excluded = any(fnmatch.fnmatch(key, pattern) for pattern in exclude)

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


def build_env_vars(
    flat_data: dict[str, str],
    prefix: str = "",
    uppercase: bool = True,
) -> dict[str, str]:
    """Build environment variable names from flatted key-value pairs.

    Args:
        flat_data: Flat dictionary of key-value pairs.
        prefix: Optional prefix for all variable names.
        uppercase: Whether to uppercase variable names.

    Returns:
        Dictionary mapping environment variable names to string values.
    """
    env_vars: dict[str, str] = {}
    for key, value in flat_data.items():
        env_key = key.replace(".", "_").replace("-", "_")
        if uppercase:
            env_key = env_key.upper()
        env_key = prefix + env_key
        env_vars[env_key] = value
    return env_vars


def shell_quote(value: str) -> str:
    """Quote a string for safe use in POSIX shell export statements.

    Uses single quotes with internal single quote escaping.

    Args:
        value: String to quote.

    Returns:
        Single-quoted string safe for bash/zsh/fish.
    """
    return f"'{value.replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'"


def format_env_export(key: str, value: str, shell: str) -> str:
    """Format a single environment variable export for a given shell.

    Args:
        key: Environment variable name.
        value: Environment variable value.
        shell: Target shell (bash, zsh, fish, nushell, powershell).

    Returns:
        Shell-specific export statement string.
    """
    if shell in ("bash", "zsh"):
        return f"export {key}={shell_quote(value)}"
    elif shell == "fish":
        return f"set -gx {key} {shell_quote(value)}"
    elif shell == "nushell":
        escaped = value.replace("'", "''")
        return f"$env.{key} = '{escaped}'"
    elif shell == "powershell":
        escaped = value.replace("'", "''")
        return f"$env:{key} = '{escaped}'"
    else:
        return f"export {key}={shell_quote(value)}"


def format_nushell_load_env(env_vars: dict[str, str]) -> str:
    """Format environment variables as a nushell record for ``load-env``.

    Args:
        env_vars: Dictionary of environment variable names and values.

    Returns:
        JSON string that nushell can consume with ``load-env``.
    """
    if not env_vars:
        return "{}"
    return json.dumps(env_vars)


def detect_shell() -> str:
    """Detect the current shell from environment variables.

    Checks ``SHELL`` first, then ``PSModulePath`` for PowerShell.
    Falls back to ``"bash"``.

    Returns:
        Shell name: bash, zsh, fish, nushell, powershell, or bash (default).
    """
    shell_path = os.environ.get("SHELL", "")
    if shell_path:
        shell_name = Path(shell_path).name
        if shell_name in ("bash", "zsh", "fish"):
            return shell_name
        if shell_name == "nu":
            return "nushell"
        if shell_name == "nushell":
            return "nushell"

    if os.environ.get("PSModulePath"):
        return "powershell"

    return "bash"

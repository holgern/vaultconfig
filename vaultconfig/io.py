"""Shared file I/O helpers for vaultconfig.

Provides unified parsing, dumping, and format detection used by CLI commands
and schema loading.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _get_format_handler(format_name: str):
    """Get format handler by name (internal)."""
    from vaultconfig.formats import INIFormat, TOMLFormat, YAMLFormat

    handlers = {
        "toml": TOMLFormat,
        "ini": INIFormat,
        "yaml": YAMLFormat,
    }
    if format_name not in handlers:
        raise ValueError(f"Unsupported format: {format_name}")
    return handlers[format_name]()


_SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
}


def detect_format_from_path(path: Path) -> str | None:
    """Detect config format from a file path extension.

    Args:
        path: File path to inspect.

    Returns:
        Format name ('json', 'yaml', 'toml', 'ini') or None if unknown.
    """
    return _SUPPORTED_EXTENSIONS.get(path.suffix.lower())


def load_mapping(text: str, format_name: str) -> dict[str, Any]:
    """Parse a text string into a dictionary.

    Args:
        text: The text content to parse.
        format_name: Format name ('json', 'yaml', 'toml', 'ini').

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If format_name is unrecognized.
        FormatError / json.JSONDecodeError: If parsing fails.
    """
    if format_name == "json":
        data = json.loads(text)
    elif format_name in ("yaml", "toml", "ini"):
        handler = _get_format_handler(format_name)
        data = handler.load(text)
    else:
        raise ValueError(f"Unsupported format: {format_name}")

    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping at root, got {type(data).__name__}")

    return data


def load_mapping_file(
    path: Path,
    format_name: str | None = None,
) -> dict[str, Any]:
    """Read a file and parse it into a dictionary.

    Args:
        path: File path to read.
        format_name: Format name. If None, auto-detected from extension.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If format cannot be detected or is unsupported.
        FormatError / json.JSONDecodeError: If parsing fails.
    """
    if format_name is None:
        format_name = detect_format_from_path(path)

    if format_name is None:
        # Try JSON first, then YAML as fallback (matching schema loader behaviour)
        content = path.read_text()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            handler = _get_format_handler("yaml")
            data = handler.load(content)
    else:
        content = path.read_text()
        data = load_mapping(content, format_name)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping at root, got {type(data).__name__}")

    return data


def dump_mapping(data: dict[str, Any], format_name: str) -> str:
    """Serialize a dictionary to a string.

    Args:
        data: Dictionary to serialize.
        format_name: Target format ('json', 'yaml', 'toml', 'ini').

    Returns:
        Serialized string.

    Raises:
        ValueError: If format_name is unsupported.
        FormatError: If serialization fails.
    """
    if format_name == "json":
        return json.dumps(data, indent=2)
    elif format_name in ("yaml", "toml", "ini"):
        handler = _get_format_handler(format_name)
        return handler.dump(data)
    else:
        raise ValueError(f"Unsupported format: {format_name}")

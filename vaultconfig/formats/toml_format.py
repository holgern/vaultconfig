"""TOML format handler."""

from __future__ import annotations

import sys
from typing import Any

from vaultconfig.exceptions import FormatError
from vaultconfig.formats.base import ConfigFormat

# Python 3.11+ has tomllib built-in, earlier versions need tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore[assignment]


class TOMLFormat(ConfigFormat):
    """TOML configuration format handler."""

    def load(self, data: str) -> dict[str, Any]:
        """Parse TOML config data.

        Args:
            data: TOML config data as string

        Returns:
            Parsed configuration as dictionary

        Raises:
            FormatError: If parsing fails or tomli/tomllib not available
        """
        if tomllib is None:
            raise FormatError(
                "TOML support requires 'tomli' for Python <3.11. "
                "Install it with: pip install tomli"
            )

        try:
            return tomllib.loads(data)
        except Exception as e:
            raise FormatError(f"Failed to parse TOML: {e}") from e

    def dump(self, data: dict[str, Any]) -> str:
        """Serialize config data to TOML.

        Args:
            data: Configuration dictionary

        Returns:
            TOML string

        Raises:
            FormatError: If serialization fails or tomli_w not available
        """
        if tomli_w is None:
            raise FormatError(
                "TOML writing requires 'tomli-w'. Install it with: pip install tomli-w"
            )

        try:
            return tomli_w.dumps(data)
        except Exception as e:
            raise FormatError(f"Failed to serialize to TOML: {e}") from e

    def get_extension(self) -> str:
        """Get TOML file extension.

        Returns:
            '.toml'
        """
        return ".toml"

    @classmethod
    def detect(cls, data: str) -> bool:
        """Detect if data is TOML format.

        Args:
            data: Config data as string

        Returns:
            True if data appears to be TOML
        """
        if not data.strip():
            return False

        # Try to parse as TOML
        if tomllib is None:
            return False  # type: ignore[unreachable]

        try:
            tomllib.loads(data)
            return True
        except Exception:
            return False

    @classmethod
    def get_name(cls) -> str:
        """Get format name.

        Returns:
            'toml'
        """
        return "toml"

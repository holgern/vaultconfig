"""INI format handler."""

from __future__ import annotations

import configparser
import io
from typing import Any

from vaultconfig.exceptions import FormatError
from vaultconfig.formats.base import ConfigFormat


class INIFormat(ConfigFormat):
    """INI configuration format handler."""

    def load(self, data: str) -> dict[str, Any]:
        """Parse INI config data.

        Args:
            data: INI config data as string

        Returns:
            Parsed configuration as nested dictionary

        Raises:
            FormatError: If parsing fails
        """
        try:
            parser = configparser.ConfigParser()
            parser.read_string(data)

            # Convert to nested dict
            result: dict[str, Any] = {}
            for section in parser.sections():
                result[section] = dict(parser.items(section))

            return result
        except Exception as e:
            raise FormatError(f"Failed to parse INI: {e}") from e

    def dump(self, data: dict[str, Any]) -> str:
        """Serialize config data to INI.

        Args:
            data: Configuration dictionary
                (must be two-level: sections -> keys -> values)

        Returns:
            INI string

        Raises:
            FormatError: If serialization fails or data structure is invalid
        """
        try:
            parser = configparser.ConfigParser()

            for section, values in data.items():
                if not isinstance(values, dict):
                    raise FormatError(
                        f"INI format requires nested structure: section '{section}' "
                        f"contains {type(values).__name__}, not dict"
                    )

                parser.add_section(section)
                for key, value in values.items():
                    # Convert value to string
                    parser.set(section, key, str(value))

            # Write to string
            output = io.StringIO()
            parser.write(output)
            return output.getvalue()
        except FormatError:
            raise
        except Exception as e:
            raise FormatError(f"Failed to serialize to INI: {e}") from e

    def get_extension(self) -> str:
        """Get INI file extension.

        Returns:
            '.ini'
        """
        return ".ini"

    @classmethod
    def detect(cls, data: str) -> bool:
        """Detect if data is INI format.

        Args:
            data: Config data as string

        Returns:
            True if data appears to be INI
        """
        if not data.strip():
            return False

        # Try to parse as INI
        try:
            parser = configparser.ConfigParser()
            parser.read_string(data)
            # Must have at least one section
            return len(parser.sections()) > 0
        except Exception:
            return False

    @classmethod
    def get_name(cls) -> str:
        """Get format name.

        Returns:
            'ini'
        """
        return "ini"

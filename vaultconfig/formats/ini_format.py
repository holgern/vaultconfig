"""INI format handler."""

from __future__ import annotations

import configparser
import io
from typing import Any

from vaultconfig.exceptions import FormatError
from vaultconfig.formats.base import ConfigFormat


class INIFormat(ConfigFormat):
    """INI configuration format handler.

    Supports:
    - Section names with dots and spaces
    - DEFAULT section (inherited by all sections)
    - Case-sensitive option names (when preserve_case=True)
    """

    def __init__(self, preserve_case: bool = True) -> None:
        """Initialize INI format handler.

        Args:
            preserve_case: If True, preserve case of option names.
                If False, convert to lowercase (default ConfigParser
                behavior).
        """
        self._preserve_case = preserve_case

    def load(self, data: str) -> dict[str, Any]:
        """Parse INI config data.

        Args:
            data: INI config data as string

        Returns:
            Parsed configuration as nested dictionary.
            The DEFAULT section values are inherited by all other sections
            (standard ConfigParser behavior).

        Raises:
            FormatError: If parsing fails
        """
        try:
            parser = configparser.ConfigParser()

            # Preserve case of option names if requested
            if self._preserve_case:
                parser.optionxform = str  # type: ignore[assignment]

            parser.read_string(data)

            # Convert to nested dict
            # Note: parser.items(section) automatically includes DEFAULT values
            # for each section (standard ConfigParser behavior)
            result: dict[str, Any] = {}

            # Add DEFAULT section if it has any values
            if parser.defaults():
                result["DEFAULT"] = dict(parser.defaults())

            # Add all other sections (with DEFAULT values inherited)
            for section in parser.sections():
                result[section] = dict(parser.items(section))

            return result
        except Exception as e:
            raise FormatError(f"Failed to parse INI: {e}") from e

    def dump(self, data: dict[str, Any]) -> str:
        """Serialize config data to INI.

        Args:
            data: Configuration dictionary
                (must be two-level: sections -> keys -> values).
                A section named 'DEFAULT' will be written as [DEFAULT]
                and its values will be inherited by all other sections.

        Returns:
            INI string

        Raises:
            FormatError: If serialization fails or data structure is invalid
        """
        try:
            parser = configparser.ConfigParser()

            # Preserve case of option names if requested
            if self._preserve_case:
                parser.optionxform = str  # type: ignore[assignment]

            for section, values in data.items():
                if not isinstance(values, dict):
                    raise FormatError(
                        f"INI format requires nested structure: section '{section}' "
                        f"contains {type(values).__name__}, not dict"
                    )

                # Handle DEFAULT section specially
                if section == "DEFAULT":
                    for key, value in values.items():
                        parser.set("DEFAULT", key, str(value))
                else:
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
            # Must have at least one section or DEFAULT values
            return len(parser.sections()) > 0 or len(parser.defaults()) > 0
        except Exception:
            return False

    @classmethod
    def get_name(cls) -> str:
        """Get format name.

        Returns:
            'ini'
        """
        return "ini"

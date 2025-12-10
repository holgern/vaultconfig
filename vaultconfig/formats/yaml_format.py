"""YAML format handler (optional)."""

from __future__ import annotations

from typing import Any

from vaultconfig.exceptions import FormatError
from vaultconfig.formats.base import ConfigFormat

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class YAMLFormat(ConfigFormat):
    """YAML configuration format handler (requires PyYAML)."""

    def load(self, data: str) -> dict[str, Any]:
        """Parse YAML config data.

        Args:
            data: YAML config data as string

        Returns:
            Parsed configuration as dictionary

        Raises:
            FormatError: If parsing fails or PyYAML not available
        """
        if not HAS_YAML:
            raise FormatError(
                "YAML support requires 'PyYAML'. Install it with: pip install pyyaml"
            )

        try:
            result = yaml.safe_load(data)
            if not isinstance(result, dict):
                raise FormatError(
                    f"YAML root must be a dict, got {type(result).__name__}"
                )
            return result
        except FormatError:
            raise
        except Exception as e:
            raise FormatError(f"Failed to parse YAML: {e}") from e

    def dump(self, data: dict[str, Any]) -> str:
        """Serialize config data to YAML.

        Args:
            data: Configuration dictionary

        Returns:
            YAML string

        Raises:
            FormatError: If serialization fails or PyYAML not available
        """
        if not HAS_YAML:
            raise FormatError(
                "YAML support requires 'PyYAML'. Install it with: pip install pyyaml"
            )

        try:
            return yaml.safe_dump(
                data, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
        except Exception as e:
            raise FormatError(f"Failed to serialize to YAML: {e}") from e

    def get_extension(self) -> str:
        """Get YAML file extension.

        Returns:
            '.yaml'
        """
        return ".yaml"

    @classmethod
    def detect(cls, data: str) -> bool:
        """Detect if data is YAML format.

        Args:
            data: Config data as string

        Returns:
            True if data appears to be YAML
        """
        if not data.strip() or not HAS_YAML:
            return False

        # Try to parse as YAML
        try:
            result = yaml.safe_load(data)
            # Must parse to a dict
            return isinstance(result, dict)
        except Exception:
            return False

    @classmethod
    def get_name(cls) -> str:
        """Get format name.

        Returns:
            'yaml'
        """
        return "yaml"

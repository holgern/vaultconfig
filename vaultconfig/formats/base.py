"""Base class for configuration format handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ConfigFormat(ABC):
    """Abstract base class for configuration format handlers."""

    @abstractmethod
    def load(self, data: str) -> dict[str, Any]:
        """Parse config data from string.

        Args:
            data: Config data as string

        Returns:
            Parsed configuration as dictionary

        Raises:
            FormatError: If parsing fails
        """
        pass

    @abstractmethod
    def dump(self, data: dict[str, Any]) -> str:
        """Serialize config data to string.

        Args:
            data: Configuration dictionary

        Returns:
            Serialized config as string

        Raises:
            FormatError: If serialization fails
        """
        pass

    @abstractmethod
    def get_extension(self) -> str:
        """Get the file extension for this format.

        Returns:
            File extension including dot (e.g., '.toml')
        """
        pass

    @classmethod
    @abstractmethod
    def detect(cls, data: str) -> bool:
        """Detect if data is in this format.

        Args:
            data: Config data as string

        Returns:
            True if data appears to be in this format
        """
        pass

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Get the format name.

        Returns:
            Format name (e.g., 'toml', 'ini', 'yaml')
        """
        pass

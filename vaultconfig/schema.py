"""Schema system for configuration validation using Pydantic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object  # type: ignore[assignment, misc]

    def Field(**kwargs):  # type: ignore[no-untyped-def, no-redef]  # noqa: N802
        """Stub for Field when pydantic is not available."""
        return None

    ValidationError = Exception  # type: ignore[assignment, misc]
    ConfigDict = dict  # type: ignore[assignment, misc]

from vaultconfig.exceptions import SchemaValidationError


class ConfigSchema:
    """Schema for configuration validation.

    This class provides a way to define and validate configuration structures
    using Pydantic models.
    """

    def __init__(self, model: Any) -> None:
        """Initialize schema with a Pydantic model.

        Args:
            model: Pydantic BaseModel class defining the schema

        Raises:
            ImportError: If Pydantic is not installed
        """
        if not HAS_PYDANTIC:
            raise ImportError(
                "Schema validation requires 'pydantic'. "
                "Install it with: pip install pydantic"
            )

        self.model = model

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate configuration data against schema.

        Args:
            data: Configuration data to validate

        Returns:
            Validated and normalized data

        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            validated = self.model(**data)
            result: dict[str, Any] = validated.model_dump()
            return result
        except ValidationError as e:
            raise SchemaValidationError(f"Schema validation failed: {e}") from e
        except Exception as e:
            raise SchemaValidationError(f"Validation error: {e}") from e

    def get_sensitive_fields(self) -> set[str]:
        """Get list of sensitive field names that should be obscured.

        Returns:
            Set of field names marked as sensitive
        """
        sensitive: set[str] = set()

        if not HAS_PYDANTIC:
            return sensitive

        # Iterate through model fields
        for field_name, field_info in self.model.model_fields.items():
            # Check if field has 'sensitive' in metadata
            if field_info.json_schema_extra:
                if isinstance(field_info.json_schema_extra, dict):
                    if field_info.json_schema_extra.get("sensitive", False):
                        sensitive.add(field_name)

        return sensitive

    def get_defaults(self) -> dict[str, Any]:
        """Get default values for all fields.

        Returns:
            Dictionary of field names to default values
        """
        defaults: dict[str, Any] = {}

        if not HAS_PYDANTIC:
            return defaults

        # Import PydanticUndefined to check for it
        from pydantic_core import PydanticUndefined as Undef

        for field_name, field_info in self.model.model_fields.items():
            if field_info.default is not Undef and field_info.default is not None:
                defaults[field_name] = field_info.default
            elif field_info.default_factory is not None:
                defaults[field_name] = field_info.default_factory()

        return defaults


def create_simple_schema(fields: dict[str, FieldDef]) -> ConfigSchema:
    """Create a simple schema from field definitions.

    This is a helper function for creating schemas without writing
    full Pydantic models.

    Args:
        fields: Dictionary of field names to FieldDef objects

    Returns:
        ConfigSchema instance

    Raises:
        ImportError: If Pydantic is not installed

    Example:
        >>> schema = create_simple_schema({
        ...     "host": FieldDef(str, default="localhost"),
        ...     "port": FieldDef(int, default=5432),
        ...     "password": FieldDef(str, sensitive=True),
        ... })
    """
    if not HAS_PYDANTIC:
        raise ImportError(
            "Schema validation requires 'pydantic'. "
            "Install it with: pip install pydantic"
        )

    # Build field definitions for Pydantic
    pydantic_fields = {}
    for field_name, field_def in fields.items():
        field_kwargs: dict[str, Any] = {}

        if field_def.default is not ...:
            field_kwargs["default"] = field_def.default
        elif field_def.default_factory is not None:
            field_kwargs["default_factory"] = field_def.default_factory

        if field_def.description:
            field_kwargs["description"] = field_def.description

        # Add sensitive flag to json_schema_extra
        if field_def.sensitive:
            field_kwargs["json_schema_extra"] = {"sensitive": True}

        pydantic_fields[field_name] = (field_def.type, Field(**field_kwargs))

    # Create dynamic Pydantic model
    model = type(
        "DynamicConfigModel",
        (BaseModel,),
        {
            "__annotations__": {
                name: ftype for name, (ftype, _) in pydantic_fields.items()
            },
            **{name: fdef for name, (_, fdef) in pydantic_fields.items()},
            "model_config": ConfigDict(extra="allow"),
        },
    )

    return ConfigSchema(model)


class FieldDef:
    """Field definition for simple schema creation."""

    def __init__(
        self,
        type: type,
        default: Any = ...,
        default_factory: Any = None,
        sensitive: bool = False,
        description: str = "",
    ) -> None:
        """Initialize field definition.

        Args:
            type: Field type (e.g., str, int, bool)
            default: Default value (use ... for required fields)
            default_factory: Factory function for default value
            sensitive: If True, field will be obscured
            description: Field description
        """
        self.type = type
        self.default = default
        self.default_factory = default_factory
        self.sensitive = sensitive
        self.description = description

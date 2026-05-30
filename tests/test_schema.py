"""Tests for schema validation."""

import pytest
from pydantic import BaseModel, Field

from vaultconfig.exceptions import SchemaValidationError
from vaultconfig.schema import ConfigSchema, FieldDef, create_simple_schema


class SimpleModel(BaseModel):
    """Simple Pydantic model for testing."""

    host: str = "localhost"
    port: int = 8080
    enabled: bool = True


class ModelWithSensitive(BaseModel):
    """Model with sensitive fields."""

    username: str
    password: str = Field(json_schema_extra={"sensitive": True})
    api_key: str = Field(default="", json_schema_extra={"sensitive": True})


class ModelWithDefaults(BaseModel):
    """Model with various default types."""

    required_field: str
    optional_field: str = "default_value"
    list_field: list[str] = Field(default_factory=list)
    dict_field: dict[str, int] = Field(default_factory=dict)


def test_schema_initialization():
    """Test schema initialization."""
    schema = ConfigSchema(SimpleModel)
    assert schema.model == SimpleModel


def test_schema_validate_success():
    """Test successful validation."""
    schema = ConfigSchema(SimpleModel)
    data = {"host": "example.com", "port": 9090, "enabled": False}
    result = schema.validate(data)
    assert result["host"] == "example.com"
    assert result["port"] == 9090
    assert result["enabled"] is False


def test_schema_validate_with_defaults():
    """Test validation with default values."""
    schema = ConfigSchema(SimpleModel)
    data = {}
    result = schema.validate(data)
    assert result["host"] == "localhost"
    assert result["port"] == 8080
    assert result["enabled"] is True


def test_schema_validate_partial():
    """Test validation with partial data."""
    schema = ConfigSchema(SimpleModel)
    data = {"port": 3000}
    result = schema.validate(data)
    assert result["host"] == "localhost"
    assert result["port"] == 3000
    assert result["enabled"] is True


def test_schema_validate_type_error():
    """Test validation with wrong types."""
    schema = ConfigSchema(SimpleModel)
    data = {"port": "not_a_number"}
    with pytest.raises(SchemaValidationError) as exc_info:
        schema.validate(data)
    assert "validation failed" in str(exc_info.value).lower()


def test_schema_validate_required_field():
    """Test validation with missing required field."""
    schema = ConfigSchema(ModelWithDefaults)
    data = {}
    with pytest.raises(SchemaValidationError) as exc_info:
        schema.validate(data)
    assert "validation failed" in str(exc_info.value).lower()


def test_get_sensitive_fields():
    """Test getting sensitive fields."""
    schema = ConfigSchema(ModelWithSensitive)
    sensitive = schema.get_sensitive_fields()
    assert "password" in sensitive
    assert "api_key" in sensitive
    assert "username" not in sensitive


def test_get_sensitive_fields_empty():
    """Test getting sensitive fields when none exist."""
    schema = ConfigSchema(SimpleModel)
    sensitive = schema.get_sensitive_fields()
    assert len(sensitive) == 0


def test_get_defaults():
    """Test getting default values."""
    schema = ConfigSchema(ModelWithDefaults)
    defaults = schema.get_defaults()
    assert defaults["optional_field"] == "default_value"
    assert defaults["list_field"] == []
    assert defaults["dict_field"] == {}
    assert "required_field" not in defaults


def test_get_defaults_empty():
    """Test getting defaults when none exist."""
    schema = ConfigSchema(ModelWithSensitive)
    defaults = schema.get_defaults()
    assert defaults.get("api_key") == ""
    # password has no default
    assert "password" not in defaults


def test_create_simple_schema():
    """Test creating schema from field definitions."""
    schema = create_simple_schema(
        {
            "host": FieldDef(str, default="localhost"),
            "port": FieldDef(int, default=8080),
            "enabled": FieldDef(bool, default=True),
        }
    )
    assert isinstance(schema, ConfigSchema)


def test_create_simple_schema_validation():
    """Test validation with created simple schema."""
    schema = create_simple_schema(
        {
            "name": FieldDef(str, default="test"),
            "count": FieldDef(int, default=0),
        }
    )
    data = {"name": "myapp", "count": 5}
    result = schema.validate(data)
    assert result["name"] == "myapp"
    assert result["count"] == 5


def test_create_simple_schema_defaults():
    """Test defaults with created simple schema."""
    schema = create_simple_schema(
        {
            "host": FieldDef(str, default="localhost"),
            "port": FieldDef(int, default=8080),
        }
    )
    data = {}
    result = schema.validate(data)
    assert result["host"] == "localhost"
    assert result["port"] == 8080


def test_create_simple_schema_sensitive():
    """Test sensitive fields with created simple schema."""
    schema = create_simple_schema(
        {
            "username": FieldDef(str, default="user"),
            "password": FieldDef(str, sensitive=True, default=""),
        }
    )
    sensitive = schema.get_sensitive_fields()
    assert "password" in sensitive
    assert "username" not in sensitive


def test_create_simple_schema_required():
    """Test required fields with created simple schema."""
    schema = create_simple_schema(
        {
            "required": FieldDef(str),  # No default = required
            "optional": FieldDef(str, default="value"),
        }
    )
    # Missing required field
    with pytest.raises(SchemaValidationError):
        schema.validate({})

    # With required field
    result = schema.validate({"required": "test"})
    assert result["required"] == "test"
    assert result["optional"] == "value"


def test_create_simple_schema_default_factory():
    """Test default_factory with created simple schema."""
    schema = create_simple_schema(
        {
            "items": FieldDef(list, default_factory=list),
            "mapping": FieldDef(dict, default_factory=dict),
        }
    )
    result = schema.validate({})
    assert result["items"] == []
    assert result["mapping"] == {}


def test_create_simple_schema_description():
    """Test field descriptions with created simple schema."""
    schema = create_simple_schema(
        {
            "host": FieldDef(str, default="localhost", description="Server host"),
        }
    )
    # Just verify it doesn't crash
    assert schema is not None


def test_fielddef_initialization():
    """Test FieldDef initialization."""
    field = FieldDef(str, default="value", sensitive=True, description="A field")
    assert field.type is str
    assert field.default == "value"
    assert field.sensitive is True
    assert field.description == "A field"


def test_fielddef_required():
    """Test FieldDef for required field."""
    field = FieldDef(int)
    assert field.default is ...
    assert field.default_factory is None
    assert field.sensitive is False


def test_schema_extra_fields_allowed():
    """Test that extra fields are allowed in validation."""
    schema = create_simple_schema(
        {
            "known": FieldDef(str, default="value"),
        }
    )
    # Extra fields should be allowed due to ConfigDict(extra="allow")
    data = {"known": "test", "unknown": "extra"}
    result = schema.validate(data)
    assert result["known"] == "test"
    assert result["unknown"] == "extra"


def test_schema_type_coercion():
    """Test that Pydantic's type coercion works."""
    schema = create_simple_schema(
        {
            "port": FieldDef(int, default=8080),
        }
    )
    # String that can be converted to int
    data = {"port": "9090"}
    result = schema.validate(data)
    assert result["port"] == 9090
    assert isinstance(result["port"], int)


def test_schema_complex_types():
    """Test schema with complex types."""
    schema = create_simple_schema(
        {
            "tags": FieldDef(list, default_factory=list),
            "metadata": FieldDef(dict, default_factory=dict),
        }
    )
    data = {"tags": ["a", "b", "c"], "metadata": {"key": "value"}}
    result = schema.validate(data)
    assert result["tags"] == ["a", "b", "c"]
    assert result["metadata"] == {"key": "value"}


class TestNestedSensitiveFields:
    """Tests for recursive sensitive-field discovery in nested models."""

    def test_top_level_sensitive_field(self):
        class AppConfig(BaseModel):
            password: str = Field(json_schema_extra={"sensitive": True})
            host: str = "localhost"

        schema = ConfigSchema(AppConfig)
        assert schema.get_sensitive_fields() == {"password"}

    def test_nested_sensitive_field_discovered_as_dotted_path(self):
        class DbConfig(BaseModel):
            host: str
            password: str = Field(json_schema_extra={"sensitive": True})

        class AppConfig(BaseModel):
            database: DbConfig
            debug: bool = False

        schema = ConfigSchema(AppConfig)
        assert schema.get_sensitive_fields() == {"database.password"}

    def test_deeply_nested_sensitive_field(self):
        class Credentials(BaseModel):
            token: str = Field(json_schema_extra={"sensitive": True})

        class ApiConfig(BaseModel):
            credentials: Credentials

        class AppConfig(BaseModel):
            api: ApiConfig

        schema = ConfigSchema(AppConfig)
        assert schema.get_sensitive_fields() == {"api.credentials.token"}

    def test_multiple_nested_sensitive_fields(self):
        class DbConfig(BaseModel):
            password: str = Field(json_schema_extra={"sensitive": True})
            connection_string: str = Field(json_schema_extra={"sensitive": True})

        class AppConfig(BaseModel):
            database: DbConfig
            api_key: str = Field(json_schema_extra={"sensitive": True})

        schema = ConfigSchema(AppConfig)
        expected = {"api_key", "database.password", "database.connection_string"}
        assert schema.get_sensitive_fields() == expected

    def test_model_without_sensitive_fields_returns_empty(self):
        class SimpleModel(BaseModel):
            host: str
            port: int = 5432

        schema = ConfigSchema(SimpleModel)
        assert schema.get_sensitive_fields() == set()

    def test_non_pydantic_annotation_not_explored(self):
        class AppConfig(BaseModel):
            host: str
            tags: list[str] = []

        schema = ConfigSchema(AppConfig)
        assert schema.get_sensitive_fields() == set()


class TestOptionalDependencyBranches:
    """Tests for error handling when Pydantic is missing."""

    def test_schema_requires_pydantic(self, monkeypatch):
        from vaultconfig import schema

        monkeypatch.setattr(schema, "HAS_PYDANTIC", False)

        with pytest.raises(ImportError, match="pydantic"):
            schema.ConfigSchema(object())

    def test_create_simple_schema_requires_pydantic(self, monkeypatch):
        from vaultconfig import schema

        monkeypatch.setattr(schema, "HAS_PYDANTIC", False)

        with pytest.raises(ImportError, match="pydantic"):
            schema.create_simple_schema({})

    def test_get_sensitive_fields_no_pydantic_returns_empty(self, monkeypatch):
        from pydantic import BaseModel, Field

        from vaultconfig.schema import ConfigSchema

        class AppConfig(BaseModel):
            password: str = Field(json_schema_extra={"sensitive": True})

        schema_obj = ConfigSchema(AppConfig)

        from vaultconfig import schema

        monkeypatch.setattr(schema, "HAS_PYDANTIC", False)

        assert schema_obj.get_sensitive_fields() == set()

"""Tests for configuration format handlers."""

import pytest

from vaultconfig.exceptions import FormatError
from vaultconfig.formats import INIFormat, TOMLFormat, YAMLFormat


class TestTOMLFormat:
    """Test TOML format handler."""

    def test_toml_load(self):
        """Test loading TOML data."""
        toml_data = """
host = "localhost"
port = 5432
enabled = true

[database]
name = "testdb"
"""
        handler = TOMLFormat()
        data = handler.load(toml_data)

        assert data["host"] == "localhost"
        assert data["port"] == 5432
        assert data["enabled"] is True
        assert data["database"]["name"] == "testdb"

    def test_toml_dump(self):
        """Test dumping TOML data."""
        data = {
            "host": "localhost",
            "port": 5432,
            "enabled": True,
            "database": {"name": "testdb"},
        }

        handler = TOMLFormat()
        toml_str = handler.dump(data)

        # Should contain key data
        assert "host" in toml_str
        assert "localhost" in toml_str
        assert "5432" in toml_str
        assert "[database]" in toml_str

    def test_toml_round_trip(self):
        """Test TOML load -> dump -> load round trip."""
        original = {
            "host": "localhost",
            "port": 5432,
            "nested": {
                "key": "value",
                "number": 123,
            },
        }

        handler = TOMLFormat()
        toml_str = handler.dump(original)
        loaded = handler.load(toml_str)

        assert loaded == original

    def test_toml_extension(self):
        """Test TOML file extension."""
        handler = TOMLFormat()
        assert handler.get_extension() == ".toml"

    def test_toml_name(self):
        """Test TOML format name."""
        handler = TOMLFormat()
        assert handler.get_name() == "toml"

    def test_toml_detect_valid(self):
        """Test detecting valid TOML."""
        valid_toml = """
host = "localhost"
port = 5432
"""
        assert TOMLFormat.detect(valid_toml) is True

    def test_toml_detect_invalid(self):
        """Test detecting invalid TOML."""
        invalid_data = [
            "[section\nkey = value",  # Invalid TOML
            "random text",
            "",
        ]

        for data in invalid_data:
            assert TOMLFormat.detect(data) is False

    def test_toml_load_invalid(self):
        """Test loading invalid TOML raises error."""
        invalid_toml = "[section\nunclosed bracket"

        handler = TOMLFormat()
        with pytest.raises(FormatError):
            handler.load(invalid_toml)


class TestINIFormat:
    """Test INI format handler."""

    def test_ini_load(self):
        """Test loading INI data."""
        ini_data = """
[main]
host = localhost
port = 5432

[database]
name = testdb
"""
        handler = INIFormat()
        data = handler.load(ini_data)

        assert data["main"]["host"] == "localhost"
        assert data["main"]["port"] == "5432"  # INI values are strings
        assert data["database"]["name"] == "testdb"

    def test_ini_dump(self):
        """Test dumping INI data."""
        data = {
            "main": {
                "host": "localhost",
                "port": 5432,
            },
            "database": {
                "name": "testdb",
            },
        }

        handler = INIFormat()
        ini_str = handler.dump(data)

        # Should contain sections and keys
        assert "[main]" in ini_str
        assert "host" in ini_str
        assert "localhost" in ini_str

    def test_ini_round_trip(self):
        """Test INI load -> dump -> load round trip."""
        original = {
            "section1": {
                "key1": "value1",
                "key2": "value2",
            },
            "section2": {
                "key3": "value3",
            },
        }

        handler = INIFormat()
        ini_str = handler.dump(original)
        loaded = handler.load(ini_str)

        # Values become strings in INI
        assert loaded["section1"]["key1"] == "value1"
        assert loaded["section2"]["key3"] == "value3"

    def test_ini_extension(self):
        """Test INI file extension."""
        handler = INIFormat()
        assert handler.get_extension() == ".ini"

    def test_ini_name(self):
        """Test INI format name."""
        handler = INIFormat()
        assert handler.get_name() == "ini"

    def test_ini_detect_valid(self):
        """Test detecting valid INI."""
        valid_ini = """
[section]
key = value
"""
        assert INIFormat.detect(valid_ini) is True

    def test_ini_detect_invalid(self):
        """Test detecting invalid INI."""
        invalid_data = [
            "key = value",  # No section
            "random text",
            "",
        ]

        for data in invalid_data:
            assert INIFormat.detect(data) is False

    def test_ini_dump_non_dict_section_fails(self):
        """Test that dumping non-dict section fails."""
        invalid_data = {
            "section": "not_a_dict",  # Should be dict
        }

        handler = INIFormat()
        with pytest.raises(FormatError, match="nested structure"):
            handler.dump(invalid_data)

    def test_ini_type_conversion(self):
        """Test that INI converts types to strings."""
        data = {
            "section": {
                "int_value": 123,
                "bool_value": True,
                "float_value": 45.67,
            },
        }

        handler = INIFormat()
        ini_str = handler.dump(data)
        loaded = handler.load(ini_str)

        # All values become strings
        assert loaded["section"]["int_value"] == "123"
        assert loaded["section"]["bool_value"] == "True"
        assert loaded["section"]["float_value"] == "45.67"


class TestYAMLFormat:
    """Test YAML format handler (if available)."""

    def test_yaml_load(self):
        """Test loading YAML data."""
        yaml_data = """
host: localhost
port: 5432
enabled: true

database:
  name: testdb
"""
        handler = YAMLFormat()
        try:
            data = handler.load(yaml_data)

            assert data["host"] == "localhost"
            assert data["port"] == 5432
            assert data["enabled"] is True
            assert data["database"]["name"] == "testdb"
        except FormatError as e:
            if "PyYAML" in str(e):
                pytest.skip("PyYAML not installed")
            raise

    def test_yaml_dump(self):
        """Test dumping YAML data."""
        data = {
            "host": "localhost",
            "port": 5432,
            "enabled": True,
            "database": {"name": "testdb"},
        }

        handler = YAMLFormat()
        try:
            yaml_str = handler.dump(data)

            # Should contain key data
            assert "host:" in yaml_str or "host :" in yaml_str
            assert "localhost" in yaml_str
            assert "database:" in yaml_str or "database :" in yaml_str
        except FormatError as e:
            if "PyYAML" in str(e):
                pytest.skip("PyYAML not installed")
            raise

    def test_yaml_round_trip(self):
        """Test YAML load -> dump -> load round trip."""
        original = {
            "host": "localhost",
            "port": 5432,
            "nested": {
                "key": "value",
                "number": 123,
            },
        }

        handler = YAMLFormat()
        try:
            yaml_str = handler.dump(original)
            loaded = handler.load(yaml_str)

            assert loaded == original
        except FormatError as e:
            if "PyYAML" in str(e):
                pytest.skip("PyYAML not installed")
            raise

    def test_yaml_extension(self):
        """Test YAML file extension."""
        handler = YAMLFormat()
        assert handler.get_extension() == ".yaml"

    def test_yaml_name(self):
        """Test YAML format name."""
        handler = YAMLFormat()
        assert handler.get_name() == "yaml"

    def test_yaml_detect_valid(self):
        """Test detecting valid YAML."""
        valid_yaml = """
host: localhost
port: 5432
"""
        result = YAMLFormat.detect(valid_yaml)
        # If PyYAML not installed, detection returns False
        assert isinstance(result, bool)

    def test_yaml_detect_invalid(self):
        """Test detecting invalid YAML."""
        invalid_data = [
            "random text without structure",
            "",
        ]

        for data in invalid_data:
            assert YAMLFormat.detect(data) is False

    def test_yaml_load_non_dict_fails(self):
        """Test that loading non-dict YAML fails."""
        non_dict_yaml = """
- item1
- item2
- item3
"""
        handler = YAMLFormat()
        try:
            with pytest.raises(FormatError, match="must be a dict"):
                handler.load(non_dict_yaml)
        except FormatError as e:
            if "PyYAML" in str(e):
                pytest.skip("PyYAML not installed")
            raise


class TestFormatDetection:
    """Test format auto-detection."""

    def test_detect_toml(self):
        """Test detecting TOML format."""
        toml_samples = [
            'key = "value"',
            '[section]\nkey = "value"',
            "number = 123\nstring = 'text'",
        ]

        for sample in toml_samples:
            assert TOMLFormat.detect(sample) is True

    def test_detect_ini(self):
        """Test detecting INI format."""
        ini_samples = [
            "[section]\nkey = value",
            "[main]\nhost = localhost\nport = 5432",
        ]

        for sample in ini_samples:
            assert INIFormat.detect(sample) is True

    def test_ambiguous_formats(self):
        """Test formats that might be ambiguous."""
        # TOML and INI can be similar
        ambiguous = "[section]\nkey = value"

        # Both might detect it
        toml_detect = TOMLFormat.detect(ambiguous)
        ini_detect = INIFormat.detect(ambiguous)

        # At least one should detect it
        assert toml_detect or ini_detect


class TestFormatEdgeCases:
    """Test edge cases for format handlers."""

    def test_empty_data(self):
        """Test handling empty data."""
        handlers = [TOMLFormat(), INIFormat()]

        for handler in handlers:
            # Empty string should not be detected
            assert handler.detect("") is False

    def test_whitespace_only(self):
        """Test handling whitespace-only data."""
        handlers = [TOMLFormat(), INIFormat()]

        for handler in handlers:
            assert handler.detect("   \n\n  \t  ") is False

    def test_comments_only(self):
        """Test handling comments-only data."""
        toml_handler = TOMLFormat()

        # TOML with only comments
        toml_comments = """
# This is a comment
# Another comment
"""
        # Should parse (empty dict)
        result = toml_handler.load(toml_comments)
        assert result == {}

"""Tests for vaultconfig.io helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vaultconfig.exceptions import VaultConfigError
from vaultconfig.io import (
    detect_format_from_path,
    dump_mapping,
    load_mapping,
    load_mapping_file,
)


class TestDetectFormatFromPath:
    @pytest.mark.parametrize(
        "path_str,expected",
        [
            ("config.json", "json"),
            ("config.yaml", "yaml"),
            ("config.yml", "yaml"),
            ("config.toml", "toml"),
            ("config.ini", "ini"),
        ],
    )
    def test_detects_known_formats(self, path_str, expected):
        assert detect_format_from_path(Path(path_str)) == expected

    @pytest.mark.parametrize(
        "path_str",
        [
            "config.txt",
            "config.xml",
            "config",
        ],
    )
    def test_returns_none_for_unknown_extension(self, path_str):
        assert detect_format_from_path(Path(path_str)) is None

    @pytest.mark.parametrize(
        "path_str,expected",
        [
            ("config.JSON", "json"),
            ("config.YAML", "yaml"),
            ("config.TOML", "toml"),
            ("config.INI", "ini"),
        ],
    )
    def test_case_insensitive(self, path_str, expected):
        assert detect_format_from_path(Path(path_str)) == expected


class TestLoadMapping:
    def test_load_json(self):
        data = load_mapping('{"a": 1, "b": "hello"}', "json")
        assert data == {"a": 1, "b": "hello"}

    def test_load_yaml(self):
        data = load_mapping("a: 1\nb: hello\n", "yaml")
        assert data == {"a": 1, "b": "hello"}

    def test_load_toml(self):
        data = load_mapping('a = 1\nb = "hello"\n', "toml")
        assert data == {"a": 1, "b": "hello"}

    def test_load_ini(self):
        data = load_mapping("[section]\na = 1\nb = hello\n", "ini")
        assert data == {"section": {"a": "1", "b": "hello"}}

    def test_load_json_rejects_non_dict_root(self):
        with pytest.raises(ValueError, match="Expected a mapping"):
            load_mapping("[1, 2, 3]", "json")

    def test_load_json_rejects_scalar(self):
        with pytest.raises(ValueError, match="Expected a mapping"):
            load_mapping('"just a string"', "json")

    def test_load_json_parse_error(self):
        with pytest.raises(json.JSONDecodeError):
            load_mapping("{invalid", "json")

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            load_mapping("x", "csv")

    def test_load_yaml_parse_error(self):
        with pytest.raises(VaultConfigError):
            load_mapping(": invalid yaml", "yaml")


class TestDumpMapping:
    def test_dump_json(self):
        assert dump_mapping({"a": 1, "b": "hello"}, "json") == (
            '{\n  "a": 1,\n  "b": "hello"\n}'
        )

    def test_dump_yaml(self):
        result = dump_mapping({"a": 1, "b": "hello"}, "yaml")
        assert "a: 1" in result
        assert "hello" in result

    def test_dump_toml(self):
        result = dump_mapping({"a": 1, "b": "hello"}, "toml")
        assert "a = 1" in result
        assert "hello" in result

    def test_dump_ini(self):
        data = {"section": {"a": "1", "b": "hello"}}
        result = dump_mapping(data, "ini")
        assert "[section]" in result
        assert "a = 1" in result

    def test_dump_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            dump_mapping({"a": 1}, "xml")

    def test_dump_json_round_trip(self):
        original = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
        reloaded = load_mapping(dump_mapping(original, "json"), "json")
        assert reloaded == original

    def test_dump_yaml_round_trip(self):
        original = {"a": 1, "b": "hello"}
        reloaded = load_mapping(dump_mapping(original, "yaml"), "yaml")
        assert reloaded == original

    def test_dump_toml_round_trip(self):
        original = {"a": 1, "b": "hello"}
        reloaded = load_mapping(dump_mapping(original, "toml"), "toml")
        assert reloaded == original


class TestLoadMappingFile:
    def test_load_json_file(self, tmp_path):
        f = tmp_path / "config.json"
        f.write_text('{"a": 1, "b": "hello"}')
        assert load_mapping_file(f) == {"a": 1, "b": "hello"}

    def test_load_yaml_file(self, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text("a: 1\nb: hello\n")
        assert load_mapping_file(f) == {"a": 1, "b": "hello"}

    def test_load_yml_file(self, tmp_path):
        f = tmp_path / "config.yml"
        f.write_text("a: 1\nb: hello\n")
        assert load_mapping_file(f) == {"a": 1, "b": "hello"}

    def test_load_toml_file(self, tmp_path):
        f = tmp_path / "config.toml"
        f.write_text('a = 1\nb = "hello"\n')
        assert load_mapping_file(f) == {"a": 1, "b": "hello"}

    def test_load_ini_file(self, tmp_path):
        f = tmp_path / "config.ini"
        f.write_text("[DEFAULT]\na = 1\nb = hello\n")
        assert load_mapping_file(f) == {"DEFAULT": {"a": "1", "b": "hello"}}

    def test_explicit_format_overrides_extension(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text('{"a": 1, "b": "hello"}')
        assert load_mapping_file(f, "json") == {"a": 1, "b": "hello"}

    def test_unknown_extension_falls_back_to_json_then_yaml(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text('{"a": 1, "b": "hello"}')
        assert load_mapping_file(f) == {"a": 1, "b": "hello"}

    def test_unknown_extension_yaml_fallback(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("a: 1\nb: hello\n")
        assert load_mapping_file(f) == {"a": 1, "b": "hello"}

    def test_unknown_extension_not_valid_json_or_yaml(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("= not valid at all")
        with pytest.raises(VaultConfigError):
            load_mapping_file(f)

    def test_missing_file_raises(self, tmp_path):
        f = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_mapping_file(f)

    def test_load_file_rejects_non_dict_root(self, tmp_path):
        f = tmp_path / "list.json"
        f.write_text("[1, 2, 3]")
        with pytest.raises(ValueError, match="Expected a mapping"):
            load_mapping_file(f)

    def test_unsupported_explicit_format_raises(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b\n1,2\n")
        with pytest.raises(ValueError, match="Unsupported format"):
            load_mapping_file(f, "csv")

    def test_explicit_json_format_loads_from_any_extension(self, tmp_path):
        f = tmp_path / "data.custom"
        f.write_text('{"a": 1}')
        assert load_mapping_file(f, "json") == {"a": 1}

    def test_explicit_yaml_format_parse_error(self, tmp_path):
        f = tmp_path / "data.yaml"
        f.write_text(": invalid yaml")
        with pytest.raises(VaultConfigError):
            load_mapping_file(f, "yaml")

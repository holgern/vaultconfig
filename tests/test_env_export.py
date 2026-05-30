"""Tests for vaultconfig.env_export helpers."""

from __future__ import annotations

from vaultconfig.env_export import (
    build_env_vars,
    detect_shell,
    filter_dict,
    flatten_dict,
    format_env_export,
    format_nushell_load_env,
    shell_quote,
)


class TestFlattenDict:
    def test_flat_dict_unchanged(self):
        data = {"a": 1, "b": "hello"}
        assert flatten_dict(data) == {"a": 1, "b": "hello"}

    def test_nested_dict_flattened(self):
        data = {"database": {"host": "localhost", "port": 5432}}
        assert flatten_dict(data) == {
            "database.host": "localhost",
            "database.port": 5432,
        }

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": 1}}}
        assert flatten_dict(data) == {"a.b.c": 1}

    def test_preserves_value_types(self):
        data = {"x": True, "y": 3.14, "z": None, "nested": {"a": 42}}
        result = flatten_dict(data)
        assert result["x"] is True
        assert result["y"] == 3.14
        assert result["z"] is None
        assert result["nested.a"] == 42

    def test_empty_dict(self):
        assert flatten_dict({}) == {}

    def test_custom_separator(self):
        data = {"a": {"b": 1}}
        assert flatten_dict(data, sep="_") == {"a_b": 1}


class TestFilterDict:
    def test_no_filters_returns_original(self):
        data = {"a": 1, "b": {"c": 2}}
        assert filter_dict(data) == data
        assert filter_dict(data, include=None, exclude=None) == data

    def test_include_matches_top_level(self):
        data = {"db": {"host": "x"}, "api": {"key": "y"}, "debug": True}
        result = filter_dict(data, include=("db.*",))
        assert "db" in result
        assert "api" not in result
        assert "debug" not in result
        assert result["db"]["host"] == "x"

    def test_exclude_by_pattern(self):
        data = {"db": {"host": "x", "password": "secret"}}
        result = filter_dict(data, exclude=("*.password",))
        assert "db" in result
        assert "host" in result["db"]
        assert "password" not in result["db"]

    def test_exclude_takes_precedence(self):
        data = {"db": {"host": "x", "password": "secret"}}
        result = filter_dict(data, include=("db.*",), exclude=("*.password",))
        assert "host" in result["db"]
        assert "password" not in result["db"]

    def test_include_specific_keys(self):
        data = {"a": {"b": 1, "c": 2}, "d": 3}
        result = filter_dict(data, include=("a.b", "d"))
        assert "a" in result
        assert "b" in result["a"]
        assert "c" not in result["a"]
        assert "d" in result

    def test_wildcard_matching(self):
        data = {"db_host": "x", "db_port": 5432, "api_key": "y"}
        result = filter_dict(data, include=("db_*",))
        assert "db_host" in result
        assert "db_port" in result
        assert "api_key" not in result


class TestBuildEnvVars:
    def test_simple_conversion(self):
        data = {"host": "localhost", "port": "5432"}
        result = build_env_vars(data)
        assert result == {"HOST": "localhost", "PORT": "5432"}

    def test_with_prefix(self):
        data = {"host": "localhost"}
        result = build_env_vars(data, prefix="DB_")
        assert result == {"DB_HOST": "localhost"}

    def test_no_uppercase(self):
        data = {"host": "localhost"}
        result = build_env_vars(data, uppercase=False)
        assert result == {"host": "localhost"}

    def test_dot_to_underscore(self):
        data = {"database.host": "localhost"}
        result = build_env_vars(data)
        assert result == {"DATABASE_HOST": "localhost"}

    def test_hyphen_to_underscore(self):
        data = {"my-key": "value"}
        result = build_env_vars(data)
        assert result == {"MY_KEY": "value"}


class TestShellQuote:
    def test_simple_string(self):
        assert shell_quote("hello") == "'hello'"

    def test_string_with_spaces(self):
        assert shell_quote("hello world") == "'hello world'"

    def test_string_with_single_quote(self):
        result = shell_quote("it's")
        assert result == "'it'\\''s'"

    def test_empty_string(self):
        assert shell_quote("") == "''"

    def test_string_with_special_chars(self):
        quoted = shell_quote("a$b`c")
        # Inside single quotes, special chars are literal
        assert quoted.startswith("'")
        assert quoted.endswith("'")
        assert "a$b`c" in quoted


class TestFormatEnvExport:
    def test_bash_format(self):
        result = format_env_export("KEY", "value", "bash")
        assert result == "export KEY='value'"

    def test_zsh_format(self):
        result = format_env_export("KEY", "value", "zsh")
        assert result == "export KEY='value'"

    def test_fish_format(self):
        result = format_env_export("KEY", "value", "fish")
        assert result == "set -gx KEY 'value'"

    def test_nushell_format(self):
        result = format_env_export("KEY", "value", "nushell")
        assert result == "$env.KEY = 'value'"

    def test_powershell_format(self):
        result = format_env_export("KEY", "value", "powershell")
        assert result == "$env:KEY = 'value'"

    def test_nushell_single_quote_escaping(self):
        result = format_env_export("KEY", "it's", "nushell")
        assert result == "$env.KEY = 'it''s'"

    def test_powershell_single_quote_escaping(self):
        result = format_env_export("KEY", "it's", "powershell")
        assert result == "$env:KEY = 'it''s'"

    def test_unknown_shell_falls_back_to_bash(self):
        result = format_env_export("KEY", "value", "unknown")
        assert result == "export KEY='value'"


class TestFormatNushellLoadEnv:
    def test_empty_vars(self):
        assert format_nushell_load_env({}) == "{}"

    def test_single_var(self):
        result = format_nushell_load_env({"KEY": "value"})
        assert '"KEY": "value"' in result
        assert result.startswith("{")
        assert result.endswith("}")

    def test_multiple_vars(self):
        result = format_nushell_load_env({"A": "1", "B": "2"})
        assert '"A": "1"' in result
        assert '"B": "2"' in result


class TestDetectShell:
    def test_detect_bash_from_shell_env(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/bin/bash")
        assert detect_shell() == "bash"

    def test_detect_zsh_from_shell_env(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/usr/bin/zsh")
        assert detect_shell() == "zsh"

    def test_detect_fish_from_shell_env(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/usr/bin/fish")
        assert detect_shell() == "fish"

    def test_detect_nu_as_nushell(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/usr/bin/nu")
        assert detect_shell() == "nushell"

    def test_detect_nushell_from_shell_env(self, monkeypatch):
        monkeypatch.setenv("SHELL", "/usr/bin/nushell")
        assert detect_shell() == "nushell"

    def test_detect_powershell(self, monkeypatch):
        monkeypatch.delenv("SHELL", raising=False)
        monkeypatch.setenv("PSModulePath", "/some/path")
        assert detect_shell() == "powershell"

    def test_default_to_bash(self, monkeypatch):
        monkeypatch.delenv("SHELL", raising=False)
        monkeypatch.delenv("PSModulePath", raising=False)
        assert detect_shell() == "bash"

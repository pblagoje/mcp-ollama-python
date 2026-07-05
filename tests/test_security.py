"""Security validation tests."""

import os

import pytest

from mcp_ollama_python.security import (
    ALLOWED_ENV_VARS,
    is_execute_enabled,
    validate_code_payload,
    validate_env_var_key,
    validate_model_name,
    validate_ollama_host,
)


class TestValidateOllamaHost:
    def test_default_localhost_ok(self):
        assert validate_ollama_host("http://127.0.0.1:11434") == "http://127.0.0.1:11434"

    def test_remote_blocked_by_default(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_ALLOW_REMOTE_HOST", raising=False)
        with pytest.raises(ValueError, match="OLLAMA_ALLOW_REMOTE_HOST"):
            validate_ollama_host("http://192.168.1.10:11434")

    def test_remote_allowed_with_env(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_ALLOW_REMOTE_HOST", "1")
        assert (
            validate_ollama_host("http://192.168.1.10:11434")
            == "http://192.168.1.10:11434"
        )

    def test_rejects_credentials_in_url(self):
        with pytest.raises(ValueError, match="credentials"):
            validate_ollama_host("http://user:pass@127.0.0.1:11434")

    def test_rejects_metadata_ip_when_remote(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_ALLOW_REMOTE_HOST", "1")
        with pytest.raises(ValueError, match="metadata"):
            validate_ollama_host("http://169.254.169.254/")

    def test_rejects_path_in_host(self):
        with pytest.raises(ValueError, match="path"):
            validate_ollama_host("http://127.0.0.1:11434/api/tags")


class TestExecuteGating:
    def test_execute_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_EXECUTE_ENABLED", raising=False)
        assert is_execute_enabled() is False

    def test_execute_enabled_with_env(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_EXECUTE_ENABLED", "1")
        assert is_execute_enabled() is True


class TestEnvAllowlist:
    def test_allowed_keys(self):
        for key in ALLOWED_ENV_VARS:
            assert validate_env_var_key(key) == key

    def test_rejects_unknown_key(self):
        with pytest.raises(ValueError, match="Unsupported"):
            validate_env_var_key("PATH")


class TestModelAndCodeValidation:
    def test_valid_model_name(self):
        assert validate_model_name("llama3.1:latest") == "llama3.1:latest"

    def test_invalid_model_name(self):
        with pytest.raises(ValueError):
            validate_model_name("../etc/passwd")

    def test_code_null_byte_rejected(self):
        with pytest.raises(ValueError, match="null"):
            validate_code_payload("print('x\x00')")

    def test_code_size_limit(self):
        with pytest.raises(ValueError, match="maximum size"):
            validate_code_payload("x" * 70_000)

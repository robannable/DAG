"""Tests for configuration utilities"""
import pytest
import json
from utils import config as config_module
from utils.config import (
    load_artefact_categories,
    load_prompt_instructions,
    load_model_config,
    enabled_providers,
)


def test_load_artefact_categories():
    """Test loading artefact categories from JSON"""
    categories = load_artefact_categories()

    assert isinstance(categories, list)
    assert len(categories) > 0
    assert "Device/Object" in categories
    assert "Personal/Intimate" in categories


def test_load_prompt_instructions():
    """Test loading prompt instructions"""
    instructions = load_prompt_instructions()

    assert isinstance(instructions, str)
    assert len(instructions) > 0
    assert "artefact" in instructions.lower()


def test_load_model_config():
    """Test loading the default provider's model configuration"""
    config = load_model_config()

    assert isinstance(config, dict)
    assert "model" in config
    assert "max_tokens" in config
    assert "api_endpoint" in config


def test_load_model_config_named_provider():
    """A named provider is loaded regardless of current_provider"""
    config = load_model_config("openrouter")

    assert config["provider"] == "openrouter"
    assert config["api_key_env"] == "OPENROUTER_API_KEY"


def test_load_model_config_returns_copy():
    """Callers mutate the returned dict (model choice); it must not leak"""
    first = load_model_config("anthropic")
    first["model"] = "changed"

    assert load_model_config("anthropic")["model"] != "changed"


def test_anthropic_default_omits_temperature():
    """Claude 5 models 400 on temperature, so the shipped config disables it"""
    config = load_model_config("anthropic")

    assert config["model"] == "claude-sonnet-5"
    assert config["supports_temperature"] is False


def test_enabled_providers_defaults_to_all(monkeypatch):
    monkeypatch.delenv("DAG_PROVIDERS", raising=False)
    config = {"providers": {"anthropic": {}, "openrouter": {}, "ollama": {}}}

    assert enabled_providers(config) == ["anthropic", "openrouter", "ollama"]


def test_enabled_providers_filters_by_env(monkeypatch):
    monkeypatch.setenv("DAG_PROVIDERS", "openrouter, Anthropic")
    config = {"providers": {"anthropic": {}, "openrouter": {}, "ollama": {}}}

    # Config order is kept, case and spaces ignored
    assert enabled_providers(config) == ["anthropic", "openrouter"]


def test_enabled_providers_ignores_unknown_only(monkeypatch):
    """A typo'd env var must not leave the UI with no providers"""
    monkeypatch.setenv("DAG_PROVIDERS", "antropic")
    config = {"providers": {"anthropic": {}, "ollama": {}}}

    assert enabled_providers(config) == ["anthropic", "ollama"]


def test_load_model_config_with_missing_file(tmp_path, monkeypatch):
    """Test that load_model_config returns default when file is missing"""
    monkeypatch.setattr(
        config_module, "MODEL_CONFIG_PATH", tmp_path / "missing.json"
    )

    config = load_model_config()

    assert isinstance(config, dict)
    assert "model" in config
    assert "max_tokens" in config

"""Tests for configuration utilities"""
import pytest
import json
import os
from utils.config import (
    load_artefact_categories,
    load_prompt_instructions,
    load_model_config,
    save_model_config,
    update_ollama_model
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
    """Test loading model configuration"""
    config = load_model_config()

    assert isinstance(config, dict)
    assert "model" in config
    assert "max_tokens" in config
    assert "temperature" in config
    assert "api_endpoint" in config


def test_save_model_config(tmp_path, monkeypatch):
    """Test saving model configuration"""
    # Create a temporary config file
    config_file = tmp_path / "model_config.json"
    test_config = {
        "current_provider": "anthropic",
        "providers": {
            "anthropic": {"model": "test-model"},
            "ollama": {"model": "test-ollama"}
        }
    }

    with open(config_file, 'w') as f:
        json.dump(test_config, f)

    # Monkeypatch to use temp file
    monkeypatch.chdir(tmp_path)

    # Save new provider
    save_model_config("ollama")

    # Verify it was saved
    with open(config_file, 'r') as f:
        saved_config = json.load(f)

    assert saved_config['current_provider'] == "ollama"


def test_update_ollama_model(tmp_path, monkeypatch):
    """Test updating Ollama model"""
    # Create a temporary config file
    config_file = tmp_path / "model_config.json"
    test_config = {
        "current_provider": "ollama",
        "providers": {
            "anthropic": {"model": "test-model"},
            "ollama": {"model": "old-model"}
        }
    }

    with open(config_file, 'w') as f:
        json.dump(test_config, f)

    # Monkeypatch to use temp file
    monkeypatch.chdir(tmp_path)

    # Update model
    update_ollama_model("new-model")

    # Verify it was updated
    with open(config_file, 'r') as f:
        saved_config = json.load(f)

    assert saved_config['providers']['ollama']['model'] == "new-model"


def test_load_model_config_with_missing_file(tmp_path, monkeypatch):
    """Test that load_model_config returns default when file is missing"""
    # Change to empty directory
    monkeypatch.chdir(tmp_path)

    # Should return default config without crashing
    config = load_model_config()

    assert isinstance(config, dict)
    assert "model" in config
    assert "max_tokens" in config

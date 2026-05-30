"""Tests for API providers"""
import pytest
from unittest.mock import Mock
from api.providers import (
    prepare_request_data,
    extract_response
)


def test_prepare_request_data_anthropic():
    """Test request preparation for Anthropic"""
    model_config = {
        "provider": "anthropic",
        "model": "claude-sonnet-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    data = prepare_request_data(
        "Test prompt",
        model_config,
        "project",
        "bio",
        "themes"
    )

    assert data["model"] == "claude-sonnet-4"
    assert data["max_tokens"] == 4000
    assert data["temperature"] == 0.7
    assert "system" in data
    assert isinstance(data["system"], list)
    assert data["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "messages" in data
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "user"


def test_prepare_request_data_ollama():
    """Test request preparation for Ollama"""
    model_config = {
        "provider": "ollama",
        "model": "llama3.1",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    data = prepare_request_data(
        "Test prompt",
        model_config,
        "project",
        "bio",
        "themes"
    )

    assert data["model"] == "llama3.1"
    assert data["stream"] is False
    assert "messages" in data
    assert "options" in data
    assert data["options"]["temperature"] == 0.7


def test_prepare_request_data_unsupported_provider():
    """Unsupported providers should fail loudly"""
    model_config = {
        "provider": "openai",
        "model": "gpt-4",
        "max_tokens": 4000,
        "temperature": 0.7,
    }

    with pytest.raises(ValueError, match="Unsupported provider"):
        prepare_request_data(
            "Test prompt", model_config, "project", "bio", "themes"
        )


def test_prepare_request_data_with_custom_temperature():
    """Test request preparation with custom temperature"""
    model_config = {
        "provider": "anthropic",
        "model": "claude-sonnet-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    data = prepare_request_data(
        "Test prompt",
        model_config,
        "project",
        "bio",
        "themes",
        temperature=0.5
    )

    assert data["temperature"] == 0.5


def test_extract_response_anthropic():
    """Test response extraction for Anthropic"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "content": [{"text": "Generated content"}]
    }

    model_config = {"provider": "anthropic"}

    content = extract_response(mock_response, model_config)
    assert content == "Generated content"


def test_extract_response_ollama():
    """Test response extraction for Ollama"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "message": {"content": "Generated content"}
    }

    model_config = {"provider": "ollama"}

    content = extract_response(mock_response, model_config)
    assert content == "Generated content"


def test_extract_response_error_handling():
    """Test response extraction error handling"""
    mock_response = Mock()
    mock_response.json.return_value = {"unexpected": "format"}

    model_config = {"provider": "anthropic"}

    content = extract_response(mock_response, model_config)
    assert "Error parsing response" in content

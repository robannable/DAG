"""Tests for API providers"""
import pytest
from unittest.mock import Mock, patch
from api.providers import (
    calculate_max_tokens,
    prepare_request_data,
    extract_response
)


def test_calculate_max_tokens_simple():
    """Test token calculation for simple input"""
    tokens = calculate_max_tokens("short", "bio", "themes")
    assert tokens == 1600


def test_calculate_max_tokens_complex():
    """Test token calculation for complex input"""
    long_text = "x" * 500
    tokens = calculate_max_tokens(long_text, long_text, long_text)
    assert tokens == 1400


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


def test_prepare_request_data_openai():
    """Test request preparation for OpenAI/Perplexity"""
    model_config = {
        "provider": "openai",
        "model": "gpt-4",
        "max_tokens": 4000,
        "temperature": 0.7,
        "top_p": 0.9,
        "presence_penalty": 0.1
    }

    data = prepare_request_data(
        "Test prompt",
        model_config,
        "project",
        "bio",
        "themes"
    )

    assert data["model"] == "gpt-4"
    assert "messages" in data
    assert data["temperature"] == 0.7
    assert data["top_p"] == 0.9
    assert data["presence_penalty"] == 0.1


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


def test_extract_response_openai():
    """Test response extraction for OpenAI/Perplexity"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Generated content"}}]
    }

    model_config = {"provider": "openai"}

    content = extract_response(mock_response, model_config)
    assert content == "Generated content"


def test_extract_response_error_handling():
    """Test response extraction error handling"""
    mock_response = Mock()
    mock_response.json.return_value = {"unexpected": "format"}

    model_config = {"provider": "anthropic"}

    content = extract_response(mock_response, model_config)
    assert "Error parsing response" in content

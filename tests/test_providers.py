"""Tests for API providers"""
import pytest
from unittest.mock import Mock
import api.providers as providers_module
from api.providers import (
    prepare_request_data,
    extract_response,
    generate_artefact,
    stream_artefact,
    consume_anthropic_stream,
)


ANTHROPIC_CFG = {
    "provider": "anthropic",
    "model": "claude-sonnet-4-6",
    "max_tokens": 4000,
    "temperature": 0.7,
    "api_endpoint": "https://example.test/v1/messages",
    "api_key_env": "ANTHROPIC_API_KEY",
    "headers": {"Content-Type": "application/json"},
}


def test_generate_artefact_http_error_is_error_prefixed(monkeypatch):
    """A non-200 response must return an 'Error'-prefixed string.

    DAG.py gates display/save on ``not result.startswith("Error")``, so any
    failure that doesn't use that prefix is silently treated as a successful
    artefact. This locks the contract.
    """
    class FakeResponse:
        status_code = 404
        text = '{"type":"error","error":{"message":"model not found"}}'

        def json(self):
            return {}

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        providers_module, "make_streaming_request_with_retry",
        lambda *a, **k: FakeResponse()
    )

    result = generate_artefact(
        "desc", "2030", "bios", "themes", "loc",
        {"category": "Device/Object", "items": ["Device/Object"]},
        ANTHROPIC_CFG, "closing instruction",
    )

    assert result.startswith("Error")
    assert "404" in result


def test_generate_artefact_streams_text(monkeypatch):
    """A 200 streaming response is accumulated into the full artefact text."""
    class FakeStream:
        status_code = 200

        def iter_lines(self, decode_unicode=False):
            yield 'data: {"type":"message_start"}'
            yield 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello "}}'
            yield ''  # keep-alive blank line
            yield 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"world"}}'
            yield 'data: {"type":"message_stop"}'

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        providers_module, "make_streaming_request_with_retry",
        lambda *a, **k: FakeStream()
    )

    result = generate_artefact(
        "desc", "2030", "bios", "themes", "loc",
        {"category": "Device/Object", "items": ["Device/Object"]},
        ANTHROPIC_CFG, "closing instruction",
    )

    assert result == "Hello world"


def test_stream_artefact_yields_incremental_chunks(monkeypatch):
    """stream_artefact yields each text delta separately for live rendering."""
    class FakeStream:
        status_code = 200

        def iter_lines(self, decode_unicode=False):
            yield 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello "}}'
            yield 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"world"}}'

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        providers_module, "make_streaming_request_with_retry",
        lambda *a, **k: FakeStream()
    )

    chunks = list(stream_artefact(
        "desc", "2030", "bios", "themes", "loc",
        {"category": "Device/Object", "items": ["Device/Object"]},
        ANTHROPIC_CFG, "closing instruction",
    ))

    assert chunks == ["Hello ", "world"]


def test_stream_artefact_yields_single_error_chunk_when_key_missing(monkeypatch):
    """A setup failure yields exactly one 'Error'-prefixed chunk."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    chunks = list(stream_artefact(
        "desc", "2030", "bios", "themes", "loc",
        {"category": "Device/Object", "items": ["Device/Object"]},
        ANTHROPIC_CFG, "closing instruction",
    ))

    assert len(chunks) == 1
    assert chunks[0].startswith("Error")


def test_consume_anthropic_stream_concatenates_text_deltas():
    """The SSE parser extracts and joins text_delta events, ignoring others."""
    class FakeStream:
        def iter_lines(self, decode_unicode=False):
            yield 'event: content_block_delta'  # non-data line ignored
            yield 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"abc"}}'
            yield 'data: {"type":"ping"}'  # ignored
            yield 'data: not-json'  # malformed, skipped
            yield 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"def"}}'

    assert consume_anthropic_stream(FakeStream()) == "abcdef"


def test_consume_anthropic_stream_surfaces_error_event():
    """An error event in the stream returns an 'Error'-prefixed string."""
    class FakeStream:
        def iter_lines(self, decode_unicode=False):
            yield 'data: {"type":"error","error":{"message":"overloaded"}}'

    result = consume_anthropic_stream(FakeStream())
    assert result.startswith("Error")
    assert "overloaded" in result


def test_prepare_request_data_anthropic():
    """Test request preparation for Anthropic"""
    model_config = {
        "provider": "anthropic",
        "model": "claude-sonnet-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    data = prepare_request_data("Test prompt", model_config)

    assert data["model"] == "claude-sonnet-4"
    assert data["max_tokens"] == 4000
    assert data["temperature"] == 0.7
    assert data["stream"] is True
    assert "system" in data
    assert isinstance(data["system"], list)
    assert data["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "messages" in data
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "user"
    # Dynamic prompt is passed through verbatim; static text stays in system
    assert data["messages"][0]["content"] == "Test prompt"


def test_prepare_request_data_ollama():
    """Test request preparation for Ollama"""
    model_config = {
        "provider": "ollama",
        "model": "llama3.1",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    data = prepare_request_data("Test prompt", model_config)

    assert data["model"] == "llama3.1"
    assert data["stream"] is False
    assert "messages" in data
    assert "options" in data
    assert data["options"]["temperature"] == 0.7
    # System carries the static scaffolding, user carries the dynamic prompt
    assert data["messages"][0]["role"] == "system"
    assert data["messages"][1]["content"] == "Test prompt"


def test_prepare_request_data_unsupported_provider():
    """Unsupported providers should fail loudly"""
    model_config = {
        "provider": "openai",
        "model": "gpt-4",
        "max_tokens": 4000,
        "temperature": 0.7,
    }

    with pytest.raises(ValueError, match="Unsupported provider"):
        prepare_request_data("Test prompt", model_config)


def test_prepare_request_data_with_custom_temperature():
    """Test request preparation with custom temperature"""
    model_config = {
        "provider": "anthropic",
        "model": "claude-sonnet-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    data = prepare_request_data("Test prompt", model_config, temperature=0.5)

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

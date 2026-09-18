"""Tests for the OpenRouter provider, error chunks, and temperature handling"""
import api.providers as providers_module
from api.providers import (
    ErrorChunk,
    iter_anthropic_stream,
    iter_openai_stream,
    parse_openrouter_models,
    prepare_request_data,
    resolve_temperature,
    stream_artefact,
)
from api.vision_providers import (
    prepare_vision_request_anthropic,
    prepare_vision_request_openrouter,
    stream_artefact_with_vision,
)

OPENROUTER_CFG = {
    "provider": "openrouter",
    "model": "google/gemini-3.8-flash",
    "max_tokens": 8000,
    "temperature": 0.7,
    "api_endpoint": "https://example.test/api/v1/chat/completions",
    "api_key_env": "OPENROUTER_API_KEY",
    "headers": {"Content-Type": "application/json", "X-Title": "DAG"},
}

SONNET5_CFG = {
    "provider": "anthropic",
    "model": "claude-sonnet-5",
    "max_tokens": 4000,
    "supports_temperature": False,
    "supports_vision": True,
    "thinking": {"type": "disabled"},
    "api_endpoint": "https://example.test/v1/messages",
    "api_key_env": "ANTHROPIC_API_KEY",
    "headers": {"Content-Type": "application/json"},
}

TYPE = {"category": "Device/Object", "items": ["Device/Object"]}
IMAGES = [{"name": "a.png", "base64": "QUJD", "media_type": "image/png", "size": 3}]


class FakeStream:
    status_code = 200

    def __init__(self, lines):
        self._lines = lines

    def iter_lines(self, decode_unicode=False):
        yield from self._lines


def _capture_request(monkeypatch, lines):
    """Patch the HTTP layer; return a dict that receives headers and data"""
    seen = {}

    def fake_post(url, headers, data, **kwargs):
        seen.update(url=url, headers=headers, data=data)
        return FakeStream(lines)

    monkeypatch.setattr(providers_module, "make_streaming_request_with_retry", fake_post)
    return seen


# --- temperature -----------------------------------------------------------

def test_resolve_temperature_disabled_returns_none():
    assert resolve_temperature(SONNET5_CFG, 0.9) is None


def test_resolve_temperature_prefers_override():
    assert resolve_temperature(OPENROUTER_CFG, 0.2) == 0.2
    assert resolve_temperature(OPENROUTER_CFG) == 0.7


def test_anthropic_request_omits_temperature_and_passes_thinking():
    data = prepare_request_data("prompt", SONNET5_CFG, temperature=0.5)

    assert "temperature" not in data
    assert data["thinking"] == {"type": "disabled"}
    assert data["model"] == "claude-sonnet-5"


# --- OpenRouter request + stream -------------------------------------------

def test_prepare_request_data_openrouter():
    data = prepare_request_data("Test prompt", OPENROUTER_CFG, temperature=0.4)

    assert data["model"] == "google/gemini-3.8-flash"
    assert data["stream"] is True
    assert data["max_tokens"] == 8000
    assert data["temperature"] == 0.4
    assert data["messages"][0]["role"] == "system"
    assert data["messages"][1] == {"role": "user", "content": "Test prompt"}
    assert "system" not in data  # OpenAI shape: system is a message


def test_prepare_request_data_openrouter_no_temperature_support():
    cfg = dict(OPENROUTER_CFG, supports_temperature=False)

    assert "temperature" not in prepare_request_data("p", cfg, temperature=0.4)


def test_iter_openai_stream_skips_comments_and_stops_at_done():
    stream = FakeStream([
        ": OPENROUTER PROCESSING",
        "",
        'data: {"choices":[{"delta":{"role":"assistant","content":""}}]}',
        'data: {"choices":[{"delta":{"content":"Hello "}}]}',
        'data: {"choices":[{"delta":{"reasoning":"hmm"}}]}',
        "data: not-json",
        'data: {"choices":[{"delta":{"content":"world"},"finish_reason":"stop"}]}',
        "data: [DONE]",
        'data: {"choices":[{"delta":{"content":"after done"}}]}',
    ])

    assert list(iter_openai_stream(stream)) == ["Hello ", "world"]


def test_iter_openai_stream_mid_stream_error_is_error_chunk():
    stream = FakeStream([
        'data: {"choices":[{"delta":{"content":"partial"}}]}',
        'data: {"error":{"code":"server_error","message":"Provider disconnected"},'
        '"choices":[{"delta":{"content":""},"finish_reason":"error"}]}',
        'data: {"choices":[{"delta":{"content":"never"}}]}',
    ])

    chunks = list(iter_openai_stream(stream))

    assert chunks[0] == "partial"
    assert len(chunks) == 2
    assert isinstance(chunks[1], ErrorChunk)
    assert "Provider disconnected" in chunks[1]


def test_iter_anthropic_stream_error_is_error_chunk():
    chunks = list(iter_anthropic_stream(FakeStream([
        'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"x"}}',
        'data: {"type":"error","error":{"message":"overloaded"}}',
    ])))

    assert chunks[0] == "x" and not isinstance(chunks[0], ErrorChunk)
    assert isinstance(chunks[1], ErrorChunk)


def test_stream_artefact_openrouter_uses_bearer_auth(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    seen = _capture_request(monkeypatch, [
        'data: {"choices":[{"delta":{"content":"Artefact"}}]}',
        "data: [DONE]",
    ])

    chunks = list(stream_artefact(
        "desc", "2030", "bios", "themes", "loc", TYPE, OPENROUTER_CFG, "closing",
    ))

    assert chunks == ["Artefact"]
    assert seen["headers"]["Authorization"] == "Bearer or-key"
    assert "x-api-key" not in seen["headers"]
    assert seen["headers"]["X-Title"] == "DAG"
    # Config headers are copied, never mutated
    assert "Authorization" not in OPENROUTER_CFG["headers"]


def test_stream_artefact_openrouter_missing_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    chunks = list(stream_artefact(
        "desc", "2030", "bios", "themes", "loc", TYPE, OPENROUTER_CFG, "closing",
    ))

    assert len(chunks) == 1
    assert isinstance(chunks[0], ErrorChunk)
    assert "OPENROUTER_API_KEY" in chunks[0]


def test_stream_artefact_http_error_is_error_chunk(monkeypatch):
    class NotFound:
        status_code = 404
        text = '{"error":{"message":"No endpoints found"}}'

    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setattr(
        providers_module, "make_streaming_request_with_retry", lambda *a, **k: NotFound()
    )

    chunks = list(stream_artefact(
        "desc", "2030", "bios", "themes", "loc", TYPE, OPENROUTER_CFG, "closing",
    ))

    assert len(chunks) == 1 and isinstance(chunks[0], ErrorChunk)
    assert "404" in chunks[0]


# --- model list ------------------------------------------------------------

def test_parse_openrouter_models():
    payload = {"data": [
        {
            "id": "anthropic/claude-sonnet-5",
            "name": "Anthropic: Claude Sonnet 5",
            "architecture": {"input_modalities": ["text", "image"], "output_modalities": ["text"]},
            "pricing": {"prompt": "0.000002", "completion": "0.00001"},
            "supported_parameters": ["max_tokens", "reasoning"],
        },
        {
            "id": "anthropic/claude-sonnet-5:batch",
            "name": "Anthropic: Claude Sonnet 5 (batch)",
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
        },
        {
            "id": "black-forest/flux",
            "name": "Image model",
            "architecture": {"input_modalities": ["text"], "output_modalities": ["image"]},
        },
        {
            "id": "deepseek/deepseek-v4-flash",
            "name": "DeepSeek: V4 Flash",
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "pricing": {"prompt": "0", "completion": "0"},
            "supported_parameters": ["temperature", "max_tokens"],
        },
        {
            "id": "openrouter/auto",
            "name": "Auto Router",
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "pricing": {"prompt": "-1", "completion": "-1"},
        },
    ]}

    models = parse_openrouter_models(payload)
    by_id = {m["id"]: m for m in models}

    assert [m["name"] for m in models] == [
        "Anthropic: Claude Sonnet 5", "Auto Router", "DeepSeek: V4 Flash"
    ]
    sonnet = by_id["anthropic/claude-sonnet-5"]
    assert sonnet["supports_vision"] is True
    assert sonnet["supports_temperature"] is False
    assert round(sonnet["prompt_price"], 6) == 2.0
    assert round(sonnet["completion_price"], 6) == 10.0
    assert by_id["deepseek/deepseek-v4-flash"]["supports_temperature"] is True
    assert by_id["openrouter/auto"]["prompt_price"] is None


# --- vision ----------------------------------------------------------------

def test_prepare_vision_request_openrouter():
    data = prepare_vision_request_openrouter("Test prompt", IMAGES, OPENROUTER_CFG)

    user = data["messages"][1]["content"]
    assert data["messages"][0]["role"] == "system"
    assert user[0] == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,QUJD"},
    }
    assert user[1]["type"] == "text" and "Test prompt" in user[1]["text"]
    assert data["temperature"] == 0.7


def test_prepare_vision_request_anthropic_sonnet5():
    data = prepare_vision_request_anthropic("p", IMAGES, SONNET5_CFG, temperature=0.3)

    assert "temperature" not in data
    assert data["thinking"] == {"type": "disabled"}


def test_vision_rejects_model_without_image_input(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    cfg = dict(OPENROUTER_CFG, supports_vision=False)

    chunks = list(stream_artefact_with_vision(
        "desc", "2030", "bios", "themes", "loc", TYPE, IMAGES, cfg, "closing",
    ))

    assert len(chunks) == 1 and isinstance(chunks[0], ErrorChunk)
    assert "cannot read images" in chunks[0]


def test_vision_streams_through_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    seen = _capture_request(monkeypatch, [
        'data: {"choices":[{"delta":{"content":"Seen it"}}]}',
        "data: [DONE]",
    ])
    cfg = dict(OPENROUTER_CFG, supports_vision=True)

    chunks = list(stream_artefact_with_vision(
        "desc", "2030", "bios", "themes", "loc", TYPE, IMAGES, cfg, "closing",
    ))

    assert chunks == ["Seen it"]
    assert seen["data"]["messages"][1]["content"][0]["type"] == "image_url"

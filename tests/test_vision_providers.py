"""Tests for vision API providers - Anthropic only"""
import pytest
from unittest.mock import Mock
from api.vision_providers import prepare_vision_request_anthropic


def test_prepare_vision_request_anthropic():
    """Test preparing Anthropic vision request"""
    model_config = {
        "provider": "anthropic",
        "model": "claude-sonnet-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    images = [
        {
            'name': 'test.png',
            'base64': 'base64data',
            'media_type': 'image/png',
            'size': 1024
        }
    ]

    data = prepare_vision_request_anthropic(
        "Test prompt",
        images,
        model_config
    )

    assert data["model"] == "claude-sonnet-4"
    assert data["max_tokens"] == 4000
    assert "system" in data
    assert "messages" in data
    assert len(data["messages"]) == 1
    assert "content" in data["messages"][0]

    # Check content has both image and text
    content = data["messages"][0]["content"]
    assert isinstance(content, list)
    assert len(content) == 2  # 1 image + 1 text

    # Check image structure
    assert content[0]["type"] == "image"
    assert content[0]["source"]["type"] == "base64"
    assert content[0]["source"]["media_type"] == "image/png"

    # Check text structure
    assert content[1]["type"] == "text"
    assert "Test prompt" in content[1]["text"]


def test_prepare_vision_request_multiple_images():
    """Test preparing request with multiple images"""
    model_config = {
        "provider": "anthropic",
        "model": "claude-sonnet-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    images = [
        {'name': 'test1.png', 'base64': 'data1', 'media_type': 'image/png', 'size': 1024},
        {'name': 'test2.jpg', 'base64': 'data2', 'media_type': 'image/jpeg', 'size': 2048},
        {'name': 'test3.png', 'base64': 'data3', 'media_type': 'image/png', 'size': 1536}
    ]

    data = prepare_vision_request_anthropic(
        "Test prompt",
        images,
        model_config
    )

    content = data["messages"][0]["content"]
    # Should have 3 images + 1 text = 4 items
    assert len(content) == 4

    # Check all images are present
    image_items = [item for item in content if item["type"] == "image"]
    assert len(image_items) == 3


def test_prepare_vision_request_custom_temperature():
    """Test preparing request with custom temperature"""
    model_config = {
        "provider": "anthropic",
        "model": "claude-sonnet-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }

    images = [
        {'name': 'test.png', 'base64': 'data', 'media_type': 'image/png', 'size': 1024}
    ]

    data = prepare_vision_request_anthropic(
        "Test prompt",
        images,
        model_config,
        temperature=0.5
    )

    assert data["temperature"] == 0.5

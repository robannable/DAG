"""Tests for image processing utilities"""
import pytest
import io
from PIL import Image
from utils.image_processing import (
    validate_image,
    resize_image_if_needed,
    encode_image_to_base64,
    get_image_media_type,
    estimate_vision_tokens,
    create_image_description
)


def create_test_image(width=800, height=600, format='PNG'):
    """Create a test image in memory"""
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    return img_bytes.getvalue()


def test_validate_image_valid():
    """Test validating a valid image"""
    image_bytes = create_test_image()
    is_valid, error_msg = validate_image(image_bytes)

    assert is_valid is True
    assert error_msg == ""


def test_validate_image_too_large():
    """Test validating an oversized image"""
    # Create a large image (simulate)
    large_bytes = b'x' * (25 * 1024 * 1024)  # 25 MB

    is_valid, error_msg = validate_image(large_bytes, max_size_mb=20)

    assert is_valid is False
    assert "too large" in error_msg.lower()


def test_validate_image_invalid():
    """Test validating invalid image data"""
    invalid_bytes = b'not an image'

    is_valid, error_msg = validate_image(invalid_bytes)

    assert is_valid is False
    assert "invalid" in error_msg.lower() or "error" in error_msg.lower()


def test_resize_image_no_resize_needed():
    """Test that small images are not resized"""
    image_bytes = create_test_image(800, 600)
    resized = resize_image_if_needed(image_bytes, max_dimension=1568)

    # Should return same bytes
    assert len(resized) == len(image_bytes)


def test_resize_image_resize_needed():
    """Test resizing a large image"""
    image_bytes = create_test_image(2000, 1500)
    resized = resize_image_if_needed(image_bytes, max_dimension=1000)

    # Should be smaller
    img = Image.open(io.BytesIO(resized))
    assert img.width <= 1000
    assert img.height <= 1000


def test_encode_image_to_base64():
    """Test base64 encoding"""
    image_bytes = create_test_image()
    encoded = encode_image_to_base64(image_bytes)

    assert isinstance(encoded, str)
    assert len(encoded) > 0
    # Base64 should be longer than original (with encoding overhead)
    assert len(encoded) > len(image_bytes) * 0.7


def test_get_image_media_type_png():
    """Test getting media type for PNG"""
    image_bytes = create_test_image(format='PNG')
    media_type = get_image_media_type(image_bytes)

    assert media_type == 'image/png'


def test_get_image_media_type_jpeg():
    """Test getting media type for JPEG"""
    image_bytes = create_test_image(format='JPEG')
    media_type = get_image_media_type(image_bytes)

    assert media_type == 'image/jpeg'


def test_estimate_vision_tokens_single_image():
    """Test token estimation for single image"""
    tokens = estimate_vision_tokens(1, avg_dimension=1024)

    assert tokens > 0
    assert tokens == 1600  # Base tokens for 1024x1024


def test_estimate_vision_tokens_multiple_images():
    """Test token estimation for multiple images"""
    tokens = estimate_vision_tokens(3, avg_dimension=1024)

    assert tokens == 3 * 1600


def test_estimate_vision_tokens_larger_images():
    """Test token estimation scales with size"""
    tokens_small = estimate_vision_tokens(1, avg_dimension=512)
    tokens_large = estimate_vision_tokens(1, avg_dimension=2048)

    assert tokens_large > tokens_small


def test_create_image_description():
    """Test creating image description"""
    image_data = {
        'name': 'test.png',
        'size': 1024 * 50,  # 50 KB
        'media_type': 'image/png'
    }

    description = create_image_description(image_data)

    assert 'test.png' in description
    assert '50' in description or '50.0' in description
    assert 'KB' in description
    assert 'image/png' in description

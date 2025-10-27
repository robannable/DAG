"""Image processing utilities for vision-enhanced artifact generation"""
import base64
import io
import logging
from typing import List, Tuple, Optional
from PIL import Image


def validate_image(file_bytes: bytes, max_size_mb: int = 20) -> Tuple[bool, str]:
    """
    Validate an image file

    Args:
        file_bytes: Image file bytes
        max_size_mb: Maximum file size in MB

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check file size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"Image too large: {size_mb:.1f}MB (max: {max_size_mb}MB)"

        # Try to open as image
        img = Image.open(io.BytesIO(file_bytes))

        # Check if it's a valid format
        if img.format not in ['PNG', 'JPEG', 'JPG', 'WEBP', 'GIF']:
            return False, f"Unsupported format: {img.format}"

        return True, ""
    except Exception as e:
        return False, f"Invalid image: {str(e)}"


def resize_image_if_needed(
    file_bytes: bytes,
    max_dimension: int = 1568
) -> bytes:
    """
    Resize image if it exceeds max dimension while maintaining aspect ratio

    Args:
        file_bytes: Original image bytes
        max_dimension: Maximum width or height

    Returns:
        Resized image bytes (or original if no resize needed)
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))

        # Check if resize needed
        if img.width <= max_dimension and img.height <= max_dimension:
            return file_bytes

        # Calculate new dimensions
        if img.width > img.height:
            new_width = max_dimension
            new_height = int(img.height * (max_dimension / img.width))
        else:
            new_height = max_dimension
            new_width = int(img.width * (max_dimension / img.height))

        # Resize
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert back to bytes
        output = io.BytesIO()
        img_resized.save(output, format=img.format or 'PNG')
        return output.getvalue()

    except Exception as e:
        logging.error(f"Error resizing image: {str(e)}")
        return file_bytes


def encode_image_to_base64(file_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string

    Args:
        file_bytes: Image file bytes

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(file_bytes).decode('utf-8')


def get_image_media_type(file_bytes: bytes) -> str:
    """
    Get the media type for an image

    Args:
        file_bytes: Image file bytes

    Returns:
        Media type string (e.g., 'image/jpeg')
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        format_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'JPG': 'image/jpeg',
            'WEBP': 'image/webp',
            'GIF': 'image/gif'
        }
        return format_map.get(img.format, 'image/png')
    except:
        return 'image/png'


def prepare_images_for_api(
    uploaded_files: List,
    resize: bool = True,
    max_images: int = 5
) -> List[dict]:
    """
    Prepare uploaded images for API consumption

    Args:
        uploaded_files: List of Streamlit UploadedFile objects
        resize: Whether to resize large images
        max_images: Maximum number of images to process

    Returns:
        List of image data dictionaries with base64 encoding and metadata
    """
    processed_images = []

    for idx, uploaded_file in enumerate(uploaded_files[:max_images]):
        try:
            # Read file bytes
            file_bytes = uploaded_file.read()

            # Validate
            is_valid, error_msg = validate_image(file_bytes)
            if not is_valid:
                logging.warning(f"Skipping invalid image {uploaded_file.name}: {error_msg}")
                continue

            # Resize if needed
            if resize:
                file_bytes = resize_image_if_needed(file_bytes)

            # Encode to base64
            base64_image = encode_image_to_base64(file_bytes)
            media_type = get_image_media_type(file_bytes)

            processed_images.append({
                'name': uploaded_file.name,
                'base64': base64_image,
                'media_type': media_type,
                'size': len(file_bytes)
            })

            logging.info(f"Processed image {idx + 1}: {uploaded_file.name}")

        except Exception as e:
            logging.error(f"Error processing image {uploaded_file.name}: {str(e)}")
            continue

    return processed_images


def estimate_vision_tokens(num_images: int, avg_dimension: int = 1024) -> int:
    """
    Estimate token usage for vision API calls

    Claude vision token estimation:
    - ~1600 tokens per image at 1024x1024
    - Scales with image size

    Args:
        num_images: Number of images
        avg_dimension: Average image dimension

    Returns:
        Estimated token count
    """
    # Base tokens per image (approximate)
    base_tokens = 1600

    # Scale factor based on dimension
    scale = (avg_dimension / 1024) ** 2

    tokens_per_image = int(base_tokens * scale)
    return num_images * tokens_per_image


def create_image_description(image_data: dict) -> str:
    """
    Create a brief description for an image for logging/display

    Args:
        image_data: Image data dictionary

    Returns:
        Human-readable description
    """
    size_kb = image_data['size'] / 1024
    return f"{image_data['name']} ({size_kb:.1f} KB, {image_data['media_type']})"

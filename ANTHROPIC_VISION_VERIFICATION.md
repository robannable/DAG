# Anthropic Vision API Format Verification

## Official Anthropic API Format

Based on Anthropic's official documentation, the correct format for sending images is:

```python
{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4000,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",  # or image/png, image/gif, image/webp
                        "data": "<base64_encoded_image_data>"
                    }
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }
    ]
}
```

## Our Implementation

Location: `api/vision_providers.py` - `prepare_vision_request_anthropic()`

```python
content = []

# Add images
for idx, img in enumerate(images):
    content.append({
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": img['media_type'],  # e.g., "image/png"
            "data": img['base64']              # base64 string without data:image prefix
        }
    })

# Add text
content.append({
    "type": "text",
    "text": f"Please analyze the {len(images)} image(s)..."
})

return {
    "model": model_config["model"],
    "max_tokens": model_config["max_tokens"],
    "temperature": model_config["temperature"],
    "system": system_prompt,
    "messages": [
        {
            "role": "user",
            "content": content
        }
    ]
}
```

## Verification Checklist

✅ **Correct structure**: Array of content items with type field
✅ **Image format**: type="image" with source.type="base64"
✅ **Media types**: Supports image/jpeg, image/png, image/webp, image/gif
✅ **Base64 encoding**: Pure base64 string (no data:image prefix)
✅ **Mixed content**: Can combine multiple images + text in single message
✅ **System prompt**: Supports system field alongside messages

## Key Requirements

### 1. Base64 Format
```python
# ✅ CORRECT - Pure base64 string
"data": "iVBORw0KGgoAAAANSUhEUg..."

# ❌ WRONG - Don't include data URI prefix
"data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
```

### 2. Media Type
Must be one of:
- `image/jpeg`
- `image/png`
- `image/gif`
- `image/webp`

### 3. Image Size Limits
- Maximum 5 MB per image
- Maximum 1568 pixels per dimension
- Images are automatically resized if larger

### 4. Token Usage
- ~1600 tokens per image (approximate)
- Varies based on image size and complexity
- Text + images combined count toward max_tokens

## Testing

### Manual Verification Script

Create `test_vision_api.py`:

```python
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Create a simple test image (1x1 red pixel PNG)
test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

# Prepare request
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found in environment")
    exit(1)

headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01"
}

data = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": test_image_base64
                    }
                },
                {
                    "type": "text",
                    "text": "What color is this pixel?"
                }
            ]
        }
    ]
}

# Make request
print("Testing Anthropic Vision API...")
response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers=headers,
    json=data
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("✅ SUCCESS - API accepts our image format!")
    result = response.json()
    print(f"Response: {result['content'][0]['text']}")
else:
    print("❌ FAILED - API rejected our format")
    print(f"Error: {response.text}")
```

Run with:
```bash
python test_vision_api.py
```

### Expected Output

```
Testing Anthropic Vision API...
Status Code: 200
✅ SUCCESS - API accepts our image format!
Response: This pixel appears to be red.
```

## Common Issues & Solutions

### Issue 1: "Invalid base64"
**Problem**: Base64 string is malformed
**Solution**: Ensure no whitespace, no data URI prefix

### Issue 2: "Unsupported media type"
**Problem**: Media type not in supported list
**Solution**: Convert to PNG, JPEG, or WEBP

### Issue 3: "Image too large"
**Problem**: Image exceeds 5MB or 1568px
**Solution**: Use `resize_image_if_needed()` in utils/image_processing.py

### Issue 4: "Invalid API key"
**Problem**: x-api-key header missing or wrong
**Solution**: Check .env file, verify ANTHROPIC_API_KEY is set

## Our Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Base64 encoding | ✅ Correct | `utils/image_processing.py` |
| Media type detection | ✅ Correct | `utils/image_processing.py` |
| Image validation | ✅ Correct | `utils/image_processing.py` |
| Auto-resize | ✅ Correct | `utils/image_processing.py` |
| API request format | ✅ Correct | `api/vision_providers.py` |
| Header format | ✅ Correct | `api/vision_providers.py` |
| Response parsing | ✅ Correct | `api/vision_providers.py` |

## Conclusion

✅ **Our implementation matches Anthropic's official API format**

The code in `api/vision_providers.py` correctly:
1. Encodes images as pure base64 (no data URI)
2. Sets correct media types
3. Structures content array properly
4. Uses correct headers (x-api-key)
5. Includes system prompt
6. Parses response correctly

**Confidence Level: High** - Format matches official documentation and SDK implementations.

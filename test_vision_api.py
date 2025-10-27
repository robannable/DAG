"""
Simple script to verify Anthropic Vision API works with our format
Run this to confirm the API accepts images before using DAG_vision.py
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_anthropic_vision():
    """Test that Anthropic accepts our image format"""

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in .env file")
        print("Please add your Anthropic API key to .env:")
        print("ANTHROPIC_API_KEY=your_key_here")
        return False

    print("🔍 Testing Anthropic Vision API...")
    print(f"Using API key: {api_key[:8]}...{api_key[-4:]}")

    # Create a minimal 1x1 red pixel PNG (base64 encoded)
    # This is a valid PNG that's only 70 bytes
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

    # Prepare headers (matches our implementation)
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    # Prepare request (matches our implementation)
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
                        "text": "What color is this single pixel? Reply in one word."
                    }
                ]
            }
        ]
    }

    try:
        # Make request
        print("📤 Sending request to Anthropic API...")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )

        print(f"📥 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']

            print("\n✅ SUCCESS - API accepts our image format!")
            print(f"Claude's response: '{content}'")
            print("\nImage format verification:")
            print("  ✓ Base64 encoding works")
            print("  ✓ Media type accepted (image/png)")
            print("  ✓ Content structure correct")
            print("  ✓ Response parsing works")
            print("\n🎉 You're ready to use DAG_vision.py!")
            return True

        else:
            print(f"\n❌ FAILED - Status {response.status_code}")
            print("Response:", response.text)

            # Provide helpful error messages
            if response.status_code == 401:
                print("\n💡 Hint: Check your ANTHROPIC_API_KEY is valid")
            elif response.status_code == 400:
                print("\n💡 Hint: Request format issue - this shouldn't happen")
                print("Please report this as a bug")

            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Anthropic Vision API Verification Test")
    print("=" * 60)
    print()

    success = test_anthropic_vision()

    print()
    print("=" * 60)

    sys.exit(0 if success else 1)

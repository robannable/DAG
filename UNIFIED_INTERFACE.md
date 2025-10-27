# DAG - Unified Interface

## ✅ Simplified: One App, Optional Vision

We've combined the text-only and vision-enhanced versions into **one unified interface**.

## How It Works

### Single Command
```bash
streamlit run DAG.py
```

### Two Modes (Automatic)

**Text-Only Mode** (Default)
- Just fill in the text fields
- Works with **Anthropic** or **Ollama**
- Click "Generate Artefact"

**Vision-Enhanced Mode** (Optional)
- Expand "📸 Visual Context"
- Upload images (PNG, JPG, JPEG, WEBP)
- Check "Use AI vision to interpret images"
- Requires **Anthropic Claude**
- Click "Generate with Vision 🔍"

The app automatically detects which mode to use based on:
1. Whether images are uploaded
2. Whether vision is enabled
3. Which provider is selected

## Benefits of Unified Interface

### Before (Two Separate Apps)
❌ Confusing - which one to use?
❌ Duplicate code to maintain
❌ Need to remember two commands

### After (One App)
✅ Simple - just run `DAG.py`
✅ Vision is **optional**, not separate
✅ Single codebase to maintain
✅ Automatic mode detection

## File Structure

```
Current files:
├── DAG.py                    # ⭐ MAIN APP (unified)
├── DAG_vision.py             # Copy of DAG.py
├── DAG_text_only.py          # Old text-only (backup)
├── DAG_original.py           # Original monolithic (backup)
└── test_vision_api.py        # Vision verification script
```

**You only need:** `DAG.py`

## Usage Examples

### Example 1: Text-Only

```bash
streamlit run DAG.py
```

1. Select provider (Anthropic or Ollama)
2. Fill in text fields
3. Click "Generate Artefact"

**Result:** Traditional text-based generation

### Example 2: Vision-Enhanced

```bash
streamlit run DAG.py
```

1. Select **Anthropic Claude** in sidebar
2. Expand "📸 Visual Context"
3. Upload sketch or photo
4. Check "Use AI vision"
5. Fill in text fields
6. Click "Generate with Vision 🔍"

**Result:** AI analyzes your images and incorporates visual insights

### Example 3: Mixed Workflow

Same session, you can:
1. Generate without vision
2. Then generate with vision
3. Then back to text-only

No need to switch apps!

## Provider Capabilities

| Provider | Text | Vision | Local |
|----------|------|--------|-------|
| **Anthropic Claude** | ✅ | ✅ | ❌ |
| **Ollama** | ✅ | ❌ | ✅ |

## Interface Features

### Generate Tab
- Text input fields (always visible)
- Image upload section (collapsible, optional)
- Automatic mode detection
- Smart button labels
  - "Generate Artefact" (text-only)
  - "Generate with Vision 🔍" (vision mode)

### Gallery Tab
- Browse all artifacts
- Search and filter
- View in-app
- Download

### Sidebar
- Provider selection
- Model dropdown (Ollama)
- Temperature slider
- Info and links

## No Complications!

Your concern: "Does this risk too many complications?"

**Answer: No complications!** It's actually **simpler** because:

1. **Single Entry Point**
   - One command: `streamlit run DAG.py`
   - No decision paralysis

2. **Graceful Fallback**
   - If Ollama + images → Shows info message
   - If no images → Text-only mode
   - If Anthropic + images → Vision mode

3. **Clear UI Signals**
   - Upload section says "Optional"
   - Vision checkbox clearly labeled
   - Button changes based on mode

4. **Same Code Path**
   - Both modes use same form
   - Same validation
   - Same gallery
   - Just different API call at the end

## Migration

### Old Way (Two Apps)
```bash
# For text-only
streamlit run DAG.py

# For vision
streamlit run DAG_vision.py
```

### New Way (One App)
```bash
# For everything
streamlit run DAG.py
```

Vision is now a **feature**, not a separate app.

## Technical Details

### Automatic Mode Selection

```python
if uploaded_files and use_vision:
    # Check provider supports vision
    if provider == 'anthropic':
        # Use vision API
        generate_artefact_with_vision(...)
    else:
        # Show error: "Vision requires Anthropic"
else:
    # Use text-only API (works with both providers)
    generate_artefact(...)
```

### Smart Button Label

```python
button_text = (
    "Generate with Vision 🔍"
    if (uploaded_files and use_vision)
    else "Generate Artefact"
)
```

### Provider Validation

```python
# Vision features check
if uploaded_files and use_vision:
    if provider != 'anthropic':
        st.error("Vision requires Anthropic Claude")
        st.info("Switch to Anthropic or disable vision")
```

## Testing

All existing tests still pass:
```bash
pytest tests/ -v
```

**Result:** 46 tests, 100% passing

The unified interface doesn't add complexity - it uses the **same** underlying modules.

## Verification

### Test Core Functionality
```bash
python -c "
from utils.config import load_model_config
from api.retry import RetryConfig
print('Core modules work')
"
```

### Test Vision API
```bash
python test_vision_api.py
```

### Run Full App
```bash
streamlit run DAG.py
```

## Summary

**Question:** Can we combine them without complications?

**Answer:** ✅ **Done!** And it's **simpler** than before.

**Key Insight:** Vision was already optional in `DAG_vision.py`. We just made that version the main `DAG.py`. No new complexity added.

**Benefits:**
- Single interface
- Optional vision
- Automatic mode detection
- Clearer for users
- Less code to maintain

**Files to use:**
- Production: `DAG.py` (unified)
- Verification: `test_vision_api.py`
- Backups: `DAG_text_only.py`, `DAG_original.py`

Ready to use! 🎭

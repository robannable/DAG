# Diegetic Artefact Generator 🎭

A specialized AI tool that generates speculative documents and artefacts for architectural projects, helping explore and communicate the social, cultural, and practical implications of spatial interventions.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/robannable/DAG.git
cd DAG

# Setup (creates venv, installs dependencies)
./setup.sh   # macOS/Linux
# or
setup.bat    # Windows

# Add your Anthropic API key to .env (required for vision features)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Run the app
streamlit run DAG.py
```

## What Are Diegetic Artefacts?

Diegetic artefacts are objects or documents that exist within a narrative world. This tool generates rich, contextual documents to help architects and spatial practitioners:

- **Explore potential futures** and alternative presents
- **Test scenarios** and user interactions through narrative documents
- **Communicate complex ideas** through familiar formats (diaries, meeting minutes, forms)
- **Develop narrative contexts** for architectural proposals
- **Ground speculative work** in tangible, believable details

**Focus:** Post-austerity themes including alternative economics, community-led development, and resource sharing.

## Features

### 🎨 Core Generation
- **8 Artifact Categories**: Personal/Intimate, Community/Collective, Economic/Resource, Device/Object, Speculative/Critical, Ecological/More-than-human, Institutional/Formal, Maintenance/Care
- **Context-Aware**: Uses project description, location, timeline, user personas, and key themes
- **Markdown Output**: Generated artifacts saved as timestamped `.md` files
- **Temperature Control**: Adjust creativity vs. consistency

### 🔍 Vision Analysis (Optional)
- **Upload sketches, diagrams, or photos** to enhance generation
- **AI vision analysis** extracts spatial relationships, annotations (OCR), materials, and context
- **Ground artifacts in reality**: References specific spaces, dimensions, and site features from your images
- **Supports**: PNG, JPG, JPEG, WEBP (up to 5 images, 20MB each)
- **Requires**: Anthropic Claude

### 📚 Artifact Gallery
- **Browse all generated artifacts** with metadata
- **Search and filter** by project name or location
- **View in-app** or download
- **Sort** by date or project name

### 🤖 AI Providers

| Provider | Text | Vision | Local | Best For |
|----------|------|--------|-------|----------|
| **Anthropic Claude** | ✅ | ✅ | ❌ | Production, vision analysis |
| **Ollama** | ✅ | ❌ | ✅ | Local/offline, privacy, no cost |

### 🔧 Robust Architecture
- **Modular codebase**: Separated API, UI, and utility modules
- **Retry logic**: Automatic retry with exponential backoff for failed requests
- **Comprehensive tests**: 46 tests covering core functionality
- **Gallery view**: Manage and browse all your artifacts

## Usage

### Basic Text Generation

1. **Select provider** in sidebar (Anthropic or Ollama)
2. **Fill in project details**:
   - Project description
   - Location
   - Date/timeframe
   - User personas
   - Key themes
3. **Choose artifact category** (e.g., "Community/Collective")
4. **Click "Generate Artefact"**
5. **View, download, or save** to gallery

### Vision-Enhanced Generation

1. **Select Anthropic Claude** in sidebar
2. **Expand "📸 Visual Context"** section
3. **Upload images**:
   - Concept sketches with annotations
   - Site plans showing spatial relationships
   - Diagrams showing workflows
   - Photos of site conditions
   - Material references
4. **Check "Use AI vision to interpret images"**
5. **Fill in text fields** as normal
6. **Click "Generate with Vision 🔍"**
7. **View visual analysis** in the optional expansion panel

**Result**: Artifacts grounded in your actual drawings and site conditions, not generic assumptions.

## Configuration

### Environment Setup (.env)

```bash
# Required for Anthropic (text + vision)
ANTHROPIC_API_KEY=sk-ant-...

# Ollama runs locally, no API key needed
```

### Model Configuration (model_config.json)

```json
{
    "current_provider": "anthropic",
    "providers": {
        "anthropic": {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "temperature": 0.7,
            ...
        },
        "ollama": {
            "model": "Llama3.1:latest",
            "max_tokens": 4000,
            ...
        }
    }
}
```

### Artifact Categories (artefact_categories.json)

8 predefined categories. Add your own:
```json
{
    "artefact_types": [
        "Device/Object",
        "Personal/Intimate",
        "Community/Collective",
        "Economic/Resource",
        "Speculative/Critical",
        "Ecological/More-than-human",
        "Institutional/Formal",
        "Maintenance/Care"
    ]
}
```

### Prompt Instructions (prompt_instructions.json)

Customize the generation guidance:
```json
{
    "closing_instruction": "Using the anomalies, frictions, and contradictions..."
}
```

## Ollama Setup (Local Inference)

1. **Install Ollama**: https://ollama.com
2. **Start Ollama**: `ollama serve` (may auto-start)
3. **Pull a model**: `ollama pull llama3.1`
4. **Select in app**: Choose "Ollama" in sidebar
5. **Pick your model**: Dropdown shows available models

**Benefits**: Free, offline, private, fast for smaller models
**Limitations**: No vision support, quality varies by model

## Vision API Verification

Test that vision features work:

```bash
python test_vision_api.py
```

This sends a tiny test image to verify:
- Your ANTHROPIC_API_KEY is valid
- API accepts our image format
- Everything is configured correctly

## Testing

Run the test suite:

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_vision_providers.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

**Test coverage**:
- 46 tests, 100% passing
- Config loading and management
- File operations (save, load, list artifacts)
- API request preparation (Anthropic, Ollama)
- Retry logic with exponential backoff
- Image processing and validation
- Vision API formatting

## Output

### Artifacts
- Saved to `artefacts/` directory
- Filename: `YYMMDD_HHMM_ProjectDescription.md`
- Contains: All input context + generated artifact + metadata

### Logs
- Debug logs: `artefact_generator_debug.log`
- Request/response details, errors, warnings

## Project Structure

```
DAG/
├── DAG.py                      # Main application (unified)
├── test_vision_api.py          # Vision verification utility
│
├── api/                        # API modules
│   ├── providers.py            # Anthropic + Ollama text generation
│   ├── vision_providers.py     # Anthropic vision (images)
│   └── retry.py                # Retry logic with exponential backoff
│
├── ui/                         # UI components
│   ├── components.py           # Reusable UI elements
│   ├── gallery.py              # Artifact browser
│   └── image_upload.py         # Image upload & preview
│
├── utils/                      # Utilities
│   ├── config.py               # Config loading/saving
│   ├── file_operations.py      # File management
│   ├── image_processing.py     # Image validation, encoding, resizing
│   └── logging_config.py       # Logging setup
│
├── tests/                      # Test suite (46 tests)
│   ├── test_config.py
│   ├── test_file_operations.py
│   ├── test_providers.py
│   ├── test_retry.py
│   ├── test_image_processing.py
│   └── test_vision_providers.py
│
├── static/                     # CSS
│   ├── styles.css
│   └── generated_content.css
│
├── artefacts/                  # Generated artifacts (created on first use)
│
├── artefact_categories.json    # Artifact type definitions
├── model_config.json           # AI provider configurations
├── prompt_instructions.json    # Generation guidelines
├── requirements.txt            # Python dependencies
└── pytest.ini                  # Test configuration
```

## Troubleshooting

### "No Ollama models found"
**Problem**: Ollama not running or no models installed
**Solution**:
```bash
ollama serve          # Start Ollama daemon
ollama pull llama3.1  # Download a model
```

### "ANTHROPIC_API_KEY not found"
**Problem**: API key not set
**Solution**: Add to `.env` file:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### "Vision features not supported"
**Problem**: Trying to use vision with Ollama
**Solution**: Switch to Anthropic Claude in sidebar

### Image upload fails
**Problem**: File format or size issues
**Solution**:
- Use PNG, JPG, JPEG, or WEBP
- Keep files under 20MB
- Try converting to PNG

### API request errors
**Problem**: Network or rate limit issues
**Solution**: The app automatically retries with exponential backoff (3 attempts). If all fail, check:
- Internet connection
- API key validity
- Rate limits

## Examples

### Example 1: Community Garden Plot Sign-Up

**Without Vision** (Text only):
```
Input: "Community garden with 20 shared plots"
Output: Generic sign-up sheet
```

**With Vision** (Sketch + Site plan + Photo):
```
Input: Same + images showing:
  - Site plan with plot layout
  - Sketch with dimensions (3m x 4m)
  - Photo of existing brick wall and oak tree

Output: Sign-up sheet referencing:
  - "Plot #7 (Row 2, east side)"
  - "3m x 4m growing space"
  - "Plots 15-20 benefit from oak tree shade"
  - "Tool storage near north brick wall"
```

### Example 2: Makerspace Tool Library

**Text Input**: "Shared tool library in warehouse"
**Visual Input**: Floor plan + workflow diagram + interior photo
**Output**: Check-out card that references specific tool zones, actual checkout process, and real spatial features

### Example 3: Ecological Monitoring Station

**Text Input**: "Wildlife monitoring in urban park"
**Visual Input**: Park map + species diagram + habitat photo
**Output**: Field log with actual monitoring locations, local species, real habitat types

## Development

### Architecture Highlights

- **Modular design**: Clean separation of API, UI, and utilities
- **Provider abstraction**: Easy to add new AI providers
- **Retry mechanism**: Resilient to transient failures
- **Vision integration**: Optional feature, graceful fallback
- **Comprehensive testing**: High confidence in changes

### Adding a New Artifact Category

1. Edit `artefact_categories.json`:
   ```json
   {
       "artefact_types": [
           "Your New Category",
           ...
       ]
   }
   ```
2. Restart app
3. New category appears in dropdown

### Extending Prompt Instructions

Edit `prompt_instructions.json` to customize how artifacts are generated:
```json
{
    "closing_instruction": "Your custom guidance here..."
}
```

## Contributing

Areas for development:
- **New artifact categories** for different domains
- **Prompt engineering** improvements for specific types
- **Additional export formats** (PDF, DOCX)
- **Batch generation** for multiple artifacts
- **Templates** for common artifact types
- **Multi-document projects** with related artifacts
- **Collaboration features** (sharing, comments)

## License

[Your License Here]

## Acknowledgments

Special thanks to **Justin Pickard** for his role as agitator, critical friend, and prompt expert.

## Questions?

- **Installation issues**: Check Python version (3.8+), virtual environment setup
- **API errors**: Verify API keys in `.env`, check rate limits
- **Vision not working**: Run `python test_vision_api.py` to diagnose
- **General questions**: Open an issue on GitHub

---

**Built for architects, spatial practitioners, and anyone exploring speculative futures through narrative artefacts.**

🎭 **Ready to generate!** Run `streamlit run DAG.py`

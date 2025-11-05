# Diegetic Artefact Generator

Generate speculative documents and artefacts for architectural projects.

## Quick Start

```bash
git clone https://github.com/robannable/DAG.git
cd DAG
./setup.sh          # or setup.bat on Windows
streamlit run DAG.py
```

## Setup

### Requirements
- Python 3.8+
- Anthropic API key (for vision features)

### Installation

```bash
pip install -r requirements.txt
```

Add API key to `.env`:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

## Usage

**Text Generation:**
1. Select provider (Anthropic or Ollama)
2. Fill in project details
3. Choose artifact category
4. Generate

**Vision-Enhanced:**
1. Select Anthropic Claude
2. Expand "Visual Context" section
3. Upload images (sketches, diagrams, photos)
4. Enable "Use AI vision"
5. Generate

## Features

- **8 Artifact Categories**: Personal, Community, Economic, Device, Speculative, Ecological, Institutional, Maintenance
- **AI Vision**: Upload sketches/diagrams for context-aware generation (Anthropic only)
- **Gallery**: Browse and search generated artifacts
- **Two Providers**: Anthropic Claude (cloud + vision) or Ollama (local)

## Configuration

### Files
- `model_config.json` - AI provider settings
- `artefact_categories.json` - Document types
- `prompt_instructions.json` - Generation parameters

### Ollama (Local)
1. Install from https://ollama.com
2. Pull a model: `ollama pull llama3.1`
3. Select "Ollama" in sidebar

## Testing

```bash
pytest tests/ -v
```

Test vision API:
```bash
python test_vision_api.py
```

## Troubleshooting

**No Ollama models found**: Start Ollama and pull a model
**API key error**: Add key to `.env` file
**Vision not working**: Use Anthropic Claude provider

## Project Structure

```
api/          - API providers and retry logic
ui/           - Interface components and gallery
utils/        - Config, file ops, image processing
tests/        - Test suite (46 tests)
static/       - CSS files
```

## Acknowledgments

Special thanks to Justin Pickard.

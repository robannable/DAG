# Diegetic Artefact Generator 🎭

A specialized AI tool that generates speculative documents and artefacts for architectural projects, helping explore and communicate the social, cultural, and practical implications of spatial interventions.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/robannable/DAG.git
cd Generator

# (Option A) One-time setup (Python env + deps)
./setup.sh   # macOS/Linux
# or
setup.bat    # Windows

# (Option B) Manual install
pip install -r requirements.txt

# Create a .env with any cloud API keys you plan to use
echo "PERPLEXITY_API_KEY=..." > .env
echo "OPENAI_API_KEY=..." >> .env
echo "ANTHROPIC_API_KEY=..." >> .env

# Run the app
streamlit run DAG.py
```

## About

Diegetic artefacts are objects or documents that exist within a narrative world. This tool generates rich, contextual documents to help architects and spatial practitioners:

- Explore potential futures and alternative presents
- Test scenarios and user interactions
- Communicate complex ideas through familiar formats
- Develop narrative contexts for architectural proposals

## Key Features

- **Flexible AI Integration**: Supports multiple AI providers including:
  - Perplexity AI
  - OpenAI
  - Anthropic
  - Ollama (local inference)
  - Easily extensible for additional providers
- **Configurable Model Settings**: Customize model parameters through `model_config.json`:
  - Temperature
  - Max tokens
  - Top P
  - Frequency penalty
  - Presence penalty
  - Provider-specific options
- **Multiple Document Types**: Supports various categories including:
  - Personal (diaries, photos, notes)
  - Community (bulletin boards, meeting minutes)
  - Economic (sharing agreements, consumption logs)
  - Digital (API docs, sensor data)
  - Speculative (alternative building codes)
  - Ecological (cohabitation agreements)
  - Institutional (manuals, policies)

- **Context-Aware**: Considers project description, location, timeline, users, and themes
- **Post-Austerity Focus**: Explores alternative economics, community-led development, and resource sharing

## Usage

1. Enter your project details:
   - Description
   - Location
   - Timeline
   - User personas
   - Key themes

2. Choose a document type
3. Generate and download your artifact

## Configuration

The tool uses three config files:
- `artefact_categories.json`: Document types and categories
- `prompt_instructions.json`: Generation parameters
- `model_config.json`: AI model settings and provider configurations, including:
  - Cloud providers (OpenAI, Anthropic, Perplexity)
  - Local inference through Ollama

### Providers and API keys

- Set your keys in `.env` (loaded via `python-dotenv`):
  - `PERPLEXITY_API_KEY`
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
- Ollama is local and does not require an API key.

### Ollama (local models)

- Install Ollama from `https://ollama.com`
- Ensure the daemon is running (defaults to `http://localhost:11434`)
- Pull at least one model, e.g.: `ollama pull llama3.1` or `ollama pull cogito`
- In the app sidebar, choose provider “Ollama”. The app will call the local server to list available models and show them in a dropdown. Your selection is saved back to `model_config.json`.
- If no models are found, a text input is shown and a warning suggests starting Ollama and pulling a model.

### Output and logs

- Generated artefacts are saved under `artefacts/` as timestamped `.md`
- Debug logs are written to `artefact_generator_debug.log`

### Common issues

- “No Ollama models found”: Start Ollama and pull a model (`ollama serve` may be required on some systems)
- API error for cloud providers: Ensure the corresponding key is present in `.env`

## Contributing

Areas for development:
- New document categories
- Improved prompt engineering
- Enhanced UI/UX
- Additional export formats
- Document templates
- New AI provider integrations

## Acknowledgments

Special thanks to Justin Pickard for his role as agitator, critical friend and prompt expert.
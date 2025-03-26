# Diegetic Artefact Generator 🎭

A specialized AI tool that generates speculative documents and artefacts for architectural projects, helping explore and communicate the social, cultural, and practical implications of spatial interventions.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/robannable/DAG.git
cd diegetic-artefact-generator

# Install dependencies
pip install -r requirements.txt

# Set up your API keys in .env
echo "PERPLEXITY_API_KEY=your_perplexity_api_key_here" > .env
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" >> .env

# Run the application
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
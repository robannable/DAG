"""Configuration loading and management"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_CONFIG_PATH = PROJECT_ROOT / "model_config.json"
ARTEFACT_CATEGORIES_PATH = PROJECT_ROOT / "artefact_categories.json"
PROMPT_INSTRUCTIONS_PATH = PROJECT_ROOT / "prompt_instructions.json"
# Overridable so a server install can keep generated files outside the code dir
ARTEFACTS_DIR = Path(os.getenv("DAG_ARTEFACTS_DIR") or PROJECT_ROOT / "artefacts")


def load_artefact_categories() -> List[str]:
    """Load artefact categories from JSON file"""
    try:
        with open(ARTEFACT_CATEGORIES_PATH, 'r') as f:
            data = json.load(f)
            logging.debug(f"Successfully loaded artefact types: {data['artefact_types']}")
            return data['artefact_types']
    except Exception as e:
        logging.error(f"Error loading artefact categories: {str(e)}")
        raise


def load_prompt_instructions() -> str:
    """Load prompt instructions from JSON file"""
    try:
        with open(PROMPT_INSTRUCTIONS_PATH, 'r') as f:
            data = json.load(f)
            return data['closing_instruction']
    except Exception as e:
        logging.error(f"Error loading prompt instructions: {str(e)}")
        return "The artefact should reflect the context and show how the architecture serves as a catalyst for change."


def load_full_model_config() -> Dict[str, Any]:
    """Load the full model configuration file (all providers)"""
    with open(MODEL_CONFIG_PATH, 'r') as f:
        return json.load(f)


def enabled_providers(config: Dict[str, Any]) -> List[str]:
    """Providers offered in the UI, in config order.

    ``DAG_PROVIDERS`` (comma-separated, e.g. "anthropic,openrouter") limits
    the list - a server install sets it to hide Ollama, which only exists
    on a local machine. Unset means every configured provider.
    """
    configured = list(config['providers'].keys())
    wanted = os.getenv("DAG_PROVIDERS", "")
    if not wanted.strip():
        return configured
    allowed = {p.strip().lower() for p in wanted.split(",") if p.strip()}
    return [p for p in configured if p in allowed] or configured


def load_model_config(provider: Optional[str] = None) -> Dict[str, Any]:
    """Load one provider's model configuration.

    ``provider`` defaults to the file's ``current_provider``. The file is
    read-only at runtime: per-user choices live in Streamlit session state.
    """
    try:
        config = load_full_model_config()
        provider = provider or config.get('current_provider', 'anthropic')
        provider_config = config['providers'].get(provider)
        if not provider_config:
            raise ValueError(f"Provider {provider} not found in configuration")
        return dict(provider_config)
    except Exception as e:
        logging.error(f"Error loading model configuration: {str(e)}")
        # Return default configuration
        return {
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "max_tokens": 4000,
            "supports_temperature": False,
            "supports_vision": True,
            "thinking": {"type": "disabled"},
            "api_endpoint": "https://api.anthropic.com/v1/messages",
            "api_key_env": "ANTHROPIC_API_KEY",
            "headers": {
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        }

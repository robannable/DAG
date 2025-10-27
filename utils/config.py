"""Configuration loading and management"""
import json
import logging
from typing import Dict, List, Any


def load_artefact_categories() -> List[str]:
    """Load artefact categories from JSON file"""
    try:
        with open('artefact_categories.json', 'r') as f:
            data = json.load(f)
            logging.info(f"Successfully loaded artefact types: {data['artefact_types']}")
            return data['artefact_types']
    except Exception as e:
        logging.error(f"Error loading artefact categories: {str(e)}")
        raise


def load_prompt_instructions() -> str:
    """Load prompt instructions from JSON file"""
    try:
        with open('prompt_instructions.json', 'r') as f:
            data = json.load(f)
            return data['closing_instruction']
    except Exception as e:
        logging.error(f"Error loading prompt instructions: {str(e)}")
        return "The artefact should reflect the context and show how the architecture serves as a catalyst for change."


def load_model_config() -> Dict[str, Any]:
    """Load the model configuration from JSON file"""
    try:
        with open('model_config.json', 'r') as f:
            config = json.load(f)
            current_provider = config.get('current_provider', 'anthropic')
            provider_config = config['providers'].get(current_provider)
            if not provider_config:
                raise ValueError(f"Provider {current_provider} not found in configuration")
            return provider_config
    except Exception as e:
        logging.error(f"Error loading model configuration: {str(e)}")
        # Return default configuration
        return {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.1,
            "api_endpoint": "https://api.anthropic.com/v1/messages",
            "api_key_env": "ANTHROPIC_API_KEY",
            "headers": {
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        }


def save_model_config(current_provider: str) -> None:
    """Save the current provider to model configuration"""
    try:
        with open('model_config.json', 'r') as f:
            config = json.load(f)

        config['current_provider'] = current_provider

        with open('model_config.json', 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving model configuration: {str(e)}")


def update_ollama_model(model_name: str) -> None:
    """Update the Ollama model in configuration"""
    try:
        with open('model_config.json', 'r') as f:
            config = json.load(f)

        config['providers']['ollama']['model'] = model_name

        with open('model_config.json', 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Error updating Ollama model: {str(e)}")

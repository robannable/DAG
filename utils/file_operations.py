"""File operations for artifact management"""
import os
import re
from datetime import datetime
from typing import Dict, List, Any
import json


def sanitize_filename(filename: str) -> str:
    """Convert a string to a valid filename"""
    # Remove invalid characters and replace spaces with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename


def save_artefact(
    artefact_content: str,
    project_description: str,
    date: str,
    location: str,
    user_bios: str,
    themes: str,
    model_config: Dict[str, Any],
    temperature: float,
    show_thinking: bool = False
) -> str:
    """Save the artefact as a markdown file"""
    # Create artefacts directory if it doesn't exist
    os.makedirs('artefacts', exist_ok=True)

    # Clean up project description:
    # 1. Replace carriage returns/newlines with spaces
    # 2. Take only first 30 chars for filename
    clean_description = ' '.join(project_description.splitlines()).strip()[:30]

    # Format timestamp more readably: YYMMDD_HHMM
    timestamp = datetime.now().strftime("%y%m%d_%H%M")

    # Create a sanitized filename
    base_filename = f"{timestamp}_{sanitize_filename(clean_description)}"
    filename = f"artefacts/{base_filename}.md"

    # Get model information
    provider = model_config.get('provider', '')
    model_name = model_config.get('model', 'unknown')

    # Create markdown content with generated-content class wrapper
    markdown_content = f"""<div class="generated-content{' show-think' if show_thinking else ''}">

# Diegetic Artefact Generation results:

## Project
{project_description}

## Location
{location}

## Date/Timeframe
{date}

## User Personas
{user_bios}

## Key Themes
{themes}

## Generated Artefact
{artefact_content}

---
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*Model: {provider}/{model_name} (temperature: {temperature})*

</div>"""

    # Save the file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return filename


def list_artefacts() -> List[Dict[str, Any]]:
    """List all saved artefacts with metadata"""
    artefacts = []

    if not os.path.exists('artefacts'):
        return artefacts

    for filename in os.listdir('artefacts'):
        if filename.endswith('.md'):
            filepath = os.path.join('artefacts', filename)
            try:
                # Get file stats
                stats = os.stat(filepath)
                created = datetime.fromtimestamp(stats.st_mtime)

                # Read first few lines to extract metadata
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract project description (simple regex)
                project_match = re.search(r'## Project\n(.+?)\n\n', content, re.DOTALL)
                project = project_match.group(1).strip() if project_match else "Unknown Project"

                # Extract location
                location_match = re.search(r'## Location\n(.+?)\n\n', content, re.DOTALL)
                location = location_match.group(1).strip() if location_match else "Unknown Location"

                # Extract model info
                model_match = re.search(r'\*Model: (.+?)\*', content)
                model = model_match.group(1) if model_match else "Unknown"

                artefacts.append({
                    'filename': filename,
                    'filepath': filepath,
                    'created': created,
                    'project': project[:100],  # Limit length
                    'location': location[:50],
                    'model': model,
                    'size': stats.st_size
                })
            except Exception as e:
                # Skip files that can't be read
                continue

    # Sort by creation time, newest first
    artefacts.sort(key=lambda x: x['created'], reverse=True)

    return artefacts


def load_artefact(filepath: str) -> str:
    """Load an artefact file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error loading artefact: {str(e)}")

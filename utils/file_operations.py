"""File operations for artifact management"""
import os
import re
import json
import base64
from datetime import datetime
from typing import Dict, List, Any

from utils.config import ARTEFACTS_DIR

# Machine-readable metadata is stored as a base64-encoded JSON payload inside
# an HTML comment at the top of each artefact file. Base64's alphabet
# ([A-Za-z0-9+/=]) can never contain "-->" or other markup, so this survives
# arbitrary user content (newlines, braces, quotes, unicode) that broke the
# previous "## Project\n(.+?)\n\n" regex parsing.
_META_PREFIX = "<!-- DAG-META:"
_META_RE = re.compile(r'<!-- DAG-META:([A-Za-z0-9+/=]+) -->')


def sanitize_filename(filename: str) -> str:
    """Convert a string to a valid filename"""
    # Remove invalid characters and replace spaces with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename


def _encode_metadata(metadata: Dict[str, Any]) -> str:
    """Encode metadata dict into a single-line HTML comment block"""
    payload = base64.b64encode(
        json.dumps(metadata, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return f"{_META_PREFIX}{payload} -->"


def _parse_metadata(content: str) -> Dict[str, Any]:
    """Extract artefact metadata, preferring the encoded block.

    Falls back to legacy section-header parsing for artefacts saved before
    the metadata block was introduced.
    """
    match = _META_RE.search(content)
    if match:
        try:
            decoded = base64.b64decode(match.group(1)).decode("utf-8")
            return json.loads(decoded)
        except (ValueError, json.JSONDecodeError):
            pass  # corrupt block -> fall through to legacy parsing

    # Legacy fallback for older artefact files
    meta: Dict[str, Any] = {}
    project_match = re.search(r'## Project\n(.+?)\n\n', content, re.DOTALL)
    if project_match:
        meta['project'] = project_match.group(1).strip()
    location_match = re.search(r'## Location\n(.+?)\n\n', content, re.DOTALL)
    if location_match:
        meta['location'] = location_match.group(1).strip()
    model_match = re.search(r'\*Model: (.+?)\*', content)
    if model_match:
        meta['model'] = model_match.group(1).strip()
    return meta


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
    os.makedirs(ARTEFACTS_DIR, exist_ok=True)

    # Clean up project description:
    # 1. Replace carriage returns/newlines with spaces
    # 2. Take only first 30 chars for filename
    clean_description = ' '.join(project_description.splitlines()).strip()[:30]

    # Format timestamp more readably: YYMMDD_HHMM
    timestamp = datetime.now().strftime("%y%m%d_%H%M")

    # Create a sanitized filename
    base_filename = f"{timestamp}_{sanitize_filename(clean_description)}"
    filename = str(ARTEFACTS_DIR / f"{base_filename}.md")

    # Get model information
    provider = model_config.get('provider', '')
    model_name = model_config.get('model', 'unknown')

    # Machine-readable metadata block (invisible when rendered)
    meta_block = _encode_metadata({
        "project": project_description,
        "location": location,
        "date": date,
        "model": f"{provider}/{model_name}",
        "temperature": temperature,
        "generated": datetime.now().isoformat(timespec="seconds"),
    })

    # Create markdown content with generated-content class wrapper
    markdown_content = f"""{meta_block}
<div class="generated-content{' show-think' if show_thinking else ''}">

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

    if not ARTEFACTS_DIR.exists():
        return artefacts

    for filename in os.listdir(ARTEFACTS_DIR):
        if filename.endswith('.md'):
            filepath = str(ARTEFACTS_DIR / filename)
            try:
                stats = os.stat(filepath)

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                meta = _parse_metadata(content)
                project = meta.get('project', "Unknown Project")
                location = meta.get('location', "Unknown Location")
                model = meta.get('model', "Unknown")

                # Prefer the recorded generation time; fall back to file
                # mtime for legacy artefacts or an unparseable value.
                created = datetime.fromtimestamp(stats.st_mtime)
                generated = meta.get('generated')
                if generated:
                    try:
                        created = datetime.fromisoformat(generated)
                    except (ValueError, TypeError):
                        pass

                artefacts.append({
                    'filename': filename,
                    'filepath': filepath,
                    'created': created,
                    'project': project[:100],  # Limit length
                    'location': location[:50],
                    'model': model,
                    'size': stats.st_size
                })
            except Exception:
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


def delete_artefact(filepath: str) -> None:
    """Delete an artefact file. Restricted to files inside ARTEFACTS_DIR."""
    resolved = os.path.realpath(filepath)
    artefacts_root = os.path.realpath(ARTEFACTS_DIR)
    if not resolved.startswith(artefacts_root + os.sep):
        raise ValueError(f"Refusing to delete file outside artefacts dir: {filepath}")
    os.remove(resolved)

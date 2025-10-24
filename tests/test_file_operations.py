"""Tests for file operations"""
import pytest
import os
from datetime import datetime
from utils.file_operations import (
    sanitize_filename,
    save_artefact,
    list_artefacts,
    load_artefact
)


def test_sanitize_filename():
    """Test filename sanitization"""
    # Test removing invalid characters
    assert sanitize_filename("hello/world") == "helloworld"
    assert sanitize_filename("test:file") == "testfile"
    assert sanitize_filename("file*name?") == "filename"

    # Test space replacement
    assert sanitize_filename("hello world") == "hello_world"
    assert sanitize_filename("multiple   spaces") == "multiple___spaces"


def test_save_artefact(tmp_path, monkeypatch):
    """Test saving an artefact"""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Test data
    content = "Test artefact content"
    project = "Test Project"
    date = "2025"
    location = "Test Location"
    user_bios = "Test User"
    themes = "Test Themes"
    model_config = {
        "provider": "anthropic",
        "model": "test-model"
    }
    temperature = 0.7

    # Save artefact
    filename = save_artefact(
        content, project, date, location,
        user_bios, themes, model_config, temperature
    )

    # Verify file was created
    assert os.path.exists(filename)
    assert filename.startswith("artefacts/")
    assert filename.endswith(".md")

    # Verify content
    with open(filename, 'r') as f:
        saved_content = f.read()

    assert "Test Project" in saved_content
    assert "Test Location" in saved_content
    assert "Test artefact content" in saved_content
    assert "anthropic/test-model" in saved_content


def test_list_artefacts_empty(tmp_path, monkeypatch):
    """Test listing artefacts when directory is empty"""
    monkeypatch.chdir(tmp_path)

    artefacts = list_artefacts()

    assert isinstance(artefacts, list)
    assert len(artefacts) == 0


def test_list_artefacts_with_files(tmp_path, monkeypatch):
    """Test listing artefacts with existing files"""
    monkeypatch.chdir(tmp_path)

    # Create some test artefacts
    os.makedirs('artefacts', exist_ok=True)

    test_content = """<div class="generated-content">

## Project
Test Project 1

## Location
Test Location

## Date/Timeframe
2025

## User Personas
Test User

## Key Themes
Test Themes

## Generated Artefact
Test content

---
*Generated on 2025-01-01 12:00:00*
*Model: anthropic/test-model (temperature: 0.7)*

</div>"""

    with open('artefacts/test1.md', 'w') as f:
        f.write(test_content)

    with open('artefacts/test2.md', 'w') as f:
        f.write(test_content.replace("Project 1", "Project 2"))

    # List artefacts
    artefacts = list_artefacts()

    assert len(artefacts) == 2
    assert all('filename' in a for a in artefacts)
    assert all('project' in a for a in artefacts)
    assert all('location' in a for a in artefacts)
    assert all('created' in a for a in artefacts)


def test_load_artefact(tmp_path, monkeypatch):
    """Test loading an artefact"""
    monkeypatch.chdir(tmp_path)

    # Create test file
    os.makedirs('artefacts', exist_ok=True)
    test_content = "Test artefact content"
    filepath = 'artefacts/test.md'

    with open(filepath, 'w') as f:
        f.write(test_content)

    # Load artefact
    loaded_content = load_artefact(filepath)

    assert loaded_content == test_content


def test_load_artefact_missing_file():
    """Test loading a missing artefact"""
    with pytest.raises(Exception):
        load_artefact('nonexistent.md')

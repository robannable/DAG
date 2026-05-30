"""Tests for file operations"""
import pytest
import os
from utils import file_operations as file_ops_module
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
    artefacts_dir = tmp_path / "artefacts"
    monkeypatch.setattr(file_ops_module, "ARTEFACTS_DIR", artefacts_dir)

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

    filename = save_artefact(
        content, project, date, location,
        user_bios, themes, model_config, temperature
    )

    assert os.path.exists(filename)
    assert filename.endswith(".md")
    assert str(artefacts_dir) in filename

    with open(filename, 'r') as f:
        saved_content = f.read()

    assert "Test Project" in saved_content
    assert "Test Location" in saved_content
    assert "Test artefact content" in saved_content
    assert "anthropic/test-model" in saved_content


def test_list_artefacts_empty(tmp_path, monkeypatch):
    """Test listing artefacts when directory is empty"""
    monkeypatch.setattr(file_ops_module, "ARTEFACTS_DIR", tmp_path / "artefacts")

    artefacts = list_artefacts()

    assert isinstance(artefacts, list)
    assert len(artefacts) == 0


def test_list_artefacts_with_files(tmp_path, monkeypatch):
    """Test listing artefacts with existing files"""
    artefacts_dir = tmp_path / "artefacts"
    artefacts_dir.mkdir()
    monkeypatch.setattr(file_ops_module, "ARTEFACTS_DIR", artefacts_dir)

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

    (artefacts_dir / "test1.md").write_text(test_content)
    (artefacts_dir / "test2.md").write_text(
        test_content.replace("Project 1", "Project 2")
    )

    artefacts = list_artefacts()

    assert len(artefacts) == 2
    assert all('filename' in a for a in artefacts)
    assert all('project' in a for a in artefacts)
    assert all('location' in a for a in artefacts)
    assert all('created' in a for a in artefacts)


def test_load_artefact(tmp_path):
    """Test loading an artefact"""
    test_content = "Test artefact content"
    filepath = tmp_path / "test.md"
    filepath.write_text(test_content)

    loaded_content = load_artefact(str(filepath))

    assert loaded_content == test_content


def test_load_artefact_missing_file():
    """Test loading a missing artefact"""
    with pytest.raises(Exception):
        load_artefact('nonexistent.md')

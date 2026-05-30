"""Tests for file operations"""
import pytest
import os
from utils import file_operations as file_ops_module
from utils.file_operations import (
    sanitize_filename,
    save_artefact,
    list_artefacts,
    load_artefact,
    delete_artefact
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
    """Legacy fallback: files without a metadata block parse via section headers"""
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


def test_save_then_list_roundtrip_tricky_content(tmp_path, monkeypatch):
    """Metadata survives content that broke the old regex parser"""
    artefacts_dir = tmp_path / "artefacts"
    monkeypatch.setattr(file_ops_module, "ARTEFACTS_DIR", artefacts_dir)

    # Project text packed with characters that defeated the legacy regex:
    # blank lines, an HTML-comment terminator, JSON braces, quotes, unicode.
    project = 'Línea Verde\n\n--> {"weird": "value"}\n\nfollow-up paragraph'
    location = "Bilbao, España"

    save_artefact(
        "Artefact body", project, "2030", location,
        "Personas", "Themes",
        {"provider": "anthropic", "model": "claude-sonnet-4-6"}, 0.7
    )

    artefacts = list_artefacts()
    assert len(artefacts) == 1
    entry = artefacts[0]
    # Project is truncated to 100 chars in the listing; compare on that basis
    assert entry['project'] == project[:100]
    assert entry['location'] == location[:50]
    assert entry['model'] == "anthropic/claude-sonnet-4-6"


def test_delete_artefact_removes_file(tmp_path, monkeypatch):
    """delete_artefact removes a file inside the artefacts dir"""
    artefacts_dir = tmp_path / "artefacts"
    artefacts_dir.mkdir()
    monkeypatch.setattr(file_ops_module, "ARTEFACTS_DIR", artefacts_dir)

    target = artefacts_dir / "victim.md"
    target.write_text("content")

    delete_artefact(str(target))
    assert not target.exists()


def test_delete_artefact_rejects_outside_dir(tmp_path, monkeypatch):
    """delete_artefact refuses paths outside the artefacts dir"""
    artefacts_dir = tmp_path / "artefacts"
    artefacts_dir.mkdir()
    monkeypatch.setattr(file_ops_module, "ARTEFACTS_DIR", artefacts_dir)

    outsider = tmp_path / "important.txt"
    outsider.write_text("do not delete")

    with pytest.raises(ValueError, match="outside artefacts dir"):
        delete_artefact(str(outsider))
    assert outsider.exists()


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

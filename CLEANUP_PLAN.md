# Repository Cleanup Plan

## Current State: Too Many Files!

### Python Scripts (5 files)
- ✅ `DAG.py` - **KEEP** (Main unified application)
- ❌ `DAG_original.py` - **REMOVE** (Old monolithic backup, 26KB)
- ❌ `DAG_text_only.py` - **REMOVE** (Old text-only backup, 8KB)
- ❌ `DAG_vision.py` - **REMOVE** (Duplicate of DAG.py, 11KB)
- ✅ `test_vision_api.py` - **KEEP** (Useful verification utility)

### Documentation (7 files - Way too many!)
- ✅ `README.md` - **KEEP & UPDATE** (Main documentation)
- ❌ `ANTHROPIC_VISION_VERIFICATION.md` - **REMOVE** (Technical details, 5KB)
- ❌ `IMPLEMENTATION_SUMMARY.md` - **REMOVE** (Project history, 19KB)
- ❌ `REFACTORING.md` - **REMOVE** (Refactoring notes, 11KB)
- ❌ `SIMPLIFIED_SUMMARY.md` - **REMOVE** (Interim summary, 14KB)
- ❌ `UNIFIED_INTERFACE.md` - **REMOVE** (Interface docs, 8KB)
- ❌ `VISION_ENHANCEMENT.md` - **REMOVE** (Vision design doc, 12KB)
- ❌ `VISION_USAGE_GUIDE.md` - **REMOVE** (Vision guide, 15KB)

### Configuration & Data (All Keep)
- ✅ `artefact_categories.json`
- ✅ `model_config.json`
- ✅ `prompt_instructions.json`
- ✅ `requirements.txt`
- ✅ `pytest.ini`

### Setup Scripts (All Keep)
- ✅ `setup.sh`
- ✅ `setup.bat`
- ✅ `run.bat`

### Directories (All Keep)
- ✅ `api/` - API modules
- ✅ `ui/` - UI components
- ✅ `utils/` - Utilities
- ✅ `tests/` - Test suite
- ✅ `static/` - CSS files
- ✅ `artefacts/` - Generated artifacts (user data)

## Cleanup Summary

**Files to Remove: 11**
- 3 backup Python scripts
- 7 redundant documentation files
- Total size saved: ~100KB

**Files to Keep: 9 + directories**
- 1 main Python app
- 1 verification script
- 1 main README (updated)
- 5 config/data files
- 3 setup scripts
- All module directories

## Why This Cleanup?

### Problems with Current State:
1. **Too many docs** - Users don't know which to read
2. **Outdated backups** - DAG_original, DAG_text_only are superseded
3. **Duplicate files** - DAG_vision.py is identical to DAG.py
4. **Confusing** - Which file is the "real" one?

### After Cleanup:
1. **One clear entry point** - `DAG.py`
2. **One documentation** - `README.md` (comprehensive)
3. **No confusion** - All essential info in one place
4. **Cleaner repo** - Easy to navigate

## What Info Will Be Lost?

The 7 documentation files contain:
- Technical implementation details
- Refactoring history
- Vision API verification specs
- Usage guides

**Solution:** Consolidate essential info into README.md:
- Quick start guide
- Feature overview
- Vision usage
- Testing
- Troubleshooting

Historical/technical details are in git history if needed.

## Updated README Structure

```markdown
# Diegetic Artefact Generator (DAG)

## Quick Start
- Installation
- Basic usage
- Running the app

## Features
- Text generation
- Vision analysis (optional)
- Artifact gallery
- Provider support (Anthropic + Ollama)

## Using Vision
- Upload images
- What Claude can analyze
- Requirements

## Testing
- Run tests
- Verify vision API

## Troubleshooting
- Common issues
- Provider setup

## Development
- Architecture
- Testing
- Contributing

## License & Credits
```

## Approval Needed

This cleanup will:
- ✅ Remove 11 unnecessary files
- ✅ Keep all functional code
- ✅ Consolidate docs into README
- ✅ Make repo clearer and more professional

**Approve this plan?**

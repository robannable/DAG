# Vision-Enhanced DAG - Usage Guide

## Overview

The vision-enhanced version of DAG allows you to upload sketches, diagrams, photographs, and reference images alongside text descriptions. The AI analyzes these visuals to extract spatial, material, and contextual insights, resulting in artifacts that are more grounded in your actual design intentions.

## Quick Start

### 1. Launch the Vision-Enhanced Version

```bash
streamlit run DAG_vision.py
```

### 2. Configure Your Provider

**Important:** Vision features require specific AI providers:

- ✅ **Anthropic Claude** (Recommended)
  - Best vision capabilities for architectural interpretation
  - Excellent at understanding spatial relationships
  - Strong OCR for handwritten annotations

- ✅ **OpenAI GPT-4 Vision**
  - Good vision capabilities
  - Works well with diagrams and reference images

- ❌ **Ollama** (Local models)
  - Vision support limited/experimental
  - Not recommended for architectural work yet

**To select a provider:** Use the sidebar dropdown to choose "Anthropic" or "OpenAI"

### 3. Upload Visual Materials

In the "Generate" tab, expand the **"📸 Visual Context (Optional)"** section:

- Click "Browse files" to upload images
- Supported formats: PNG, JPG, JPEG, WEBP
- Maximum 5 images per generation
- Each image should be under 20MB
- Check "Use AI vision to interpret images"

### 4. Fill in Text Fields

Complete all required text fields as usual:
- Project Description
- Location
- Date/Timeframe
- User Personas
- Key Themes
- Artifact Category

### 5. Generate

Click **"Generate with Vision 🔍"**

The AI will:
1. Analyze all uploaded images
2. Extract visual information
3. Combine with text context
4. Generate an enriched artifact

## What to Upload

### Best Image Types for Each Use Case

#### 1. Concept Sketches
**Upload:** Hand-drawn sketches showing spatial concepts
**AI Extracts:**
- Layout and organization
- Spatial relationships
- Proportions and scale
- Design intentions

**Example Use:** Community kitchen concept
- Sketch showing cooking stations, seating, storage
- AI generates meal sign-up sheet referencing specific spaces

#### 2. Site Plans with Annotations
**Upload:** Plans with notes, dimensions, labels
**AI Extracts:**
- Site boundaries
- Circulation patterns
- Zoning/program areas
- Handwritten notes (OCR)

**Example Use:** Urban garden project
- Annotated site plan with plot divisions
- AI generates plot allocation log with real plot numbers

#### 3. Diagrams
**Upload:** Flow diagrams, relationship maps, program diagrams
**AI Extracts:**
- Connections and relationships
- Hierarchies
- Process flows
- System organization

**Example Use:** Tool library system
- Diagram showing borrowing process
- AI generates check-out card reflecting actual workflow

#### 4. Context Photographs
**Upload:** Photos of existing site, neighborhood, conditions
**AI Extracts:**
- Environmental characteristics
- Material palette
- Scale and density
- Atmospheric qualities

**Example Use:** Retrofit project
- Photos of existing warehouse interior
- AI generates maintenance log with specific existing features

#### 5. Reference Images
**Upload:** Mood boards, material samples, precedents
**AI Extracts:**
- Aesthetic intentions
- Material qualities
- Atmosphere and tone
- Design language

**Example Use:** Community center
- References showing warm, welcoming spaces
- AI generates welcome letter with appropriate tone

## Tips for Best Results

### Image Quality

✅ **Do:**
- Use clear, well-lit images
- Include annotations and labels
- Show multiple views/scales
- Combine sketch + photo + diagram

❌ **Don't:**
- Upload blurry or dark images
- Use tiny thumbnails
- Include sensitive information
- Upload unrelated images

### Image Labels

Give your uploads descriptive filenames:
- ✅ `site-plan-annotated.png`
- ✅ `sketch-community-kitchen.jpg`
- ✅ `ref-material-palette.png`
- ❌ `IMG_1234.jpg`

The AI can see filenames and uses them as context clues.

### Number of Images

- **1-2 images:** Focused, specific context
- **3-4 images:** Rich, multi-faceted context
- **5+ images:** Maximum context (5 image limit)

**Recommendation:** Start with 2-3 carefully chosen images

### Combining Image Types

**Good combinations:**
1. Site plan + sketch + photo = grounded, complete context
2. Diagram + reference images = clear system + aesthetic
3. Sketch + context photo = concept + reality

## Understanding Vision Analysis

### The <think> Block

When using vision, the AI first analyzes your images in a `<think>` block:

```
<think>
Looking at the three images:

1. Site plan shows a 30x40m plot with...
2. The sketch indicates three main zones...
3. The reference photos suggest a material palette of...

I'll create a maintenance log that references these specific spaces...
</think>
```

**To view this:**
- Expand "🔍 Visual Analysis" after generation
- Or check "Show AI thinking process"

This helps you understand:
- What the AI "saw" in your images
- How it interpreted spatial relationships
- Why it made certain choices

### Token Usage

Vision uses more API tokens:
- ~1,600 tokens per image (1024x1024)
- Automatically estimated in the UI
- Images are resized to optimize cost

**Cost Example (Claude):**
- Text-only: ~2,000 tokens (~$0.006)
- With 3 images: ~6,800 tokens (~$0.020)

## Artifact Categories + Vision

Some categories benefit more from visual input:

### High Value
- **Device/Object:** See the actual object design
- **Ecological/More-than-human:** Site photos, ecosystem diagrams
- **Community/Collective:** Social relationship diagrams
- **Maintenance/Care:** Workflow diagrams, space layouts

### Medium Value
- **Economic/Resource:** Flow diagrams, exchange systems
- **Institutional/Formal:** Org charts, building layouts
- **Speculative/Critical:** Provocative references, contrasts

### All Categories Benefit From:
- Site context (grounds the artifact in reality)
- Mood/aesthetic references (sets appropriate tone)
- User personas (if you have photo references)

## Example Workflows

### Workflow 1: Community Garden Plot Sign-Up Sheet

**Text Inputs:**
- Description: "Community garden with shared plots"
- Location: "Digbeth, Birmingham"
- Themes: "Food sovereignty, neighborhood connection"

**Images:**
1. `site-plan.png` - Shows 20 plots, tool shed, compost area
2. `plot-sketch.jpg` - Hand-drawn plot dimensions with notes
3. `garden-photo.jpg` - Photo of existing overgrown lot

**Vision Enhancement:**
- AI references specific plot numbers from plan
- Mentions actual dimensions from sketch
- Includes real site features (brick wall, tree)
- Reflects current conditions from photo

**Result:** Highly specific sign-up sheet that feels authentically site-based

### Workflow 2: Makerspace Tool Check-Out Card

**Text Inputs:**
- Description: "Shared tool library in warehouse"
- Themes: "Access to means of production, skill sharing"

**Images:**
1. `floor-plan.png` - Layout with tool zones
2. `workflow-diagram.jpg` - How borrowing works
3. `warehouse-interior.jpg` - Existing space character

**Vision Enhancement:**
- References specific tool zones from plan
- Reflects actual checkout process from diagram
- Captures industrial aesthetic from photo
- Mentions real spatial features

**Result:** Check-out card that reflects actual organizational system

### Workflow 3: Ecological Monitoring Log

**Text Inputs:**
- Description: "Wildlife monitoring in urban park"
- Themes: "Biodiversity, citizen science"

**Images:**
1. `park-map.png` - Shows monitoring points
2. `species-diagram.jpg` - Local species guide
3. `habitat-photo.jpg` - Current park conditions

**Vision Enhancement:**
- Uses actual monitoring point locations
- References species visible in diagram
- Reflects real habitat types from photo
- Grounds observations in actual site

**Result:** Field log that feels based on real ecological context

## Troubleshooting

### "Vision features not supported"

**Problem:** Selected provider doesn't support vision

**Solution:**
1. Open sidebar
2. Switch to "Anthropic" or "OpenAI"
3. Ensure API key is set in `.env`

### Images not uploading

**Problem:** File format or size issues

**Solution:**
- Check format (must be PNG, JPG, JPEG, WEBP)
- Reduce file size if over 20MB
- Try converting to PNG

### Vision interpretation seems generic

**Problem:** AI not extracting specific details

**Solution:**
- Add annotations/labels to images
- Upload higher resolution images
- Include multiple views/scales
- Combine different image types

### High costs

**Problem:** Token usage with images adds up

**Solution:**
- Use vision selectively for important projects
- Limit to 2-3 most important images
- Images are auto-resized to balance quality/cost
- Consider using fewer images for iteration

## Comparing Text-Only vs Vision-Enhanced

### Text-Only Example

**Input:**
```
Description: Community meal sharing cooperative
Location: Leeds
Themes: Food security, mutual aid
```

**Output:** Generic meal log with assumed features
- "Kitchen area" (no specifics)
- "Shared dining space" (vague)
- "Storage" (where?)

### Vision-Enhanced Example

**Input:** Same text + images showing:
- Kitchen layout with 3 cooking stations
- Dining hall with long tables
- Walk-in cold storage
- Outdoor herb garden

**Output:** Specific meal log with:
- "Cooking Station 2" (knows there are 3)
- "Long table by window" (from photo)
- "Cold storage prep instructions" (saw it in plan)
- "Fresh herbs from garden bed" (noticed outdoor space)

**Result:** Artifact feels grounded in a specific, real place

## Advanced Tips

### 1. Layer Your Visuals

Provide different scales/views:
- Wide view (site context)
- Medium view (space organization)
- Detail view (specific features)

### 2. Annotate Everything

The AI can read handwritten notes:
- Label spaces
- Add dimensions
- Write notes about intentions
- Circle important features

### 3. Show Process, Not Just Product

Include:
- Early sketches showing thinking
- Iteration comparisons
- Constraints and opportunities
- Problem-solving diagrams

### 4. Combine Types

**Example combination:**
```
Image 1: Analytical diagram (understanding)
Image 2: Concept sketch (intention)
Image 3: Reference photos (atmosphere)
```

This gives the AI both logic and feeling.

### 5. Use Real Context

Photographs of actual sites are powerful:
- Current conditions
- Existing materials
- Neighborhood character
- Environmental factors

Makes artifacts feel authentically placed.

## Next Steps

1. **Try it:** Start with a simple project + 1-2 images
2. **Compare:** Generate with and without vision to see the difference
3. **Iterate:** Experiment with different image combinations
4. **Share:** Let us know what works well!

## Questions or Issues?

- See `VISION_ENHANCEMENT.md` for technical details
- Check GitHub issues: https://github.com/robannable/DAG/issues
- Review test examples in `tests/test_image_processing.py`

Happy generating! 🎭🔍

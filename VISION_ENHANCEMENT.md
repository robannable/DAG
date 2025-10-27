# Vision Enhancement: Multimodal Input for DAG

## Concept Analysis

### Current Limitations
1. **Text-only input** - Users must articulate visual/spatial ideas in words
2. **Translation barrier** - Architects think visually but must translate to text
3. **Lost context** - Spatial relationships, proportions, materiality hard to describe
4. **No visual reference** - Cannot upload sketches, diagrams, or mood boards

### Vision Enhancement Opportunities

#### What Architects Could Upload
1. **Sketches & Drawings**
   - Hand-drawn concept sketches
   - Section drawings with annotations
   - Plan views with spatial relationships
   - Quick ideation doodles

2. **Site Context**
   - Site plans with annotations
   - Photographs of existing conditions
   - Context maps
   - Environmental diagrams

3. **Reference Materials**
   - Mood boards
   - Material palettes
   - Precedent images
   - Typological references

4. **Diagrams**
   - Program diagrams
   - Circulation studies
   - Social relationship maps
   - Flow diagrams

#### What Vision AI Can Extract

1. **Spatial Information**
   - Layout and organization
   - Proportions and scale indicators
   - Relationships between spaces
   - Circulation patterns
   - Hierarchy of spaces

2. **Annotations & Text**
   - Handwritten notes via OCR
   - Labels and dimensions
   - Material callouts
   - User annotations

3. **Visual Themes**
   - Aesthetic qualities
   - Material suggestions
   - Atmospheric intentions
   - Color palettes

4. **Context & Setting**
   - Urban/rural context
   - Density and scale
   - Existing conditions
   - Site characteristics

## Technical Implementation

### Supported AI Providers with Vision

1. **Anthropic Claude** ✅
   - Claude 3.5 Sonnet has excellent vision capabilities
   - Supports image analysis with text generation
   - Already configured in DAG

2. **OpenAI GPT-4 Vision** ✅
   - Strong vision capabilities
   - Good for architectural interpretation
   - Already supported in model config

3. **Local Models (Ollama)** ⚠️
   - LLaVA and other vision models available
   - May have lower quality for complex architectural interpretation

### Architecture Changes Required

```python
# New modules needed:
utils/
  └── image_processing.py   # Image handling, base64 encoding, validation

api/
  └── vision_providers.py   # Vision-specific API formatting

ui/
  └── image_upload.py       # Image upload components
```

### Image Upload Flow

```
User uploads image(s)
    ↓
Validate format (PNG, JPG, PDF)
    ↓
Convert to base64 or handle file upload
    ↓
Send to vision model with text prompt
    ↓
Extract visual interpretation
    ↓
Combine with text inputs
    ↓
Generate enriched artifact
```

## Enhanced Input Schema

### Before (Text Only)
```yaml
inputs:
  - project_description: text
  - location: text
  - date: text
  - user_bios: text
  - themes: text
  - category: selection
```

### After (Multimodal)
```yaml
inputs:
  - project_description: text
  - location: text
  - date: text
  - user_bios: text
  - themes: text
  - category: selection
  - sketches: [images]         # NEW
  - site_photos: [images]      # NEW
  - references: [images]       # NEW
  - interpret_visuals: boolean # NEW
```

## Enhanced Prompt Structure

### Current Prompt Pattern
```
"Create a diegetic artifact based on:
Description: {text}
Location: {text}
Themes: {text}
..."
```

### Vision-Enhanced Pattern
```
"I'm sharing visual materials for this architectural project:

[IMAGE 1: Concept sketch]
[IMAGE 2: Site plan]
[IMAGE 3: Reference images]

First, analyze these images and extract:
1. Spatial organization and relationships
2. Material intentions and aesthetic qualities
3. Scale, proportion, and atmospheric qualities
4. Any annotations or notes visible
5. Context and site characteristics

Then, combine this visual analysis with the text description:
Description: {text}
Location: {text}
...

Create a diegetic artifact that reflects both the visual and textual context."
```

## UI Enhancements

### New Components Needed

1. **Image Upload Area**
   ```python
   # In Generate tab
   with st.expander("📸 Visual Context (Optional)", expanded=False):
       uploaded_files = st.file_uploader(
           "Upload sketches, diagrams, or reference images",
           type=["png", "jpg", "jpeg", "pdf"],
           accept_multiple_files=True
       )
   ```

2. **Image Preview Grid**
   - Show thumbnails of uploaded images
   - Option to remove images
   - Caption/label each image

3. **Vision Analysis Toggle**
   - Checkbox: "Use AI vision to interpret images"
   - Shows estimated token usage (images consume more tokens)

4. **Visual Interpretation Display**
   - Show AI's interpretation of images
   - Helps user understand what the model "sees"

## Artifact Category Enhancements

Some categories would particularly benefit from visual input:

### High Value for Vision
1. **Device/Object** - See actual sketches of the object
2. **Ecological/More-than-human** - Site photos, ecosystem diagrams
3. **Community/Collective** - Social diagrams, gathering space layouts
4. **Maintenance/Care** - Process diagrams, workflow sketches

### Medium Value for Vision
5. **Economic/Resource** - Flow diagrams, resource maps
6. **Institutional/Formal** - Organizational charts, building layouts

### All categories can benefit from:**
- Site context photos
- Mood boards for tone/atmosphere
- Reference images for style

## Quality Improvements Expected

### Before (Text Only)
```
Input: "A community garden with shared tool library in Birmingham"
Output: Generic artifact, relies on model's assumptions
```

### After (With Vision)
```
Input: "A community garden..."
       + [Sketch showing layout]
       + [Photo of actual site]
       + [Reference: tool sharing system]

Output: Highly specific artifact reflecting actual:
- Site constraints and opportunities
- Proposed spatial organization
- Intended aesthetic and materials
- Social relationships depicted
```

## Implementation Priority

### Phase 1: Basic Vision (Quick Win)
- [ ] Image upload component
- [ ] Base64 encoding for images
- [ ] Send to Anthropic Claude with vision
- [ ] Basic prompt enhancement
- [ ] Display interpreted content

### Phase 2: Enhanced Features
- [ ] Multiple image support
- [ ] Image labeling/captions
- [ ] PDF upload support (extract pages)
- [ ] OCR for handwritten notes
- [ ] Vision interpretation preview

### Phase 3: Advanced Features
- [ ] Image annotation tools
- [ ] Highlight regions of interest
- [ ] Multi-image comparison
- [ ] Save image context with artifacts
- [ ] Gallery view with image thumbnails

## Cost Considerations

Vision API calls are more expensive:
- Claude: ~$0.024 per image (1024x1024)
- GPT-4 Vision: ~$0.01-0.03 per image

**Mitigation strategies:**
1. Optional feature (user chooses when to use)
2. Image resize/compression before sending
3. Show estimated cost before generation
4. Limit to 3-5 images per artifact

## Use Case Examples

### Example 1: Community Meal Sharing System
**Text Input:** "A neighborhood meal sharing cooperative"

**Visual Inputs:**
- Sketch of community kitchen layout
- Diagram of meal exchange flow
- Photo of neighborhood context

**Enhanced Output:** Meal log book that references specific spatial features, actual neighborhood characteristics, and social dynamics visible in diagrams

### Example 2: Tool Library in Makerspace
**Text Input:** "Shared tool library for local makers"

**Visual Inputs:**
- Floor plan sketch with tool zones
- Photo of existing space
- Reference images of tool organization systems

**Enhanced Output:** Check-out card that reflects actual spatial organization, specific tools visible in plans, and realistic usage patterns

### Example 3: Ecological Monitoring Station
**Text Input:** "Wildlife monitoring station in urban park"

**Visual Inputs:**
- Site plan showing monitoring locations
- Ecosystem diagram
- Photos of park conditions

**Enhanced Output:** Field observation log that incorporates real site features, specific species from context, and reflects actual spatial relationships

## Next Steps

1. **Create proof of concept** with basic image upload
2. **Test with Anthropic Claude Vision** (already available)
3. **Gather feedback** on interpretation quality
4. **Iterate on prompt engineering** for architectural context
5. **Expand to multiple images** and advanced features

## Questions to Consider

1. **How many images is optimal?** (1-3 for focused context? 5-10 for rich context?)
2. **Should images be required or optional?** (Optional keeps existing workflow)
3. **Show vision interpretation to user?** (Transparency vs. cluttered UI)
4. **Save images with artifacts?** (Privacy/storage considerations)
5. **Support PDF uploads?** (Architects often have multi-page documents)

This enhancement would transform DAG from a text-based tool into a truly multimodal design artifact generator that works the way architects actually think and communicate.

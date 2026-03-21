---
name: gemini-image
description: "Generate images with Gemini 3.1 Flash. Create images for web UI (icons, banners, backgrounds, illustrations, logos, thumbnails, diagrams, etc.) from a text prompt and save to file. Can also reference existing images for style conversion, dark mode switching, and color changes. This skill MUST be used whenever the user requests image generation, drawing, creating icons/banners/logos/illustrations, image conversion, UI mockup creation, visual asset production, or any similar task. Even if the user does not explicitly use the word 'image', this skill should be used whenever the context requires creating visual assets."
---

# Gemini Image — AI Image Generation

A skill that generates images using the Gemini 3.1 Flash Image Preview model. You can create new images from text prompts alone, or transform existing images by providing references.

## Prerequisites

Verify the following before running the script:

1. **API Key**: The `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable must be set. If present in a `.env` file at the project root, it will be loaded automatically.
2. **Python Package**: The `google-genai` package is required. The script attempts auto-installation if missing, but if that fails, install manually:
   ```bash
   pip install google-genai
   ```

If no API key is available, direct the user to obtain one at https://aistudio.google.com/apikey.

## Execution

Script path: `.claude/skills/gemini-image/scripts/generate_image.py`

```bash
# Basic: prompt only
python3 .claude/skills/gemini-image/scripts/generate_image.py "prompt" -o output_path.png

# Aspect ratio + size
python3 .claude/skills/gemini-image/scripts/generate_image.py "prompt" -o out.png --aspect 16:9 --size 2K

# Reference image-based transformation
python3 .claude/skills/gemini-image/scripts/generate_image.py "Convert this image to dark theme" -r reference.png -o result.png

# Multiple generations (for comparing variations)
python3 .claude/skills/gemini-image/scripts/generate_image.py "prompt" -o out.png -n 3

# Google Search reference (for latest trends)
python3 .claude/skills/gemini-image/scripts/generate_image.py "trending web UI banner" --search -o banner.png
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt` (required) | - | Image generation prompt. English recommended (better quality) |
| `-o, --output` | `generated_image.png` | Output file path (PNG/JPEG/WEBP) |
| `--aspect` | auto | Aspect ratio: `1:1`, `16:9`, `9:16`, `3:4`, `4:3` |
| `--size` | `1K` | Image size: `1K` (1024px), `2K` (2048px) |
| `--thinking` | `MINIMAL` | Thinking level. `MEDIUM` or higher recommended for complex images |
| `-r, --reference` | - | Reference image path (can be used multiple times) |
| `--search` | off | Enable Google Search tool (for trend/style references) |
| `-n, --count` | 1 | Number of images to generate (max 5) |
| `--model` | `gemini-3.1-flash-image-preview` | Gemini model to use (default: Flash 3.1, no need to specify) |

## Workflow

When an image generation request is received, proceed in the following order:

1. **Identify purpose**: Determine the intended use — icon, banner, illustration, logo, background, thumbnail, etc.
2. **Determine output path**: Choose a path that fits the project structure (see rules below)
3. **Compose prompt**: Write a detailed prompt in English following the guide below
4. **Select parameters**: Set aspect ratio, size, and thinking level appropriate for the use case
5. **Run generation**: Execute the script
6. **Verify result**: Use the Read tool to show the generated image to the user

## Prompt Writing Guide

The key to a good prompt is **specificity**. Instead of "a nice icon", specify the color, style, size, background, and purpose.

### Prompt Structure
Effective prompt structure: `[subject] + [style] + [color/mood] + [technical requirements]`

### Web UI Icons/Logos
```
"Minimalist flat icon of a [specific object], [primary color] color, on [background color] background, clean edges, no text, suitable for 256x256 web icon"
```
- Use `--aspect 1:1`
- For transparent background, specify "transparent background" or "on white background"

### Hero Banners/Backgrounds
```
"Wide cinematic hero banner for [topic/service], [mood] atmosphere, smooth gradient from [color1] to [color2], modern and professional, no text overlay, 16:9"
```
- Use `--aspect 16:9 --size 2K`

### Illustrations/Characters
```
"[style] style illustration of [subject], [specific description], [color palette], clean composition, high detail"
```
- Style examples: flat, isometric, watercolor, pixel art, line art, kawaii
- `--thinking MEDIUM` or higher recommended (for complex scenes)

### Thumbnails/Social Cards
```
"Eye-catching thumbnail for [topic], bold visual, [color] dominant color, engaging composition, 16:9"
```

### UI Mockup Conversion
Pass a reference image with `-r` and provide conversion instructions:
```bash
python3 .claude/skills/gemini-image/scripts/generate_image.py \
  "Convert this UI to dark mode, change accent color to electric blue, keep layout" \
  -r current_ui.png -o dark_ui.png
```

### Diagrams/Infographics
```
"Clean technical diagram showing [structure/flow], minimalist style, [color] color scheme, labeled sections, white background"
```
- `--thinking HIGH` recommended (requires logical structure)

## Rules

- **Output path**: When saving within a project, use the appropriate asset directory
  - Frontend: `public/images/`, `src/assets/`, etc.
  - Documentation: `docs/images/`
  - General: user-specified path
- **Model**: Default is `gemini-3.1-flash-image-preview` (auto-selected, no need to change)
- **Limit bulk generation**: Keep `-n` value at 5 or below (API cost and speed)
- **Prompt language**: Prompts should be written in English for better quality. Even if the user requests in another language, translate the prompt to English before passing it
- **Verify results**: Always use the Read tool to show the generated image to the user after generation

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `google-genai package is required` | Package not installed | `pip install google-genai` |
| `API_KEY environment variable is not set` | No API key | Add `GEMINI_API_KEY=...` to `.env` |
| `No images were generated` | Prompt rejected or API error | Make the prompt more specific, remove inappropriate content |
| `429 Too Many Requests` | API rate limit exceeded | Wait and retry (script retries automatically) |
| `Reference image not found` | Incorrect file path | Verify absolute path or correct relative path |

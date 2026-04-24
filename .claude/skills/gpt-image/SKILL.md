---
name: gpt-image
description: "Generate images with OpenAI's gpt-image model using the user's ChatGPT Plus/Pro subscription (no API key required). Create images for web UI (icons, banners, backgrounds, illustrations, logos, thumbnails, diagrams, etc.) from a text prompt and save to file. Can also transform existing images (style conversion, dark mode switch, color change, image-to-image restyle). This skill MUST be used whenever the user requests image generation, drawing, creating icons/banners/logos/illustrations, image conversion, UI mockup creation, visual asset production, or any similar task. Even if the user does not explicitly use the word 'image', use this skill whenever the context requires creating visual assets. Keywords: image generation, 이미지 생성, 배너 만들어, 아이콘 생성, 로고 만들어, 일러스트 생성, gpt image, 그림 그려줘, imagine, 이미지 만들어줘."
---

# GPT Image — AI Image Generation via ChatGPT Subscription

A skill that generates and edits images through OpenAI's `gpt-image` model, billed against the user's ChatGPT Plus/Pro subscription — no OpenAI API key required. A local OAuth proxy reuses the Codex CLI session stored in `~/.codex/auth.json`.

## Prerequisites

Verify the following before running the scripts:

1. **Node.js ≥ 18** — scripts use native `fetch`, `AbortSignal.timeout`, and ES modules.
2. **Codex OAuth session** — `~/.codex/auth.json` (or `~/.chatgpt-local/auth.json`) must exist. If neither is present, tell the user to run once in their own terminal:
   ```bash
   npx @openai/codex login
   ```
   Do **not** attempt to log in on the user's behalf — it needs interactive browser auth.
3. **ChatGPT Plus or Pro subscription** with image quota available.
4. **npx available** — scripts spawn `npx openai-oauth --port 10531` automatically. `openai-oauth` is fetched on first run; no manual install needed.

See `reference/installation.md` for deeper setup, port conflicts, re-login, and troubleshooting.

## Execution

Scripts live at `.claude/skills/gpt-image/scripts/`.

```bash
# Basic: prompt only → saves to ./images/gpt-img_<timestamp>_0.png
node .claude/skills/gpt-image/scripts/generate.js --prompt "prompt here"

# Specify size + quality + count
node .claude/skills/gpt-image/scripts/generate.js \
  --prompt "prompt here" --size 1536x1024 --quality high --n 2

# Custom output directory
node .claude/skills/gpt-image/scripts/generate.js \
  --prompt "prompt here" --out-dir ./public/images

# Image → image (restyle an existing image)
node .claude/skills/gpt-image/scripts/edit.js \
  --input reference.png --prompt "convert to dark theme" \
  --out ./images/result.png

# Verify a PNG manually (generate/edit already calls this)
node .claude/skills/gpt-image/scripts/verify.js --input ./images/result.png
```

Run from the **project root** so relative paths like `./images/` resolve to the project folder.

## Parameters

### `generate.js` (text → image)

| Flag | Required | Values | Default |
|------|----------|--------|---------|
| `--prompt` | yes | free text (English recommended) | — |
| `--n` | no | `1` – `8` | `1` |
| `--size` | no | `1024x1024` (1:1) \| `1024x1536` (2:3 portrait) \| `1536x1024` (3:2 landscape) | `1024x1024` |
| `--quality` | no | `low` \| `medium` \| `high` | `medium` |
| `--format` | no | `png` \| `jpeg` \| `webp` | `png` |
| `--out-dir` | no | any path | `./images` |

### `edit.js` (image → image)

| Flag | Required | Values | Default |
|------|----------|--------|---------|
| `--input` | yes | path to source image | — |
| `--prompt` | yes | transformation description | — |
| `--out` | yes | output file path | — |
| `--quality` | no | `low` \| `medium` \| `high` | `medium` |
| `--size` | no | same as `generate.js` | `1024x1024` |
| `--format` | no | `png` \| `jpeg` \| `webp` | `png` |

`edit.js` preserves the source composition, subject, and pose while applying the requested transformation.

## Workflow

When you receive an image generation request:

1. **Identify purpose** — icon, banner, illustration, logo, background, thumbnail, mockup, etc.
2. **Pick size by aspect**:
   - Square (icons, avatars, logos, social posts) → `1024x1024`
   - Portrait (posters, character art, phone wallpapers) → `1024x1536`
   - Landscape (hero banners, desktop backgrounds, wide scenes) → `1536x1024`
3. **Pick quality**:
   - `medium` — default for normal use.
   - `high` — only when the user explicitly says "high quality", "detailed", "polished", "hero shot", or when producing final production assets.
   - `low` — quick drafts / ideation.
4. **Compose prompt** — write specific English prompts. Even if the user asks in Korean, translate to English before passing. The model handles typography (text inside images) well; pass text content verbatim.
5. **Determine output path** — project-appropriate location (see Rules below).
6. **Run the script** — `generate.js` or `edit.js`. Both auto-start and auto-kill the OAuth proxy.
7. **Verify result** — scripts auto-run PNG validation and print ✅/❌. Use the Read tool to show the generated image to the user.

## Prompt Writing Guide

Effective structure: `[subject] + [style] + [color/mood] + [technical requirements]`.

Pass the user's intent through as specifically as possible. The model follows prompts literally — do **not** wrap with extra "quality boosters" (the scripts append a developer prompt that handles that). Avoid contradicting the user (e.g. don't add "photorealistic" when they asked for "flat illustration").

### Web UI Icons / Logos
```
"Minimalist flat icon of [subject], [primary color] on [background] background, clean edges, no text, 256×256 web icon"
```
→ `--size 1024x1024`. For transparent look, say "transparent background" or "solid white background".

### Hero Banners / Backgrounds
```
"Wide cinematic hero banner for [topic/service], [mood] atmosphere, smooth gradient from [color1] to [color2], modern and professional, no text overlay"
```
→ `--size 1536x1024 --quality high`.

### Illustrations / Characters
```
"[style] illustration of [subject], [specific description], [color palette], clean composition, high detail"
```
Styles: flat, isometric, watercolor, pixel art, line art, kawaii. Use `--size 1024x1536` for tall character portraits.

### Thumbnails / Social Cards
```
"Eye-catching thumbnail for [topic], bold visual, [color] dominant, engaging composition"
```
→ `--size 1536x1024`. For multiple variations, use `--n 3` (or up to 8).

### UI Dark-Mode Conversion
Use `edit.js` with the existing UI screenshot:
```bash
node .claude/skills/gpt-image/scripts/edit.js \
  --input current_ui.png \
  --prompt "Convert this UI to dark mode, keep layout identical, change accent to electric blue" \
  --out dark_ui.png
```

### Diagrams / Infographics
```
"Clean technical diagram showing [structure/flow], minimalist style, [color] scheme, labeled sections, white background"
```
→ `--quality high` (logical structure benefits from more compute).

## Rules

- **Output path defaults to `./images/` in the project**. Override with `--out-dir` for generate or `--out` for edit. Suggested conventions:
  - Frontend assets: `public/images/`, `src/assets/`
  - Documentation: `docs/images/`
  - Scratch: default `./images/`
- **File naming**: `generate.js` produces `gpt-img_<unix-ms>_<index>.<ext>`. Parallel runs won't collide.
- **Keep `--n` ≤ 8** (hard cap). For normal use stay at 1–3 to respect subscription quota.
- **Prompt language**: English produces better quality. Translate Korean/other languages before passing.
- **Verify output**: scripts auto-validate PNGs and print ✅/❌. If `❌ Verification failed`, re-run that single prompt once; if it fails again, surface the error to the user instead of silently retrying.
- **Never bypass the OAuth proxy** by asking for an API key. This skill is explicitly designed around the ChatGPT subscription flow.

## Failure Handling

If a script exits with one of these, stop and point the user at `reference/installation.md`:

| Error | Cause | Action |
|-------|-------|--------|
| `No OAuth session found` | `auth.json` missing | User runs `npx @openai/codex login` |
| `Proxy did not respond` / `OAuth proxy failed to start` | Port 10531 busy or `openai-oauth` unreachable | `lsof -ti:10531 \| xargs kill -9`, retry |
| `OAuth proxy returned 401` / `403` | Token expired | Re-run `npx @openai/codex login` |
| `OAuth proxy returned 429` / `Rate limit` | Hit ChatGPT tier cap | Wait; reduce `--n`; drop quality |
| `No image data received` | Stream interrupted or model refused | Retry once; if persistent, simplify prompt |
| `❌ Verification failed` | Corrupt write (usually truncated stream) | Re-run the same prompt once |

These are user-side credential/quota issues; resolving them requires the user's own terminal.

## Layout

```
gpt-image/
├── SKILL.md                   ← this file
├── config.json                ← defaults (quality / size / format / output_dir)
├── scripts/
│   ├── generate.js            ← text → image
│   ├── edit.js                ← image → image
│   └── verify.js              ← PNG integrity check (also used internally)
├── reference/
│   └── installation.md        ← setup, config, troubleshooting deep-dive
└── evals/
    └── evals.json             ← 3 eval scenarios (logo, hero banner, thumbnails)
```

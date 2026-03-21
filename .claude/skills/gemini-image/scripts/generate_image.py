#!/usr/bin/env python3
"""Gemini image generation script.

Usage:
    python generate_image.py "prompt" [options]

Examples:
    # Basic generation
    python generate_image.py "minimalist flat logo, tech startup theme"

    # Output path + aspect ratio
    python generate_image.py "wide hero banner, dark gradient" -o banner.png --aspect 16:9

    # 2K high resolution
    python generate_image.py "detailed infographic" -o info.png --size 2K

    # Reference image-based transformation
    python generate_image.py "Convert to dark mode" -r reference.png -o dark.png

    # Multiple generations
    python generate_image.py "blog thumbnail, modern AI theme" -o thumb.png -n 3
"""

import argparse
import mimetypes
import os
import subprocess
import sys
import time
from pathlib import Path

VALID_ASPECTS = {"1:1", "16:9", "9:16", "3:4", "4:3"}
MAX_RETRIES = 2
RETRY_DELAY = 3

# Image-capable models in priority order
IMAGE_MODELS = [
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-preview-image-generation",
]

THINKING_BUDGET = {
    "NONE": 0,
    "MINIMAL": 128,
    "LOW": 1024,
    "MEDIUM": 4096,
    "HIGH": 8192,
}


def _ensure_genai_installed():
    """Auto-install google-genai package if not found."""
    try:
        import google.genai  # noqa: F401
        return True
    except ImportError:
        print("Installing google-genai package...", file=sys.stderr)
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "google-genai"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("google-genai installation complete.", file=sys.stderr)
            return True
        except subprocess.CalledProcessError:
            print(
                "ERROR: Failed to auto-install google-genai. Please install manually: pip install google-genai",
                file=sys.stderr,
            )
            sys.exit(1)


_ensure_genai_installed()

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402


def _find_project_root() -> Path:
    """Find project root by looking for git root or a directory containing .env."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / ".env").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    return Path.cwd()


def _load_env_files():
    """Auto-load API keys from project .env files."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return

    project_root = _find_project_root()

    for env_name in (".env", ".env.local", ".env.production"):
        env_file = project_root / env_name
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key in ("GOOGLE_API_KEY", "GEMINI_API_KEY") and value:
                os.environ[key] = value
                return


_load_env_files()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate images with Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("-o", "--output", default=None, help="Output file path (default: generated_image.png)")
    parser.add_argument("--aspect", default=None, help="Aspect ratio (e.g., 1:1, 16:9, 9:16, 3:4, 4:3)")
    parser.add_argument("--size", default="1K", choices=["1K", "2K"], help="Image size (default: 1K)")
    parser.add_argument("--thinking", default="MINIMAL", choices=list(THINKING_BUDGET.keys()), help="Thinking level (default: MINIMAL)")
    parser.add_argument("-r", "--reference", action="append", default=[], help="Reference image path (can specify multiple)")
    parser.add_argument("--search", action="store_true", help="Enable Google Search tool")
    parser.add_argument("--model", default=None, help="Model (auto-selected)")
    parser.add_argument("-n", "--count", type=int, default=1, help="Number of images to generate (default: 1, max: 5)")
    args = parser.parse_args()

    if args.aspect and args.aspect not in VALID_ASPECTS:
        parser.error(f"Invalid aspect ratio: {args.aspect}. Allowed values: {', '.join(sorted(VALID_ASPECTS))}")
    if args.count < 1 or args.count > 5:
        parser.error(f"Count must be between 1 and 5: {args.count}")
    for ref_path in args.reference:
        if not Path(ref_path).exists():
            parser.error(f"Reference image not found: {ref_path}")

    return args


def load_reference_image(path: str) -> types.Part:
    """Load a reference image as a Part."""
    file_path = Path(path)
    mime_type = mimetypes.guess_type(str(file_path))[0] or "image/png"
    data = file_path.read_bytes()
    return types.Part.from_bytes(data=data, mime_type=mime_type)


def _find_working_model(client) -> str:
    """Try image models in order and return the first one that works."""
    for model_name in IMAGE_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Generate a 1x1 white pixel",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            if response.candidates:
                print(f"Using model: {model_name}", file=sys.stderr)
                return model_name
        except Exception:
            continue
    # If all models fail, fall back to the first model (for error message purposes)
    print(f"WARNING: Auto-detection failed, using {IMAGE_MODELS[0]}", file=sys.stderr)
    return IMAGE_MODELS[0]


def _build_enhanced_prompt(prompt: str, aspect: str | None, size: str) -> str:
    """Include aspect ratio and size requirements in the prompt."""
    parts = [prompt]
    if aspect:
        parts.append(f"Aspect ratio: {aspect}.")
    if size == "2K":
        parts.append("High resolution, detailed, 2048px.")
    return " ".join(parts)


def _generate_once(client, model, contents, config):
    """Single generation attempt. Returns (image data list, text list)."""
    images = []
    texts = []

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                images.append(part.inline_data)
            elif part.text:
                texts.append(part.text)

    return images, texts


def generate_image(args):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            "ERROR: GEMINI_API_KEY or GOOGLE_API_KEY environment variable is not set.\n"
            "  1. Get an API key at https://aistudio.google.com/apikey\n"
            "  2. Add GEMINI_API_KEY=your_key to your project .env file\n"
            "     or run: export GEMINI_API_KEY=your_key",
            file=sys.stderr,
        )
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Determine model: default to gemini-3.1-flash-image-preview
    model = args.model or IMAGE_MODELS[0]

    # Build prompt with aspect/size hints
    enhanced_prompt = _build_enhanced_prompt(args.prompt, args.aspect, args.size)

    # Build parts
    parts = []
    for ref_path in args.reference:
        parts.append(load_reference_image(ref_path))
    parts.append(types.Part.from_text(text=enhanced_prompt))

    contents = [types.Content(role="user", parts=parts)]

    # Tools
    tools = []
    if args.search:
        tools.append(types.Tool(google_search=types.GoogleSearch()))

    # Config
    config_kwargs = {
        "response_modalities": ["IMAGE", "TEXT"],
    }

    # Thinking config
    budget = THINKING_BUDGET.get(args.thinking, 128)
    if budget > 0:
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinkingBudget=budget)

    if tools:
        config_kwargs["tools"] = tools

    config = types.GenerateContentConfig(**config_kwargs)

    # Determine output path
    output_base = args.output or "generated_image.png"
    output_path = Path(output_base)

    file_index = 0
    image_count = 0
    all_text_parts = []

    print(f"Generating with model={model}, aspect={args.aspect or 'auto'}, size={args.size}...")

    for attempt_num in range(args.count):
        last_error = None
        for retry in range(MAX_RETRIES + 1):
            try:
                images, texts = _generate_once(client, model, contents, config)
                all_text_parts.extend(texts)

                for inline_data in images:
                    ext = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                    if ext == ".jpeg":
                        ext = ".jpg"
                    if args.count == 1 and file_index == 0:
                        save_path = output_path.with_suffix(ext) if output_path.suffix != ext else output_path
                    else:
                        stem = output_path.stem
                        parent = output_path.parent
                        save_path = parent / f"{stem}_{file_index}{ext}"
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_bytes(inline_data.data)
                    size_kb = len(inline_data.data) / 1024
                    print(f"OK: {save_path} ({size_kb:.1f} KB)")
                    file_index += 1
                    image_count += 1

                last_error = None
                break

            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if retry < MAX_RETRIES:
                        wait = RETRY_DELAY * (retry + 1)
                        print(f"Rate limited, retrying in {wait}s... ({retry + 1}/{MAX_RETRIES})", file=sys.stderr)
                        time.sleep(wait)
                        continue
                print(f"ERROR: Image generation failed (image {attempt_num + 1}): {e}", file=sys.stderr)
                break

    if all_text_parts:
        print("\n--- Model Response ---")
        print("".join(all_text_parts))

    if image_count == 0:
        print("WARNING: No images were generated. Try making the prompt more specific.", file=sys.stderr)
        sys.exit(1)

    print(f"\nTotal: {image_count} image(s) generated")


if __name__ == "__main__":
    args = parse_args()
    generate_image(args)

#!/usr/bin/env python3
"""Generate 3 thumbnail variations using Gemini, compatible with installed google-genai."""
import os, sys, base64
from pathlib import Path
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY not set"); sys.exit(1)

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash-image"

PROMPT = (
    "Eye-catching blog post thumbnail about AI and the Future, "
    "modern minimalist design, futuristic technology aesthetic, "
    "abstract neural network and circuit patterns, "
    "bold gradient from deep electric blue to vivid purple, "
    "clean composition with dynamic geometric shapes, "
    "glowing light accents, professional and sleek, no text overlay, 16:9 aspect ratio"
)

OUTPUT_DIR = Path("/home/lazydok/src/cc-skills-template/gemini-image-workspace/iteration-1/multi-thumbnail/with_skill/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for i in range(3):
    print(f"\n--- Generating image {i} of 3 ---")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=PROMPT,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        saved = False
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                out_path = OUTPUT_DIR / f"ai-future_{i}.png"
                out_path.write_bytes(part.inline_data.data)
                print(f"Saved: {out_path} ({len(part.inline_data.data)} bytes)")
                saved = True
                break
            elif part.text:
                print(f"Text response: {part.text[:200]}")

        if not saved:
            print(f"Warning: No image generated for variation {i}")
    except Exception as e:
        print(f"Error generating image {i}: {e}")

print("\nDone!")

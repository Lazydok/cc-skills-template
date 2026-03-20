#!/usr/bin/env python3
"""Gemini 3.1 Flash 이미지 생성 스크립트.

Usage:
    python generate_image.py "프롬프트" [옵션]

Examples:
    # 기본 생성
    python generate_image.py "minimalist flat logo, tech startup theme"

    # 출력 경로 + 종횡비 지정
    python generate_image.py "wide hero banner, dark gradient" -o banner.png --aspect 16:9

    # 2K 고해상도 + 참조 이미지
    python generate_image.py "이 UI를 dark 모드로 변환" --size 2K -r reference.png

    # thinking 레벨 조정
    python generate_image.py "복잡한 인포그래픽" --thinking MEDIUM
"""

import argparse
import mimetypes
import os
import sys
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai 패키지가 필요합니다. pip install google-genai", file=sys.stderr)
    sys.exit(1)


def _load_env_files():
    """프로젝트 .env 파일들에서 API 키를 자동 로드."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return  # 이미 설정됨

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[3]  # .claude/skills/gemini-image/scripts/ → root

    env_candidates = [
        project_root / ".env",
        project_root / ".env.local",
        project_root / ".env.production",
    ]

    for env_file in env_candidates:
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
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
        description="Gemini 3.1 Flash로 이미지 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("prompt", help="이미지 생성 프롬프트")
    parser.add_argument("-o", "--output", default=None, help="출력 파일 경로 (기본: generated_image.png)")
    parser.add_argument("--aspect", default=None, help="종횡비 (예: 1:1, 16:9, 9:16, 3:4, 4:3)")
    parser.add_argument("--size", default="1K", choices=["1K", "2K"], help="이미지 크기 (기본: 1K)")
    parser.add_argument("--thinking", default="MINIMAL", choices=["NONE", "MINIMAL", "LOW", "MEDIUM", "HIGH"], help="Thinking 레벨 (기본: MINIMAL)")
    parser.add_argument("-r", "--reference", action="append", default=[], help="참조 이미지 경로 (여러 개 가능)")
    parser.add_argument("--search", action="store_true", help="Google 검색 도구 활성화")
    parser.add_argument("--model", default="gemini-3.1-flash-image-preview", help="모델 (기본: gemini-3.1-flash-image-preview)")
    parser.add_argument("-n", "--count", type=int, default=1, help="생성할 이미지 수 (기본: 1)")
    return parser.parse_args()


def load_reference_image(path: str) -> types.Part:
    """참조 이미지를 Part로 로드."""
    file_path = Path(path)
    if not file_path.exists():
        print(f"ERROR: 참조 이미지를 찾을 수 없습니다: {path}", file=sys.stderr)
        sys.exit(1)
    mime_type = mimetypes.guess_type(str(file_path))[0] or "image/png"
    data = file_path.read_bytes()
    return types.Part.from_bytes(data=data, mime_type=mime_type)


def generate_image(args):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Build parts
    parts = []
    for ref_path in args.reference:
        parts.append(load_reference_image(ref_path))
    parts.append(types.Part.from_text(text=args.prompt))

    contents = [types.Content(role="user", parts=parts)]

    # Tools
    tools = []
    if args.search:
        tools.append(
            types.Tool(
                googleSearch=types.GoogleSearch(
                    search_types=types.SearchTypes(web_search=types.WebSearch())
                )
            )
        )

    # Config
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=args.thinking),
        image_config=types.ImageConfig(
            aspect_ratio=args.aspect,
            image_size=args.size,
        ),
        response_modalities=["IMAGE", "TEXT"],
        tools=tools if tools else None,
    )

    # Determine output path
    output_base = args.output or "generated_image.png"
    output_path = Path(output_base)

    file_index = 0
    image_count = 0
    text_parts = []

    print(f"Generating with model={args.model}, aspect={args.aspect or 'auto'}, size={args.size or '1K'}...")

    for attempt in range(args.count):
        try:
            for chunk in client.models.generate_content_stream(
                model=args.model,
                contents=contents,
                config=config,
            ):
                if chunk.parts is None:
                    continue
                for part in chunk.parts:
                    if part.inline_data and part.inline_data.data:
                        ext = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                        if args.count == 1 and file_index == 0:
                            # 단일 이미지: 지정된 이름 사용
                            save_path = output_path.with_suffix(ext) if output_path.suffix != ext else output_path
                        else:
                            # 다중 이미지: 번호 붙이기
                            stem = output_path.stem
                            parent = output_path.parent
                            save_path = parent / f"{stem}_{file_index}{ext}"
                        save_path.parent.mkdir(parents=True, exist_ok=True)
                        save_path.write_bytes(part.inline_data.data)
                        print(f"OK: {save_path} ({len(part.inline_data.data)} bytes)")
                        file_index += 1
                        image_count += 1
                    elif part.text:
                        text_parts.append(part.text)
        except Exception as e:
            print(f"ERROR: 이미지 생성 실패 (attempt {attempt + 1}): {e}", file=sys.stderr)

    if text_parts:
        print("\n--- Model Response ---")
        print("".join(text_parts))

    if image_count == 0:
        print("WARNING: 이미지가 생성되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"\nTotal: {image_count} image(s) generated")


if __name__ == "__main__":
    args = parse_args()
    generate_image(args)

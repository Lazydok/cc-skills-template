---
name: gemini-image
description: "Gemini 3.1 Flash로 이미지 생성. 웹 UI용 이미지(아이콘, 배너, 배경, 일러스트, 로고 등)를 프롬프트로 생성하고 파일로 저장. 키워드: 이미지 생성, image generate, 배너 만들어, 아이콘 생성, 로고 만들어, 일러스트 생성, gemini image, 이미지 만들어줘, 그림 그려줘"
---

# Gemini Image — AI 이미지 생성

Gemini 3.1 Flash Image Preview 모델로 이미지를 생성한다.

## 실행

```bash
# 기본: 프롬프트만
python3 .claude/skills/gemini-image/scripts/generate_image.py "프롬프트" -o 출력경로.png

# 종횡비 + 크기 지정
python3 .claude/skills/gemini-image/scripts/generate_image.py "프롬프트" -o out.png --aspect 16:9 --size 2K

# 참조 이미지 기반 변환
python3 .claude/skills/gemini-image/scripts/generate_image.py "이 이미지를 dark 테마로" -r reference.png -o result.png

# 다중 생성
python3 .claude/skills/gemini-image/scripts/generate_image.py "프롬프트" -o out.png -n 3

# Google 검색 참조
python3 .claude/skills/gemini-image/scripts/generate_image.py "최신 트렌드 웹 UI 배너" --search -o banner.png
```

## 파라미터

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `prompt` (필수) | - | 이미지 생성 프롬프트 |
| `-o, --output` | `generated_image.png` | 출력 파일 경로 |
| `--aspect` | auto | 종횡비: `1:1`, `16:9`, `9:16`, `3:4`, `4:3` |
| `--size` | `1K` | 이미지 크기: `1K`, `2K` |
| `--thinking` | `MINIMAL` | Thinking: `NONE`, `MINIMAL`, `LOW`, `MEDIUM`, `HIGH` |
| `-r, --reference` | - | 참조 이미지 (여러 번 사용 가능) |
| `--search` | off | Google 검색 도구 활성화 |
| `-n, --count` | 1 | 생성할 이미지 수 |
| `--model` | `gemini-3.1-flash-image-preview` | 사용할 Gemini 모델 |

## 사용 시나리오별 프롬프트 가이드

### 웹 UI 아이콘/로고
```
"Minimalist flat icon for [기능], [주색상] on [배경색] background, 256x256, no text"
```

### 히어로 배너/배경
```
"Wide hero banner, [테마] atmosphere, gradient from dark to [색상], 16:9 aspect ratio, web-ready"
```

### 일러스트/캐릭터
```
"[테마] themed illustration, [설명], [스타일] style, vibrant colors"
```

### UI 목업 변환
참조 이미지를 `-r`로 전달하고 변환 지시:
```
python3 ... "Convert this UI to dark mode with [accent color] accents" -r current_ui.png -o dark_ui.png
```

## 규칙

- **API 키**: `GEMINI_API_KEY` 환경변수 필수
- **출력 경로**: 프로젝트 내 저장 시 `docs/screenshots/` 또는 `frontend/public/` 하위 권장
- **모델 고정**: `gemini-3.1-flash-image-preview` (변경 불필요)
- **대량 생성 자제**: `-n` 값은 5 이하 권장 (API 비용)

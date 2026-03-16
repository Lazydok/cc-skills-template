# CC Skills Template

Claude Code의 능력을 극대화하는 **스킬 템플릿 모음**입니다.
간단한 프롬프트 하나로 여러 AI 에이전트가 팀을 이루어 병렬로 작업하고, 서로 교차검증하며, 단일 에이전트보다 더 빠르고 정확한 결과를 만들어냅니다.

![Subagents vs Agent Teams](images/01-subagents-vs-agent-teams.png)
> **Subagents vs Agent Teams**: Subagents는 개별 결과를 반환하는 독립 워커인 반면, Agent Teams는 공유 태스크 리스트와 양방향 통신으로 협업하는 팀입니다.

---

## 포함된 스킬

```
.claude/skills/
├── gemini-cli/                          # Google Gemini CLI 서브에이전트
│   ├── SKILL.md (101줄)                 # 핵심 호출 패턴 5가지 + 플래그 + 제한사항
│   └── references/
│       └── invocation-patterns.md       # JSON envelope, 동시실행, 에러코드, 빌트인 툴
│
├── codex-cli/                           # OpenAI Codex CLI 서브에이전트
│   ├── SKILL.md (157줄)                 # exec 패턴 5가지 + 구조화출력 + 리뷰모드
│   └── references/
│       ├── invocation-patterns.md       # 전체 플래그, 샌드박스, JSONL, MCP 서버
│       └── review-patterns.md           # 코드리뷰/보안감사/테스트갭 프롬프트 템플릿
│
├── agent-teams/                         # 멀티 에이전트 팀 협업 + 교차검증
│   ├── SKILL.md (564줄)                 # 팀 구성 + 필수 앙상블 규칙 + 아티팩트 패턴
│   └── references/
│       ├── team-sizing.md               # 팀 규모 가이드 + 역할 템플릿
│       └── cross-verification.md        # 상세 워크플로 + 3-way 게이트
│
└── gemini-image/                        # Gemini 이미지 생성
    ├── SKILL.md                         # 프롬프트 가이드 + 파라미터
    └── scripts/
        └── generate_image.py            # 이미지 생성 스크립트
```

| 스킬 | 설명 | 용도 |
|------|------|------|
| **agent-teams** | 멀티 에이전트 팀 협업 | 병렬 작업, 태스크 분배, 팀 간 통신 |
| **gemini-cli** | Google Gemini CLI 서브에이전트 | 코드 리뷰, 웹 검색, 프론트엔드 분석 |
| **codex-cli** | OpenAI Codex CLI 서브에이전트 | 독립 코드 분석, 로직 검증, 보안 감사 |
| **gemini-image** | Gemini 이미지 생성 | UI 목업, 아이콘, 배너, 일러스트 생성 |

---

## 설정 가이드

### 1. Agent Teams 활성화

Agent Teams는 실험적 기능으로, 환경변수를 설정해야 활성화됩니다.

**방법 A: settings.json (권장)**

`~/.claude/settings.json` 파일에 추가:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

**방법 B: 셸 환경변수**

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude
```

> 셸 시작 시 자동 적용하려면 `~/.bashrc` 또는 `~/.zshrc`에 위 export 줄을 추가하세요.

**표시 모드 설정 (선택)**

```json
{
  "teammateMode": "tmux"
}
```

| 모드 | 설명 | 요구사항 |
|------|------|----------|
| `auto` (기본) | tmux 있으면 분할 패널, 없으면 인프로세스 | 없음 |
| `in-process` | 메인 터미널에서 `Shift+Up/Down`으로 팀원 전환 | 없음 |
| `tmux` | 각 팀원이 별도 패널에 표시 | tmux 설치 필요 |

---

### 2. Gemini Image (이미지 생성)

Gemini 3.1 Flash 모델로 이미지를 생성합니다. **유료 계정이 필요합니다.**

1. [Google AI Studio](https://aistudio.google.com/)에서 API 키 발급
2. 프로젝트 루트에 `.env` 파일 생성:

```bash
GEMINI_API_KEY=AIza...your-key-here
```

> `.env` 파일은 반드시 `.gitignore`에 추가하여 API 키가 커밋되지 않도록 하세요.

사용 예시:

```bash
python3 .claude/skills/gemini-image/scripts/generate_image.py "minimalist dashboard icon, blue" -o icon.png
python3 .claude/skills/gemini-image/scripts/generate_image.py "dark mode hero banner" -o banner.png --aspect 16:9 --size 2K
```

---

### 3. Gemini CLI (Gemini 서브에이전트)

Google Gemini CLI를 서브에이전트로 사용합니다. 코드 리뷰, 웹 검색, 프론트엔드 분석에 활용됩니다.

```bash
# 설치
npm install -g @anthropic-ai/gemini-cli

# 설치 확인 (v0.32.1 이상 필요)
gemini --version

# 최초 인증 (브라우저에서 Google 계정 로그인)
gemini
```

> 모델은 **auto**를 권장합니다. 별도 설정 없이 Gemini CLI가 자동으로 적절한 모델을 선택합니다.

---

### 4. Codex CLI (Codex 서브에이전트)

OpenAI Codex CLI를 서브에이전트로 사용합니다. 독립적인 코드 분석과 로직 검증에 활용됩니다.

```bash
# 설치
npm install -g @openai/codex

# 설치 확인 (v0.112.0 이상 필요)
codex --version

# 최초 인증 (브라우저에서 ChatGPT 계정 로그인)
codex
```

> 모델은 **auto**를 권장합니다. 별도 설정 없이 Codex CLI가 자동으로 적절한 모델을 선택합니다.

---

### 빠른 체크리스트

| 스킬 | 필요한 것 | 확인 방법 |
|------|-----------|-----------|
| Agent Teams | 환경변수 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | `~/.claude/settings.json` 확인 |
| Gemini Image | `.env`에 `GEMINI_API_KEY` 등록 | `cat .env \| grep GEMINI` |
| Gemini CLI | `gemini` 설치 + OAuth 인증 | `gemini --version` |
| Codex CLI | `codex` 설치 + ChatGPT 로그인 | `codex --version` |

---

## 교차검증 규칙 (MUST Rules)

작업 유형에 따라 **반드시** 사용해야 하는 AI 앙상블 조합입니다. **이 규칙은 비협상 사항입니다:**

| 작업 유형 | 필수 앙상블 | 이유 |
|-----------|-------------|------|
| 복잡한 코드 분석, 알고리즘, 수학/이론 | Claude + **Codex** | Codex가 논리적 추론과 코드 정확성에 뛰어남 |
| 웹 UI, 프론트엔드, 스크린샷/이미지 분석 | Claude + **Gemini** | Gemini가 VLM과 웹 검색에 뛰어남 |
| 아키텍처 설계, 계획, 제안서 | Claude + **Codex** + **Gemini** (3-way 게이트) | 3명 모두 통과해야 계획 진행 |
| 보안 감사 | Claude + **Codex** | 최소 2개 독립 보안 관점 필요 |
| 금융/트레이딩 로직 | Claude + **Codex** | 수학적 정확성 크로스체크 필수 |

### 신뢰도 판정 기준

```
CRITICAL (전원 합의)  →  반드시 수정 — 예외 없음
HIGH     (2/3 합의)   →  수정 권장, 불일치 원인 조사 필요
MEDIUM   (1/3만 지적) →  조사 필요, 대부분 오탐(false positive)
```

### 아티팩트 기반 커뮤니케이션

CLI 에이전트(Gemini/Codex)는 Claude Code 팀과 직접 메시지를 주고받을 수 없습니다. 대신 `/tmp/xv/{task-name}/`에 구조화된 아티팩트 파일을 드롭하고, Claude Code 팀원이 읽는 방식으로 소통합니다:

```
/tmp/xv/{task-name}/
├── plan_draft.md              # Claude 팀의 설계안
├── claude_review.md           # Claude 팀의 리뷰
├── codex_review.md            # Codex CLI가 작성
├── codex_critique.md          # Codex CLI가 작성 (설계 비평)
├── gemini_review.md           # Gemini CLI가 작성
├── gemini_critique.md         # Gemini CLI가 작성 (설계 비평)
├── gemini_research.md         # Gemini 웹 검색 결과
└── synthesis_report.md        # 최종 종합 보고서
```

**표준 아티팩트 형식** (모든 리뷰/비평 파일이 따라야 하는 형식):

```markdown
# [Agent] Review - {대상 파일명}
Date: {timestamp}
Status: PASS | FAIL | PASS_WITH_COMMENTS

## Findings
- [CRITICAL] Line N: 설명
- [HIGH] Line N: 설명

## Summary
1-3문장 요약

## Verdict: APPROVE | REQUEST_CHANGES
```

---

## 활용 예제

> 간단한 한 줄 프롬프트가 정교한 멀티 에이전트 워크플로우로 변환되는 실전 예제입니다.

### 대표 예제: SaaS 랜딩페이지 — AI 이미지 생성 + 자동 검증 루프

> **"우리 SaaS 제품 랜딩페이지 만들어줘. 히어로 섹션, 기능 소개, 가격표, CTA 포함."**

이 예제는 **모든 스킬을 조합**하여, AI가 이미지를 생성하고 랜딩페이지에 녹여내고, 스크린샷을 찍어 자가 평가한 뒤, 점수가 기준에 도달할 때까지 **자동으로 루프를 돌며 개선**하는 워크플로우입니다.

#### 팀 구성 (8명)

| 에이전트 | 역할 | 사용 스킬 | 작업 내용 |
|----------|------|-----------|-----------|
| `architect` | 설계 | claude (mode=plan) | 랜딩페이지 구조 설계, 섹션별 와이어프레임 |
| `image-gen` | 이미지 생성 | **gemini-image** | 히어로 배너, 기능 아이콘, 일러스트, 배경 |
| `ui-dev` | 프론트엔드 구현 | claude | HTML/CSS/JS 구현, 생성 이미지 배치 |
| `e2e-runner` | E2E 테스트 | claude (Playwright) | 스크린샷 캡처, 반응형 테스트, 성능 측정 |
| `vlm-judge` | **시각 품질 판정** | **gemini-cli** | **스크린샷 분석 → 디자인 점수 매기기 (100점)** |
| **`xv-gemini`** | **트렌드 조사** | **gemini-cli** | **최신 랜딩페이지 트렌드 웹 검색** |
| **`xv-codex`** | **코드 품질** | **codex-cli** | **성능/접근성/SEO 독립 감사** |
| `synthesizer` | 품질 게이트 | claude | 종합 점수 판정, 루프 계속/종료 결정 |

#### 핵심 메커니즘: 자동 검증 루프

```
                    ┌──────────────────────────────────────────────┐
                    │          DESIGN-VERIFY-REFINE LOOP           │
                    │                                              │
                    │  ┌─────────┐    ┌─────────┐    ┌─────────┐  │
                    │  │ image   │───→│ ui-dev  │───→│  e2e    │  │
                    │  │  -gen   │    │ 구현    │    │ 스크린샷│  │
                    │  └─────────┘    └─────────┘    └────┬────┘  │
                    │       ↑                              │       │
                    │       │                              ↓       │
                    │  ┌─────────┐    ┌─────────┐    ┌─────────┐  │
                    │  │ 프롬프트│←───│synthe-  │←───│  vlm-   │  │
                    │  │ 조정    │    │ sizer   │    │ judge   │  │
                    │  └─────────┘    │ 판정    │    │(gemini) │  │
                    │                 └────┬────┘    └─────────┘  │
                    │                      │                       │
                    │              점수 < 85점?                    │
                    │              YES → 루프 반복                 │
                    │              NO  → 통과 ✅                   │
                    └──────────────────────────────────────────────┘
```

#### 워크플로우 전체 흐름

```
사용자: "우리 SaaS 제품 랜딩페이지 만들어줘"
         │
    /agent-teams (8명 스폰)
         │
         ├── Phase 1: 설계 + 트렌드 조사 (병렬) ────────────────┐
         │                                                        │
         │   architect ──── 랜딩페이지 구조 설계 (mode=plan):    │
         │     섹션 1: 히어로 (풀스크린 배너 + CTA)              │
         │     섹션 2: 핵심 기능 3개 (아이콘 + 설명)             │
         │     섹션 3: 사용 사례 (일러스트 + 텍스트)             │
         │     섹션 4: 가격표 (3단 카드)                          │
         │     섹션 5: CTA + 푸터                                 │
         │                                                        │
         │   xv-gemini ──── 웹 검색:                             │
         │     "2026 SaaS landing page design trends"             │
         │     "hero section best practices gradient glass"       │
         │     -> glassmorphism + gradient mesh + 3D 일러스트     │
         │     -> 무채색 배경 + 컬러 액센트 트렌드 보고          │
         │                                                        │
         ├── Phase 2: 이미지 생성 (1차) ─────────────────────────┤
         │                                                        │
         │   image-gen ──── gemini-image로 5개 이미지 생성:      │
         │                                                        │
         │   [1] 히어로 배너:                                     │
         │       "Wide SaaS hero banner, abstract gradient mesh   │
         │        in deep blue (#0a1628) to teal (#0d9488),       │
         │        floating 3D geometric shapes, glassmorphism     │
         │        overlay, modern tech atmosphere, 16:9, no text" │
         │       -> hero-banner.png (--aspect 16:9 --size 2K)    │
         │                                                        │
         │   [2-4] 기능 아이콘 3개:                               │
         │       "Minimalist flat icon, [analytics/security/      │
         │        integration], teal accent on transparent,       │
         │        256x256, clean vector style"                    │
         │       -> feature-1.png, feature-2.png, feature-3.png  │
         │                                                        │
         │   [5] 사용 사례 일러스트:                               │
         │       "Isometric illustration of team collaborating    │
         │        on dashboard, teal and blue palette, modern     │
         │        flat style, white background"                   │
         │       -> usecase-illustration.png (--aspect 4:3)      │
         │                                                        │
         ├── Phase 3: 구현 ──────────────────────────────────────┤
         │                                                        │
         │   ui-dev ─────── 설계 + 트렌드 + 이미지를 종합하여:  │
         │     - HTML 시맨틱 구조 (header, main, sections)       │
         │     - CSS: glassmorphism 카드, gradient mesh 배경      │
         │     - 히어로: hero-banner.png을 배경으로, CTA 버튼     │
         │     - 기능 섹션: 3-column grid, 아이콘 이미지 배치    │
         │     - 가격표: 3단 카드 (Basic/Pro/Enterprise)          │
         │     - 반응형: mobile-first, breakpoints 설정           │
         │                                                        │
         ├── Phase 4: E2E 스크린샷 캡처 ─────────────────────────┤
         │                                                        │
         │   e2e-runner ─── Playwright로 스크린샷:               │
         │     - desktop (1920x1080)                              │
         │     - tablet (768x1024)                                │
         │     - mobile (375x812)                                 │
         │     -> /tmp/screenshots/landing-desktop.png            │
         │     -> /tmp/screenshots/landing-tablet.png             │
         │     -> /tmp/screenshots/landing-mobile.png             │
         │                                                        │
         │                                                        │
         ├══ Phase 5: 시각 품질 판정 (자동 검증 루프 시작) ══════╡
         │                                                        │
         │   vlm-judge ─── 스크린샷 3장을 분석하여 점수 산정:   │
         │                                                        │
         │   ┌────────────────────────────────────────────────┐   │
         │   │  시각 품질 스코어카드 (Round 1)                 │   │
         │   │                                                │   │
         │   │  시각적 조화 (이미지-레이아웃 융합)  .... 72/100│   │
         │   │  색상 일관성 (이미지-UI 팔레트 통일)  .... 68/100│   │
         │   │  타이포그래피 밸런스                   .... 81/100│   │
         │   │  여백/정렬 품질                        .... 78/100│   │
         │   │  반응형 적응도                         .... 85/100│   │
         │   │  CTA 시인성                            .... 74/100│   │
         │   │  ─────────────────────────────────────────────│   │
         │   │  종합 점수:  76/100  ❌ (기준: 85점)          │   │
         │   │                                                │   │
         │   │  개선 필요 항목:                                │   │
         │   │  [1] 히어로 배너 그라데이션이 텍스트 가독성 저하│   │
         │   │      → 배너 하단에 어두운 오버레이 필요         │   │
         │   │  [2] 기능 아이콘 스타일 불일치 (2번이 너무 복잡)│   │
         │   │      → feature-2.png 재생성 (더 단순하게)       │   │
         │   │  [3] 가격표 카드에 시각적 강조 부족             │   │
         │   │      → Pro 카드에 glassmorphism 효과 추가        │   │
         │   └────────────────────────────────────────────────┘   │
         │                                                        │
         │   synthesizer ── 76점 < 85점 → 루프 계속 판정         │
         │     → image-gen에게 개선 피드백 전달                   │
         │     → ui-dev에게 CSS 수정 사항 전달                    │
         │                                                        │
         │                                                        │
         ├── [Loop Round 2] 이미지 재생성 + 수정 ────────────────┤
         │                                                        │
         │   image-gen ──── 피드백 반영하여 재생성:              │
         │     [1] 히어로 배너 (수정):                            │
         │         "...same prompt + add dark gradient overlay    │
         │          at bottom 30%, ensure text readability"       │
         │         -> hero-banner-v2.png                          │
         │     [2] feature-2 아이콘 (재생성):                     │
         │         "...simpler, more minimalist, match style      │
         │          of feature-1 and feature-3"                   │
         │         -> feature-2-v2.png                            │
         │                                                        │
         │   ui-dev ──────  수정 사항 반영:                      │
         │     - 히어로 배너 교체 + 하단 gradient overlay 추가   │
         │     - feature-2 아이콘 교체                            │
         │     - Pro 가격 카드에 glassmorphism + 테두리 강조      │
         │                                                        │
         │   e2e-runner ─── 스크린샷 재캡처 (3장)                │
         │                                                        │
         │   vlm-judge ─── 재평가:                              │
         │                                                        │
         │   ┌────────────────────────────────────────────────┐   │
         │   │  시각 품질 스코어카드 (Round 2)                 │   │
         │   │                                                │   │
         │   │  시각적 조화 (이미지-레이아웃 융합)  .... 88/100│   │
         │   │  색상 일관성 (이미지-UI 팔레트 통일)  .... 84/100│   │
         │   │  타이포그래피 밸런스                   .... 83/100│   │
         │   │  여백/정렬 품질                        .... 80/100│   │
         │   │  반응형 적응도                         .... 87/100│   │
         │   │  CTA 시인성                            .... 86/100│   │
         │   │  ─────────────────────────────────────────────│   │
         │   │  종합 점수:  84/100  ❌ (기준: 85점, 근접!)    │   │
         │   │                                                │   │
         │   │  개선 필요 항목:                                │   │
         │   │  [1] 색상 일관성: usecase 일러스트 배경색이     │   │
         │   │      섹션 배경과 미세하게 불일치                 │   │
         │   │      → 일러스트 배경을 transparent로 재생성      │   │
         │   └────────────────────────────────────────────────┘   │
         │                                                        │
         │   synthesizer ── 84점 < 85점 → 루프 1회 더            │
         │                                                        │
         │                                                        │
         ├── [Loop Round 3] 최종 미세 조정 ──────────────────────┤
         │                                                        │
         │   image-gen ──── usecase 일러스트 재생성:             │
         │     "...same style, transparent background,            │
         │      teal (#0d9488) accent only"                       │
         │     -> usecase-illustration-v2.png                     │
         │                                                        │
         │   ui-dev ─────── 일러스트 교체 + 미세 조정            │
         │   e2e-runner ─── 최종 스크린샷 캡처                   │
         │                                                        │
         │   vlm-judge ─── 최종 평가:                           │
         │                                                        │
         │   ┌────────────────────────────────────────────────┐   │
         │   │  시각 품질 스코어카드 (Round 3 — FINAL)         │   │
         │   │                                                │   │
         │   │  시각적 조화 (이미지-레이아웃 융합)  .... 91/100│   │
         │   │  색상 일관성 (이미지-UI 팔레트 통일)  .... 90/100│   │
         │   │  타이포그래피 밸런스                   .... 84/100│   │
         │   │  여백/정렬 품질                        .... 82/100│   │
         │   │  반응형 적응도                         .... 88/100│   │
         │   │  CTA 시인성                            .... 89/100│   │
         │   │  ─────────────────────────────────────────────│   │
         │   │  종합 점수:  87/100  ✅ (기준 통과!)           │   │
         │   └────────────────────────────────────────────────┘   │
         │                                                        │
         │   synthesizer ── 87점 ≥ 85점 → 루프 종료, Phase 6으로 │
         │                                                        │
         │                                                        │
         ├── Phase 6: 최종 교차검증 (병렬) ──────────────────────┤
         │                                                        │
         │   xv-codex ──── 독립 코드 감사:                       │
         │     - Lighthouse: Performance 94, A11y 98, SEO 100    │
         │     - 이미지 최적화: WebP 변환 권장 (2건)             │
         │     - VERDICT: PASS_WITH_COMMENTS                     │
         │                                                        │
         │   xv-gemini ──── 최종 트렌드 검증:                    │
         │     "이 랜딩페이지가 2026 SaaS 트렌드에 부합하는가?"  │
         │     - glassmorphism ✅, gradient mesh ✅               │
         │     - micro-interaction 추가 권장 (enhancement)       │
         │     - VERDICT: APPROVE                                │
         │                                                        │
         └───────────────────────────────────────── 완료 ─────────┘
```

#### 이미지 생성 프롬프트 진화 과정

> 루프를 거치면서 이미지 프롬프트가 어떻게 정교해지는지 보여줍니다:

```
[Round 1] 초기 프롬프트:
  "Wide SaaS hero banner, abstract gradient mesh in deep blue
   to teal, floating 3D shapes, glassmorphism, 16:9, no text"

  → 결과: 그라데이션이 밝아서 위에 흰색 텍스트가 안 보임 (72점)

[Round 2] vlm-judge 피드백 반영:
  "Wide SaaS hero banner, abstract gradient mesh in deep blue
   (#0a1628) to teal (#0d9488), floating 3D shapes,
   glassmorphism, dark gradient overlay at bottom 30% for
   text readability, 16:9, no text"
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                              피드백에서 추가된 부분

  → 결과: 텍스트 가독성 개선, 전체 톤 안정 (88점)

[Round 3] 일러스트 배경 수정:
  "Isometric illustration of team collaborating on dashboard,
   teal (#0d9488) and blue palette, modern flat style,
   transparent background"
   ^^^^^^^^^^^^^^^^^^^^^^
   불투명 흰색 → 투명으로 변경

  → 결과: 섹션 배경과 완벽히 융합 (91점)
```

#### 최종 결과

```
SaaS 랜딩페이지 — 완성
═══════════════════════
생성 이미지: 7개 (히어로 배너 v2, 아이콘 3개, 일러스트 v2 + 원본 2개)
루프 횟수:   3회 (76점 → 84점 → 87점 ✅)
구현 파일:   index.html, styles.css, script.js
반응형:      desktop / tablet / mobile 대응
검증 결과:
  - VLM 시각 품질:  87/100 (기준 85점 통과)
  - Codex 코드 감사: PASS_WITH_COMMENTS (Lighthouse 94점)
  - Gemini 트렌드:   APPROVE (2026 트렌드 부합)

이미지-디자인 융합 점수 변화:
  Round 1:  72/100  ███████░░░  "이미지가 붕 떠 보임"
  Round 2:  88/100  ████████░░  "거의 자연스러움"
  Round 3:  91/100  █████████░  "완전히 녹아듦" ✅
```

> **이 예제의 핵심**: AI가 이미지를 생성하고 끝나는 것이 아니라, **스크린샷 → VLM 점수 → 피드백 → 이미지 재생성 → 재구현**의 루프를 자동으로 반복하여, 생성된 이미지가 웹 디자인에 **완전히 녹아드는 수준**까지 도달합니다. 사람이 개입하지 않아도 점수 기반으로 자가 판단하여 품질을 끌어올립니다.

---

### 예제 1: 풀스택 기능 개발 + 교차검증

> **"결제 시스템에 환불 기능 추가해줘"**

| 에이전트 | 역할 | 사용 스킬 | 작업 내용 |
|----------|------|-----------|-----------|
| `api-dev` | API 개발 | claude | `POST /refunds`, `GET /refunds/:id` 구현 |
| `service-dev` | 비즈니스 로직 | claude | RefundService, 부분환불/전체환불 로직 |
| `db-migration` | DB 스키마 | claude | refunds 테이블 마이그레이션 |
| `ui-dev` | 프론트엔드 | claude | 환불 요청 UI, 환불 내역 페이지 |
| **`xv-codex`** | **교차검증** | **codex-cli** | **결제 금액 계산 로직 독립 검증** |
| `tester` | 테스트 | claude | 통합 테스트, 엣지 케이스 검증 |

```
사용자: "결제 시스템에 환불 기능 추가해줘"
         │
    /agent-teams
         │
         ├── Phase 1: 병렬 구현 ─────────────────────────────────┐
         │   api-dev ────── POST /refunds 엔드포인트 구현        │
         │   service-dev ── RefundService 비즈니스 로직           │
         │   db-migration ─ refunds 테이블 스키마 설계            │
         │   ui-dev ─────── 환불 요청 폼 + 내역 페이지           │
         │                                                        │
         ├── Phase 2: 교차검증 ──────────────────────────────────┤
         │   xv-codex ─── Codex가 환불 금액 계산 로직 독립 검증  │
         │     -> 쿠폰 비례 배분 오류 발견, service-dev에 전달    │
         │                                                        │
         ├── Phase 3: 통합 테스트 ───────────────────────────────┤
         │   tester ────── 전체 환불 플로우 E2E 테스트            │
         └───────────────────────────────────────── 완료 ─────────┘
```

**교차검증 핵심 순간:**

```
[xv-codex] Codex 분석 결과:
  - 부분 환불 계산식에서 쿠폰 적용 순서 이슈 발견
  - calculateRefundAmount()에서 쿠폰 할인을 환불 후
    재적용하지 않는 버그 식별
  - 수정 제안: 쿠폰 비례 배분 방식으로 변경 필요

[service-dev] 쿠폰 비례 배분 로직으로 수정 완료
[tester] 통합 테스트 12개 전체 통과
```

---

### 예제 2: 프론트엔드 리디자인 + 이미지 생성

> **"대시보드 페이지 다크모드로 리디자인해줘"**

| 에이전트 | 역할 | 사용 스킬 | 작업 내용 |
|----------|------|-----------|-----------|
| `ui-designer` | 디자인 컨셉 | **gemini-image** | 다크모드 대시보드 목업 이미지 생성 |
| `ui-dev` | 프론트엔드 구현 | claude | CSS 변수, 테마 토글, 컴포넌트 스타일링 |
| **`xv-gemini`** | **트렌드 조사** | **gemini-cli** | **최신 다크모드 패턴 웹 검색** |
| `vlm-judge` | 시각 검증 | **gemini-cli** | **구현 결과 스크린샷 vs 목업 비교** |
| `tester` | 접근성 테스트 | claude | WCAG 대비율 검증 |

```
    /agent-teams
         │
         ├── Phase 1: 조사 + 디자인 (병렬) ─────────────────────┐
         │   xv-gemini ──── 웹 검색: "2026 dark mode best       │
         │                   practices dashboard design"         │
         │                   -> Adaptive dimming, semantic tokens │
         │                                                        │
         │   ui-designer ── gemini-image로 목업 생성:             │
         │                   "Modern dark mode dashboard,         │
         │                    charts, sidebar, KPI cards"          │
         │                   -> /tmp/dashboard-dark-mockup.png    │
         │                                                        │
         ├── Phase 2: 구현 ──────────────────────────────────────┤
         │   ui-dev ─────── 조사 결과 + 목업을 참고하여 구현     │
         │                                                        │
         ├── Phase 3: 시각 검증 ─────────────────────────────────┤
         │   vlm-judge ─── 스크린샷 vs 목업 비교:               │
         │                   "사이드바 패딩 부족, KPI 카드 수정"   │
         │   tester ─────── WCAG AA 대비율 검증 통과             │
         └───────────────────────────────────────── 완료 ─────────┘
```

---

### 예제 3: 보안 감사 + 3-way 교차검증

> **"인증 모듈 보안 감사 진행해줘"**

| 에이전트 | 역할 | 사용 스킬 | 작업 내용 |
|----------|------|-----------|-----------|
| `security-analyst` | 1차 보안 분석 | claude | OWASP Top 10 정적 분석 |
| **`xv-codex`** | **독립 보안 리뷰** | **codex-cli** | **인증 플로우 독립 취약점 분석** |
| **`xv-gemini`** | **최신 CVE 조사** | **gemini-cli** | **사용 라이브러리 최신 CVE 확인** |
| `synthesizer` | 3-way 게이트 | claude | 3개 분석 결과 종합 판정 |

```
    /agent-teams
         │
         ├── Phase 1: 3-way 독립 분석 (완전 병렬) ──────────────┐
         │                                                        │
         │   security-analyst (Claude):                           │
         │     [HIGH] JWT alg:none 검증 누락                     │
         │     [MED]  Rate limiting 미적용                       │
         │                                                        │
         │   xv-codex (Codex CLI - 독립 검증):                   │
         │     [HIGH] JWT alg:none 검증 누락 (Claude와 일치!)    │
         │     [HIGH] refresh token 재사용 가능 (추가 발견)      │
         │     [LOW]  에러 메시지에 스택 트레이스 노출            │
         │                                                        │
         │   xv-gemini (Gemini CLI - 웹 검색):                   │
         │     [CRITICAL] jsonwebtoken < 9.0.3 CVE 발견          │
         │     현재 사용 버전 8.5.1 → 취약!                      │
         │                                                        │
         ├── Phase 2: 3-way 게이트 판정 ─────────────────────────┤
         │                                                        │
         │   ┌─────────────────────────────────────────────┐      │
         │   │  Claude  : FAIL (2건)                       │      │
         │   │  Codex   : FAIL (3건)                       │      │
         │   │  Gemini  : FAIL (1건 CRITICAL)              │      │
         │   │                                             │      │
         │   │  판정: FAIL (3/3 일치)                      │      │
         │   │  고유 취약점: 5건 (중복 제거)               │      │
         │   │  단일 분석 대비 2.5배 더 많은 이슈 포착     │      │
         │   └─────────────────────────────────────────────┘      │
         └───────────────────────────────────────── 완료 ─────────┘
```

> **핵심**: Claude + Codex가 독립적으로 동일한 JWT 취약점을 발견 (높은 신뢰도), Codex가 refresh token 이슈를 추가 발견, Gemini가 웹 검색으로 실시간 CVE 데이터를 제공 — 3가지 관점의 결합으로 단일 분석 대비 **2.5배** 더 많은 취약점을 포착했습니다.

---

### 예제 4: 버그 조사 + 멀티 에이전트 디버깅

> **"프로덕션에서 간헐적 타임아웃 발생하는데 원인 찾아줘"**

| 에이전트 | 역할 | 작업 내용 |
|----------|------|-----------|
| `log-analyst` | 로그 분석 | 에러 로그 패턴 분석, 타임라인 구성 |
| `db-tracer` | DB 추적 | 슬로우 쿼리, 커넥션 풀, 락 경합 조사 |
| `api-tracer` | API 추적 | 엔드포인트별 응답시간, 타임아웃 패턴 |
| `cache-checker` | 캐시 점검 | Redis 히트율, 메모리, 만료 정책 조사 |
| **`xv-codex`** | **독립 분석** | **codex-cli로 코드 레벨 타임아웃 원인 분석** |

```
    /agent-teams (5명 병렬 조사)
         │
         ├── cache-checker:  14:00 캐시 대량 만료 발견 ← 근본 원인
         ├── api-tracer:     14:00 /api/dashboard 응답 200ms → 12s
         ├── db-tracer:      14:00 analytics_events 풀스캔 급증
         ├── log-analyst:    14:00-14:30 타임아웃 에러 집중
         │
         └── xv-codex (코드 레벨 독립 분석):
               cache.set(key, data, 86400) ← 고정 TTL이 문제
               쿼리에 LIMIT 없음 ← 데이터 증가 시 악화

    근본 원인: 캐시 스탬피드 (Cache Stampede)
    수정: TTL jitter 추가 + 쿼리 LIMIT + singleflight 패턴
    예상 효과: p99 응답시간 12s → 200ms 이하
```

> 단일 에이전트였다면 로그만 보고 "서버 과부하"로 결론냈을 것입니다. 4개 관점을 교차하니 **캐시 스탬피드**가 근본 원인임을 정확히 특정할 수 있었습니다.

---

### 예제 5: 아키텍처 설계 + 3-way 게이트

> **"마이크로서비스 전환 계획 세워줘"**

| 에이전트 | 역할 | 사용 스킬 | 관점 |
|----------|------|-----------|------|
| `architect` | 설계 | claude | 전환 계획서 초안 작성 |
| `claude-critic` | 비평가 1 | claude | 팀/조직 역량 관점 |
| **`xv-codex-critic`** | **비평가 2** | **codex-cli** | **코드 결합도/기술적 정합성** |
| **`xv-gemini-critic`** | **비평가 3** | **gemini-cli** | **업계 사례/최신 트렌드 (웹 검색)** |
| `synthesizer` | 3-way 게이트 | claude | 3명의 리뷰 종합 판정 |

```
    /agent-teams
         │
         ├── Phase 1: architect ── 전환 계획서 v1 작성
         │
         ├── Phase 2: 3-way 독립 리뷰 (완전 병렬)
         │   claude-critic:     "5명이 4개 서비스 관리는 과도"     → CONDITIONAL PASS
         │   xv-codex-critic:   "user-order 결합도 47개, 동시 분리 불가" → FAIL
         │   xv-gemini-critic:  "모듈화 선행 없이 분리 실패율 높음"    → FAIL
         │
         ├── Phase 3: 3-way 게이트 ── REJECTED (2/3 실패)
         │   → architect에게 피드백 전달, v2 재설계 요청
         │
         ├── Phase 4: architect ── 피드백 반영하여 v2 작성
         │   + Phase 0 모듈러 모놀리스 추가 (Gemini 피드백)
         │   + payment 먼저 분리 (Codex 피드백)
         │   + 단계적 확장 (Claude 피드백)
         │
         ├── Phase 5: 3-way 게이트 재판정
         │   ┌──────────────────────────────────┐
         │   │  Claude  : PASS                  │
         │   │  Codex   : PASS                  │
         │   │  Gemini  : PASS                  │
         │   │                                  │
         │   │  판정: APPROVED (3/3 전원 승인)   │
         │   └──────────────────────────────────┘
         └───────────────────────── 구현 진행 허가
```

> 1차에서 REJECTED된 설계가 3명의 독립 비평가의 피드백을 반영하여 **훨씬 더 현실적이고 안전한 계획**으로 개선되었습니다. 이것이 3-way 게이트의 핵심 가치입니다.

---

## 실제 워크플로우 데모

> 실제 프로젝트에서 `/agent-teams`를 사용한 워크플로우의 실행 과정입니다.

### Phase 1: 병렬 리서치 스폰

```
● 2 agents launched (ctrl+o to expand)
  ├─ @ui-researcher (Explore)
  │  └─ Frontend HRP UI flow research
  └─ @api-researcher (Explore)
     └─ Backend WF engine + API research
```

| 팀원 | 역할 | 태스크 |
|------|------|--------|
| **ui-researcher** | 프론트엔드 HRP UI 플로우 분석 | #1 |
| **api-researcher** | 백엔드 WF 엔진 + API 분석 | #2 |

**4단계 파이프라인 자동 설계:**

```
Phase 1: 리서치 (#1, #2) — 병렬 진행
↓
Phase 2: 설계 (#3) → Codex (#4) + Gemini (#5) 교차검증 → 합성 (#6)
↓
Phase 3: 구현 — Frontend (#7) + Backend (#8) 병렬
↓
Phase 4: 테스트 (#9) — 단위 + E2E
```

### Phase 1 확장: 3명 병렬 + 교차검증 에이전트

```
● 3 agents launched (ctrl+o to expand)
  ├─ @equity-tracer (Explore)
  │  └─ Equity curve generation logic audit
  ├─ @weight-tracer (Explore)
  │  └─ Weight precompute + HRP consumption audit
  └─ @xv-codex
     └─ Codex cross-verify precompute logic
```

| 팀원 | 조사 범위 |
|------|-----------|
| **equity-tracer** | 에쿼티커브 생성 파이프라인, 연도 파티션, 정규화, 시그널 생성 |
| **weight-tracer** | SharedDataCache 로딩, 다연도 체이닝, HRP 소비 로직, 이론적 타당성 |
| **xv-codex** | Codex 독립 교차검증 (체인 정규화, 스케일 불일치, 논리적 결함) |

### Phase 2: Codex 교차검증 실행

```
● 17/17 tests passed. 이제 Codex 교차검증을 진행합니다.

Bash(codex exec --ephemeral --full-auto -s read-only #
  "$(cat <<'EOF'...)")
└ Running... (2m 36s · timeout 5m)

+ Running Codex cross-verification... (9m 42s · 133.7k tokens)
✓ PO: Cache key에 Stage + 파라미터 11개 추가
✓ PI: Config 통합 로더 생성 → backtest handler 연동
✓ PO+PI 테스트 통과
✓ 코드 감사 완료 (@drift-analyst)
```

### 전체 완료 요약: 9개 태스크, 4 Phase 완료

| Phase | Task | 상태 |
|-------|------|------|
| **1. 리서치** | #1 프론트엔드 UI 플로우 | ✅ |
| | #2 백엔드 WF 엔진 + API | ✅ |
| **2. 설계 + 검증** | #3 IW Direct 설계안 | ✅ |
| | #4 Codex 교차검증 | ✅ (APPROVE, 2 CRITICAL) |
| | #5 Gemini 교차검증 | ✅ (APPROVE, 1 CRITICAL) |
| | #6 3-way 합성 | ✅ (3 CRITICAL + 5 HIGH 해결) |
| **3. 구현** | #7 프론트엔드 (4파일) | ✅ |
| | #8 백엔드 (2파일) | ✅ |
| **4. 테스트** | #9 단위 + E2E | ✅ 46/46 pass, 530 전체 무회귀 |

**구현 내역:**

```
백엔드 (2파일):
  - falsy 버그 수정 (6곳)
  - end_date midnight → 23:59:59 (윈도우 누락 방지)
  - overfitting_score ≤ 0 guard + negative IS Sharpe 처리
  - run_iw_direct() 신규 메서드 (215줄)

프론트엔드 (4파일):
  - IW Direct 옵션 + DSR 자동 비활성화
  - 조건부 요약 카드 + 3-way 배지
  - TypeScript 타입 추가 + backward compatibility

산출물:
  - 합성 보고서: /tmp/xv/hrp-ui/synthesis_report.md
  - 테스트: tests/backtest/test_walk_forward_iw_direct.py (46 tests)
```

> 간단한 프롬프트 하나로 **리서치 → 설계 → 교차검증 → 구현 → 테스트**까지 9개 태스크가 자동으로 생성되고, 병렬로 실행되며, 교차검증을 거쳐 완료됩니다.

---

## 스킬 커스터마이징 — 나만의 워크플로우 최적화

`.claude/skills/`의 `SKILL.md` 파일들은 Claude Code의 행동을 정의하는 **프롬프트**입니다. 이 스킬들은 **범용 템플릿**으로 설계되어 있어 그대로 사용해도 강력하지만, **프로젝트 특성에 맞게 수정하면 효율이 극대화**됩니다.

가장 쉬운 방법은 Claude Code에게 자연어로 요청하는 것입니다:

```
나는 Django + React 프로젝트를 주로 개발하는데,
agent-teams 스킬을 내 프로젝트에 맞게 최적화해줘
```

이렇게 요청하면 Claude Code가 `.claude/skills/agent-teams/SKILL.md`를 읽고, Django + React에 특화된 팀 구성 패턴, 체크리스트, 역할 분담 등을 자동으로 반영합니다.

### 구체적 예시

**백엔드 개발자 (Python/FastAPI)**

```
나는 FastAPI + SQLAlchemy 프로젝트를 주로 하는데,
agent-teams 스킬에서 팀 구성할 때 항상 db-migration 팀원과
API 문서 자동생성 팀원을 포함하도록 최적화해줘
```

→ `SKILL.md`의 팀 구성 템플릿에 `db-migration-specialist`와 `api-docs-generator` 역할이 기본 포함되고, Alembic 마이그레이션 검증 단계와 OpenAPI 스펙 자동 갱신 단계가 워크플로우에 추가됩니다.

**프론트엔드 개발자 (Next.js)**

```
Next.js App Router 프로젝트인데, gemini-cli 스킬에서
코드 리뷰할 때 Server Component vs Client Component 구분을
중점적으로 체크하도록 수정해줘
```

→ `gemini-cli`의 리뷰 프롬프트에 `'use client'` 디렉티브 누락 검출, 불필요한 클라이언트 컴포넌트 경고, 서버 컴포넌트에서의 상태 관리 안티패턴 체크 등 Next.js App Router 특화 규칙이 추가됩니다.

**데이터 엔지니어 (Spark/Airflow)**

```
나는 Spark + Airflow DAG 개발이 주 업무야.
codex-cli 스킬의 코드 리뷰 템플릿에 DAG 의존성 검증과
Spark 성능 안티패턴 체크를 추가해줘
```

→ `codex-cli`의 리뷰 체크리스트에 DAG 순환 의존성 검출, `collect()` 남용 경고, 파티션 편향(skew) 감지 등 데이터 파이프라인 특화 검증 항목이 포함됩니다.

**모바일 개발자 (Flutter)**

```
Flutter 프로젝트에 맞게 agent-teams 스킬을 수정해줘.
팀 구성 시 iOS/Android 플랫폼별 테스터를 분리하고,
gemini-image로 앱 스크린샷 목업을 생성하는 팀원도 포함해줘
```

→ 팀 템플릿에 `ios-tester`, `android-tester`, `ui-mockup-designer` 역할이 추가되고, 플랫폼별 빌드 검증과 `gemini-image`를 활용한 UI 목업 생성 단계가 워크플로우에 통합됩니다.

**금융/퀀트 개발자**

```
퀀트 트레이딩 시스템 개발하는데, agent-teams에서
수학적 검증이 필요한 로직은 반드시 Codex 교차검증을
거치도록 MUST 규칙을 강화해줘
```

→ MUST 규칙 섹션에 "수학적 연산, 통계 모델, 리스크 계산 로직은 반드시 Codex CLI를 통한 독립적 교차검증을 수행할 것"이 추가됩니다.

### 커스터마이징 팁

- **`SKILL.md`는 마크다운**이므로 Claude Code에게 요청하지 않고 직접 편집해도 됩니다
- **프로젝트의 `CLAUDE.md`에 공통 규칙을 정의**하면 모든 스킬에 자동 적용됩니다
- **`.claude/skills/`를 git으로 버전 관리**하면 팀원 간 동일한 최적화된 워크플로우를 공유할 수 있습니다
- **`references/` 디렉토리에 프로젝트 특화 프롬프트 템플릿**을 추가하면 더 정교한 커스터마이징이 가능합니다

---

## 예제 요약

| 예제 | 프롬프트 | 에이전트 | 핵심 기능 |
|------|----------|----------|-----------|
| **랜딩페이지** | **"SaaS 랜딩페이지 만들어줘"** | **8명** | **이미지 생성 + VLM 자동 검증 루프 (76→87점)** |
| 풀스택 개발 | "환불 기능 추가해줘" | 6명 | Codex 교차검증으로 버그 사전 발견 |
| 리디자인 | "다크모드로 리디자인해줘" | 5명 | 이미지 생성 + 웹 검색 + 시각 검증 |
| 보안 감사 | "보안 감사 진행해줘" | 4명 | 3-way 독립 분석으로 취약점 2.5배 포착 |
| 버그 조사 | "타임아웃 원인 찾아줘" | 5명 | 멀티 관점 동시 조사로 근본 원인 특정 |
| 아키텍처 | "마이크로서비스 전환 계획" | 5명 | 3-way 게이트로 설계 품질 보장 |

> **핵심 가치**: 간단한 한 줄 프롬프트 → `/agent-teams`가 전문가 팀을 구성 → 병렬 작업 + 교차검증 → 단일 에이전트 대비 **더 빠르고, 더 정확하고, 더 안전한** 결과

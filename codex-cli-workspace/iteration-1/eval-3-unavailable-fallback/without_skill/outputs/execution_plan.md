# Codex CLI 알고리즘 정확성 검증 — 실행 계획

## 개요

Codex CLI가 설치되어 있는 경우와 설치되어 있지 않은 경우를 모두 처리하는 실행 계획입니다.

---

## 1. Codex CLI 가용성 확인

```bash
if command -v codex &>/dev/null; then
  echo "Codex CLI가 설치되어 있습니다. (버전: $(codex --version))"
  CODEX_AVAILABLE=true
else
  echo "Codex CLI가 설치되어 있지 않습니다."
  CODEX_AVAILABLE=false
fi
```

---

## 2. 설치되어 있는 경우: Codex로 알고리즘 검증 실행

```bash
if [ "$CODEX_AVAILABLE" = true ]; then
  # 알고리즘 파일을 heredoc 패턴으로 프롬프트에 포함하여 검증
  timeout 120 codex exec --ephemeral -s read-only -o /tmp/algorithm_verification.txt \
    "$(cat <<'EOF'
다음 알고리즘의 정확성을 검증해주세요:

$(cat src/algorithm.py)

검증 항목:
1) 알고리즘의 논리적 정확성 (correctness)
2) 엣지 케이스 처리 (빈 입력, 단일 원소, 중복 값 등)
3) 시간/공간 복잡도 분석
4) Off-by-one 에러 여부
5) 종료 조건 (termination) 보장 여부

결과를 마크다운으로 출력해주세요.
EOF
  )"
  EXIT_CODE=$?

  if [ $EXIT_CODE -eq 124 ]; then
    echo "CODEX_TIMEOUT: Codex 실행이 시간 초과되었습니다."
  elif [ $EXIT_CODE -ne 0 ]; then
    echo "CODEX_ERROR: 종료 코드 $EXIT_CODE"
  else
    echo "=== Codex 알고리즘 검증 결과 ==="
    cat /tmp/algorithm_verification.txt
  fi
fi
```

---

## 3. 설치되어 있지 않은 경우: 설치 안내 및 대안 전략

### 3-A. 설치 방법

Codex CLI를 설치하려면 다음 조건과 절차를 따릅니다:

**필수 요구사항**: Node.js 22 이상

```bash
# 1. Node.js 버전 확인
node --version  # v22.x.x 이상이어야 함

# 2. Codex CLI 설치
npm install -g @openai/codex

# 3. 인증 (최초 1회)
codex login

# 4. 설치 확인
codex --version  # v0.1.0 이상
```

### 3-B. 대안 전략: Claude 자체 분석으로 대체

Codex CLI를 즉시 설치할 수 없는 환경이라면, Claude가 직접 알고리즘 정확성 검증을 수행합니다. 이 경우 동일한 검증 항목을 Claude가 분석합니다:

- 논리적 정확성 (correctness)
- 엣지 케이스 처리
- 시간/공간 복잡도
- Off-by-one 에러
- 종료 조건 보장

> Codex를 통한 독립적 교차 검증(cross-verification)의 장점은 서로 다른 모델의 관점에서 분석한다는 것입니다. Codex 설치 후 재검증하면 더 신뢰도 높은 결과를 얻을 수 있습니다.

---

## 4. 통합 스크립트 (전체)

아래는 위 모든 단계를 하나의 스크립트로 통합한 것입니다:

```bash
#!/usr/bin/env bash
set -euo pipefail

ALGORITHM_FILE="${1:-src/algorithm.py}"
OUTPUT_FILE="/tmp/algorithm_verification.txt"

# Step 1: Codex CLI 가용성 확인
if ! command -v codex &>/dev/null; then
  echo "============================================"
  echo " Codex CLI가 설치되어 있지 않습니다."
  echo "============================================"
  echo ""
  echo "[설치 방법]"
  echo "  필수: Node.js 22+"
  echo "  $ npm install -g @openai/codex"
  echo "  $ codex login"
  echo "  $ codex --version"
  echo ""
  echo "[대안] Codex 없이 Claude가 직접 알고리즘을 분석합니다."
  echo ""

  # 대안: 알고리즘 파일 내용 출력하여 Claude가 직접 분석할 수 있도록 함
  if [ -f "$ALGORITHM_FILE" ]; then
    echo "=== 알고리즘 파일 내용 ($ALGORITHM_FILE) ==="
    cat "$ALGORITHM_FILE"
    echo ""
    echo "=== Claude 자체 분석을 진행합니다 ==="
  else
    echo "ERROR: 알고리즘 파일을 찾을 수 없습니다: $ALGORITHM_FILE"
  fi

  # placeholder artifact 생성
  cat > "$OUTPUT_FILE" <<'PLACEHOLDER'
# Algorithm Verification — SKIPPED (Codex Unavailable)

Status: UNAVAILABLE
Reason: codex CLI not installed
Fallback: Claude 자체 분석으로 대체

## 설치 후 재검증 명령어
```
npm install -g @openai/codex
codex login
timeout 120 codex exec --ephemeral -s read-only -o /tmp/algorithm_verification.txt \
  "알고리즘 정확성을 검증해주세요: $(cat src/algorithm.py)"
```
PLACEHOLDER

  exit 0
fi

# Step 2: Codex가 설치된 경우 — 알고리즘 검증 실행
echo "Codex CLI 감지됨: $(codex --version)"
echo "알고리즘 검증을 시작합니다: $ALGORITHM_FILE"

timeout 120 codex exec --ephemeral -s read-only -o "$OUTPUT_FILE" \
  "$(cat <<EOF
다음 알고리즘의 정확성을 검증해주세요:

$(cat "$ALGORITHM_FILE")

검증 항목:
1) 알고리즘의 논리적 정확성 (correctness)
2) 엣지 케이스 처리 (빈 입력, 단일 원소, 중복 값, 음수 등)
3) 시간/공간 복잡도 분석
4) Off-by-one 에러 여부
5) 종료 조건 (termination) 보장 여부

결과를 마크다운으로 출력해주세요.
EOF
)"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
  echo "CODEX_TIMEOUT: 120초 시간 초과"
  echo "# Algorithm Verification — TIMEOUT" > "$OUTPUT_FILE"
elif [ $EXIT_CODE -ne 0 ]; then
  echo "CODEX_ERROR: 종료 코드 $EXIT_CODE"
else
  echo "=== 검증 완료 ==="
  cat "$OUTPUT_FILE"
fi
```

---

## 핵심 요약

| 상황 | 동작 |
|------|------|
| `codex` 설치됨 | `codex exec --ephemeral -s read-only`로 알고리즘 검증 실행 |
| `codex` 미설치 | 설치 안내(`npm install -g @openai/codex`) 출력 + Claude 자체 분석으로 대체 |
| 실행 시간 초과 | `timeout 120`으로 감지하여 TIMEOUT 처리 |
| 인증 오류 등 | exit code 확인 후 에러 메시지 출력 |

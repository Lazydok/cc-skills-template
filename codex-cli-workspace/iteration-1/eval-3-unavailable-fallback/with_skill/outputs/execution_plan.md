# Codex CLI Algorithm Verification - Execution Plan

## Task

Codex CLI를 사용하여 알고리즘 정확성을 검증한다. Codex가 설치되어 있지 않은 경우에 대한 대체 경로를 포함한다.

## Complete Bash Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
ALGO_FILE="${1:?Usage: $0 <algorithm_file>}"
OUTPUT_FILE="/tmp/codex_algo_verification.md"
TIMEOUT_SEC=120

# ──────────────────────────────────────────────
# Step 1: Availability Check
# ──────────────────────────────────────────────
if ! command -v codex &>/dev/null; then
  echo "============================================"
  echo " CODEX CLI NOT INSTALLED"
  echo "============================================"
  echo ""
  echo "Codex CLI가 설치되어 있지 않습니다."
  echo ""
  echo "[설치 방법]"
  echo ""
  echo "  1. Node.js 22 이상이 필요합니다."
  echo "     node --version  # v22.x 이상 확인"
  echo ""
  echo "  2. npm으로 전역 설치:"
  echo "     npm install -g @openai/codex"
  echo ""
  echo "  3. 인증 (최초 1회):"
  echo "     codex login"
  echo "     # 브라우저에서 ChatGPT 로그인으로 인증됩니다."
  echo ""
  echo "  4. 설치 확인:"
  echo "     codex --version  # v0.1.0 이상"
  echo ""
  echo "============================================"
  echo " FALLBACK: Claude 자체 분석 수행"
  echo "============================================"
  echo ""

  # Fallback: Codex 없이 placeholder artifact를 생성하여
  # 다른 agent나 synthesizer가 상태를 파악할 수 있게 한다.
  cat > "$OUTPUT_FILE" << 'FALLBACK_EOF'
# Algorithm Verification - SKIPPED

Status: CODEX_NOT_AVAILABLE
Reason: codex CLI not installed on this system

## Fallback Recommendation

Codex CLI를 통한 독립적 cross-verification이 불가하므로 다음 대안을 고려하세요:

1. **수동 설치 후 재실행**: `npm install -g @openai/codex && codex login`
2. **Claude 자체 분석**: 현재 Claude agent가 직접 알고리즘을 분석 (독립 검증은 아님)
3. **다른 도구 활용**: 정적 분석기(mypy, pylint 등)나 테스트 프레임워크로 보완
FALLBACK_EOF

  echo "Placeholder artifact 생성됨: $OUTPUT_FILE"
  echo ""
  echo "Codex 없이 Claude가 직접 알고리즘 파일을 분석합니다..."
  echo "대상 파일: $ALGO_FILE"
  echo ""
  echo "--- Claude 직접 분석을 위해 파일 내용 출력 ---"
  cat "$ALGO_FILE"
  exit 0
fi

# ──────────────────────────────────────────────
# Step 2: Version Check
# ──────────────────────────────────────────────
echo "Codex CLI 감지됨: $(codex --version)"

# ──────────────────────────────────────────────
# Step 3: JSON Schema 정의 (구조화된 출력용)
# ──────────────────────────────────────────────
cat > /tmp/algo_verify_schema.json << 'SCHEMA'
{
  "type": "object",
  "properties": {
    "summary": { "type": "string" },
    "correctness_issues": {
      "type": "array",
      "items": { "type": "string" }
    },
    "edge_cases": {
      "type": "array",
      "items": { "type": "string" }
    },
    "time_complexity": { "type": "string" },
    "space_complexity": { "type": "string" },
    "severity": {
      "type": "string",
      "enum": ["correct", "low", "medium", "high", "critical"]
    },
    "recommendation": { "type": "string" }
  },
  "required": [
    "summary",
    "correctness_issues",
    "edge_cases",
    "time_complexity",
    "space_complexity",
    "severity",
    "recommendation"
  ],
  "additionalProperties": false
}
SCHEMA

# ──────────────────────────────────────────────
# Step 4: Codex로 알고리즘 검증 실행
# ──────────────────────────────────────────────
echo "알고리즘 검증 시작: $ALGO_FILE"
echo "Timeout: ${TIMEOUT_SEC}s"

timeout "$TIMEOUT_SEC" codex exec --ephemeral -s read-only --json \
  --output-schema /tmp/algo_verify_schema.json \
  -o "$OUTPUT_FILE" \
  "$(cat <<PROMPT
Verify the correctness of the following algorithm implementation.
Check for:
1. Logical correctness - does it produce the right output for all valid inputs?
2. Edge cases - empty input, single element, duplicates, negative numbers, overflow
3. Off-by-one errors in loops and index operations
4. Time and space complexity analysis
5. Potential infinite loops or non-termination conditions

Algorithm code:

$(cat "$ALGO_FILE")

Respond with structured analysis including severity assessment.
PROMPT
)" || {
  EXIT_CODE=$?
  if [ "$EXIT_CODE" -eq 124 ]; then
    echo "CODEX_TIMEOUT: ${TIMEOUT_SEC}s 초과"
    cat > "$OUTPUT_FILE" << 'TIMEOUT_EOF'
# Algorithm Verification - TIMEOUT

Status: CODEX_TIMEOUT
Reason: Codex CLI did not respond within the time limit.
Recommendation: 파일 크기를 줄이거나 timeout 값을 늘려 재시도하세요.
TIMEOUT_EOF
  else
    echo "CODEX_ERROR: exit code $EXIT_CODE"
    cat > "$OUTPUT_FILE" << 'ERROR_EOF'
# Algorithm Verification - ERROR

Status: CODEX_ERROR
Reason: Codex CLI returned a non-zero exit code.
Recommendation: `codex login` 으로 인증 상태를 확인하고 재시도하세요.
ERROR_EOF
  fi
}

# ──────────────────────────────────────────────
# Step 5: 결과 출력
# ──────────────────────────────────────────────
echo ""
echo "============================================"
echo " 검증 결과"
echo "============================================"
cat "$OUTPUT_FILE"
echo ""
echo "결과 저장 위치: $OUTPUT_FILE"
```

## Script Behavior Summary

| Condition | Action |
|-----------|--------|
| `codex` not found | 설치 방법 안내 출력, placeholder artifact 생성, Claude 직접 분석으로 fallback |
| `codex` found, normal execution | JSON Schema 기반 구조화 출력으로 알고리즘 검증 수행 |
| `codex` found, timeout (124) | TIMEOUT artifact 생성, 재시도 권고 |
| `codex` found, other error | ERROR artifact 생성, 인증 확인 권고 |

## Key Design Decisions

1. **Availability check**: `command -v codex &>/dev/null` -- SKILL.md에서 권장하는 패턴 그대로 사용
2. **Read-only sandbox**: `-s read-only` -- 알고리즘 검증은 파일 수정이 불필요하므로 가장 안전한 모드 사용
3. **Structured output**: `--output-schema`로 JSON Schema를 강제하여 파싱 가능한 결과 확보
4. **Timeout wrapper**: `timeout 120` -- SKILL.md에서 sub-agent 사용 시 필수로 권장
5. **Ephemeral mode**: `--ephemeral` -- 세션 파일 미생성으로 깔끔한 실행
6. **Placeholder artifact**: Codex 미설치 시에도 다른 agent/synthesizer가 상태를 파악할 수 있도록 파일 생성

## Installation Quick Reference

```bash
# Node.js 22+ 필요
npm install -g @openai/codex
codex login
codex --version   # v0.1.0+ 확인
```

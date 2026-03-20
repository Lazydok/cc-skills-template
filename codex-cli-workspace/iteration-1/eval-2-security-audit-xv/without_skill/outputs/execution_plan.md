# Execution Plan: Security Audit Cross-Verification with Codex CLI

## Task

PR의 `src/auth/` 디렉토리 변경사항을 보안 관점에서 Codex CLI로 독립 검증하고,
cross-verification 아티팩트를 `/tmp/xv/`에 저장한다.

---

## Step 1: Artifact Directory Setup

```bash
# 아티팩트 루트 및 하위 구조 생성
mkdir -p /tmp/xv/security-audit/{pass-1,pass-2,summary}

# 타임스탬프 기록 (재현성 확보)
date -u +"%Y-%m-%dT%H:%M:%SZ" > /tmp/xv/security-audit/timestamp.txt

# PR에서 변경된 src/auth/ 파일 목록 추출 (base branch 대비)
git diff --name-only main -- src/auth/ > /tmp/xv/security-audit/changed_files.txt
```

---

## Step 2: Pass 1 -- Codex CLI 보안 감사 (첫 번째 독립 패스)

```bash
codex exec \
  -s read-only \
  -o /tmp/xv/security-audit/pass-1/report.md \
  "You are a security auditor. Review ALL files under src/auth/ for security vulnerabilities.
Focus on:
1. Authentication bypass risks
2. Injection vulnerabilities (SQL, NoSQL, command injection)
3. Insecure token/session handling (hardcoded secrets, weak algorithms, missing expiry)
4. Improper input validation or sanitization
5. Broken access control or privilege escalation paths
6. Information leakage (verbose errors, stack traces, PII exposure)
7. Insecure cryptographic usage (weak hashing, missing salts, ECB mode)
8. Race conditions in auth flows

Output a structured markdown report with:
- CRITICAL / HIGH / MEDIUM / LOW severity per finding
- Affected file path and line range
- Description of the vulnerability
- Recommended fix"
```

---

## Step 3: Pass 2 -- Codex CLI 보안 감사 (두 번째 독립 패스, 다른 모델 또는 프롬프트)

두 번째 패스는 의도적으로 다른 관점(공격자 시뮬레이션)으로 수행하여 교차 검증 효과를 높인다.

```bash
codex exec \
  -s read-only \
  -m o3 \
  -o /tmp/xv/security-audit/pass-2/report.md \
  "You are a penetration tester simulating attacks against this application.
Examine every file under src/auth/ and attempt to find exploitable weaknesses.
For each finding provide:
- Attack scenario (step-by-step how an attacker would exploit it)
- Severity (CRITICAL / HIGH / MEDIUM / LOW)
- Affected file and line numbers
- Proof-of-concept payload or code snippet if applicable
- Mitigation recommendation

Be thorough: check for OWASP Top 10 issues, SSRF, CSRF token handling,
JWT misconfiguration, OAuth flow weaknesses, password storage issues,
and any logic flaws in authentication state machines."
```

---

## Step 4: Cross-Verification Summary 생성

두 패스의 결과를 비교하여 일치/불일치 항목을 정리한다.

```bash
codex exec \
  -s read-only \
  -o /tmp/xv/security-audit/summary/cross_verification.md \
  "You have two independent security audit reports.

Pass 1 report:
$(cat /tmp/xv/security-audit/pass-1/report.md)

Pass 2 report:
$(cat /tmp/xv/security-audit/pass-2/report.md)

Compare these two reports and produce a cross-verification summary:
1. CONFIRMED findings: issues found by BOTH passes (highest confidence)
2. UNIQUE to Pass 1: issues only the first auditor found
3. UNIQUE to Pass 2: issues only the second auditor found
4. CONTRADICTIONS: any conflicting assessments between the two passes
5. OVERALL RISK ASSESSMENT: combined severity rating for src/auth/
6. RECOMMENDED ACTIONS: prioritized list of fixes

Format as structured markdown with clear tables where appropriate."
```

---

## Step 5: JSONL 이벤트 로그 보존 (선택적, 디버깅용)

각 패스에서 `--json` 플래그로 전체 에이전트 이벤트를 기록할 수도 있다.

```bash
# Pass 1 with full event log
codex exec \
  -s read-only \
  --json \
  -o /tmp/xv/security-audit/pass-1/report.md \
  "..." \
  > /tmp/xv/security-audit/pass-1/events.jsonl

# Pass 2 with full event log
codex exec \
  -s read-only \
  -m o3 \
  --json \
  -o /tmp/xv/security-audit/pass-2/report.md \
  "..." \
  > /tmp/xv/security-audit/pass-2/events.jsonl
```

---

## Final Artifact Structure

```
/tmp/xv/
└── security-audit/
    ├── timestamp.txt                  # 실행 시각
    ├── changed_files.txt              # PR에서 변경된 src/auth/ 파일 목록
    ├── pass-1/
    │   ├── report.md                  # 첫 번째 패스 보안 감사 보고서
    │   └── events.jsonl               # (선택) 에이전트 이벤트 로그
    ├── pass-2/
    │   ├── report.md                  # 두 번째 패스 보안 감사 보고서
    │   └── events.jsonl               # (선택) 에이전트 이벤트 로그
    └── summary/
        └── cross_verification.md      # 교차 검증 종합 보고서
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `read-only` sandbox | 보안 감사는 코드를 읽기만 해야 하므로 쓰기 권한 불필요 |
| 두 패스에 다른 모델/프롬프트 사용 | 독립적 관점 확보로 cross-verification 신뢰도 향상 |
| `-o` 플래그로 마지막 메시지 저장 | 에이전트의 최종 보고서만 깔끔하게 추출 |
| `--json` 이벤트 로그 | 감사 과정의 재현성과 추적성 확보 |
| 변경 파일 목록 별도 기록 | 어떤 파일이 감사 대상이었는지 명시적 기록 |

---

## Execution (One-Shot Script)

아래는 전체 과정을 하나의 스크립트로 실행하는 예시이다.

```bash
#!/usr/bin/env bash
set -euo pipefail

XV_DIR="/tmp/xv/security-audit"
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Setup
mkdir -p "$XV_DIR"/{pass-1,pass-2,summary}
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$XV_DIR/timestamp.txt"
git diff --name-only main -- src/auth/ > "$XV_DIR/changed_files.txt"

PASS1_PROMPT="You are a security auditor. Review ALL files under src/auth/ for security vulnerabilities. Focus on: authentication bypass, injection, insecure token handling, input validation, access control, information leakage, weak crypto, race conditions. Output a structured markdown report with CRITICAL/HIGH/MEDIUM/LOW severity, affected file and line range, description, and recommended fix."

PASS2_PROMPT="You are a penetration tester simulating attacks against this application. Examine every file under src/auth/ for exploitable weaknesses. For each finding: attack scenario, severity, affected file/lines, PoC payload, mitigation. Check OWASP Top 10, SSRF, CSRF, JWT, OAuth, password storage, auth logic flaws."

# Pass 1
codex exec -s read-only \
  --json \
  -o "$XV_DIR/pass-1/report.md" \
  "$PASS1_PROMPT" \
  > "$XV_DIR/pass-1/events.jsonl"

# Pass 2 (different model for independence)
codex exec -s read-only \
  -m o3 \
  --json \
  -o "$XV_DIR/pass-2/report.md" \
  "$PASS2_PROMPT" \
  > "$XV_DIR/pass-2/events.jsonl"

# Cross-verification summary
SUMMARY_PROMPT="$(cat <<XVEOF
You have two independent security audit reports for src/auth/.

--- PASS 1 ---
$(cat "$XV_DIR/pass-1/report.md")

--- PASS 2 ---
$(cat "$XV_DIR/pass-2/report.md")

Compare and produce a cross-verification summary:
1. CONFIRMED findings (both passes agree)
2. UNIQUE to Pass 1
3. UNIQUE to Pass 2
4. CONTRADICTIONS
5. OVERALL RISK ASSESSMENT
6. RECOMMENDED ACTIONS (prioritized)
XVEOF
)"

codex exec -s read-only \
  -o "$XV_DIR/summary/cross_verification.md" \
  "$SUMMARY_PROMPT"

echo "Cross-verification complete. Artifacts at: $XV_DIR"
```

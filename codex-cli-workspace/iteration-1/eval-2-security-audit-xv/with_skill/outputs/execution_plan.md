# Execution Plan: Security Audit Cross-Verification of src/auth/

Task: PR의 `src/auth/` 디렉토리 전체를 보안 관점에서 Codex CLI로 독립 검증하고, cross-verification 아티팩트를 `/tmp/xv/`에 생성한다.

---

## Step 1: Codex CLI Availability Check

```bash
if ! command -v codex &>/dev/null; then
  echo "CODEX_NOT_AVAILABLE: skipping cross-verification"
  mkdir -p /tmp/xv/
  cat > /tmp/xv/codex_security_audit.md << 'UNAVAIL'
# Codex Security Audit — SKIPPED
Status: UNAVAILABLE
Reason: codex CLI not installed. Install: npm install -g @openai/codex
UNAVAIL
  exit 1
fi
```

## Step 2: Artifact Directory Setup

```bash
mkdir -p /tmp/xv/security-audit/
```

## Step 3: Identify All Files in src/auth/

```bash
AUTH_FILES=$(find src/auth/ -type f -name '*.py' -o -name '*.ts' -o -name '*.js' | sort)
echo "Files to audit:"
echo "$AUTH_FILES"
```

## Step 4: Per-File Parallel Security Audit via Codex

Each file in `src/auth/` is reviewed independently in parallel, using read-only sandbox mode with a 120-second timeout per file.

```bash
for FILE in $AUTH_FILES; do
  BASENAME=$(basename "$FILE" | sed 's/\.[^.]*$//')
  timeout 120 codex exec --ephemeral -s read-only \
    -o "/tmp/xv/security-audit/codex_${BASENAME}.md" \
    "$(cat <<PROMPT
You are performing an independent security audit for cross-verification.
Another AI has already reviewed this code. Your job is to provide an independent security-focused perspective.

## File Under Audit
File: $FILE

$(cat "$FILE")

## Security Audit Criteria
1. **Injection Vulnerabilities**: SQL injection, command injection, template injection, LDAP injection
2. **Authentication Gaps**: Weak credential handling, missing MFA checks, session fixation
3. **Authorization Bypass**: Privilege escalation, IDOR, missing role checks, broken access control
4. **Sensitive Data Exposure**: Hardcoded secrets, API keys in code, credentials in logs, PII leakage
5. **Input Validation**: Missing or insufficient validation on auth endpoints, type confusion
6. **Cryptographic Issues**: Weak hashing algorithms, insecure token generation, missing salt
7. **Session Management**: Insecure cookie flags, missing expiration, token reuse
8. **Deserialization**: Unsafe deserialization of auth tokens or session data

## Output Format
# Codex Security Audit — ${BASENAME}
Status: PASS | FAIL | PASS_WITH_COMMENTS

## Findings
For each finding:
- **[CRITICAL/HIGH/MEDIUM/LOW]** Line N — Description
- **Attack Vector**: How this could be exploited
- **Recommendation**: How to fix

## Summary Table
| File | Line | Issue | Severity | Recommendation |
|------|------|-------|----------|----------------|

## Verdict: APPROVE | APPROVE_WITH_COMMENTS | REQUEST_CHANGES
PROMPT
  )" || echo "# Codex Security Audit — ${BASENAME} — TIMEOUT" > "/tmp/xv/security-audit/codex_${BASENAME}.md" &
done

# Wait for all parallel jobs with an overall timeout of 180 seconds
WAIT_PID=$$
( sleep 180 && kill -TERM $WAIT_PID 2>/dev/null ) &
WATCHDOG=$!
wait
kill $WATCHDOG 2>/dev/null
```

## Step 5: Directory-Level Holistic Security Audit

After per-file reviews, run a single holistic audit across the entire directory to catch cross-file issues (e.g., inconsistent auth checks, missing middleware on certain routes).

```bash
timeout 120 codex exec --ephemeral -s read-only \
  -o /tmp/xv/security-audit/codex_holistic_auth.md \
  "$(cat <<'PROMPT'
You are performing a holistic security audit of the entire src/auth/ directory for cross-verification.

## All Auth Files
$(find src/auth/ -type f \( -name '*.py' -o -name '*.ts' -o -name '*.js' \) -exec echo "=== {} ===" \; -exec cat {} \;)

## Cross-File Security Audit Criteria
1. **Consistency**: Are auth checks applied uniformly across all entry points?
2. **Middleware Gaps**: Are there routes or handlers that skip authentication/authorization?
3. **Token Flow**: Is token generation, validation, and revocation handled consistently?
4. **Privilege Boundaries**: Are role/permission checks consistent across the module?
5. **Error Handling**: Do auth failures leak implementation details or timing information?
6. **Dependency Issues**: Are auth dependencies (JWT libs, bcrypt, etc.) used securely?

## Output Format
# Codex Holistic Security Audit — src/auth/

## Cross-File Findings
- **[SEVERITY]** Files involved — Description
- **Attack Vector**: Explanation
- **Recommendation**: Fix

## Architecture Concerns
(Any structural issues with the auth module design)

## Verdict: APPROVE | APPROVE_WITH_COMMENTS | REQUEST_CHANGES
PROMPT
)" || echo "# Codex Holistic Security Audit — TIMEOUT" > /tmp/xv/security-audit/codex_holistic_auth.md
```

## Step 6: Verify Artifacts and Generate Summary

```bash
echo "=== Cross-Verification Artifacts ==="
ls -la /tmp/xv/security-audit/codex_*.md
echo ""
echo "=== Artifact Contents Summary ==="
for f in /tmp/xv/security-audit/codex_*.md; do
  echo "--- $(basename "$f") ---"
  head -5 "$f"
  echo ""
done
```

## Step 7: Aggregate Verdict

```bash
# Check for any FAIL or REQUEST_CHANGES verdicts
if grep -ril "REQUEST_CHANGES\|Status: FAIL" /tmp/xv/security-audit/codex_*.md; then
  echo "CROSS-VERIFICATION RESULT: ISSUES FOUND — see artifacts in /tmp/xv/security-audit/"
elif grep -ril "TIMEOUT" /tmp/xv/security-audit/codex_*.md; then
  echo "CROSS-VERIFICATION RESULT: INCOMPLETE — some reviews timed out"
else
  echo "CROSS-VERIFICATION RESULT: PASS"
fi
```

---

## Artifact Structure

```
/tmp/xv/
└── security-audit/
    ├── codex_middleware.md        # Per-file: auth middleware review
    ├── codex_routes.md           # Per-file: auth routes review
    ├── codex_tokens.md           # Per-file: token handling review
    ├── codex_<basename>.md       # Per-file: one per src/auth/ file
    └── codex_holistic_auth.md    # Cross-file: holistic directory audit
```

## Key Design Decisions

| Decision | Rationale | Skill Reference |
|----------|-----------|-----------------|
| `--ephemeral` on every call | No session clutter; clean isolated runs | SKILL.md Pattern 1 |
| `-s read-only` sandbox | Safety — Codex cannot modify any files | SKILL.md Key Flags |
| `timeout 120` per invocation | Prevents hangs on large files; exit code signals timeout | SKILL.md Pattern 7 |
| Parallel `&` with `wait` | Speed — all files reviewed concurrently | review-patterns.md Multi-File section |
| `-o` file output per review | Clean artifact per file; no stdout parsing needed | SKILL.md Pattern 1 |
| Holistic pass after per-file | Catches cross-file auth inconsistencies not visible per-file | Custom addition based on security audit scope |
| Timeout fallback writes marker file | Downstream aggregation knows which reviews completed | SKILL.md Agent Teams Integration |
| Availability check first | Graceful degradation if codex not installed | SKILL.md Prerequisites |

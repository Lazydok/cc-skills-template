# Codex CLI — Review & Analysis Prompt Patterns

## Code Review Prompts

### General Code Review
```bash
codex exec --ephemeral -s read-only -o /tmp/review.md \
  "Review the file src/services/order_processor.py for:
   1. Logic errors in the main processing loop
   2. Edge cases in input handling
   3. Memory leaks or resource cleanup issues
   Output as structured markdown with [CRITICAL/HIGH/MEDIUM/LOW] severity levels."
```

### Security Audit
```bash
codex exec --ephemeral -s read-only -o /tmp/security.md \
  "Security audit of src/api/ directory:
   1. Injection vulnerabilities (SQL, command, template)
   2. Authentication/authorization gaps
   3. Sensitive data exposure (API keys, credentials in code)
   4. Input validation issues on HTTP endpoints
   5. Deserialization vulnerabilities
   Format: markdown table with file, line, issue, severity, recommendation."
```

### Algorithm Verification
```bash
codex exec --ephemeral -s read-only -o /tmp/algo.md \
  "$(cat <<'EOF'
Verify the algorithm correctness:

$(cat src/utils/statistics.py)

Check:
1. Is the statistical formula mathematically correct?
2. Are edge cases handled (zero variance, negative values, empty input)?
3. Does the implementation match the documented specification?
EOF
)"
```

### Test Gap Analysis
```bash
codex exec --ephemeral -s read-only -o /tmp/gaps.md \
  "Compare source files in src/services/ against tests in tests/services/.
   Identify:
   1. Functions/methods with NO test coverage
   2. Edge cases not covered by existing tests
   3. Suggested test cases for each gap
   Format as checklist."
```

## Structured Output Schemas

### Bug Report Schema
```json
{
  "type": "object",
  "properties": {
    "file": { "type": "string" },
    "bugs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "line": { "type": "integer" },
          "description": { "type": "string" },
          "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
          "fix": { "type": "string" }
        },
        "required": ["description", "severity"],
        "additionalProperties": false
      }
    },
    "overall_quality": { "type": "string", "enum": ["poor", "fair", "good", "excellent"] }
  },
  "required": ["file", "bugs", "overall_quality"],
  "additionalProperties": false
}
```

### Review Summary Schema
```json
{
  "type": "object",
  "properties": {
    "summary": { "type": "string" },
    "critical_issues": { "type": "array", "items": { "type": "string" } },
    "suggestions": { "type": "array", "items": { "type": "string" } },
    "approved": { "type": "boolean" }
  },
  "required": ["summary", "critical_issues", "suggestions", "approved"],
  "additionalProperties": false
}
```

## Cross-Verification Template

For agent-teams cross-verification, use this standard prompt:

```bash
codex exec --ephemeral -s read-only -o /tmp/codex_review.md \
  "$(cat <<'PROMPT'
You are performing an independent code review for cross-verification.
Another AI has already reviewed this code. Your job is to provide an independent perspective.

## Code to Review
$(cat $TARGET_FILE)

## Review Criteria
1. **Correctness**: Logic errors, off-by-one, race conditions
2. **Edge Cases**: Null/empty inputs, boundary values, overflow
3. **Security**: Injection, auth bypass, data exposure
4. **Performance**: N+1 queries, unnecessary allocations, blocking calls

## Output Format
For each finding:
- **[SEVERITY]** File:Line — Description
- **Recommendation**: How to fix

End with a summary: APPROVE / APPROVE_WITH_COMMENTS / REQUEST_CHANGES
PROMPT
)"
```

# Execution Plan: Codex CLI Code Review

## Task
"src/utils/calculator.py 파일을 Codex로 리뷰해줘. 로직 오류나 엣지 케이스 문제가 있는지 확인해줘."

## Skill Used
`codex-cli` — Pattern 4 (Inline Code via Heredoc) + Pattern 7 (With Timeout)

## Rationale for Pattern Selection

- **Pattern 4 (Heredoc)**: The file content must be embedded directly in the prompt string because Codex ignores stdin when a prompt argument is given. The heredoc pattern with `$(cat file)` is the correct way to feed file content.
- **Pattern 7 (Timeout)**: Wrapping with `timeout` is recommended for sub-agent use to prevent hangs on large files or complex prompts.
- **`-s read-only`**: This is a review-only task; no file modifications needed. Safest sandbox mode.

## Execution Steps

### Step 1: Verify Codex CLI Availability

```bash
if ! command -v codex &>/dev/null; then
  echo "codex CLI not installed. Install: npm install -g @openai/codex"
  exit 1
fi
```

### Step 2: Verify Target File Exists

```bash
if [ ! -f src/utils/calculator.py ]; then
  echo "ERROR: src/utils/calculator.py not found"
  exit 1
fi
```

### Step 3: Invoke Codex CLI for Code Review

```bash
timeout 120 codex exec --ephemeral -s read-only -o /tmp/codex_calculator_review.md \
  "$(cat <<'EOF'
Review this Python module for logic errors and edge case issues:

$(cat src/utils/calculator.py)

Focus on:
1) Logic errors — incorrect calculations, wrong operator precedence, flawed conditionals
2) Edge cases — division by zero, overflow/underflow, empty input, None/null handling
3) Off-by-one errors
4) Type handling — unexpected input types, missing type checks
5) Boundary conditions — extreme values, negative numbers, floating point precision

Output as markdown with severity levels: [CRITICAL/HIGH/MEDIUM/LOW]
For each finding include: description, affected line/function, severity, and suggested fix.
EOF
)" || echo "# Codex Review — TIMEOUT" > /tmp/codex_calculator_review.md
```

### Step 4: Read and Display Results

```bash
cat /tmp/codex_calculator_review.md
```

## Complete Single-Copy Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# Step 1: Check codex availability
if ! command -v codex &>/dev/null; then
  echo "CODEX_NOT_AVAILABLE: codex CLI not installed."
  echo "Install: npm install -g @openai/codex"
  exit 1
fi

# Step 2: Check target file
TARGET="src/utils/calculator.py"
if [ ! -f "$TARGET" ]; then
  echo "ERROR: $TARGET not found"
  exit 1
fi

# Step 3: Run Codex review with timeout
OUTPUT_FILE="/tmp/codex_calculator_review.md"

timeout 120 codex exec --ephemeral -s read-only -o "$OUTPUT_FILE" \
  "$(cat <<'EOF'
Review this Python module for logic errors and edge case issues:

$(cat src/utils/calculator.py)

Focus on:
1) Logic errors — incorrect calculations, wrong operator precedence, flawed conditionals
2) Edge cases — division by zero, overflow/underflow, empty input, None/null handling
3) Off-by-one errors
4) Type handling — unexpected input types, missing type checks
5) Boundary conditions — extreme values, negative numbers, floating point precision

Output as markdown with severity levels: [CRITICAL/HIGH/MEDIUM/LOW]
For each finding include: description, affected line/function, severity, and suggested fix.
EOF
)" || echo "# Codex Review — TIMEOUT" > "$OUTPUT_FILE"

# Step 4: Display results
echo "=== Codex Review Results ==="
cat "$OUTPUT_FILE"
```

## Key Flags Explained

| Flag | Purpose |
|------|---------|
| `timeout 120` | 120-second timeout to prevent hangs |
| `--ephemeral` | No session persistence; clean execution |
| `-s read-only` | Read-only sandbox — safest mode for review |
| `-o /tmp/codex_calculator_review.md` | Write clean output to file |
| Heredoc `<<'EOF'` | Single-quoted delimiter prevents premature shell expansion |
| `$(cat src/utils/calculator.py)` | Embeds file content into prompt (required because stdin is ignored with a prompt argument) |

## Expected Performance

- **Estimated time**: ~5-15 seconds (single file analysis)
- **Estimated input tokens**: ~10-45K (depending on file size + CLAUDE.md overhead)

## Error Handling

- If `codex` is not installed: exits with install instructions
- If the target file is missing: exits with error message
- If Codex hangs or takes >120s: the `timeout` command kills the process and writes a TIMEOUT marker to the output file
- Codex exit code is 0 even on model errors, so the timeout wrapper is the primary safety net

---
name: codex-cli
description: >
  Invoke OpenAI Codex CLI as a sub-agent for independent code review,
  logical analysis, or cross-verification. Use when needing "second opinion from Codex",
  "Codex review", "cross-verify with Codex", "independent code analysis", or when
  agent-teams cross-verification requires a non-Claude perspective for code correctness.
  Codex CLI runs via `codex exec` with read-only sandbox and structured output support.
  Triggers on: "codex", "codex-cli", "second opinion codex", "cross-verify codex",
  "independent review", "openai review", "gpt review".
---

# Codex CLI Sub-Agent

Invoke OpenAI Codex CLI in exec mode as a sub-agent for independent code analysis.

## Prerequisites

**Install**: `npm install -g @openai/codex` (requires Node.js 22+)
**Auth**: `codex login` — authenticates via ChatGPT browser login (cached after first use)
**Verify**: `codex --version` (minimum v0.1.0+)

Before invoking Codex in scripts or teammate prompts, always check availability:

```bash
if ! command -v codex &>/dev/null; then
  echo "codex CLI not installed. Install: npm install -g @openai/codex"
  exit 1
fi
```

## Core Invocation Patterns

### Pattern 1: Read-Only Analysis (~5-15s)

```bash
codex exec --ephemeral -s read-only -o /tmp/result.txt \
  "Review src/models/user.py for logic errors. Output as markdown."
cat /tmp/result.txt
```

Flags: `--ephemeral` (no session files), `-s read-only` (safe sandbox), `-o FILE` (clean output to file). Exec mode is non-interactive — no approval prompts needed.

### Pattern 2: Structured JSON Output

```bash
cat > /tmp/schema.json << 'SCHEMA'
{
  "type": "object",
  "properties": {
    "summary": { "type": "string" },
    "bugs": { "type": "array", "items": { "type": "string" } },
    "severity": { "type": "string", "enum": ["low", "medium", "high", "critical"] }
  },
  "required": ["summary", "bugs", "severity"],
  "additionalProperties": false
}
SCHEMA

codex exec --ephemeral -s read-only --json \
  --output-schema /tmp/schema.json \
  -o /tmp/analysis.txt \
  "Analyze src/services/order_processor.py for potential bugs"
```

`--output-schema` enforces JSON Schema on the response. Schema MUST include `"additionalProperties": false`.

### Pattern 3: Code Review (Branch Diff, ~30-120s)

```bash
codex exec review --base main --ephemeral --full-auto --json \
  -o /tmp/review.txt \
  "Focus on correctness and potential runtime errors"
cat /tmp/review.txt
```

Review targets: `--base BRANCH`, `--commit SHA`, `--uncommitted`.

### Pattern 4: Inline Code via Heredoc

```bash
codex exec --ephemeral -s read-only -o /tmp/result.txt \
  "$(cat <<'EOF'
Review this module for edge cases and logic errors:

$(cat src/feature.py)

Focus on: 1) Off-by-one errors 2) Null handling 3) Concurrency issues
EOF
)"
cat /tmp/result.txt
```

**Critical**: When a prompt argument is given, stdin is silently ignored. Always embed code in the prompt string via heredoc or `$(cat file)`. To read from stdin instead, omit the positional argument or pass `-` as the prompt.

### Pattern 5: Image-Assisted Review

```bash
codex exec --ephemeral -s read-only \
  -i /tmp/screenshots/error_screenshot.png \
  -o /tmp/result.txt \
  "This screenshot shows a UI rendering bug. What CSS/layout issues could cause this?"
```

`-i/--image` attaches images to the prompt. Useful for visual bug reports, UI review, and diagram analysis. Multiple images supported: `-i img1.png -i img2.png`.

### Pattern 6: Low-Cost Quick Query

```bash
codex exec --ephemeral -s read-only \
  -c 'model_reasoning_effort="low"' \
  -o /tmp/result.txt \
  "Quick: is this function O(n) or O(n^2)? $(cat algo.py)"
```

### Pattern 7: With Timeout (Recommended for Sub-Agent Use)

```bash
timeout 120 codex exec --ephemeral -s read-only -o /tmp/result.txt \
  "Review this code for security issues: $(cat src/auth.py)" \
  || echo "CODEX_TIMEOUT"
```

Always wrap with `timeout` when invoking from a teammate or script — Codex can hang on large files or complex prompts.

## Key Flags

| Flag | Purpose |
|------|---------|
| `--ephemeral` | No session persistence (clean, no disk clutter) |
| `-s read-only` | **Safest** — can read files, cannot modify |
| `-s workspace-write` | Default — can write to workdir and /tmp |
| `-o FILE` | Write last message to file (cleanest output) |
| `--json` | JSONL events to stdout (for programmatic parsing) |
| `--output-schema FILE` | Enforce JSON Schema on response |
| `-c key=value` | Config override (e.g., `model_reasoning_effort="low"`) |
| `-i FILE` | Attach image(s) to prompt (repeatable) |
| `-p PROFILE` | Use named config profile from config.toml |
| `--full-auto` | Auto-approve + workspace-write sandbox — do NOT combine with `-s read-only` (it overrides sandbox to workspace-write) |

## JSONL Output Parsing (`--json`)

```bash
# Extract just the agent message text
codex exec --json --ephemeral -s read-only "prompt" 2>/dev/null \
  | jq -r 'select(.type == "item.completed" and .item.type == "agent_message") | .item.text'
```

Key event types in JSONL:
- `thread.started` — Session ID
- `item.completed` + `type: "agent_message"` — **The response text** (in `.item.text`)
- `item.completed` + `type: "command_execution"` — Shell command results
- `turn.completed` — Token usage: `{input_tokens, cached_input_tokens, output_tokens}`

## Performance

| Scenario | Time | Input Tokens |
|----------|------|-------------|
| Simple Q&A | ~3-5s | ~7-11K |
| File analysis | ~5-15s | ~10-45K |
| Branch review | ~30-120s | ~50-150K |

**Overhead**: CLAUDE.md (~5K tokens) read on every call + MCP server startup (~2-3s).

## Agent Teams Integration

A teammate invokes Codex for cross-verification via Bash tool:

```bash
# Always check availability first
if ! command -v codex &>/dev/null; then
  echo "CODEX_NOT_AVAILABLE: skipping cross-verification"
  # Write a placeholder artifact so synthesizer knows Codex was unavailable
  echo "# Codex Review — SKIPPED\nStatus: UNAVAILABLE\nReason: codex CLI not installed" \
    > /tmp/codex_review.md
else
  timeout 120 codex exec --ephemeral -s read-only -o /tmp/codex_review.md \
    "$(cat <<'PROMPT'
Review this implementation for correctness, edge cases, and security:

$(cat src/feature.py)

Output as markdown with severity levels: [CRITICAL/HIGH/MEDIUM/LOW]
PROMPT
  )" || echo "# Codex Review — TIMEOUT" > /tmp/codex_review.md
fi
CODEX_REVIEW=$(cat /tmp/codex_review.md)
```

## Limitations

- **Stdin ignored with prompt arg** — Must embed code in prompt string (heredoc pattern), or omit the positional arg and pass `-` to read from stdin
- **CLAUDE.md always read** — ~5K tokens consumed per call automatically
- **MCP startup overhead** — ~2-3s per call for configured MCP servers
- **No separate context channel** — Code must be embedded in the prompt itself
- **Exit code 0 even on model errors** — Model handles shell failures internally; wrap with `timeout` to catch hangs
- **`--full-auto` overrides sandbox** — If you need read-only safety, do NOT use `--full-auto`; it forces `workspace-write`

## Detailed Reference

- **[references/invocation-patterns.md](references/invocation-patterns.md)** — Full exec flags, review mode details, sandbox permissions, MCP server mode, error handling
- **[references/review-patterns.md](references/review-patterns.md)** — Code review prompts, security audit templates, test gap analysis patterns

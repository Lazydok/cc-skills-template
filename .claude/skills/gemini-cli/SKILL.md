---
name: gemini-cli
description: >
  Invoke Google Gemini CLI as a sub-agent for second-opinion code review, web search
  via built-in tools, or alternative analysis perspective. Use when needing a "second
  opinion from Gemini", "Gemini review", "cross-verify with Gemini", "web search with
  Gemini", or when agent-teams cross-verification requires a non-Claude perspective.
  Gemini CLI runs headless via -p flag with stdin piping.
  Triggers on: "gemini", "gemini-cli", "second opinion gemini", "cross-verify",
  "web search grounding", "google search".
---

# Gemini CLI Sub-Agent

Invoke Google Gemini CLI in non-interactive mode as a sub-agent from Claude Code.

## Prerequisites

**Install**: `npm install -g @google/gemini-cli` (requires Node.js 20+)
**Auth**: `gemini` — first run triggers OAuth browser login (cached after first use)
**Verify**: `gemini --version`

Before invoking Gemini in scripts or teammate prompts, always check availability:

```bash
if ! command -v gemini &>/dev/null; then
  echo "gemini CLI not installed. Install: npm install -g @google/gemini-cli"
  exit 1
fi
```

## Core Invocation Patterns

All patterns use: `-y` (auto-approve tools) + `-p` (headless) + `-o text` (clean output) + `2>/dev/null` (suppress stderr). Always wrap with `timeout` to prevent auth-related hangs.

### Pattern 1: Simple Analysis

```bash
timeout 60 gemini -y -p "Your question here" -o text 2>/dev/null
```

### Pattern 2: Code Review via Stdin

```bash
cat /path/to/code.py | timeout 60 gemini -y -p "Review this code for bugs and edge cases. Be concise." -o text 2>/dev/null
```

Stdin content is prepended to the `-p` prompt. Code goes through stdin, instruction through `-p`.

### Pattern 3: JSON Structured Output

```bash
RESULT=$(cat file.py | timeout 60 gemini -y -p "Return JSON: {bugs: [], severity: string}" -o json 2>/dev/null)
# Parse envelope: echo "$RESULT" | jq -r '.response'
```

The `-o json` flag wraps the response in an envelope — the actual model output is in `.response`. See [references/invocation-patterns.md](references/invocation-patterns.md) for the full envelope structure.

### Pattern 4: File-Aware with Tools

```bash
timeout 60 gemini -y -p "Read src/models/user.py and summarize the key classes" -o text 2>/dev/null
```

`-y` auto-approves all 14 built-in tools including `read_file`, `grep_search`, `google_web_search`.

### Pattern 5: Web Search via Built-in Tools

```bash
timeout 60 gemini -y -p "Search the web for 'React 19 breaking changes' and summarize" -o text 2>/dev/null
```

Gemini's `google_web_search` tool provides grounded, up-to-date results — useful for verifying library versions, checking API changes, or finding recent issues.

### Pattern 6: With Timeout and Error Handling (Recommended for Sub-Agent Use)

```bash
timeout 120 gemini -y -p "Review this code for security issues: $(cat src/auth.py)" \
  -o text 2>/dev/null || echo "GEMINI_TIMEOUT"
```

## Key Flags

| Flag | Purpose |
|------|---------|
| `-p "prompt"` | **Required** — non-interactive headless mode |
| `-o text/json/stream-json` | Output format (text = cleanest) |
| `-y` | **ALWAYS USE** — auto-approve all built-in tools, no approval prompts |
| `-s` | Sandbox mode (isolates tool execution) |

## Output Capture

```bash
# Variable
GEMINI_RESULT=$(timeout 60 gemini -y -p "review this: $(cat file.py)" -o text 2>/dev/null)

# File
cat file.py | timeout 60 gemini -y -p "review" -o text 2>/dev/null > /tmp/gemini_review.md

# JSON envelope → extract response
timeout 60 gemini -y -p "analyze" -o json 2>/dev/null | jq -r '.response'
```

## Performance

| Scenario | Time | Notes |
|----------|------|-------|
| Simple Q&A | ~3-8s | Includes ~3-5s Node.js cold start |
| Code review (single file) | ~8-20s | Via stdin or read_file tool |
| Web search + summarize | ~10-25s | google_web_search tool invocation |
| Multi-file analysis | ~15-45s | Multiple tool calls with `-y` |

**Overhead**: ~3-5s Node.js cold start per call. Batch related questions into a single prompt when possible.

## Agent Teams Integration

A teammate invokes Gemini for cross-verification via Bash tool:

```bash
# Always check availability first
if ! command -v gemini &>/dev/null; then
  echo "GEMINI_NOT_AVAILABLE: skipping cross-verification"
  echo "# Gemini Review — SKIPPED\nStatus: UNAVAILABLE\nReason: gemini CLI not installed" \
    > /tmp/cross-verify/gemini_review.md
else
  timeout 120 gemini -y \
    -p "Review this Python code. Focus on: 1) Logic errors 2) Edge cases 3) Security. Format as markdown with [CRITICAL/HIGH/MEDIUM/LOW] severity.

$(cat src/feature.py)" \
    -o text 2>/dev/null > /tmp/cross-verify/gemini_review.md \
    || echo "# Gemini Review — TIMEOUT" > /tmp/cross-verify/gemini_review.md
fi
GEMINI_REVIEW=$(cat /tmp/cross-verify/gemini_review.md)
```

## Limitations

- **No image input via CLI** — No flag for images. VLM requires interactive mode only.
- **~3-5s startup overhead** per call (Node.js cold start). Batch work together.
- **No system/user prompt separation** — Everything via `-p` + stdin.
- **Tool text in output** — When `-y` used, intermediate tool text may appear in `-o text`.
- **Auth blocking** — If OAuth expires, CLI blocks waiting for input. Always wrap with `timeout 60`.
- **Write tools auto-approved with `-y`** — For read-only analysis, pipe code via stdin instead of using `-y` with file tools.

## Detailed Reference

- **[references/invocation-patterns.md](references/invocation-patterns.md)** — JSON envelope structure, concurrent execution, error codes, built-in tools list, stream-json parsing
- **[references/review-patterns.md](references/review-patterns.md)** — Code review prompts, security audit templates, web search patterns

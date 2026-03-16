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

**Auth**: OAuth personal (cached). **Binary**: `gemini` (v0.32.1+).

## Core Invocation Patterns

All patterns: `-y` (yolo/auto-approve) + `-p` (headless) + `-o text` (clean output) + `2>/dev/null` (suppress stderr).

### Pattern 1: Simple Analysis

```bash
gemini -y -p "Your question here" -o text 2>/dev/null
```

### Pattern 2: Code Review via Stdin

```bash
cat /path/to/code.py | gemini -y -p "Review this code for bugs and edge cases. Be concise." -o text 2>/dev/null
```

Stdin is prepended to `-p` prompt. Code goes through stdin, instruction through `-p`.

### Pattern 3: JSON Structured Output

```bash
RESULT=$(cat file.py | gemini -y -p "Return JSON: {bugs: [], severity: string}" -o json 2>/dev/null)
# Parse envelope: echo "$RESULT" | jq -r '.response'
```

### Pattern 4: File-Aware with Tools

```bash
gemini -y -p "Read src/models/user.py and summarize the key classes" -o text 2>/dev/null
```

`-y` auto-approves all 14 built-in tools including `read_file`, `grep_search`, `google_web_search`.

### Pattern 5: Web Search via Built-in Tools

```bash
gemini -y -p "Search the web for 'React 19 breaking changes' and summarize" -o text 2>/dev/null
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
GEMINI_RESULT=$(cat file.py | gemini -y -p "review" -o text 2>/dev/null)

# File
cat file.py | gemini -y -p "review" -o text 2>/dev/null > /tmp/gemini_review.md

# With timeout (prevent auth blocking)
timeout 60 gemini -y -p "question" -o text 2>/dev/null
```

## Agent Teams Integration

A teammate invokes Gemini for cross-verification via Bash tool:

```bash
GEMINI_REVIEW=$(cat src/feature.py | gemini -y \
  -p "Review this Python code. Focus on: 1) Logic errors 2) Edge cases 3) Security. Format as markdown with [CRITICAL/HIGH/MEDIUM/LOW] severity." \
  -o text 2>/dev/null)
echo "$GEMINI_REVIEW" > /tmp/cross-verify/gemini_review.md
```

## Limitations

- **No image input via CLI** — No flag for images. VLM requires interactive mode only.
- **~3-5s startup overhead** per call (Node.js cold start). Batch work together.
- **No system/user prompt separation** — Everything via `-p` + stdin.
- **Tool text in output** — When `-y` used, intermediate tool text may appear in `-o text`.
- **Auth blocking** — If OAuth expires, CLI blocks. Always wrap with `timeout 60`.

## Detailed Reference

- **[references/invocation-patterns.md](references/invocation-patterns.md)** — JSON envelope structure, concurrent execution, error codes, built-in tools list

# Gemini CLI — Advanced Invocation Patterns

## Output Format Details

### `-o json` Envelope Structure

The JSON output wraps the model response in an envelope with session info and token stats:

```json
{
  "session_id": "dbb3750b-...",
  "response": "The model's text response here",
  "stats": {
    "models": {
      "gemini-2.5-flash-lite": {
        "api": { "totalRequests": 1, "totalLatencyMs": 1614 },
        "tokens": { "input": 2571, "candidates": 30, "cached": 0, "thoughts": 86 }
      },
      "gemini-3-flash-preview": {
        "api": { "totalRequests": 1, "totalLatencyMs": 2588 },
        "tokens": { "input": 3998, "candidates": 11, "cached": 3391, "thoughts": 29 }
      }
    },
    "tools": { "totalCalls": 0 },
    "files": { "totalLinesAdded": 0, "totalLinesRemoved": 0 }
  }
}
```

**Parse in bash**:
```bash
# Extract just the response text
timeout 60 gemini -y -p "Your prompt" -o json 2>/dev/null | jq -r '.response'

# Extract token usage
timeout 60 gemini -y -p "Your prompt" -o json 2>/dev/null | jq '.stats.models'
```

**Parse in Python**:
```python
import json, subprocess
result = subprocess.run(
    ["timeout", "60", "gemini", "-y", "-p", "Return JSON with key 'answer'", "-o", "json"],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"Gemini failed with exit code {result.returncode}")
else:
    envelope = json.loads(result.stdout)
    model_response = envelope["response"]  # The actual text
    token_stats = envelope["stats"]        # Usage info
```

### `-o stream-json` NDJSON Events

Streaming output delivers events line-by-line. Useful for real-time processing of long responses:

```json
{"type":"init","timestamp":"...","session_id":"...","model":"auto-gemini-3"}
{"type":"message","role":"user","content":"What is 2+2?"}
{"type":"message","role":"assistant","content":"4","delta":true}
{"type":"tool_use","tool_name":"read_file","parameters":{"file_path":"/path"}}
{"type":"tool_result","tool_id":"...","status":"success","output":"..."}
{"type":"result","status":"success","stats":{"total_tokens":10239}}
```

**Parse NDJSON in bash**:
```bash
# Extract only assistant messages (the actual response text)
timeout 120 gemini -y -p "Analyze this codebase" -o stream-json 2>/dev/null \
  | jq -r 'select(.type == "message" and .role == "assistant") | .content'

# Monitor tool usage in real-time
timeout 120 gemini -y -p "Search and analyze" -o stream-json 2>/dev/null \
  | jq -r 'select(.type == "tool_use") | "\(.tool_name): \(.parameters | tostring)"'
```

## Concurrent Execution

```bash
# Run 2 reviews in parallel (~12s instead of ~20s sequential)
timeout 60 gemini -y -p "Review file A" -o text 2>/dev/null > /tmp/review_a.txt &
timeout 60 gemini -y -p "Review file B" -o text 2>/dev/null > /tmp/review_b.txt &
wait

# Check results
for f in /tmp/review_a.txt /tmp/review_b.txt; do
  if [ ! -s "$f" ]; then
    echo "WARNING: $f is empty — Gemini may have timed out or failed"
  fi
done
```

~40% speedup with concurrent calls. No shared state issues between parallel invocations.

## Error Handling

| Exit Code | Meaning | Recovery |
|-----------|---------|----------|
| 0 | Success | — |
| 1 | API error (invalid model, network, rate limit) | Retry after brief wait |
| 124 | Timeout (via `timeout` command) | Simplify prompt or increase timeout |
| 137 | Process killed (SIGKILL) | Check system memory |
| 144 | Process killed (SIGTERM) | Check parent process |

**Robust error handling pattern**:
```bash
GEMINI_OUTPUT=$(timeout 60 gemini -y -p "prompt" -o text 2>/dev/null)
EXIT_CODE=$?

case $EXIT_CODE in
  0)
    if [ -z "$GEMINI_OUTPUT" ]; then
      echo "WARNING: Gemini returned empty output"
    fi
    ;;
  124)
    echo "GEMINI_TIMEOUT: Gemini did not respond within 60s"
    GEMINI_OUTPUT="[Gemini timed out]"
    ;;
  *)
    echo "GEMINI_ERROR: Exit code $EXIT_CODE"
    GEMINI_OUTPUT="[Gemini error: exit $EXIT_CODE]"
    ;;
esac
```

**Auth failure**: CLI blocks waiting for OAuth URL input. Always wrap with `timeout` — this is the most common cause of hangs in automated usage.

## Built-in Tools (14 total)

Available when using `-y` or `--approval-mode yolo`:

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write/create files |
| `replace` | Edit file contents |
| `list_directory` | List directory |
| `grep_search` | Search file contents |
| `glob` | Find files by pattern |
| `run_shell_command` | Execute shell commands |
| `web_fetch` | Fetch web content |
| `google_web_search` | Web search (Google grounding) |
| `codebase_investigator` | Analyze codebase structure |

**Caution**: In yolo mode (`-y`), write tools (`write_file`, `replace`, `run_shell_command`) are also auto-approved. For read-only analysis, pipe code via stdin instead of relying on file tools:

```bash
# Safe: read-only via stdin (no write risk)
cat src/feature.py | timeout 60 gemini -y -p "Review this code" -o text 2>/dev/null

# Risky: -y lets Gemini write/execute if it decides to
timeout 60 gemini -y -p "Fix bugs in src/feature.py" -o text 2>/dev/null
```

## Cross-Verification Bash Snippet

```bash
# Full cross-verification pattern used by agent-teams
if ! command -v gemini &>/dev/null; then
  echo "# Gemini Review — SKIPPED\nStatus: UNAVAILABLE" > /tmp/cross-verify/gemini_review.md
else
  timeout 120 gemini -y \
    -p "Review this Python code for: 1) Logic errors with line numbers 2) Edge cases 3) Security issues. Format: markdown with [CRITICAL/HIGH/MEDIUM/LOW] severity.

$(cat src/feature.py)" \
    -o text 2>/dev/null > /tmp/cross-verify/gemini_review.md \
    || echo "# Gemini Review — TIMEOUT" > /tmp/cross-verify/gemini_review.md
fi
```

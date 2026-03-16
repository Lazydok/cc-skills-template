# Gemini CLI — Advanced Invocation Patterns

## Output Format Details

### `-o json` Envelope Structure

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

**Parse in Python**:
```python
import json, subprocess
result = subprocess.run(
    ["gemini", "-p", "Return JSON with key 'answer'", "-o", "json"],
    capture_output=True, text=True
)
envelope = json.loads(result.stdout)
model_response = envelope["response"]  # The actual text
token_stats = envelope["stats"]        # Usage info
```

### `-o stream-json` NDJSON Events

```json
{"type":"init","timestamp":"...","session_id":"...","model":"auto-gemini-3"}
{"type":"message","role":"user","content":"What is 2+2?"}
{"type":"message","role":"assistant","content":"4","delta":true}
{"type":"tool_use","tool_name":"read_file","parameters":{"file_path":"/path"}}
{"type":"tool_result","tool_id":"...","status":"success","output":"..."}
{"type":"result","status":"success","stats":{"total_tokens":10239}}
```

## Concurrent Execution

```bash
# Run 2 reviews in parallel (~12s instead of ~20s sequential)
gemini -p "Review file A" -o text 2>/dev/null > /tmp/review_a.txt &
gemini -p "Review file B" -o text 2>/dev/null > /tmp/review_b.txt &
wait
```

~40% speedup with concurrent calls. No shared state issues.

## Error Handling

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | API error (invalid model, network) |
| 124 | Timeout (via `timeout` command) |
| 137/144 | Process killed (SIGKILL/SIGTERM) |

**Auth failure**: CLI blocks waiting for OAuth URL input. Always wrap with `timeout`:
```bash
timeout 60 gemini -p "prompt" -o text 2>/dev/null || echo "GEMINI_TIMEOUT"
```

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
| `google_web_search` | Web search |
| `codebase_investigator` | Analyze codebase |

**Caution**: In yolo mode, write tools are also auto-approved. For read-only analysis, pipe code via stdin instead.

## Cross-Verification Bash Snippet

```bash
# Full cross-verification pattern used by agent-teams
CODE=$(cat src/feature.py)

GEMINI_REVIEW=$(echo "$CODE" | gemini \
  -p "Review this Python code for: 1) Logic errors with line numbers 2) Edge cases 3) Security issues. Format: markdown with [CRITICAL/HIGH/MEDIUM/LOW] severity." \
  -o text 2>/dev/null)

# Write to shared location for synthesis
echo "$GEMINI_REVIEW" > /tmp/cross-verify/gemini_review.md
```

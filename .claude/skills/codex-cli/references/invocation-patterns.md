# Codex CLI — Advanced Invocation Patterns

## Complete Exec Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--ephemeral` | No session persistence | Always use for sub-agent |
| `-s MODE` | Sandbox: `read-only`, `workspace-write`, `danger-full-access` | `-s read-only` |
| `-o FILE` | Last message to file | `-o /tmp/result.txt` |
| `--json` | JSONL events to stdout | For programmatic parsing |
| `--output-schema FILE` | JSON Schema enforcement | Schema must have `additionalProperties: false` |
| `-m MODEL` | Model override (use default) | Rarely needed |
| `-c key=value` | Config override (TOML) | `-c 'model_reasoning_effort="low"'` |
| `-C DIR` | Working directory | Requires `--skip-git-repo-check` if not git repo |
| `--add-dir DIR` | Additional writable dirs | `-add-dir /data` |
| `--full-auto` | Auto-approve + workspace-write | Alias for `-a on-request -s workspace-write` (**overrides** `-s`, do NOT combine with `-s read-only`) |
| `--skip-git-repo-check` | Run outside git repos | Required with `-C` to non-git dirs |

## Input Methods

### Positional Argument (Recommended)
```bash
codex exec "Your prompt here"
```
When provided, stdin is SILENTLY ignored.

### Stdin (No Argument)
```bash
echo "What is 2+2?" | codex exec
# Prints: "Reading prompt from stdin..."
```
Entire stdin becomes the prompt. Only works when NO positional arg given.

### Heredoc (Best for Code)
```bash
codex exec "$(cat <<'EOF'
Analyze this code:

$(cat /path/to/file.py)

Focus on logic errors.
EOF
)"
```

## Review Mode Details

Two interfaces exist:

| Command | JSON | -o FILE | Best For |
|---------|------|---------|----------|
| `codex review` | No | No | Interactive review |
| `codex exec review` | Yes | Yes | **Sub-agent use** |

### Review Targets
```bash
codex exec review --base main --json -o /tmp/r.txt          # vs branch
codex exec review --commit HEAD --json -o /tmp/r.txt        # specific commit
codex exec review --uncommitted --json -o /tmp/r.txt        # staged + unstaged
codex exec review --commit abc123 "Focus on security" --json  # with instructions
```

## Sandbox Permissions

| Mode | Read Files | Write Files | Shell | Network |
|------|-----------|-------------|-------|---------|
| `read-only` | workdir | No | Read cmds only | No |
| `workspace-write` | workdir | workdir, /tmp | Yes | No |
| `danger-full-access` | All | All | All | Yes |

For sub-agent: always use `read-only` unless writes are explicitly needed.

## Config Overrides

```bash
# Low reasoning effort (faster, cheaper)
codex exec -c 'model_reasoning_effort="low"' "prompt"

# High reasoning effort (thorough)
codex exec -c 'model_reasoning_effort="xhigh"' "prompt"

# Full read access (beyond workdir)
codex exec -c 'sandbox_permissions=["disk-full-read-access"]' "prompt"
```

## JSONL Output Structure

```json
{"type":"thread.started","thread_id":"019cd2ad-..."}
{"type":"turn.started"}
{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"response text"}}
{"type":"turn.completed","usage":{"input_tokens":10956,"cached_input_tokens":5888,"output_tokens":32}}
```

**Parse in bash**:
```bash
codex exec --json --ephemeral "prompt" 2>/dev/null \
  | jq -r 'select(.type == "item.completed" and .item.type == "agent_message") | .item.text'
```

## MCP Server Mode (Future Integration)

```bash
codex mcp-server  # Starts stdio-based MCP server
```

Could be added to Claude Code's MCP config for direct tool access instead of CLI invocation.
Waits for JSON-RPC messages on stdin. Standard MCP protocol.

## Error Handling

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success (also when model's shell commands fail internally) |
| 1 | API error, auth error, schema validation error |
| 2 | CLI argument error |
| 124 | Timeout (via `timeout` wrapper) |

```bash
# With timeout
timeout 120 codex exec --ephemeral -s read-only -o /tmp/r.txt "prompt" || echo "CODEX_TIMEOUT"
```

## Token Overhead

Every call consumes baseline tokens:
- CLAUDE.md reading: ~5K tokens
- MCP server init: ~2K tokens
- Minimum per call: ~7K input tokens even for simple queries
- Recommendation: batch related questions into single calls when possible

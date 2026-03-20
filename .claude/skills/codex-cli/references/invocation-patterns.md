# Codex CLI — Advanced Invocation Patterns

## Complete Exec Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--ephemeral` | No session persistence | Always use for sub-agent |
| `-s MODE` | Sandbox: `read-only`, `workspace-write`, `danger-full-access` | `-s read-only` |
| `-o FILE` | Last message to file | `-o /tmp/result.txt` |
| `--json` | JSONL events to stdout | For programmatic parsing |
| `--output-schema FILE` | JSON Schema enforcement | Schema must have `additionalProperties: false` |
| `-m MODEL` | Model override | `-m o3` (use default unless specific model needed) |
| `-c key=value` | Config override (TOML) | `-c 'model_reasoning_effort="low"'` |
| `-C DIR` | Working directory | Requires `--skip-git-repo-check` if not git repo |
| `-i FILE` | Attach image(s) to prompt | `-i screenshot.png` (repeatable) |
| `-p PROFILE` | Named config profile from config.toml | `-p fast-review` |
| `--full-auto` | Auto-approve + workspace-write | Alias for `-a on-request -s workspace-write` (**overrides** `-s`, do NOT combine with `-s read-only`) |
| `--skip-git-repo-check` | Run outside git repos | Required with `-C` to non-git dirs |
| `--oss` | Use local open-source model | Requires LM Studio or Ollama running locally |
| `--local-provider PROVIDER` | Specify local provider | `--local-provider lmstudio` or `--local-provider ollama` |
| `--enable FEATURE` | Enable a feature flag | `--enable some-feature` |
| `--disable FEATURE` | Disable a feature flag | `--disable some-feature` |

## Input Methods

### Positional Argument (Recommended)
```bash
codex exec "Your prompt here"
```
When provided, stdin is SILENTLY ignored.

### Stdin (No Argument or `-`)
```bash
echo "What is 2+2?" | codex exec
# Prints: "Reading prompt from stdin..."

# Or explicitly with `-` placeholder:
cat prompt.txt | codex exec -
```
Entire stdin becomes the prompt. Only works when NO positional arg given (or `-` is used).

### Heredoc (Best for Code)
```bash
codex exec "$(cat <<'EOF'
Analyze this code:

$(cat /path/to/file.py)

Focus on logic errors.
EOF
)"
```

### Image Input
```bash
# Single image
codex exec -i screenshot.png "What UI issues do you see in this screenshot?"

# Multiple images
codex exec -i before.png -i after.png "Compare these two UI states and identify the visual regression"
```

## Review Mode Details

Two interfaces exist — use `codex exec review` for sub-agent automation:

| Command | JSON | -o FILE | --ephemeral | Best For |
|---------|------|---------|-------------|----------|
| `codex review` | No | No | No | Interactive review (human at terminal) |
| `codex exec review` | Yes | Yes | Yes | **Sub-agent / automation use** |

### Review Targets
```bash
codex exec review --base main --json -o /tmp/r.txt          # vs branch
codex exec review --commit HEAD --json -o /tmp/r.txt        # specific commit
codex exec review --uncommitted --json -o /tmp/r.txt        # staged + unstaged
codex exec review --commit abc123 "Focus on security" --json  # with instructions
codex exec review --base main --title "Auth refactor" --json  # with title context
```

### Review-Specific Flags
| Flag | Purpose |
|------|---------|
| `--base BRANCH` | Review changes against a base branch |
| `--commit SHA` | Review changes introduced by a specific commit |
| `--uncommitted` | Review staged, unstaged, and untracked changes |
| `--title TITLE` | Optional commit/PR title for context |

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

# Use a config profile
codex exec -p my-review-profile "prompt"
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

## MCP Server Mode

Codex can run as an MCP server over stdio, allowing direct tool integration:

```bash
codex mcp-server  # Starts stdio-based MCP server
```

This could be added to Claude Code's MCP config for direct tool access instead of CLI invocation. It accepts JSON-RPC messages on stdin following the standard MCP protocol.

## Applying Agent Diffs

When Codex produces code changes, you can apply them to your working tree:

```bash
codex apply        # Pick from recent sessions
codex apply --last # Apply the most recent session's diff
```

This runs `git apply` under the hood, so changes are unstaged and reversible.

## Error Handling

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success (also when model's shell commands fail internally) |
| 1 | API error, auth error, schema validation error |
| 2 | CLI argument error |
| 124 | Timeout (via `timeout` wrapper) |

```bash
# Recommended: always use timeout for sub-agent invocations
timeout 120 codex exec --ephemeral -s read-only -o /tmp/r.txt "prompt"
EXIT_CODE=$?
if [ $EXIT_CODE -eq 124 ]; then
  echo "CODEX_TIMEOUT"
elif [ $EXIT_CODE -ne 0 ]; then
  echo "CODEX_ERROR (exit $EXIT_CODE)"
fi
```

## Token Overhead

Every call consumes baseline tokens:
- CLAUDE.md reading: ~5K tokens
- MCP server init: ~2K tokens
- Minimum per call: ~7K input tokens even for simple queries
- Recommendation: batch related questions into single calls when possible

---
name: codex-cli
description: >
  Invoke OpenAI Codex via the codex plugin for independent code review,
  logical analysis, task delegation, or cross-verification. Use when needing
  "second opinion from Codex", "Codex review", "cross-verify with Codex",
  "independent code analysis", or when agent-teams cross-verification requires
  a non-Claude perspective for code correctness. Provides slash commands,
  companion script for teammates, and subagent integration.
  Triggers on: "codex", "codex-cli", "second opinion codex", "cross-verify codex",
  "independent review", "openai review", "gpt review".
---

# Codex CLI — Plugin Integration

Invoke Codex through the `openai/codex` plugin for code review, task delegation, and cross-verification.

## Prerequisites

Run `/codex:setup` to check installation, authentication, and optionally enable the stop-time review gate. The setup command reports readiness and next steps.

```
/codex:setup
/codex:setup --enable-review-gate
```

## Core Commands

### Code Review

Reviews local git changes using the built-in Codex reviewer. Does not accept custom focus text — use adversarial review for that.

```
/codex:review
/codex:review --base main
/codex:review --scope working-tree
/codex:review --scope branch --base feature-branch
```

Flags: `--wait` (block until done), `--background` (return immediately), `--base <ref>`, `--scope <auto|working-tree|branch>`.

### Adversarial Review

Deep review with custom focus areas. Supports structured JSON output with verdict/findings/next_steps.

```
/codex:adversarial-review
/codex:adversarial-review security injection auth
/codex:adversarial-review --base main concurrency edge-cases
```

Same flags as review, plus positional focus text.

### Task Delegation (Rescue)

Delegate work to Codex — diagnosis, fixes, research, implementation.

```
/codex:rescue fix the failing test in tests/test_auth.py
/codex:rescue --model spark diagnose why the API returns 500
/codex:rescue --effort high implement input validation for the signup form
/codex:rescue --resume        # continue previous Codex thread
/codex:rescue --fresh          # force new thread
```

Flags: `--background`, `--wait`, `--resume` / `--fresh`, `--model <name|spark>`, `--effort <none|minimal|low|medium|high|xhigh>`, `--write` (default for task).

Note: `/codex:rescue --resume` maps internally to the companion script's `--resume-last` flag. Similarly, `--fresh` prevents `--resume-last` from being added.

Model alias: `spark` maps to `gpt-5.3-codex-spark`.

### Job Management

```
/codex:status              # all active jobs
/codex:status <job-id>     # single job
/codex:status <job-id> --wait   # poll until complete
/codex:result <job-id>     # fetch completed output
/codex:cancel <job-id>     # cancel active job
```

## Programmatic Integration

### Subagent (from Claude Code)

Use `Agent(subagent_type="codex:codex-rescue")` to delegate to Codex programmatically:

```python
Agent(
  subagent_type="codex:codex-rescue",
  prompt="Diagnose why tests/test_order.py::test_cancel fails",
  description="Codex diagnosis of test failure"
)
```

The rescue subagent is a thin forwarder — it invokes one `task` call and returns the output unchanged.

### Companion Script (for Teammates / Bash)

Teammates invoke Codex through the companion script:

```bash
COMPANION="${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"

# Review
node "$COMPANION" review --base main --scope auto

# Adversarial review with focus
node "$COMPANION" adversarial-review --base main "security injection"

# Task
node "$COMPANION" task "diagnose the test failure in tests/test_auth.py" --write

# Task with model and effort
node "$COMPANION" task --model spark --effort high "fix the broken migration"

# Resume previous thread
node "$COMPANION" task --resume-last "apply the top recommendation"

# Job management
node "$COMPANION" status
node "$COMPANION" result <job-id>
node "$COMPANION" cancel <job-id>
```

### Agent Teams Cross-Verification

A teammate uses the companion script for independent analysis, saving artifacts to `/tmp/xv/`:

```bash
COMPANION="${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"
mkdir -p /tmp/xv/review/

# Check availability first
node "$COMPANION" setup --json | jq -e '.ready' > /dev/null 2>&1 || {
  echo "# Codex Review — SKIPPED\nStatus: UNAVAILABLE" > /tmp/xv/review/codex.md
  exit 0
}

# Run adversarial review and save artifact
node "$COMPANION" adversarial-review --base main "correctness edge-cases security" \
  > /tmp/xv/review/codex.md 2>&1
```

## Prompt Composition (GPT-5.4)

When crafting prompts for `/codex:rescue` tasks, use XML block structure for best results. The `gpt-5-4-prompting` plugin skill provides the full reference.

### Key Blocks

| Block | When to Use |
|-------|-------------|
| `<task>` | Always — describe the job and expected end state |
| `<structured_output_contract>` | When response shape matters |
| `<compact_output_contract>` | When you want concise prose |
| `<default_follow_through_policy>` | Codex should act without asking routine questions |
| `<completeness_contract>` | Multi-step tasks that must not stop early |
| `<verification_loop>` | When correctness matters |
| `<missing_context_gating>` | Prevent guessing missing facts |
| `<grounding_rules>` | Review/research — ground claims in evidence |
| `<action_safety>` | Write-capable tasks — keep changes scoped |
| `<dig_deeper_nudge>` | Review — check for second-order failures |
| `<research_mode>` | Exploration/comparison — separate facts vs inferences |
| `<citation_rules>` | Research — back claims with references |

### Example: Diagnosis Prompt

```xml
<task>
Diagnose why tests/test_auth.py::test_login_expired fails.
Use repository context and tools to identify the root cause.
</task>

<compact_output_contract>
Return: 1. root cause  2. evidence  3. smallest safe next step
</compact_output_contract>

<verification_loop>
Verify the proposed root cause matches observed evidence before finalizing.
</verification_loop>
```

## Review Output Format

Adversarial reviews return structured JSON. Note: the plugin uses `approve`/`needs-attention` verdicts, while cross-verification artifacts use `APPROVE`/`REQUEST_CHANGES` — synthesizers should handle this mapping.

```json
{
  "verdict": "approve | needs-attention",
  "summary": "...",
  "findings": [{
    "severity": "critical|high|medium|low",
    "title": "...", "body": "...",
    "file": "...", "line_start": 1, "line_end": 10,
    "confidence": 0.9, "recommendation": "..."
  }],
  "next_steps": ["..."]
}
```

## Result Handling

- Preserve verdict, findings, and next_steps structure from Codex output
- Present findings ordered by severity
- Keep file paths and line numbers exactly as reported
- After presenting review findings, **STOP** — do not auto-apply fixes. Ask the user which issues to fix
- If Codex fails or was never invoked, report the failure — do not generate a substitute answer
- If setup/auth is required, direct to `/codex:setup`

## Performance

| Scenario | Time |
|----------|------|
| Native review | ~30-60s |
| Adversarial review | ~30-120s |
| Task (simple) | ~10-30s |
| Task (complex) | ~60-300s |

## Limitations

- `/codex:review` does not accept custom focus text — use `/codex:adversarial-review` for focused reviews
- Codex reads CLAUDE.md on every call (~5K token overhead)
- MCP server startup adds ~2-3s per call
- Background tasks require polling via `/codex:status` for completion
- Thread resumption (`--resume`) requires a previous task thread in the same workspace

## Detailed Reference

- **[references/plugin-integration.md](references/plugin-integration.md)** — Companion script reference, teammate patterns, prompt blocks, recipes, job lifecycle, error handling

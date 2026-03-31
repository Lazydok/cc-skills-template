# Codex Plugin — Advanced Integration Reference

## Companion Script Command Reference

The companion script is the primary interface for teammates and Bash-level Codex integration.

```
COMPANION="${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"
```

### setup

Check readiness and configure the review gate.

```bash
node "$COMPANION" setup                          # human-readable report
node "$COMPANION" setup --json                   # machine-readable
node "$COMPANION" setup --enable-review-gate     # require review before stop
node "$COMPANION" setup --disable-review-gate    # remove review gate
```

JSON output includes: `ready`, `node`, `npm`, `codex`, `auth`, `sessionRuntime`, `reviewGateEnabled`, `nextSteps`.

### review

Native Codex code review against git state. Does not support custom focus text.

```bash
node "$COMPANION" review                         # auto-detect scope
node "$COMPANION" review --base main             # diff against main
node "$COMPANION" review --scope working-tree    # uncommitted changes only
node "$COMPANION" review --scope branch --base main
node "$COMPANION" review --wait                  # block until complete
node "$COMPANION" review --background            # return immediately
```

### adversarial-review

Deep review with custom focus. Returns structured JSON (verdict, findings, next_steps).

```bash
node "$COMPANION" adversarial-review                              # no extra focus
node "$COMPANION" adversarial-review "security injection auth"    # with focus
node "$COMPANION" adversarial-review --base main "concurrency"    # against branch
node "$COMPANION" adversarial-review --scope working-tree "edge cases"
```

### task

Delegate work to Codex. Default is write-capable.

```bash
node "$COMPANION" task "fix the failing test"                     # write mode
node "$COMPANION" task "explain this algorithm" --write           # explicit write
node "$COMPANION" task --model spark "quick diagnosis"            # use spark model
node "$COMPANION" task --effort high "thorough security audit"    # high reasoning
node "$COMPANION" task --resume-last "apply the top fix"          # resume thread
node "$COMPANION" task --resume-last                              # continue with default prompt
node "$COMPANION" task --fresh "start over on this problem"       # force new thread
node "$COMPANION" task --background "long running analysis"       # background execution
node "$COMPANION" task --prompt-file /tmp/prompt.txt              # read prompt from file
```

Piped stdin also works when no positional prompt is given:

```bash
echo "Review this code for bugs" | node "$COMPANION" task
```

### status

```bash
node "$COMPANION" status                         # all recent jobs
node "$COMPANION" status --all                   # include completed/cancelled
node "$COMPANION" status <job-id>                # single job
node "$COMPANION" status <job-id> --wait         # poll until complete
node "$COMPANION" status <job-id> --json         # machine-readable
```

### result

```bash
node "$COMPANION" result                         # latest completed job
node "$COMPANION" result <job-id>                # specific job
node "$COMPANION" result <job-id> --json         # machine-readable
```

### cancel

```bash
node "$COMPANION" cancel                         # cancel latest active job
node "$COMPANION" cancel <job-id>                # cancel specific job
```

Cancellation sends an interrupt to the Codex turn and terminates the background process.

## Teammate Invocation Patterns

### General-Purpose Teammate

A teammate can use the companion script directly via Bash:

```bash
COMPANION="${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"

# Check availability
if ! node "$COMPANION" setup --json 2>/dev/null | jq -e '.ready' > /dev/null 2>&1; then
  echo "CODEX_NOT_AVAILABLE"
  exit 1
fi

# Run task
node "$COMPANION" task "Review src/auth/middleware.py for security issues" 2>&1
```

### Cross-Verification Teammate

```bash
COMPANION="${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"
mkdir -p /tmp/xv/review/

# Adversarial review with artifact output
node "$COMPANION" adversarial-review --base main "correctness security edge-cases" \
  > /tmp/xv/review/codex_adversarial.md 2>&1

# Or review specific files via task
node "$COMPANION" task "$(cat <<'PROMPT'
Independent code review of the following files for cross-verification:

$(cat src/auth/middleware.py)

Focus on: correctness, edge cases, security, performance.
Format findings by severity: CRITICAL > HIGH > MEDIUM > LOW.
End with verdict: APPROVE | APPROVE_WITH_COMMENTS | REQUEST_CHANGES
PROMPT
)" > /tmp/xv/review/codex_task.md 2>&1
```

### Multi-File Parallel Review

```bash
COMPANION="${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"
mkdir -p /tmp/xv/review/

for FILE in src/auth/middleware.py src/api/routes.py; do
  BASENAME=$(basename "$FILE" .py)
  node "$COMPANION" task "Independent review of $FILE: $(cat "$FILE")" \
    > "/tmp/xv/review/codex_${BASENAME}.md" 2>&1 &
done
wait

ls -la /tmp/xv/review/codex_*.md
```

## Artifact Workflow

Cross-verification artifacts follow the `/tmp/xv/` convention:

```
/tmp/xv/
  review/
    codex_adversarial.md    # adversarial review output
    codex_middleware.md     # per-file review
    codex_routes.md
  task/
    codex_diagnosis.md      # task output
```

## Job Lifecycle and State Management

Jobs progress through states: `queued` -> `running` -> `completed` | `failed` | `cancelled`.

State is persisted per workspace. The companion script manages job records automatically.

### Background Jobs

```bash
# Launch in background
node "$COMPANION" task --background "long analysis task"
# Output: "Codex Task started in the background as task-abc123"

# Poll for completion
node "$COMPANION" status task-abc123 --wait

# Fetch result
node "$COMPANION" result task-abc123
```

### Thread Resumption

Codex threads persist across task runs within the same workspace. Use `--resume-last` to continue a previous thread:

```bash
# Initial task
node "$COMPANION" task "diagnose why the migration fails"

# Follow-up on same thread
node "$COMPANION" task --resume-last "apply the fix you recommended"

# Force a fresh thread
node "$COMPANION" task --fresh "start a new investigation"
```

`--resume-last` finds the most recent completed task thread. If a task is still running, it throws an error.

## Model and Effort Configuration

### Models

- Default: Codex default model (unset)
- `spark`: alias for `gpt-5.3-codex-spark` (faster, lower cost)
- Any model name: passed through directly (e.g., `--model o3`)

### Reasoning Effort

Accepted values: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`.

- Leave unset for default reasoning
- Use `low`/`minimal` for quick queries
- Use `high`/`xhigh` for thorough analysis

```bash
node "$COMPANION" task --effort low "quick: is this O(n) or O(n^2)?"
node "$COMPANION" task --effort xhigh "thorough security audit of src/auth/"
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Codex not installed | `setup` reports not ready; commands throw with install instructions |
| Not authenticated | Commands throw with `codex login` instructions |
| Task with no prompt | Throws "Provide a prompt, a prompt file, piped stdin, or use --resume-last" |
| `--resume` + `--fresh` | Throws "Choose either --resume/--resume-last or --fresh" |
| No previous thread for `--resume` | Throws "No previous Codex task thread was found" |
| Active task when resuming | Throws "Task X is still running. Use /codex:status" |
| Background job failure | Job status set to `failed`; check via `status` or `result` |
| Cancel with no active job | Throws error via `resolveCancelableJob` |

When Codex fails in a rescue subagent, report the failure and stop. Do not generate a substitute answer.

## Prompt Block Reference (GPT-5.4)

Use these XML blocks when composing prompts for `task` calls. Wrap each in its XML tag.

### Core

```xml
<task>
Describe the concrete job, repository context, and expected end state.
</task>
```

### Output

```xml
<structured_output_contract>
Return exactly the requested output shape. Put highest-value findings first.
</structured_output_contract>

<compact_output_contract>
Keep the answer compact and structured. No long scene-setting or recap.
</compact_output_contract>
```

### Follow-Through

```xml
<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
Only stop for missing details that change correctness, safety, or irreversible actions.
</default_follow_through_policy>

<completeness_contract>
Resolve the task fully. Do not stop at the first plausible answer.
Check for follow-on fixes, edge cases, or cleanup needed.
</completeness_contract>

<verification_loop>
Before finalizing, verify the result against task requirements and changed files.
If a check fails, revise instead of reporting the first draft.
</verification_loop>
```

### Grounding

```xml
<missing_context_gating>
Do not guess missing repository facts. Retrieve with tools or state what remains unknown.
</missing_context_gating>

<grounding_rules>
Ground every claim in provided context or tool outputs. Label hypotheses clearly.
</grounding_rules>

<citation_rules>
Back important claims with citations or explicit references. Prefer primary sources.
</citation_rules>
```

### Safety and Scope

```xml
<action_safety>
Keep changes tightly scoped. Avoid unrelated refactors. Call out risky actions first.
</action_safety>

<dig_deeper_nudge>
After the first plausible issue, check for second-order failures, empty-state behavior,
retries, stale state, and rollback paths before finalizing.
</dig_deeper_nudge>
```

### Block Selection Guide

| Task Type | Required Blocks | Optional Blocks |
|-----------|----------------|-----------------|
| Coding/Debugging | `task`, `completeness_contract`, `verification_loop` | `missing_context_gating`, `action_safety` |
| Review | `task`, `grounding_rules`, `structured_output_contract` | `dig_deeper_nudge`, `verification_loop` |
| Research | `task`, `research_mode`, `citation_rules` | `structured_output_contract` |
| Write-capable fix | `task`, `action_safety`, `verification_loop` | `completeness_contract` |

## Prompt Recipe Templates

### Diagnosis

```xml
<task>
Diagnose why [test/command] is failing. Identify the most likely root cause.
</task>
<compact_output_contract>
Return: 1. root cause  2. evidence  3. smallest safe next step
</compact_output_contract>
<default_follow_through_policy>
Keep going until you have enough evidence for a confident diagnosis.
</default_follow_through_policy>
<verification_loop>
Verify the proposed root cause matches observed evidence.
</verification_loop>
<missing_context_gating>
Do not guess. State what remains unknown.
</missing_context_gating>
```

### Narrow Fix

```xml
<task>
Implement the smallest safe fix for [issue]. Preserve existing behavior outside the failing path.
</task>
<structured_output_contract>
Return: 1. fix summary  2. touched files  3. verification performed  4. residual risks
</structured_output_contract>
<completeness_contract>
Do not stop after identifying the issue without applying the fix.
</completeness_contract>
<verification_loop>
Verify the fix is coherent and matches requirements.
</verification_loop>
<action_safety>
Keep changes tightly scoped. Avoid unrelated refactors.
</action_safety>
```

### Root-Cause Review

```xml
<task>
Analyze this change for correctness or regression issues. Focus on repository context only.
</task>
<structured_output_contract>
Return: 1. findings by severity  2. evidence  3. next steps
</structured_output_contract>
<grounding_rules>
Ground every claim in repository context. Label inferences clearly.
</grounding_rules>
<dig_deeper_nudge>
Check for second-order failures, empty-state handling, retries, stale state, rollback paths.
</dig_deeper_nudge>
```

### Research / Recommendation

```xml
<task>
Research available options and recommend the best path for [goal].
</task>
<structured_output_contract>
Return: 1. observed facts  2. recommendation  3. tradeoffs  4. open questions
</structured_output_contract>
<research_mode>
Separate facts, inferences, and open questions. Breadth first, then depth where evidence warrants.
</research_mode>
<citation_rules>
Back claims with explicit references. Prefer primary sources.
</citation_rules>
```

## Review Output Schema

Adversarial reviews produce structured JSON:

```json
{
  "verdict": "approve | needs-attention",
  "summary": "string",
  "findings": [
    {
      "severity": "critical | high | medium | low",
      "title": "string",
      "body": "string",
      "file": "string",
      "line_start": 1,
      "line_end": 10,
      "confidence": 0.9,
      "recommendation": "string"
    }
  ],
  "next_steps": ["string"]
}
```

Native `/codex:review` returns rendered text directly from the built-in Codex reviewer.

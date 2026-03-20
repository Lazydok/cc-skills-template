---
name: agent-teams
description: >
  Use Agent Teams (TeamCreate → Agent with team_name) for tasks that benefit from
  coordinated parallel work: multi-module features (3+ files across different directories),
  multi-perspective code review, team-based debugging/investigation, cross-verification
  with external agents, or any task where 2+ independent work streams can run in parallel.
  Not needed for single-file edits, simple lookups, or sequential tasks that touch 1-2 files.
  When this skill triggers, create a team with TeamCreate first, then spawn teammates via
  Agent tool WITH team_name parameter — never fall back to plain subagents (Agent without
  team_name) when this skill is active.
  Triggers on: "agent team", "team", "parallel", "teammates", "coordinate", "swarm",
  "multi-agent", "cross-verify", "code review team", "investigation team".
---

# Agent Teams

**MANDATORY**: When this skill is loaded, you MUST use `TeamCreate` + `Agent(team_name=...)` to create a real agent team. Do NOT use `Agent()` without `team_name` — that creates a subagent, not a teammate.

## Quick Start (Minimum Viable Team)

```
1. TeamCreate(team_name="my-team", description="...")
2. Agent(team_name="my-team", name="worker-1", prompt="...", description="...")
3. Agent(team_name="my-team", name="worker-2", prompt="...", description="...")
   ... teammates work, communicate via SendMessage ...
4. SendMessage(type="shutdown_request", recipient="worker-1", ...)
5. SendMessage(type="shutdown_request", recipient="worker-2", ...)
6. TeamDelete()
```

## The Critical Difference: `team_name` Parameter

```
# WRONG — creates a subagent (no team coordination, no messaging)
Agent(prompt="...", description="...")

# CORRECT — creates a teammate (shared tasks, SendMessage, team coordination)
Agent(team_name="my-team", name="worker-1", prompt="...", description="...")
```

The `team_name` parameter on the `Agent` tool is what makes it a teammate instead of a subagent. Without it, you get an isolated subagent that cannot communicate with others.

## When to Use Teams vs Subagents

| Use Teams (this skill) | Use Subagents (no team) |
|---|---|
| 2+ independent work streams | Single isolated lookup |
| Teammates need to communicate | Result-only matters |
| Multi-file changes in parallel | Reading 1 file for info |
| Code review from multiple perspectives | Quick one-shot question |
| Investigation with competing hypotheses | Simple grep/search |

**When this skill is triggered, default to Teams.** Only fall back to subagents for trivially simple single-query lookups.

## Tool Reference

### Step 1: Create Team → `TeamCreate`

```
TeamCreate(team_name="feature-x", description="Building feature X")
```

### Step 2: Spawn Teammates → `Agent` with `team_name` + `name`

```
Agent(
  team_name="feature-x",            # REQUIRED — makes it a teammate
  name="api-dev",                    # REQUIRED — teammate's display name
  subagent_type="general-purpose",   # or "Explore", "Plan"
  prompt="Implement API endpoints...",
  description="Build analytics API",
  mode="plan",                       # optional: require plan approval
)
```

Agent types for teammates:
- `general-purpose`: Full capabilities (read, write, edit, bash) — use for implementation
- `Explore`: Read-only — use for research/investigation (cannot edit files)
- `Plan`: Read-only — use for planning/architecture (cannot edit files)

### Step 3: Create & Assign Tasks → `TaskCreate` + `TaskUpdate`

```
TaskCreate(subject="Build API", description="Create REST endpoints...")
TaskUpdate(taskId="1", owner="api-dev")
TaskUpdate(taskId="2", addBlockedBy=["1"])  # Task 2 waits for Task 1
```

### Step 4: Communicate → `SendMessage`

**Direct message** (default — always prefer):
```
SendMessage(type="message", recipient="api-dev", content="...", summary="Brief summary")
```

**Broadcast** (expensive — use only for critical blockers):
```
SendMessage(type="broadcast", content="Stop all work, blocking bug found", summary="Critical blocker")
```

### Step 5: Shutdown & Cleanup

```
SendMessage(type="shutdown_request", recipient="api-dev", content="Task complete")
# Wait for all teammates to shut down, then:
TeamDelete()
```

### Monitor Progress → `TaskList` / `TaskGet`

```
TaskList()                    # See all tasks and status
TaskGet(taskId="1")           # Full details of specific task
```

### Approve Plans → `SendMessage` plan_approval_response

When a teammate with `mode="plan"` submits a plan:
```
SendMessage(
  type="plan_approval_response",
  request_id="abc-123",
  recipient="api-dev",
  approve=true
)
```

## Complete Execution Sequence

```
1. TeamCreate(team_name="feature-x")
2. TaskCreate(subject="Build API", ...)
3. TaskCreate(subject="Build UI", ...)
4. TaskUpdate(taskId="2", addBlockedBy=["1"])
5. Agent(team_name="feature-x", name="api-dev",
         subagent_type="general-purpose", prompt="...", description="...")
6. Agent(team_name="feature-x", name="ui-dev",
         subagent_type="general-purpose", prompt="...", description="...")
7. TaskUpdate(taskId="1", owner="api-dev")
8. TaskUpdate(taskId="2", owner="ui-dev")
   ... teammates work, communicate, complete tasks ...
9. SendMessage(type="shutdown_request", recipient="api-dev", ...)
10. SendMessage(type="shutdown_request", recipient="ui-dev", ...)
11. TeamDelete()
```

## Team Sizing Strategy

Right-size the team based on the actual parallelism available. Small tasks need small teams; large tasks need larger ones.

### Sizing Rules

1. **Count independent file groups** — each group = 1 teammate
2. **Count distinct concerns** — each = 1 teammate
3. **Team size = max(file groups, concerns)**, minimum 2 teammates
4. **Include a dedicated test teammate** when implementation is involved
5. When in doubt, **round up** — an idle teammate costs less than a missing one

### Quick Sizing Guide

| Task Scope | Teammates | Example |
|---|---|---|
| Single-module fix | 2-3 | Fix + test (+ review if complex) |
| Multi-module feature | 4-6 | One per module + test + review |
| Full-stack feature | 5-7 | Backend, DB, frontend UI, frontend state, tests, docs |
| Large refactoring | 5-8 | One per subsystem + migration + test |
| Investigation/debug | 3-6 | One per hypothesis/subsystem |
| Code review | 3-5 | Security, performance, correctness, coverage |

**Detailed sizing with role templates**: See [references/team-sizing.md](references/team-sizing.md)

### File Ownership Is Key

Each teammate MUST own a distinct set of files:
- **Good**: teammate-A owns `src/api/`, teammate-B owns `src/components/`
- **Bad**: teammate-A and teammate-B both edit `src/config.ts`

## Display Modes

| Mode | Setting | How | Requirement |
|------|---------|-----|-------------|
| `auto` (default) | Auto-detect | Split panes if in tmux, else in-process | None |
| `in-process` | Main terminal | Shift+Up/Down to select teammates | Any terminal |
| `tmux` | Own panes | Click into pane to interact | tmux installed |

Configure in `~/.claude/settings.json`:
```json
{ "teammateMode": "tmux" }
```

Or per-session: `claude --teammate-mode in-process`

## Controlling the Team

### In-Process Shortcuts

| Action | Key |
|--------|-----|
| Select teammate | `Shift+Up/Down` |
| Message selected teammate | Type and Enter |
| View teammate session | `Enter` on selected |
| Interrupt teammate | `Escape` (while viewing) |
| Toggle task list | `Ctrl+T` |
| Switch to delegate mode | `Shift+Tab` |

### Delegate Mode

Prevents lead from implementing tasks itself. Lead focuses on coordination only.
Enable after starting team with `Shift+Tab`.

## Spawn Context

Teammates don't inherit the lead's conversation. Include all needed specifics in the spawn prompt:

```
Agent(
  team_name="debug-team",
  name="data-tracer",
  subagent_type="Explore",
  prompt="Trace data processing pipeline in src/services/data_processor.py. "
         "The system reads CSV input and applies transformations via pandas. "
         "Check if input validation handles empty/malformed rows correctly. "
         "Report findings as markdown summary.",
  description="Trace data flow"
)
```

## Use Case Examples

### 1. Full-Stack Feature (6 teammates)

```
Create an agent team to build the analytics dashboard:
1. "dash-api": API endpoints in src/api/handlers/analytics.py
2. "dash-service": Business logic in src/services/analytics_service.py
3. "dash-models": Request/response models in src/models/
4. "dash-ui": React components in frontend/src/components/analytics/
5. "dash-hooks": Data fetching hooks in frontend/src/hooks/
6. "dash-tests": Tests across backend and frontend in tests/

Use delegate mode. Require plan approval for dash-api and dash-service.
```

### 2. Investigation (5 teammates)

```
Users report data inconsistency between API response and database.
Spawn 5 teammates to investigate:
1. "api-flow": Trace request handling in src/api/handlers/
2. "query-flow": Trace database queries in src/repositories/
3. "data-check": Verify data transformation in src/services/
4. "cache-check": Check caching layer in src/cache/
5. "log-analyst": Query application logs, correlate timestamps

Have them share findings and challenge each other's hypotheses.
```

### 3. Code Review (5 teammates)

```
Create an agent team with 5 reviewers for pre-release audit:
1. "security": Injection, auth bypass, secret leaks
2. "performance": Hot paths, N+1 queries, async patterns
3. "correctness": Business logic, edge cases, error handling
4. "test-gaps": Untested code paths, missing assertions
5. "architecture": Module boundaries, dependency cycles, abstractions

Each reviewer writes to a shared findings doc. Lead synthesizes final report.
```

## Best Practices

### DO

| Practice | Why |
|----------|-----|
| Always use `Agent(team_name=..., name=...)` | Without `team_name` it's a subagent, not teammate |
| Spawn 4+ teammates for non-trivial tasks | Maximize parallelism |
| Map teammates to directory boundaries | Zero file conflicts |
| Include dedicated test teammate | Tests parallelize perfectly |
| Give exhaustive spawn context in `prompt` | Teammates don't inherit history |
| Use delegate mode (`Shift+Tab`) | Prevents lead from doing work itself |
| Set task dependencies via `TaskUpdate(addBlockedBy=...)` | Auto-unblocking |
| Use `mode="plan"` for high-risk teammates | Review before changes |

### DON'T

| Anti-Pattern | Why |
|-------------|-----|
| Use `Agent()` without `team_name` | Creates subagent, NOT teammate — no team coordination |
| Under-size the team when more parallel streams exist | Leaves parallelism on the table |
| Two teammates editing same file | Causes overwrites |
| Broadcast when a DM suffices | Token cost scales with team size |
| Skip spawn context in `prompt` | Teammates start blind |
| Let team run unattended too long | Risk of wasted effort |
| Forget to `TeamDelete` after shutdown | Leaves orphaned resources |

## Cross-Verification Rules

External CLI agents (Gemini, Codex) communicate with teammates through **structured artifact files** in `/tmp/xv/`. Load **gemini-cli** and **codex-cli** skills for invocation details.

| Task Type | Required Ensemble |
|-----------|-------------------|
| Code analysis, algorithms, math, business-critical logic | Claude + **Codex** |
| Debugging, root cause analysis, investigation | Claude + **Codex** |
| Security audit | Claude + **Codex** |
| Performance analysis, optimization review | Claude + **Codex** |
| Frontend code review, UI patterns, web research | Claude + **Gemini** |
| E2E visual regression, screenshot validation | Claude (native VLM) + **Gemini** (code-side) |
| Architecture design, plans, proposals | Claude + **Codex** + **Gemini** (3-way gate) |

**VLM note**: For screenshot/image analysis, Claude reads images natively via Read tool. Gemini CLI does not support direct image input — use Gemini for frontend code review and web search for latest UI patterns instead.

**Pattern**: `xv-*` teammate creates `/tmp/xv/{task}/`, invokes CLI, drops artifact, sends summary via `SendMessage`. Synthesizer reads all artifacts and produces unified verdict.

**Confidence**: CRITICAL (all agree) → must fix; HIGH (2/3) → investigate; MEDIUM (1/3) → likely false positive.

**Full details**: Team patterns, artifact format, CLI invocation examples, gate logic → **[references/cross-verification.md](references/cross-verification.md)**

## Prerequisites

Agent Teams requires the experimental feature flag. Ensure it is set in `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Without this flag, `TeamCreate`, `SendMessage`, and team-related `Agent` parameters will not be available.

## Handling Teammate Failures

Teammates can fail, time out, or get stuck. Here's how to handle each scenario:

### Teammate Times Out or Stops Responding

1. Check task status: `TaskGet(taskId="X")` — if still `in_progress` for too long, the teammate may be stuck
2. Try nudging via `SendMessage(type="message", recipient="stuck-teammate", content="Status update?")`
3. If no response, spawn a **replacement teammate** with the same role and assign the incomplete task to it
4. Send a `shutdown_request` to the stuck teammate to clean it up

### Teammate Produces Wrong Output

1. Review the output via `TaskGet` or by reading the output files
2. Send corrective feedback: `SendMessage(type="message", recipient="teammate", content="The output has issue X. Please fix Y.")`
3. If the teammate cannot recover, spawn a replacement with a more specific prompt that addresses the issue

### Teammate Hits Permission Error

If a teammate cannot access a file or run a command it needs:
1. Check that the teammate was spawned with the right `subagent_type` — `Explore` cannot write files, `general-purpose` can
2. If it needs elevated permissions, spawn a new teammate with `mode` unset (default allows all operations)

### Partial Team Failure

If some teammates succeed but others fail, the lead should:
1. Collect completed work from successful teammates
2. Spawn replacement teammates only for the failed tasks
3. Pass the successful teammates' output as context in the replacement's prompt
4. Update task dependencies if the original dependency graph has changed

## Troubleshooting

### Lead Uses Subagents Instead of Teammates

**Most common mistake.** If you see `Agent(prompt=..., description=...)` without `team_name`, the lead is creating subagents. The fix:
1. Ensure `TeamCreate` was called first
2. Every `Agent()` call MUST include `team_name="..."` and `name="..."`

### Lead Implements Instead of Delegating

Say: `Wait for your teammates to complete their tasks before proceeding`
Or enable delegate mode with `Shift+Tab`.

### Teammates Not Appearing

1. Press `Shift+Down` to cycle through active teammates (in-process)
2. For split panes: verify `which tmux` returns a path

### Task Status Lags

Tell lead to nudge the teammate, or manually `TaskUpdate(taskId="X", status="completed")`.

## Limitations

| Limitation | Workaround |
|-----------|-----------|
| No session resume for in-process teammates | Spawn new teammates after `/resume` |
| Task status can lag | Manually update or nudge |
| Slow shutdown (waits for current op) | Be patient or force-kill |
| One team per session | Clean up before starting new |
| No nested teams | Only lead manages the team |
| Lead is fixed | Plan lead role before starting |
| Split panes need tmux/iTerm2 | Use in-process mode as fallback |
| Permissions set at spawn | Change individual modes after spawning |

# Reasoning Transcript: PR Code Review with Codex Cross-Verification

## Task Analysis

The user's request (in Korean) asks to:
1. Review a PR's code changes
2. Cover three perspectives: security, performance, correctness
3. Cross-verify with Codex
4. Changed files: `src/auth/middleware.py`, `src/api/routes.py`, `tests/test_auth.py`

## Skill Matching

This task triggers the agent-teams skill because:
- It involves multiple independent review perspectives (3+ work streams)
- It explicitly requests cross-verification ("Codex로도 크로스 검증해줘")
- The skill's trigger words match: "code review", "cross-verify"

The cross-verification MUST rules table requires:
- **Security audit** -> Claude + Codex (MUST)
- **Code analysis** -> Claude + Codex (MUST)
- **Performance analysis** -> Claude + Codex (MUST)

All three perspectives require Codex cross-verification. This is not optional.

## Team Sizing Decision

Per the skill's sizing guide:
- Code review tasks -> 4-5 teammates
- We need: security reviewer, performance reviewer, correctness reviewer, xv-codex agent, synthesizer = **5 teammates**

This is within the recommended range. I considered adding a dedicated test-gaps reviewer but decided correctness-reviewer can cover test quality since `tests/test_auth.py` is one of only 3 files.

## Teammate Type Selection

- **security-reviewer**: `Explore` type. Read-only is sufficient -- reviewers should not modify code.
- **perf-reviewer**: `Explore` type. Same reasoning.
- **correctness-reviewer**: `Explore` type. Same reasoning.
- **xv-codex**: `general-purpose` type. MUST be general-purpose because it needs to run Bash commands (codex exec CLI), create directories (mkdir), and write artifact files.
- **synthesizer**: `general-purpose` type. Needs to write the synthesis report file via Write tool.

## File Ownership Strategy

No file conflicts here because all reviewers are Explore (read-only). Only xv-codex and synthesizer write, and they write to separate artifact files in `/tmp/xv/pr-review/`.

- Claude reviewers write to: `claude_security_review.md`, `claude_perf_review.md`, `claude_correctness_review.md`
- Codex agent writes to: `codex_review_middleware.md`, `codex_review_routes.md`, `codex_review_tests.md`
- Synthesizer writes to: `synthesis_report.md`

No overlap. Clean ownership.

## Task Dependency Design

The synthesis task (Task 5) MUST be blocked by all four review tasks (Tasks 1-4). The synthesizer cannot start until all artifacts exist. I use `TaskUpdate(taskId="5", addBlockedBy=["1", "2", "3", "4"])` to enforce this.

Tasks 1-4 have no dependencies on each other and run fully in parallel.

## Codex Invocation Strategy

Per the cross-verification reference, the xv-codex teammate:
1. Creates `/tmp/xv/pr-review/` directory
2. Runs `codex exec` with `--ephemeral --full-auto -s read-only` flags
3. Uses `-o` flag to write output directly to artifact files
4. Reviews each file separately (3 parallel Codex invocations using `&` + `wait`)
5. Verifies artifacts were written
6. Sends summary to synthesizer via SendMessage

I chose to review each file separately rather than all at once because:
- Per-file reviews produce more focused, actionable findings
- Line-number references are clearer per file
- Parallel execution means no time penalty

## Confidence Scoring Logic

The synthesizer uses the cross-verification confidence model:
- **CRITICAL**: Both Claude reviewers AND Codex flag the same issue. All agree = must fix.
- **HIGH**: 2+ reviewers agree (could be 2 Claude reviewers, or 1 Claude + Codex). Should fix, investigate disagreement.
- **MEDIUM**: Only 1 reviewer flags it. Likely false positive, worth investigating.

This maps directly to the reference: "CRITICAL (all agree) -> must fix; HIGH (2/3) -> investigate; MEDIUM (1/3) -> likely false positive."

## Spawn Context Rationale

Each teammate's prompt is deliberately exhaustive because teammates do NOT inherit the lead's conversation context. Each prompt includes:
- Exact file paths to review
- Specific review criteria per their perspective
- Exact artifact output format (standard artifact format from reference)
- Instructions to send summary via SendMessage to synthesizer
- Instructions to mark task as completed

## Shutdown Sequence

After synthesis is complete:
1. Lead reads `/tmp/xv/pr-review/synthesis_report.md`
2. Send `shutdown_request` to all 5 teammates
3. Call `TeamDelete()` to clean up
4. Present findings to user

Workers shut down before synthesizer to maintain clean ordering, though the order doesn't strictly matter since all work is done.

## Why Not 3-Way Gate?

The user asked for Codex cross-verification, not a design/plan review. The 3-way gate (Claude + Codex + Gemini) is reserved for "Architecture design, plans, proposals." A code review with security/performance/correctness is covered by the "Code analysis" and "Security audit" patterns, both of which require Claude + Codex only.

## Alternative Designs Considered

1. **Single Codex call reviewing all files**: Rejected because per-file reviews are more focused and produce better line-number references.
2. **Adding Gemini**: Not required by the MUST rules for code review/security/performance. Would add latency without clear benefit.
3. **Fewer teammates (3)**: Rejected because the skill explicitly says "Never default to 2-3 when more parallel streams exist" and code review sizing guide says 4-5.
4. **Using `mode="plan"` on reviewers**: Unnecessary. Reviewers are Explore type (read-only) so there's no risk of unreviewed changes.

# Execution Plan: PR Code Review with Codex Cross-Verification

## Task

Review PR code changes across `src/auth/middleware.py`, `src/api/routes.py`, `tests/test_auth.py` from security, performance, and correctness perspectives, with Codex cross-verification.

## Team Design

- **Team name**: `pr-review`
- **Team size**: 5 teammates
- **Pattern**: Code Analysis / Security Audit (Claude + Codex) per cross-verification MUST rules
- **Artifact directory**: `/tmp/xv/pr-review/`

### Teammates

| Name | Type | Role | Files Owned |
|------|------|------|-------------|
| `security-reviewer` | Explore | Security audit: injection, auth bypass, secret leaks | `src/auth/middleware.py` (primary) |
| `perf-reviewer` | Explore | Performance: hot paths, async patterns, middleware overhead | `src/api/routes.py` (primary) |
| `correctness-reviewer` | Explore | Logic correctness, edge cases, error handling | All 3 files |
| `xv-codex` | general-purpose | Codex CLI cross-verification across all 3 files | `/tmp/xv/pr-review/` artifacts |
| `synthesizer` | general-purpose | Read all artifacts, produce unified verdict | `/tmp/xv/pr-review/synthesis_report.md` |

### Task Dependencies

```
Task 1 (Security Review)     ─┐
Task 2 (Performance Review)  ─┼─► Task 5 (Synthesis)
Task 3 (Correctness Review)  ─┤
Task 4 (Codex XV Review)     ─┘
```

---

## Exact Tool Call Sequence

### Phase 1: Team Creation and Artifact Setup

#### Call 1: TeamCreate

```
TeamCreate(
  team_name="pr-review",
  description="PR code review with security/performance/correctness analysis and Codex cross-verification"
)
```

### Phase 2: Task Creation

#### Call 2: TaskCreate — Security Review

```
TaskCreate(
  subject="Security Review",
  description="Review src/auth/middleware.py, src/api/routes.py, tests/test_auth.py for security vulnerabilities: injection attacks, authentication bypass, authorization flaws, secret/credential leaks, CSRF, session management issues. Write findings to /tmp/xv/pr-review/claude_security_review.md using standard artifact format."
)
```

#### Call 3: TaskCreate — Performance Review

```
TaskCreate(
  subject="Performance Review",
  description="Review src/auth/middleware.py, src/api/routes.py for performance concerns: middleware overhead, N+1 queries, blocking I/O in async handlers, unnecessary computation on hot paths, caching opportunities. Write findings to /tmp/xv/pr-review/claude_perf_review.md using standard artifact format."
)
```

#### Call 4: TaskCreate — Correctness Review

```
TaskCreate(
  subject="Correctness Review",
  description="Review src/auth/middleware.py, src/api/routes.py, tests/test_auth.py for correctness: logic errors, edge cases (null/empty input, boundary values), error handling gaps, race conditions, test coverage gaps. Write findings to /tmp/xv/pr-review/claude_correctness_review.md using standard artifact format."
)
```

#### Call 5: TaskCreate — Codex Cross-Verification

```
TaskCreate(
  subject="Codex Cross-Verification",
  description="Run Codex CLI to independently review all 3 changed files. Drop artifacts in /tmp/xv/pr-review/. Send verdict summary to synthesizer via SendMessage."
)
```

#### Call 6: TaskCreate — Synthesis

```
TaskCreate(
  subject="Synthesis Report",
  description="Read ALL review artifacts from /tmp/xv/pr-review/ (claude_security_review.md, claude_perf_review.md, claude_correctness_review.md, codex_review_middleware.md, codex_review_routes.md, codex_review_tests.md). Produce unified cross-verification synthesis report with confidence scoring. Write to /tmp/xv/pr-review/synthesis_report.md."
)
```

### Phase 3: Task Dependency Setup

#### Call 7: TaskUpdate — Synthesis blocked by all reviews

```
TaskUpdate(taskId="5", addBlockedBy=["1", "2", "3", "4"])
```

### Phase 4: Spawn Teammates (parallel)

#### Call 8: Agent — security-reviewer

```
Agent(
  team_name="pr-review",
  name="security-reviewer",
  subagent_type="Explore",
  prompt="You are a security-focused code reviewer for a PR. Your job:

1. mkdir -p /tmp/xv/pr-review/
2. Read and analyze these changed files for security vulnerabilities:
   - src/auth/middleware.py — Focus on: authentication logic, token validation, session handling, middleware bypass vectors
   - src/api/routes.py — Focus on: input validation, injection (SQL/NoSQL/command), authorization checks on each endpoint, IDOR
   - tests/test_auth.py — Focus on: whether security-critical paths are tested, missing negative test cases

3. Write your findings to /tmp/xv/pr-review/claude_security_review.md using this EXACT format:
   # Claude Security Review — PR Changed Files
   Date: 2026-03-20
   Status: PASS | FAIL | PASS_WITH_COMMENTS

   ## Findings
   - [CRITICAL] File, Line N: Description
   - [HIGH] File, Line N: Description
   - [MEDIUM] Description
   - [LOW] Description

   ## Summary
   1-3 sentence overall security assessment.

   ## Verdict: APPROVE | REQUEST_CHANGES
   If REQUEST_CHANGES, list what must change.

4. After writing the artifact, send a summary of your top findings to 'synthesizer' via SendMessage.
5. Mark your task as completed.",
  description="Security audit of PR changes"
)
```

#### Call 9: Agent — perf-reviewer

```
Agent(
  team_name="pr-review",
  name="perf-reviewer",
  subagent_type="Explore",
  prompt="You are a performance-focused code reviewer for a PR. Your job:

1. mkdir -p /tmp/xv/pr-review/
2. Read and analyze these changed files for performance issues:
   - src/auth/middleware.py — Focus on: middleware execution overhead per request, database lookups in hot path, token cache strategy, blocking operations
   - src/api/routes.py — Focus on: N+1 query patterns, unnecessary serialization, missing pagination, async/await correctness, response size
   - tests/test_auth.py — Focus on: test efficiency, fixture reuse

3. Write your findings to /tmp/xv/pr-review/claude_perf_review.md using this EXACT format:
   # Claude Performance Review — PR Changed Files
   Date: 2026-03-20
   Status: PASS | FAIL | PASS_WITH_COMMENTS

   ## Findings
   - [CRITICAL] File, Line N: Description
   - [HIGH] File, Line N: Description
   - [MEDIUM] Description
   - [LOW] Description

   ## Summary
   1-3 sentence overall performance assessment.

   ## Verdict: APPROVE | REQUEST_CHANGES
   If REQUEST_CHANGES, list what must change.

4. After writing the artifact, send a summary of your top findings to 'synthesizer' via SendMessage.
5. Mark your task as completed.",
  description="Performance analysis of PR changes"
)
```

#### Call 10: Agent — correctness-reviewer

```
Agent(
  team_name="pr-review",
  name="correctness-reviewer",
  subagent_type="Explore",
  prompt="You are a correctness-focused code reviewer for a PR. Your job:

1. mkdir -p /tmp/xv/pr-review/
2. Read and analyze these changed files for correctness issues:
   - src/auth/middleware.py — Focus on: logic errors in auth flow, edge cases (expired tokens, malformed headers, missing fields), error propagation
   - src/api/routes.py — Focus on: business logic correctness, error handling (proper HTTP status codes, error messages), race conditions, input boundary handling
   - tests/test_auth.py — Focus on: test correctness (do assertions actually validate the right thing?), missing edge case tests, test isolation, mock correctness

3. Write your findings to /tmp/xv/pr-review/claude_correctness_review.md using this EXACT format:
   # Claude Correctness Review — PR Changed Files
   Date: 2026-03-20
   Status: PASS | FAIL | PASS_WITH_COMMENTS

   ## Findings
   - [CRITICAL] File, Line N: Description
   - [HIGH] File, Line N: Description
   - [MEDIUM] Description
   - [LOW] Description

   ## Summary
   1-3 sentence overall correctness assessment.

   ## Verdict: APPROVE | REQUEST_CHANGES
   If REQUEST_CHANGES, list what must change.

4. After writing the artifact, send a summary of your top findings to 'synthesizer' via SendMessage.
5. Mark your task as completed.",
  description="Correctness analysis of PR changes"
)
```

#### Call 11: Agent — xv-codex

```
Agent(
  team_name="pr-review",
  name="xv-codex",
  subagent_type="general-purpose",
  prompt="You are a cross-verification agent. Your job is to run Codex CLI to independently review the PR's changed files. Follow these steps exactly:

1. Create artifact directory:
   mkdir -p /tmp/xv/pr-review/

2. Run Codex CLI for each changed file (run in parallel with & and wait):

   codex exec --ephemeral --full-auto -s read-only -o /tmp/xv/pr-review/codex_review_middleware.md \
     \"$(cat <<'PROMPT'
   You are performing an independent code review for cross-verification.
   Another AI has already reviewed this code — your job is to find things it might have missed.

   ## Output Format (MUST follow exactly)
   # Codex Review — middleware.py
   Date: 2026-03-20
   Status: PASS | FAIL | PASS_WITH_COMMENTS

   ## Findings
   - [SEVERITY] Line N: Description

   ## Summary
   1-3 sentences.

   ## Verdict: APPROVE | REQUEST_CHANGES

   ## Review Criteria
   1. Security: injection, auth bypass, data exposure, CSRF
   2. Performance: middleware overhead, blocking I/O, caching
   3. Correctness: logic errors, edge cases, error handling
   4. Race conditions, concurrency issues

   ## Code to Review
   $(cat src/auth/middleware.py)
   PROMPT
   )\" &
   PID1=$!

   codex exec --ephemeral --full-auto -s read-only -o /tmp/xv/pr-review/codex_review_routes.md \
     \"$(cat <<'PROMPT'
   You are performing an independent code review for cross-verification.
   Another AI has already reviewed this code — your job is to find things it might have missed.

   ## Output Format (MUST follow exactly)
   # Codex Review — routes.py
   Date: 2026-03-20
   Status: PASS | FAIL | PASS_WITH_COMMENTS

   ## Findings
   - [SEVERITY] Line N: Description

   ## Summary
   1-3 sentences.

   ## Verdict: APPROVE | REQUEST_CHANGES

   ## Review Criteria
   1. Security: input validation, authorization on endpoints, IDOR
   2. Performance: N+1 queries, async correctness, response size
   3. Correctness: HTTP status codes, error handling, business logic
   4. API design: RESTful conventions, consistency

   ## Code to Review
   $(cat src/api/routes.py)
   PROMPT
   )\" &
   PID2=$!

   codex exec --ephemeral --full-auto -s read-only -o /tmp/xv/pr-review/codex_review_tests.md \
     \"$(cat <<'PROMPT'
   You are performing an independent code review for cross-verification.
   Another AI has already reviewed this code — your job is to find things it might have missed.

   ## Output Format (MUST follow exactly)
   # Codex Review — test_auth.py
   Date: 2026-03-20
   Status: PASS | FAIL | PASS_WITH_COMMENTS

   ## Findings
   - [SEVERITY] Line N: Description

   ## Summary
   1-3 sentences.

   ## Verdict: APPROVE | REQUEST_CHANGES

   ## Review Criteria
   1. Test coverage: are all auth flows tested?
   2. Assertion quality: do assertions validate the right thing?
   3. Edge cases: expired tokens, malformed input, missing fields
   4. Test isolation: proper mocking, no shared state leaks

   ## Code to Review
   $(cat tests/test_auth.py)
   PROMPT
   )\" &
   PID3=$!

   # Wait for all with timeout
   timeout 120 bash -c \"wait $PID1\" || echo 'Codex middleware review timed out'
   timeout 120 bash -c \"wait $PID2\" || echo 'Codex routes review timed out'
   timeout 120 bash -c \"wait $PID3\" || echo 'Codex tests review timed out'

3. Verify all artifacts were written:
   ls -la /tmp/xv/pr-review/codex_review_*.md
   cat /tmp/xv/pr-review/codex_review_middleware.md | head -5
   cat /tmp/xv/pr-review/codex_review_routes.md | head -5
   cat /tmp/xv/pr-review/codex_review_tests.md | head -5

4. Send a summary of Codex's verdicts (per file: APPROVE/REQUEST_CHANGES + top findings) to 'synthesizer' via SendMessage.

5. Mark your task as completed.",
  description="Run Codex CLI for independent cross-verification review of all PR files"
)
```

#### Call 12: Agent — synthesizer

```
Agent(
  team_name="pr-review",
  name="synthesizer",
  subagent_type="general-purpose",
  prompt="You are the synthesis agent. You MUST wait until all 4 review tasks are completed before starting. Your job:

1. Read ALL review artifacts from /tmp/xv/pr-review/:
   - /tmp/xv/pr-review/claude_security_review.md
   - /tmp/xv/pr-review/claude_perf_review.md
   - /tmp/xv/pr-review/claude_correctness_review.md
   - /tmp/xv/pr-review/codex_review_middleware.md
   - /tmp/xv/pr-review/codex_review_routes.md
   - /tmp/xv/pr-review/codex_review_tests.md

2. Cross-reference findings between Claude reviewers and Codex:
   - CRITICAL confidence: Both Claude AND Codex flag the same issue -> Must fix
   - HIGH confidence: Multiple Claude reviewers flag it OR one Claude + one Codex -> Should fix
   - MEDIUM confidence: Only one reviewer flags it -> Investigate, likely false positive

3. Write the synthesis report to /tmp/xv/pr-review/synthesis_report.md using this format:

   # Cross-Verification Synthesis Report — PR Code Review
   Date: 2026-03-20

   ## Changed Files
   - src/auth/middleware.py
   - src/api/routes.py
   - tests/test_auth.py

   ## Findings by Confidence Level

   ### CRITICAL (Multiple reviewers + Codex agree)
   | Finding | Security | Performance | Correctness | Codex | Action |
   |---------|----------|-------------|-------------|-------|--------|
   | ... | Yes/No | Yes/No | Yes/No | Yes/No | Must fix |

   ### HIGH (2+ reviewers agree)
   | Finding | Security | Performance | Correctness | Codex | Action |
   |---------|----------|-------------|-------------|-------|--------|
   | ... | Yes/No | Yes/No | Yes/No | Yes/No | Should fix |

   ### MEDIUM (Single reviewer flags)
   | Finding | Source | Action |
   |---------|--------|--------|
   | ... | ... | Investigate |

   ## Disagreement Analysis
   Where Claude and Codex reviewers disagreed, explain why and which is more likely correct.

   ## Per-File Summary
   ### src/auth/middleware.py
   Overall: APPROVE | REQUEST_CHANGES
   Key findings: ...

   ### src/api/routes.py
   Overall: APPROVE | REQUEST_CHANGES
   Key findings: ...

   ### tests/test_auth.py
   Overall: APPROVE | REQUEST_CHANGES
   Key findings: ...

   ## Final Verdict: APPROVE | REQUEST_CHANGES
   Consolidated recommendation with prioritized action items.

4. Send the final verdict and top-3 action items to the lead (team owner) via SendMessage.
5. Mark your task as completed.",
  description="Synthesize all Claude and Codex review artifacts into unified verdict"
)
```

### Phase 5: Task Assignment

#### Call 13: TaskUpdate — Assign tasks to teammates

```
TaskUpdate(taskId="1", owner="security-reviewer")
TaskUpdate(taskId="2", owner="perf-reviewer")
TaskUpdate(taskId="3", owner="correctness-reviewer")
TaskUpdate(taskId="4", owner="xv-codex")
TaskUpdate(taskId="5", owner="synthesizer")
```

### Phase 6: Monitor Progress

#### Call 14: Periodic monitoring

```
TaskList()   # Check status of all tasks periodically
TaskGet(taskId="5")  # Check synthesis task specifically
```

### Phase 7: Shutdown Sequence

After synthesizer completes and sends its final verdict:

#### Call 15: Read synthesis report

```
# Lead reads the final report
Read /tmp/xv/pr-review/synthesis_report.md
```

#### Call 16: Shutdown teammates (in order: workers first, then synthesizer)

```
SendMessage(type="shutdown_request", recipient="security-reviewer", content="Review complete. Shutting down.")
SendMessage(type="shutdown_request", recipient="perf-reviewer", content="Review complete. Shutting down.")
SendMessage(type="shutdown_request", recipient="correctness-reviewer", content="Review complete. Shutting down.")
SendMessage(type="shutdown_request", recipient="xv-codex", content="Review complete. Shutting down.")
SendMessage(type="shutdown_request", recipient="synthesizer", content="Synthesis complete. Shutting down.")
```

#### Call 17: Delete team

```
TeamDelete()
```

### Phase 8: Report to User

Present the synthesis report contents to the user, highlighting:
1. CRITICAL findings that must be fixed
2. HIGH findings that should be investigated
3. Areas of agreement/disagreement between Claude and Codex
4. Final verdict (APPROVE or REQUEST_CHANGES)

---

## Artifact File Map

```
/tmp/xv/pr-review/
├── claude_security_review.md      # security-reviewer output
├── claude_perf_review.md          # perf-reviewer output
├── claude_correctness_review.md   # correctness-reviewer output
├── codex_review_middleware.md     # xv-codex Codex CLI output for middleware.py
├── codex_review_routes.md         # xv-codex Codex CLI output for routes.py
├── codex_review_tests.md          # xv-codex Codex CLI output for test_auth.py
└── synthesis_report.md            # synthesizer final report
```

## Summary

- **Total tool calls**: ~25-30 (TeamCreate, 5x TaskCreate, 1x TaskUpdate for dependencies, 5x Agent spawn, 5x TaskUpdate for owners, periodic TaskList/TaskGet, Read synthesis, 5x SendMessage shutdown, TeamDelete)
- **Parallelism**: 4 reviewers work simultaneously; synthesizer waits for all via task dependency blocking
- **Cross-verification**: Codex CLI reviews all 3 files independently in parallel within the xv-codex teammate
- **Confidence scoring**: Findings are rated CRITICAL/HIGH/MEDIUM based on reviewer agreement per cross-verification methodology

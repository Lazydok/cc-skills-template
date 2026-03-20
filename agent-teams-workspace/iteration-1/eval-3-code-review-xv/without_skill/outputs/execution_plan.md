# Execution Plan: PR Code Review with Cross-Verification

## Task Summary

Review PR changes in `src/auth/middleware.py`, `src/api/routes.py`, `tests/test_auth.py` from security, performance, and correctness perspectives, plus cross-verify with Codex.

---

## Phase 1: Gather Context (Parallel)

All of these calls are independent and can be executed simultaneously.

### Tool Call 1a: Get PR diff for the three files
```
Tool: Bash
command: "git diff main...HEAD -- src/auth/middleware.py src/api/routes.py tests/test_auth.py"
```
(If the PR is on a different branch, adjust accordingly. If this is a GitHub PR, use `gh pr diff <PR_NUMBER>` instead.)

### Tool Call 1b: Read full file — src/auth/middleware.py
```
Tool: Read
file_path: "<repo_root>/src/auth/middleware.py"
```

### Tool Call 1c: Read full file — src/api/routes.py
```
Tool: Read
file_path: "<repo_root>/src/api/routes.py"
```

### Tool Call 1d: Read full file — tests/test_auth.py
```
Tool: Read
file_path: "<repo_root>/tests/test_auth.py"
```

### Tool Call 1e: Check for dependency/config files
```
Tool: Glob
pattern: "**/requirements*.txt"
```
```
Tool: Glob
pattern: "**/pyproject.toml"
```
(To understand which auth libraries are in use — e.g., PyJWT, passlib, etc.)

### Tool Call 1f: Search for related auth patterns across the codebase
```
Tool: Grep
pattern: "secret|SECRET|jwt|JWT|token|password|hash"
path: "<repo_root>/src/"
output_mode: "files_with_matches"
```

---

## Phase 2: Deep Security Review (Sequential)

These depend on the file contents obtained in Phase 1.

### Tool Call 2a: Search for hardcoded secrets
```
Tool: Grep
pattern: "(secret|password|api_key|token)\\s*=\\s*[\"'][^\"']{4,}"
path: "<repo_root>/src/"
output_mode: "content"
-i: true
```

### Tool Call 2b: Check for SQL injection patterns
```
Tool: Grep
pattern: "f\"|f'|\.format\\(|%s.*execute"
path: "<repo_root>/src/"
output_mode: "content"
```

### Tool Call 2c: Check for unsafe deserialization / eval
```
Tool: Grep
pattern: "pickle\\.|eval\\(|exec\\(|yaml\\.load\\("
path: "<repo_root>/src/"
output_mode: "content"
```

### Tool Call 2d: Check JWT configuration (algorithm, expiry, verification)
```
Tool: Grep
pattern: "algorithms|verify|decode|encode|exp|iat|iss"
path: "<repo_root>/src/auth/"
output_mode: "content"
-C: 3
```

### Tool Call 2e: Check for missing authentication on routes
```
Tool: Grep
pattern: "@(app|router)\\.(get|post|put|delete|patch)"
path: "<repo_root>/src/api/routes.py"
output_mode: "content"
-C: 2
```

---

## Phase 3: Performance Review (Parallel where possible)

### Tool Call 3a: Look for N+1 query patterns or unbounded loops
```
Tool: Grep
pattern: "for .* in .*\\.all\\(|select_related|prefetch_related|\.query"
path: "<repo_root>/src/"
output_mode: "content"
-C: 3
```

### Tool Call 3b: Check for blocking I/O in async contexts
```
Tool: Grep
pattern: "(async def|await).*"
path: "<repo_root>/src/"
output_mode: "content"
-C: 2
```

### Tool Call 3c: Check for caching patterns
```
Tool: Grep
pattern: "cache|lru_cache|redis|memcache"
path: "<repo_root>/src/"
output_mode: "content"
-i: true
```

---

## Phase 4: Correctness Review (Sequential)

### Tool Call 4a: Review test coverage — check what's tested
```
Tool: Grep
pattern: "def test_"
path: "<repo_root>/tests/test_auth.py"
output_mode: "content"
```

### Tool Call 4b: Check for proper error handling
```
Tool: Grep
pattern: "try:|except |raise |HTTPException|abort"
path: "<repo_root>/src/"
output_mode: "content"
-C: 2
```

### Tool Call 4c: Run existing tests to verify they pass
```
Tool: Bash
command: "cd <repo_root> && python -m pytest tests/test_auth.py -v --tb=short 2>&1 | head -100"
timeout: 60000
```

---

## Phase 5: Codex Cross-Verification

The user requested cross-verification with "Codex." In a standard Claude Code environment without specialized skills loaded, there are two interpretations:

### Option A: OpenAI Codex CLI (if installed)

```
Tool: Bash
command: "which codex 2>/dev/null || echo 'codex not found'"
```

If codex CLI is available:
```
Tool: Bash
command: "codex --approval-mode full-auto 'Review the following files for security, performance, and correctness issues: src/auth/middleware.py, src/api/routes.py, tests/test_auth.py. Focus on: 1) Auth bypass vulnerabilities 2) Token handling flaws 3) Missing input validation 4) Performance bottlenecks 5) Test coverage gaps'"
timeout: 120000
```

### Option B: Codex CLI not available

If codex is not installed, report to the user that the Codex cross-verification cannot be performed in this environment and suggest alternatives:
- Install Codex CLI: `npm install -g @openai/codex`
- Use a web-based Codex interface manually
- Rely on the thorough review already performed by Claude

---

## Phase 6: Synthesize Review Report

No tool calls needed — this is a synthesis step where I compile all findings from Phases 1-5 into a structured code review covering:

1. **Security Findings** (Critical / High / Medium / Low)
2. **Performance Findings**
3. **Correctness Findings**
4. **Test Coverage Assessment**
5. **Codex Cross-Verification Results** (if available)
6. **Recommendations**

---

## Execution Strategy Summary

| Phase | Approach | Rationale |
|-------|----------|-----------|
| 1 - Gather Context | **Parallel** (5-6 calls at once) | All reads are independent |
| 2 - Security Review | **Parallel** (5 grep calls) | Each grep is independent |
| 3 - Performance Review | **Parallel** (3 calls at once) | Independent searches |
| 4 - Correctness Review | **Mostly parallel**, test run sequential | Tests depend on nothing but need time |
| 5 - Codex Cross-Verify | **Sequential** | Must check availability first |
| 6 - Synthesize | **Single step** | Depends on all prior phases |

### Why NOT use subagents?

In this environment, there is no Agent tool or subagent dispatch mechanism available. All work is done directly with the available tools (Bash, Read, Write, Edit, Grep, Glob). This is actually fine for a code review of 3 files — the overhead of subagent coordination would exceed the benefit. The key optimization is parallelizing independent tool calls within each phase.

### Handling the Codex Cross-Verification

Without a dedicated Codex skill or integration:
1. First check if the `codex` CLI binary is installed on the system.
2. If yes, invoke it in `full-auto` approval mode with a focused review prompt.
3. If no, transparently inform the user and explain the limitation.
4. The Claude-based review itself already provides comprehensive coverage; Codex would serve as a second opinion, not a replacement.

---

## Total Estimated Tool Calls

- Phase 1: ~6 parallel calls
- Phase 2: ~5 parallel calls
- Phase 3: ~3 parallel calls
- Phase 4: ~3 calls (2 parallel + 1 sequential)
- Phase 5: 1-2 sequential calls
- **Total: ~18-20 tool calls across ~5-6 round trips**

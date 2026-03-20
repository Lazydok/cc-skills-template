# Gemini CLI — Review & Analysis Patterns

Reusable prompt templates for common code review and analysis tasks via Gemini CLI.

## Code Review Prompts

### General Code Review

```bash
cat src/feature.py | timeout 120 gemini -y \
  -p "Review this code for:
1) Logic errors — identify specific lines
2) Edge cases — inputs that could cause failures
3) Performance issues — inefficient patterns
4) Readability — naming, structure clarity

Format as markdown with severity: [CRITICAL/HIGH/MEDIUM/LOW]" \
  -o text 2>/dev/null
```

### Security Audit

```bash
cat src/auth.py | timeout 120 gemini -y \
  -p "Security audit this code. Check for:
1) Injection vulnerabilities (SQL, command, XSS)
2) Authentication/authorization flaws
3) Sensitive data exposure (hardcoded secrets, logging PII)
4) Input validation gaps
5) OWASP Top 10 relevance

For each finding: severity, affected line(s), exploit scenario, and fix recommendation." \
  -o text 2>/dev/null
```

### Test Gap Analysis

```bash
timeout 120 gemini -y \
  -p "Analyze test coverage gaps:

Implementation:
$(cat src/order_processor.py)

Tests:
$(cat tests/test_order_processor.py)

Identify:
1) Untested code paths and branches
2) Missing edge case tests (null, empty, boundary values)
3) Error handling paths without test coverage
4) Suggest specific test cases to add with expected behavior" \
  -o text 2>/dev/null
```

### PR/Diff Review

```bash
git diff main...HEAD | timeout 120 gemini -y \
  -p "Review this git diff as a pull request reviewer:
1) Correctness — will this break anything?
2) Missing error handling
3) API contract changes
4) Test coverage for changed code
Be concise. Flag only real issues, not style preferences." \
  -o text 2>/dev/null
```

## Web Search Patterns

### Library Version Check

```bash
timeout 60 gemini -y \
  -p "Search the web for the latest stable version of 'react' npm package and any breaking changes in the most recent major version. Summarize in 3-5 bullet points." \
  -o text 2>/dev/null
```

### API Documentation Lookup

```bash
timeout 60 gemini -y \
  -p "Search the web for the official documentation of Python's asyncio.TaskGroup. Summarize: constructor, key methods, exception handling behavior, and a minimal usage example." \
  -o text 2>/dev/null
```

### Bug/Issue Research

```bash
timeout 60 gemini -y \
  -p "Search the web for known issues with 'TypeError: Cannot read properties of undefined' in Next.js 14 app router. Find common causes and fixes from GitHub issues and Stack Overflow." \
  -o text 2>/dev/null
```

## Architecture Analysis

### Dependency Analysis

```bash
timeout 120 gemini -y \
  -p "Analyze the dependency structure of this project. Read package.json (or requirements.txt) and identify:
1) Outdated or deprecated dependencies
2) Security-flagged packages
3) Unnecessary dependencies that could be removed
4) Version conflict risks" \
  -o text 2>/dev/null
```

### Codebase Summary

```bash
timeout 120 gemini -y \
  -p "Read the project structure and key files. Provide:
1) Project purpose and tech stack
2) Directory structure overview
3) Key entry points
4) Data flow summary
Keep it under 200 words." \
  -o text 2>/dev/null
```

## Tips for Effective Prompts

- **Be specific about output format** — "Format as markdown with severity levels" produces more structured results than "review this code"
- **Embed code in prompt** via stdin or `$(cat file)` — avoids relying on `-y` file tools for read-only tasks
- **Set scope explicitly** — "Focus on security only" prevents the model from giving generic advice
- **Request line numbers** — "identify specific lines" helps map findings back to code
- **Batch related files** — Review implementation + tests together for coverage analysis

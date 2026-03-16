# Cross-Verification Methodology — Detailed Reference

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [MUST Rules — Required Ensembles](#must-rules--required-ensembles)
- [Artifact File Standard](#artifact-file-standard)
- [Team Patterns](#team-patterns)
  - [Code Analysis / Algorithm / Math (Claude + Codex)](#team-pattern-code-analysis--algorithm--math)
  - [Web UI / VLM / Frontend (Claude + Gemini)](#team-pattern-web-ui--vlm--frontend)
  - [Design / Architecture / Planning (3-Way Gate)](#team-pattern-design--architecture--planning-3-way-gate)
- [Artifact Directory Convention](#artifact-directory-convention)
- [Confidence Scoring](#confidence-scoring)
- [Complete Workflows](#complete-workflows)
- [Capability Matrix](#capability-matrix)
- [Best Practices](#best-practices)

## Overview

Cross-verification uses mandatory ensemble patterns: CLI agents (Gemini, Codex) are invoked as terminal sub-processes that drop structured artifact files. Claude Code teammates read those files to synthesize findings. This creates an asynchronous, artifact-based communication channel between different AI models.

## Prerequisites

- **gemini-cli** skill loaded — `gemini --version` must work without prompts
- **codex-cli** skill loaded — `codex --version` must work without prompts
- Artifact directory created: `mkdir -p /tmp/xv/{task-name}/`

## MUST Rules — Required Ensembles

| Task Type | Required Ensemble | Why |
|-----------|-------------------|-----|
| Complex code analysis, algorithms, math/theory | Claude + **Codex** | Codex excels at logical reasoning and code correctness |
| Debugging, root cause analysis, investigation | Claude + **Codex** | Independent trace analysis catches blind spots |
| Security audit | Claude + **Codex** | Two independent security perspectives minimum |
| Business-critical logic | Claude + **Codex** | Correctness of core domain logic requires cross-check |
| Performance analysis, optimization review | Claude + **Codex** | Algorithmic complexity and hot-path analysis |
| Frontend code review, UI patterns | Claude + **Gemini** | Gemini has web search for latest UI/framework docs |
| E2E visual regression, screenshot validation | Claude (native VLM) + **Gemini** (code-side) | Claude reads screenshots natively; Gemini reviews test code and searches for latest patterns |
| Architecture design, plans, proposals | Claude + **Codex** + **Gemini** (3-way gate) | No plan proceeds without all 3 critics passing |

**Important — VLM capabilities**:
- **Claude**: Reads images natively via Read tool (screenshots, diagrams, UI captures). Primary VLM agent.
- **Gemini CLI**: Does NOT support direct image input via CLI flags. Use for frontend code review and web search only.
- **Codex CLI**: No VLM capability. Use for code logic and algorithmic analysis.

## Team Patterns

### Team Pattern: Code Analysis / Algorithm / Math

**MUST include Codex cross-check.** The `xv-codex` teammate runs Codex independently, drops artifacts for the synthesizer.

```
Team (5+ teammates):
1. "implementer": Write/modify code (general-purpose)
2. "claude-analyst": Claude's own deep analysis (Explore)
3. "xv-codex": Run Codex review, drop artifacts (general-purpose)
4. "test-dev": Write/run tests (general-purpose)
5. "synthesizer": Read Claude + Codex artifacts → unified verdict (general-purpose)
```

The `xv-codex` teammate prompt includes:
```
You are a cross-verification agent. Your job:
1. mkdir -p /tmp/xv/code-review/
2. Run Codex CLI to independently analyze the target code:
   codex exec --ephemeral --full-auto -s read-only -o /tmp/xv/code-review/codex_review.md \
     "$(cat <<'EOF'
   You are performing an independent code review. Write your full review
   to the output. Use this format:
   # Codex Review — {filename}
   Status: PASS | FAIL | PASS_WITH_COMMENTS
   ## Findings
   - [SEVERITY] Line N: Description
   ## Verdict: APPROVE | REQUEST_CHANGES

   Review target: {description of what to review}
   $(cat {target_file})
   EOF
   )"
3. Read /tmp/xv/code-review/codex_review.md to verify it was written
4. Send the verdict summary to the synthesizer via SendMessage
```

### Team Pattern: Web UI / Frontend / E2E Visual

**MUST include Gemini cross-check for frontend code + Claude native VLM for screenshots.**

Gemini CLI cannot accept image input directly. For visual analysis, Claude reads screenshots natively via the Read tool. Gemini's role is frontend code review + web search for latest framework patterns.

```
Team (6+ teammates):
1. "ui-dev": Build frontend components (general-purpose)
2. "claude-vlm": Analyze screenshots/images via Read tool — visual regression (Explore)
3. "xv-gemini": Frontend code review + web search for latest patterns (general-purpose)
4. "e2e-dev": Write E2E tests, capture screenshots via Playwright (general-purpose)
5. "test-dev": Write unit/integration tests (general-purpose)
6. "synthesizer": Read all artifacts → unified verdict (general-purpose)
```

The `claude-vlm` teammate prompt (for E2E screenshot validation):
```
You are a visual analysis agent. Your job:
1. Read E2E screenshots captured by Playwright via the Read tool:
   - Read /tmp/screenshots/before.png  (baseline)
   - Read /tmp/screenshots/after.png   (current)
2. Compare layout, colors, text rendering, element positioning
3. Write findings to /tmp/xv/ui-review/claude_vlm_review.md:
   # Visual Regression Review
   Status: PASS | FAIL | PASS_WITH_COMMENTS
   ## Findings
   - [SEVERITY] Description of visual difference
   ## Verdict: APPROVE | REQUEST_CHANGES
4. Send summary to synthesizer via SendMessage
```

The `xv-gemini` teammate prompt (for code review + web research):
```
You are a cross-verification agent for frontend code. Your job:
1. mkdir -p /tmp/xv/ui-review/
2. Review frontend code for quality and patterns:
   cat src/components/Dashboard.tsx | gemini -y \
     -p "Review this React component for: 1) Accessibility issues 2) Layout problems
     3) State management anti-patterns 4) Performance concerns.
     Format: # Gemini Review — Dashboard.tsx
     Status: PASS | FAIL | PASS_WITH_COMMENTS
     ## Findings (with [SEVERITY])
     ## Verdict: APPROVE | REQUEST_CHANGES" \
     -o text 2>/dev/null > /tmp/xv/ui-review/gemini_review.md
3. Search for latest framework best practices:
   gemini -y -p "Search for latest React 19 patterns for dashboard components.
     Focus on: Server Components, Suspense boundaries, streaming patterns." \
     -o text 2>/dev/null > /tmp/xv/ui-review/gemini_research.md
4. Read artifacts to verify, then send summary to synthesizer via SendMessage
```

### Team Pattern: Design / Architecture / Planning (3-Way Gate)

**ALL THREE must pass before a plan is approved.** The plan CANNOT proceed unless Claude, Codex, AND Gemini critics all approve.

```
Team (6+ teammates):
1. "architect": Draft the design/plan (general-purpose, mode="plan")
2. "claude-critic": Critique the plan — find flaws (Explore)
3. "xv-codex-critic": Run Codex to critique the plan (general-purpose)
4. "xv-gemini-critic": Run Gemini to critique the plan (general-purpose)
5. "synthesizer": Aggregate 3 critiques → PASS/FAIL gate (general-purpose)
6. "implementer": Only starts after synthesizer approves (general-purpose)

Dependencies:
- Tasks 2-4 blocked by Task 1 (plan must be drafted first)
- Task 5 blocked by Tasks 2-4 (all critiques must complete)
- Task 6 blocked by Task 5 (implementation only after gate passes)
```

**Gate rule**: If ANY critic issues a FAIL verdict, the plan goes back to the architect for revision. The cycle repeats until all 3 pass.

### Artifact Directory Convention

```
/tmp/xv/
├── {task-name}/
│   ├── plan_draft.md          # Architect's plan (input for critics)
│   ├── claude_review.md       # Claude teammate's review
│   ├── codex_review.md        # Codex CLI output artifact
│   ├── codex_critique.md      # Codex CLI critique artifact
│   ├── gemini_review.md       # Gemini CLI output artifact
│   ├── gemini_critique.md     # Gemini CLI critique artifact
│   ├── gemini_research.md     # Gemini web search results
│   └── synthesis_report.md    # Synthesizer's final report
```

### Confidence Scoring (Synthesizer Output)

```
CRITICAL (all 3 agree): Must fix — no exceptions
HIGH     (2 of 3 agree): Should fix, investigate the disagreement
MEDIUM   (1 of 3 flags): Investigate, likely false positive
```

## Artifact File Standard

Every artifact MUST follow this format for consistent parsing:

```markdown
# {Agent Name} Review — {target filename or plan name}
Date: {YYYY-MM-DD HH:MM}
Status: PASS | FAIL | PASS_WITH_COMMENTS

## Findings
- [CRITICAL] Line {N}: {description}
- [HIGH] Line {N}: {description}
- [MEDIUM] {description}
- [LOW] {description}

## Summary
{1-3 sentence overall assessment}

## Verdict: APPROVE | REQUEST_CHANGES
{If REQUEST_CHANGES, list what must change}
```

## Complete Workflow: Code Analysis with Codex (MUST)

### Step 1: Set Up Artifacts

```bash
mkdir -p /tmp/xv/code-review/
```

### Step 2: Claude Review (claude-analyst teammate)

The Claude teammate reviews using native Read/Grep tools and writes:

```bash
# Claude teammate writes its own review via Write tool
# Output: /tmp/xv/code-review/claude_review.md
```

### Step 3: Codex Review (xv-codex teammate)

The xv-codex teammate runs Codex CLI and drops the artifact:

```bash
TARGET="src/services/order_processor.py"

codex exec --ephemeral --full-auto -s read-only -o /tmp/xv/code-review/codex_review.md \
  "$(cat <<'EOF'
You are performing an independent code review for cross-verification.
Another AI has already reviewed this code — your job is to find things it might have missed.

## Output Format (MUST follow exactly)
# Codex Review — order_processor.py
Date: $(date '+%Y-%m-%d %H:%M')
Status: PASS | FAIL | PASS_WITH_COMMENTS

## Findings
- [SEVERITY] Line N: Description

## Summary
1-3 sentences.

## Verdict: APPROVE | REQUEST_CHANGES

## Review Target
$(cat $TARGET)

## Review Criteria
1. Logic errors, off-by-one, race conditions
2. Edge cases: null/empty, boundary values, overflow
3. Security: injection, auth bypass, data exposure
4. Mathematical correctness of any formulas
EOF
)"

# Verify artifact was written
cat /tmp/xv/code-review/codex_review.md | head -5
```

### Step 4: Synthesis (synthesizer teammate)

The synthesizer reads both artifacts and produces:

```bash
# synthesizer reads:
cat /tmp/xv/code-review/claude_review.md
cat /tmp/xv/code-review/codex_review.md

# synthesizer writes:
# /tmp/xv/code-review/synthesis_report.md
```

**Synthesis report format**:
```markdown
# Cross-Verification Synthesis Report

## Findings by Confidence Level

### CRITICAL (Both Agree)
| Finding | Claude | Codex | Action |
|---------|--------|-------|--------|
| Race condition line 42 | Yes | Yes | Must fix |

### HIGH (One Flags)
| Finding | Claude | Codex | Action |
|---------|--------|-------|--------|
| Null check line 87 | Yes | No | Investigate |

## Disagreement Analysis
{Why did they disagree? Which is more likely correct?}

## Final Verdict: APPROVE / REQUEST_CHANGES
```

## Complete Workflow: UI/Frontend with Gemini + Claude VLM (MUST)

This workflow splits responsibilities: **Claude handles VLM** (screenshot analysis), **Gemini handles code review + web search**.

### Step 1: Set Up Artifacts

```bash
mkdir -p /tmp/xv/ui-review/
mkdir -p /tmp/screenshots/
```

### Step 2: E2E Screenshots (e2e-dev teammate)

The e2e-dev teammate captures screenshots during E2E tests (e.g., via Playwright):

```bash
# Playwright captures screenshots during test runs
# Output: /tmp/screenshots/homepage.png, /tmp/screenshots/dashboard.png, etc.
```

### Step 3: Claude VLM Review (claude-vlm teammate)

Claude reads screenshots natively via Read tool and performs visual analysis:

```bash
# Claude teammate reads screenshot files directly:
#   Read /tmp/screenshots/dashboard.png
#   Read /tmp/screenshots/dashboard_baseline.png
# Compares visual elements and writes:
# /tmp/xv/ui-review/claude_vlm_review.md
```

### Step 4: Gemini Code Review (xv-gemini teammate)

```bash
# Frontend code review
cat src/components/Dashboard.tsx | gemini -y \
  -p "Independent review of this React component.
  Focus on: 1) Accessibility (a11y) issues 2) Layout/responsive problems
  3) State management anti-patterns 4) Performance (re-renders, memo)
  Format:
  # Gemini Review — Dashboard.tsx
  Date: $(date)
  Status: PASS | FAIL | PASS_WITH_COMMENTS
  ## Findings with [CRITICAL/HIGH/MEDIUM/LOW]
  ## Summary
  ## Verdict: APPROVE | REQUEST_CHANGES" \
  -o text 2>/dev/null > /tmp/xv/ui-review/gemini_review.md

# Web research for latest patterns
gemini -y \
  -p "Search for latest React 19 best practices for dashboard components.
  Focus on: Server Components, Suspense boundaries, streaming patterns.
  Write a concise summary of relevant patterns." \
  -o text 2>/dev/null > /tmp/xv/ui-review/gemini_research.md

# Verify artifacts
ls -la /tmp/xv/ui-review/
```

### Step 5: Synthesis

Synthesizer reads all artifacts: `claude_vlm_review.md` + `gemini_review.md` + `gemini_research.md` → unified UI verdict.

## Complete Workflow: Design/Plan 3-Way Gate (MUST)

This is the most rigorous pattern. No plan proceeds without unanimous approval.

### Step 1: Architect drafts the plan

The architect teammate writes the plan to the artifact directory:
```bash
# Architect writes via Write tool:
# /tmp/xv/plan-review/plan_draft.md
```

### Step 2: Three critics review in parallel

**Claude critic** (claude-critic teammate):
```bash
# Reads /tmp/xv/plan-review/plan_draft.md via Read tool
# Writes /tmp/xv/plan-review/claude_critique.md via Write tool
# Focus: architectural soundness, integration risks, maintainability
```

**Codex critic** (xv-codex-critic teammate):
```bash
codex exec --ephemeral --full-auto -s read-only -o /tmp/xv/plan-review/codex_critique.md \
  "$(cat <<'EOF'
You are an adversarial critic reviewing a software design plan.
Your job is to find every flaw, risk, and oversight. Be thorough and skeptical.

## Plan to Review
$(cat /tmp/xv/plan-review/plan_draft.md)

## Output Format
# Codex Critique
Date: $(date '+%Y-%m-%d %H:%M')
Status: PASS | FAIL

## Critical Flaws (must fix before proceeding)
- ...

## Concerns (should address)
- ...

## Missing Considerations
- ...

## Verdict: APPROVE | REJECT
If REJECT, list exactly what must change.
EOF
)"
```

**Gemini critic** (xv-gemini-critic teammate):
```bash
cat /tmp/xv/plan-review/plan_draft.md | gemini \
  -p "You are an adversarial critic. Find every flaw in this plan.
  Focus on: 1) Scalability risks 2) Edge cases not covered
  3) Alternative approaches not considered 4) Operational concerns 5) Cost implications
  Format:
  # Gemini Critique
  Date: {now}
  Status: PASS | FAIL
  ## Critical Flaws
  ## Concerns
  ## Missing Considerations
  ## Verdict: APPROVE | REJECT" \
  -o text 2>/dev/null > /tmp/xv/plan-review/gemini_critique.md
```

### Step 3: Gate evaluation (synthesizer)

```bash
# Synthesizer reads all 3:
cat /tmp/xv/plan-review/claude_critique.md
cat /tmp/xv/plan-review/codex_critique.md
cat /tmp/xv/plan-review/gemini_critique.md
```

**Gate logic**:
- ALL 3 APPROVE → Plan proceeds to implementation
- ANY REJECT → Plan returns to architect with consolidated feedback
- Architect revises → All 3 critics re-review (new artifacts overwrite old)
- Maximum 3 revision cycles before escalating to human

### Step 4: Revision cycle (if gate fails)

The synthesizer writes a consolidated feedback file:
```bash
# /tmp/xv/plan-review/revision_feedback.md
# Contains: merged critical flaws + concerns from all 3 critics
```

The architect reads this, revises `plan_draft.md`, and the cycle repeats.

## Parallel Execution Pattern

When a teammate runs both Gemini and Codex, run them in parallel:

```bash
mkdir -p /tmp/xv/dual-review/

# Background both
cat target.py | gemini -y -p "Review..." -o text 2>/dev/null > /tmp/xv/dual-review/gemini_review.md &
PID_GEMINI=$!

codex exec --ephemeral --full-auto -s read-only -o /tmp/xv/dual-review/codex_review.md "Review $(cat target.py)" &
PID_CODEX=$!

# Wait with timeout
timeout 120 bash -c "wait $PID_GEMINI" || echo "Gemini timed out"
timeout 120 bash -c "wait $PID_CODEX" || echo "Codex timed out"

# Verify both artifacts exist
ls -la /tmp/xv/dual-review/
```

## Capability Matrix

| Capability | Claude (native) | Gemini CLI | Codex CLI |
|-----------|-----------------|------------|-----------|
| Code logic review | Excellent | Good | Excellent |
| Mathematical/algorithmic verification | Excellent | Fair | Excellent |
| Security audit | Excellent | Good | Very Good |
| Web search / latest docs | Via WebSearch tool | Built-in (`-y` flag) | No |
| UI/Frontend code review | Good | Good (code review + web search) | Good |
| VLM / Screenshot analysis | Excellent (native Read) | Not supported via CLI | Not supported |
| Structured output | Via tools | `-o json` envelope | `--output-schema` (enforced) |
| Branch diff review | Via git tools | Manual | Built-in (`codex exec review`) |
| Plan/design critique | Excellent | Good | Very Good |
| Speed | Instant (in-process) | ~5-12s per call | ~5-15s per call |

## Best Practices

1. **Always create `/tmp/xv/{task}/` first** — artifacts need a directory
2. **Use standard artifact format** — enables automated synthesis
3. **Run CLI calls in parallel** — `&` + `wait` pattern, ~40% faster
4. **Set timeouts** — `timeout 60 gemini ...` and `timeout 120 codex exec ...`
5. **Verify artifacts after CLI call** — `cat /tmp/xv/.../file.md | head -5`
6. **xv-* teammates send summary via SendMessage** — don't rely solely on artifacts
7. **Synthesizer reads ALL artifacts** — never skip a review
8. **3-way gate for plans is NON-NEGOTIABLE** — no shortcuts on design reviews

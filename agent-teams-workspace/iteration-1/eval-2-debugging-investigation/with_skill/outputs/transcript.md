# Reasoning Transcript: Order Processing Bug Investigation

## Initial Analysis

The user reports an intermittent bug where order amounts are sometimes calculated incorrectly. Three files are identified as relevant:

1. `src/services/order_processor.py` - Business logic (likely where calculation happens)
2. `src/models/order.py` - Data model (likely where types/validation are defined)
3. `src/api/handlers/orders.py` - API handler (likely where input parsing happens)

Key observation: The bug is **intermittent** ("sometimes"). This suggests it is not a simple formula error (which would be wrong every time) but rather:
- A floating point precision issue that only manifests with certain input values
- A race condition in concurrent order processing
- A conditional code path that only triggers under certain input combinations (e.g., specific discount types, item counts, or tax rules)
- A type coercion issue where some inputs get converted differently

## Team Design Decisions

### Why 5 teammates (not 3)?

The skill guidelines specify 4-6 teammates for investigation/debug tasks. While there are 3 files, there are more than 3 concerns:

1. **Per-file analysis** (3 teammates) - Each file needs deep individual analysis
2. **Cross-module integration** (1 teammate) - The bug likely lives at the boundary between modules, not within a single file. A dedicated integration tracer can focus on data flow across module boundaries.
3. **Test coverage review** (1 teammate) - Understanding what is NOT tested reveals where intermittent bugs hide. The skill guidelines say "Always include a dedicated test teammate."

Total: 5 teammates. This matches the sizing guide for "Investigation/debug: 4-6."

### Why Explore subagent_type for all?

This is a pure investigation task. No files need to be edited. All teammates need read access only. Using `Explore` type:
- Prevents accidental file modifications
- Signals the intent clearly
- Is the recommended type for research/investigation per the skill docs

### Why not mode="plan"?

`mode="plan"` requires plan approval before execution, which adds latency. For a read-only investigation, there is no risk of destructive changes, so plan approval is unnecessary overhead.

## Task Dependency Design

The dependency graph is:

```
Task 1 (processor analysis) ──┐
Task 2 (model analysis) ──────┼──> Task 4 (integration trace) ──┐
Task 3 (handler analysis) ────┘                                  │
                                                                  ├──> Task 6 (synthesis)
Task 5 (test review) ────────────────────────────────────────────┘
```

Rationale:
- Tasks 1, 2, 3, 5 can all run in parallel (no dependencies on each other)
- Task 4 (integration tracing) needs the individual analyses first so it can cross-reference findings
- Task 6 (synthesis by lead) needs everything before producing final report

## Communication Design

### Why direct messages, not broadcasts?

The skill warns: "Broadcast expensive -- use only for critical blockers." In this investigation:
- Each file analyst sends findings directly to `integration-tracer` (targeted)
- `integration-tracer` and `test-reviewer` send final results to lead (targeted)
- Broadcast only if a critical finding needs all teammates to re-check their modules

### Message flow

```
order-processor-analyst ──> integration-tracer
order-model-analyst ──────> integration-tracer
api-handler-analyst ──────> integration-tracer
integration-tracer ────────> lead
test-reviewer ─────────────> lead
```

This is efficient: each message goes to exactly who needs it.

## Prompt Design Decisions

Each teammate's prompt includes:
1. **Context**: What the bug is (intermittent amount miscalculation)
2. **Scope**: Exactly which file(s) to read
3. **Checklist**: Specific things to look for (tailored to the file's role)
4. **Output format**: Structured markdown summary
5. **Communication instruction**: Who to send findings to

This follows the skill's guidance: "Teammates don't inherit the lead's conversation. Include all needed specifics in the spawn prompt."

The checklists are tailored per role:
- **Processor analyst**: Calculation order, floating point, rounding, edge cases
- **Model analyst**: Field types, defaults, validation, serialization
- **Handler analyst**: Parsing, coercion, response formatting
- **Integration tracer**: Boundary mismatches, type flow, assumptions
- **Test reviewer**: Coverage gaps, untested scenarios

## Common Bug Hypotheses (Guiding the Investigation)

Based on the symptom (intermittent incorrect amount calculation), the most likely root causes to investigate:

1. **Float vs Decimal for money** - Using Python `float` for monetary calculations causes precision errors with certain values (classic: 0.1 + 0.2 != 0.3). This is intermittent because only certain price/quantity combinations trigger visible errors.

2. **Rounding at wrong stage** - If rounding happens per-item then summed (vs sum then round), certain multi-item orders will have different totals.

3. **Discount/tax ordering** - If discount is applied before tax in some code paths but after tax in others, amounts differ.

4. **Type coercion at API boundary** - JSON numbers may arrive as float or string depending on the client. If the handler converts inconsistently, some orders get wrong types passed to the processor.

5. **Race condition** - If the processor uses shared state (e.g., a cached tax rate that gets updated mid-calculation), concurrent orders could see stale values.

These hypotheses are distributed across the teammate prompts so each analyst knows what patterns to look for in their specific file.

## Shutdown Reasoning

Shutdown is done individually per teammate with `shutdown_request` type SendMessage, followed by `TeamDelete`. This ensures:
- Each teammate finishes any in-progress work gracefully
- No orphaned resources remain
- Clean state for any subsequent team creation

# gemini-image Skill Benchmark — Iteration 1

## Summary

| Configuration | Pass Rate | Avg Time | Avg Tokens |
|---------------|-----------|----------|------------|
| **with_skill (improved)** | **91.7%** | 179.3s | 25,463 |
| old_skill (baseline) | 8.3% | 72.4s | 15,990 |
| **Delta** | **+83.4%** | +147% | +59% |

## Per-Eval Breakdown

| Eval | with_skill | old_skill |
|------|-----------|-----------|
| icon-generation | 3/4 (75%) | 1/4 (25%) |
| hero-banner | 4/4 (100%) | 0/4 (0%) |
| multi-thumbnail | 3/3 (100%) | 0/3 (0%) |

## Key Observations

1. Old skill: SDK incompatibility caused 100% script failure
2. New skill: Agents recovered from script failure via improved workflow guidance
3. Script has been fixed for SDK v1.27.0 — iteration 2 should show direct script success
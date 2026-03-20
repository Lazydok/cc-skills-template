# Execution Plan: Order Processing Bug Investigation

## Task Summary

Investigate a bug where order amounts are sometimes calculated incorrectly. Three files to examine:
- `src/services/order_processor.py` (business logic)
- `src/models/order.py` (data model)
- `src/api/handlers/orders.py` (API handler)

## Team Design

**Team name**: `order-bug-investigation`
**Team size**: 5 teammates (Investigation/debug scope per sizing guide: 4-6)
**All agents use `Explore` subagent_type** since this is a read-only investigation (no file edits needed).

### Teammate Roles

| Name | Responsibility | File Ownership |
|------|---------------|----------------|
| `order-processor-analyst` | Analyze business logic in order_processor.py | `src/services/order_processor.py` |
| `order-model-analyst` | Analyze data model in order.py | `src/models/order.py` |
| `api-handler-analyst` | Analyze API handler in orders.py | `src/api/handlers/orders.py` |
| `integration-tracer` | Trace data flow across all three files, looking for mismatches | All three files (read-only cross-reference) |
| `test-reviewer` | Check existing tests for coverage gaps related to amount calculation | `tests/` directory |

---

## Exact Tool Call Sequence

### Step 1: Create Team

```
TeamCreate(
  team_name="order-bug-investigation",
  description="Investigate intermittent order amount miscalculation bug across order_processor.py, order.py, and orders.py"
)
```

### Step 2: Create Tasks

```
TaskCreate(
  subject="Analyze order_processor.py business logic",
  description="Read src/services/order_processor.py. Focus on: amount calculation logic, discount/tax application order, rounding behavior, floating point arithmetic, currency handling, edge cases (empty cart, zero quantity, negative prices). Report all suspicious code paths."
)
```
-> Returns taskId="1"

```
TaskCreate(
  subject="Analyze order.py data model",
  description="Read src/models/order.py. Focus on: field types for monetary values (float vs Decimal), default values, validation rules, property calculations, serialization/deserialization of amounts, any computed fields. Report type safety issues and missing validations."
)
```
-> Returns taskId="2"

```
TaskCreate(
  subject="Analyze orders.py API handler",
  description="Read src/api/handlers/orders.py. Focus on: request parsing, type coercion of amount fields, how order data flows from request to model to processor, response serialization, any transformations that could lose precision. Report suspicious conversions or missing validations."
)
```
-> Returns taskId="3"

```
TaskCreate(
  subject="Trace data flow across all three modules",
  description="After initial analyses complete, read all three files and trace the full order lifecycle: API request -> handler parsing -> model instantiation -> processor calculation -> response. Identify any points where amount data is transformed, truncated, or retyped. Cross-reference findings from other analysts."
)
```
-> Returns taskId="4"

```
TaskCreate(
  subject="Review test coverage for amount calculation",
  description="Search tests/ directory for order-related tests. Check coverage of: discount combinations, tax calculation, rounding edge cases, large/small amounts, concurrent orders, currency precision. Identify gaps that could hide the intermittent bug."
)
```
-> Returns taskId="5"

```
TaskCreate(
  subject="Synthesize findings and identify root cause",
  description="Combine all teammate findings into a unified root cause analysis with recommended fix."
)
```
-> Returns taskId="6"

### Step 3: Set Task Dependencies

```
TaskUpdate(taskId="4", addBlockedBy=["1", "2", "3"])
```
Task 4 (integration tracing) waits for the three individual file analyses to complete.

```
TaskUpdate(taskId="6", addBlockedBy=["1", "2", "3", "4", "5"])
```
Task 6 (synthesis) waits for all investigation tasks.

### Step 4: Spawn Teammates (parallel)

All five Agent calls are issued in parallel:

```
Agent(
  team_name="order-bug-investigation",
  name="order-processor-analyst",
  subagent_type="Explore",
  prompt="You are investigating an intermittent bug where order amounts are sometimes calculated incorrectly. Your job is to thoroughly analyze src/services/order_processor.py. Look for:\n\n1. How total amounts are calculated (subtotal, discounts, taxes, fees)\n2. Order of operations in calculations (e.g., discount applied before or after tax?)\n3. Floating point arithmetic issues (using float instead of Decimal for money)\n4. Rounding errors or truncation\n5. Race conditions if any shared state is used\n6. Edge cases: empty items list, zero quantity, negative prices, very large amounts\n7. Any conditional logic that only triggers sometimes (the bug is intermittent)\n8. Currency handling and precision\n\nRead the file carefully, then report your findings as a structured markdown summary. Send your findings to 'integration-tracer' via SendMessage when done. Mark your task as completed.",
  description="Analyze order processing business logic for calculation bugs"
)
```

```
Agent(
  team_name="order-bug-investigation",
  name="order-model-analyst",
  subagent_type="Explore",
  prompt="You are investigating an intermittent bug where order amounts are sometimes calculated incorrectly. Your job is to thoroughly analyze src/models/order.py. Look for:\n\n1. Data types used for monetary fields (float vs Decimal vs int cents)\n2. Default values that could cause unexpected calculations\n3. Validation rules (or lack thereof) on price/quantity/amount fields\n4. Any computed properties or __post_init__ that modify amounts\n5. Serialization/deserialization methods that might lose precision\n6. Type coercion that happens implicitly\n7. Whether the model enforces non-negative amounts\n8. Any inheritance or mixin that affects field behavior\n\nRead the file carefully, then report your findings as a structured markdown summary. Send your findings to 'integration-tracer' via SendMessage when done. Mark your task as completed.",
  description="Analyze order data model for type and validation issues"
)
```

```
Agent(
  team_name="order-bug-investigation",
  name="api-handler-analyst",
  subagent_type="Explore",
  prompt="You are investigating an intermittent bug where order amounts are sometimes calculated incorrectly. Your job is to thoroughly analyze src/api/handlers/orders.py. Look for:\n\n1. How request body is parsed — are amount fields parsed as float or string?\n2. Type coercion when creating order model from request data\n3. Any rounding or formatting applied to amounts in the handler\n4. Whether the handler passes raw user input or transforms it before calling the processor\n5. Response serialization — does it round or truncate the calculated amount?\n6. Error handling that might silently swallow calculation errors\n7. Any middleware or decorators that modify request/response data\n8. Differences between create-order and update-order paths\n\nRead the file carefully, then report your findings as a structured markdown summary. Send your findings to 'integration-tracer' via SendMessage when done. Mark your task as completed.",
  description="Analyze API handler for data transformation issues"
)
```

```
Agent(
  team_name="order-bug-investigation",
  name="integration-tracer",
  subagent_type="Explore",
  prompt="You are the integration tracer on a debugging team investigating intermittent order amount miscalculation. Wait for findings from 'order-processor-analyst', 'order-model-analyst', and 'api-handler-analyst' via SendMessage.\n\nOnce you receive their findings, read all three files yourself:\n- src/services/order_processor.py\n- src/models/order.py\n- src/api/handlers/orders.py\n\nThen trace the complete data flow:\n1. API request arrives at orders.py handler\n2. Handler parses request and creates Order model\n3. Order model instantiates with field types/defaults from order.py\n4. order_processor.py receives the model and calculates amounts\n5. Result flows back through handler to API response\n\nFocus on boundaries between modules:\n- Type mismatches at interfaces (float vs Decimal vs string)\n- Data lost in transit between layers\n- Assumptions one module makes about another's behavior\n- Intermittent conditions (timing, input-dependent paths)\n\nProduce a data flow diagram (text-based) and highlight the exact point(s) where the bug likely occurs. Send your analysis to the lead.",
  description="Trace order data flow across all three modules to find boundary bugs"
)
```

```
Agent(
  team_name="order-bug-investigation",
  name="test-reviewer",
  subagent_type="Explore",
  prompt="You are reviewing test coverage for an intermittent order amount calculation bug. Search the tests/ directory (and any test files near the source files) for tests related to orders, order processing, and amount calculation.\n\nSpecifically check for:\n1. Tests that verify total amount calculation with discounts + tax\n2. Tests for floating point edge cases (e.g., 0.1 + 0.2)\n3. Tests with multiple items at different prices\n4. Tests for discount stacking or percentage vs fixed discounts\n5. Tests for tax calculation rounding\n6. Tests for boundary values (very small amounts, very large amounts)\n7. Tests for concurrent order creation\n8. Integration tests that go from API request to final amount\n\nReport which scenarios are tested and, critically, which are NOT tested. The untested scenarios are likely where the intermittent bug hides. Send your findings to the lead.",
  description="Review test coverage gaps for order amount calculation"
)
```

### Step 5: Assign Tasks to Teammates

```
TaskUpdate(taskId="1", owner="order-processor-analyst")
TaskUpdate(taskId="2", owner="order-model-analyst")
TaskUpdate(taskId="3", owner="api-handler-analyst")
TaskUpdate(taskId="4", owner="integration-tracer")
TaskUpdate(taskId="5", owner="test-reviewer")
```

Task 6 (synthesis) is owned by the lead (no owner assignment needed).

### Step 6: Monitor Progress

```
TaskList()
```

Periodically check task status. When tasks 1, 2, 3 complete, task 4 auto-unblocks.

```
TaskGet(taskId="4")
```

Check integration-tracer progress after individual analyses complete.

### Step 7: SendMessage Patterns During Execution

**Teammates -> integration-tracer** (each analyst sends findings when done):
```
SendMessage(
  type="message",
  recipient="integration-tracer",
  content="[Findings from order-processor-analyst analysis...]",
  summary="Completed analysis of order_processor.py - found potential floating point issue in discount calculation"
)
```

**integration-tracer -> lead** (after cross-referencing):
```
SendMessage(
  type="message",
  recipient="lead",
  content="[Cross-module analysis with data flow diagram and identified bug location...]",
  summary="Root cause identified at boundary between handler and processor - float conversion loses precision"
)
```

**test-reviewer -> lead** (after coverage analysis):
```
SendMessage(
  type="message",
  recipient="lead",
  content="[Test coverage gaps report...]",
  summary="No tests cover multi-item orders with percentage discounts - likely untested bug path"
)
```

**Lead broadcast (only if critical finding):**
```
SendMessage(
  type="broadcast",
  content="Critical: order-processor-analyst found that discount is applied using float multiplication. All analysts check if your module interacts with this path.",
  summary="Float multiplication in discount path - cross-check needed"
)
```

### Step 8: Synthesis (Lead performs Task 6)

After all tasks complete, the lead reads all teammate findings and produces a unified report:
- Root cause identification
- Affected code paths with line references
- Recommended fix
- Suggested test cases to add

### Step 9: Shutdown Sequence

```
SendMessage(type="shutdown_request", recipient="order-processor-analyst", content="Investigation complete. Thank you for your analysis.")
SendMessage(type="shutdown_request", recipient="order-model-analyst", content="Investigation complete. Thank you for your analysis.")
SendMessage(type="shutdown_request", recipient="api-handler-analyst", content="Investigation complete. Thank you for your analysis.")
SendMessage(type="shutdown_request", recipient="integration-tracer", content="Investigation complete. Thank you for your analysis.")
SendMessage(type="shutdown_request", recipient="test-reviewer", content="Investigation complete. Thank you for your analysis.")
```

### Step 10: Cleanup

```
TeamDelete()
```

---

## Summary of Tool Calls

| # | Tool | Key Parameters |
|---|------|---------------|
| 1 | `TeamCreate` | team_name="order-bug-investigation" |
| 2-7 | `TaskCreate` x6 | One per investigation task + synthesis |
| 8-9 | `TaskUpdate` x2 | Set dependencies (task 4 blocked by 1,2,3; task 6 blocked by all) |
| 10-14 | `Agent` x5 | All with team_name, name, subagent_type="Explore", detailed prompts |
| 15-19 | `TaskUpdate` x5 | Assign owners to tasks |
| 20+ | `TaskList`/`TaskGet` | Monitor progress |
| -- | `SendMessage` (by teammates) | Direct messages between analysts and integration-tracer |
| -- | `SendMessage` x5 | shutdown_request to each teammate |
| Final | `TeamDelete` | Clean up team resources |

**Total tool calls**: ~30 (6 TaskCreate + 2 dependency TaskUpdate + 5 Agent + 5 owner TaskUpdate + 1 TeamCreate + 5 shutdown SendMessage + 1 TeamDelete + monitoring calls)

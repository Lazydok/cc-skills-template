# Execution Plan: Debugging Order Amount Calculation Bug

## Task Summary

Investigate a bug in order processing logic where the calculated amount is sometimes incorrect. Three files to examine:
- `src/services/order_processor.py`
- `src/models/order.py`
- `src/api/handlers/orders.py`

---

## Phase 1: Read All Three Files in Parallel

Since all three files are independent reads, execute them simultaneously to minimize latency.

### Tool Calls (parallel):

```
Read(file_path="src/services/order_processor.py")
Read(file_path="src/models/order.py")
Read(file_path="src/api/handlers/orders.py")
```

**Rationale:** Reading all three files in parallel gives us the full picture immediately. No dependencies between these reads.

---

## Phase 2: Targeted Search for Calculation Logic

After reading the files, search for specific patterns related to amount calculation. These searches run in parallel.

### Tool Calls (parallel):

```
Grep(pattern="total|amount|price|subtotal|discount|tax|sum|calculate",
     path="src/services/order_processor.py",
     output_mode="content", -n=true)

Grep(pattern="total|amount|price|subtotal|discount|tax|sum|calculate",
     path="src/models/order.py",
     output_mode="content", -n=true)

Grep(pattern="total|amount|price|subtotal|discount|tax|sum|calculate",
     path="src/api/handlers/orders.py",
     output_mode="content", -n=true)
```

**Rationale:** Isolate all lines dealing with monetary calculations across all three files. This narrows the investigation scope.

---

## Phase 3: Search for Common Bug Patterns

Search for patterns that commonly cause calculation bugs. These run in parallel.

### Tool Calls (parallel):

```
# Float arithmetic issues (classic source of money bugs)
Grep(pattern="float|round|decimal|Decimal",
     path="src/",
     output_mode="content", -n=true,
     glob="*.py")

# Integer division issues
Grep(pattern="/[^/]|//|int\(|floor|ceil",
     path="src/",
     output_mode="content", -n=true,
     glob="*.py")

# Type conversion or casting that could lose precision
Grep(pattern="int\(|float\(|str\(",
     path="src/",
     output_mode="content", -n=true,
     glob="*.py")
```

**Rationale:** The most common causes of incorrect money calculations are:
1. Floating-point precision errors (using `float` instead of `Decimal`)
2. Integer division truncation
3. Incorrect type conversions
4. Rounding errors

---

## Phase 4: Search for Data Flow and State Issues

Look for how order data flows between the three files.

### Tool Calls (parallel):

```
# How does the API handler pass data to the service?
Grep(pattern="order_processor|OrderProcessor|process_order",
     path="src/api/handlers/orders.py",
     output_mode="content", -n=true)

# How does the service use the model?
Grep(pattern="from.*models|import.*order|Order\(",
     path="src/services/order_processor.py",
     output_mode="content", -n=true)

# What fields does the Order model expose?
Grep(pattern="class Order|def __init__|@property|def calculate|def total",
     path="src/models/order.py",
     output_mode="content", -n=true)
```

**Rationale:** Bugs often occur at boundaries between modules -- wrong fields passed, missing data, or mismatched assumptions.

---

## Phase 5: Check for Race Conditions or Mutability Issues

### Tool Calls (parallel):

```
# Mutable default arguments or shared state
Grep(pattern="def.*=\[\]|def.*=\{\}|cls\.|class.*var",
     path="src/",
     output_mode="content", -n=true,
     glob="*.py")

# Async issues that could cause intermittent bugs
Grep(pattern="async|await|thread|lock|concurrent",
     path="src/",
     output_mode="content", -n=true,
     glob="*.py")
```

**Rationale:** The user said the bug happens "sometimes" (intermittent), which suggests either:
- A race condition / concurrency issue
- An edge case triggered by specific data (e.g., discounts, tax, empty items)
- Mutable default arguments causing shared state

---

## Phase 6: Look for Edge Case Handling

### Tool Calls (parallel):

```
# Check for missing None/null checks
Grep(pattern="if.*None|is None|is not None|or 0|or \[\]",
     path="src/services/order_processor.py",
     output_mode="content", -n=true)

# Check for discount/coupon logic
Grep(pattern="discount|coupon|promo|voucher",
     path="src/",
     output_mode="content", -n=true,
     glob="*.py")

# Check for quantity handling
Grep(pattern="quantity|qty|count|items",
     path="src/services/order_processor.py",
     output_mode="content", -n=true)
```

**Rationale:** Edge cases like zero-quantity items, null prices, or stacked discounts are common sources of calculation errors.

---

## Phase 7: Check Related Test Files

### Tool Calls (sequential after parallel):

```
# Find related test files
Glob(pattern="**/test*order*")
Glob(pattern="**/test*processor*")
```

Then, if test files are found:

```
Read(file_path="<discovered_test_file_path>")
```

**Rationale:** Tests reveal expected behavior, edge cases the developers considered, and potentially which cases are NOT covered.

---

## Phase 8: Check Git History for Recent Changes

### Tool Call:

```
Bash(command="git log --oneline -20 -- src/services/order_processor.py src/models/order.py src/api/handlers/orders.py",
     description="Show recent commits touching the three target files")
```

Then for suspicious commits:

```
Bash(command="git diff <commit_hash>~1 <commit_hash> -- src/services/order_processor.py src/models/order.py src/api/handlers/orders.py",
     description="Show diff for suspicious commit")
```

**Rationale:** Regressions are introduced by recent changes. Reviewing the git history can pinpoint when the bug was introduced.

---

## Investigation Strategy Summary

| Phase | Parallelism | Purpose |
|-------|------------|---------|
| 1 | 3 parallel reads | Get full file contents |
| 2 | 3 parallel greps | Find calculation logic |
| 3 | 3 parallel greps | Find common bug patterns |
| 4 | 3 parallel greps | Trace data flow |
| 5 | 2 parallel greps | Check concurrency/state |
| 6 | 3 parallel greps | Check edge cases |
| 7 | 2 parallel globs + reads | Review tests |
| 8 | Sequential bash | Git history analysis |

**Total estimated tool calls:** 22-25 calls across 8 phases.

**Key principle:** Maximize parallel execution. All file reads happen together. All independent searches within a phase happen together. Sequential execution only where one step's output determines the next step's parameters.

---

## Common Root Causes to Watch For

1. **Floating-point arithmetic** -- Using `float` for money instead of `Decimal` or integer cents
2. **Missing rounding** -- Not rounding to 2 decimal places after multiplication
3. **Order of operations** -- Applying discount after tax vs. before tax inconsistently
4. **Race condition** -- Concurrent order modifications during calculation
5. **Mutable default arguments** -- Shared list/dict between order instances
6. **Type coercion** -- API handler sending string prices that get silently converted
7. **Missing items** -- Iteration skipping first/last item, or off-by-one in quantity
8. **Null/None fields** -- Unhandled None price or quantity defaulting to unexpected value

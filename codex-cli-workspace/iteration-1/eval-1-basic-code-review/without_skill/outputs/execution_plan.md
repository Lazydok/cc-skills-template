# Execution Plan: Code Review of src/utils/calculator.py with Codex CLI

## Objective

Use the Codex CLI to review `src/utils/calculator.py` for logic errors and edge case issues.

## Commands

### Command 1: Review the file with Codex CLI

```bash
codex --approval-mode suggest \
  "src/utils/calculator.py 파일을 리뷰해줘. 다음 항목을 중점적으로 확인해줘:
   1. 로직 오류 (잘못된 연산, 조건문 실수 등)
   2. 엣지 케이스 처리 (0으로 나누기, 오버플로우, 빈 입력, None 값 등)
   3. 타입 관련 문제 (잘못된 타입 입력 시 동작)
   4. 경계값 처리 (음수, 매우 큰 수, 소수점 정밀도 등)
   해당 파일의 코드를 읽고 문제점과 개선 사항을 정리해줘."
```

### Explanation of flags and parameters

| Flag / Parameter | Description |
|---|---|
| `codex` | Codex CLI binary (OpenAI Codex CLI tool) |
| `--approval-mode suggest` | Codex can read files and suggest changes but cannot write without approval. This is appropriate for a review task where we want analysis, not automatic modifications. |
| `"src/utils/calculator.py ..."` | The prompt describing the review task, passed as a positional argument. |

### Alternative: Full auto mode (read-only review)

If you only want Codex to read and analyze without any write suggestions:

```bash
codex --approval-mode suggest \
  "Read the file src/utils/calculator.py and perform a thorough code review. Focus on:
   1. Logic errors (incorrect operations, conditional mistakes)
   2. Edge case handling (division by zero, overflow, empty input, None values)
   3. Type safety issues (behavior with wrong input types)
   4. Boundary value handling (negative numbers, very large numbers, floating point precision)
   Summarize all issues found with line numbers and suggested fixes."
```

### Alternative: Using a specific model

```bash
codex --model o4-mini --approval-mode suggest \
  "Review src/utils/calculator.py for logic errors and edge cases. Report all issues."
```

### Alternative: Piping file content directly

If you want to ensure the file content is included in the prompt:

```bash
cat src/utils/calculator.py | codex --approval-mode suggest \
  "위 코드를 리뷰해줘. 로직 오류, 엣지 케이스 누락, 타입 안전성 문제를 찾아줘."
```

## Notes

- `--approval-mode suggest` is the recommended mode for code review. It allows Codex to read files freely and suggest changes, but requires user approval before any writes.
- Other approval modes: `full-auto` (no approval needed), `ask` (approval needed for all file operations).
- The Codex CLI automatically has access to the working directory's files, so it can read `src/utils/calculator.py` directly.
- No `--exec` flag is needed since we are not running shell commands; we are asking for analysis.

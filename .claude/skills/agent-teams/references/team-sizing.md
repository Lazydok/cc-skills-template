# Team Sizing Reference

## Task Decomposition → Team Size Matrix

Map project scope to optimal team size. The goal is maximum parallelism with minimal file conflicts.

### By Project Type

| Project Type | Teammates | Rationale |
|---|---|---|
| **Single-module bug fix** | 2-3 | Fix + test (+ review if complex) |
| **Multi-module feature** | 4-6 | One per module + test + integration |
| **Full-stack feature** | 5-7 | Backend API, DB/migration, frontend UI, frontend state, tests, docs, review |
| **Large refactoring** | 5-8 | One per subsystem + migration + test + review |
| **System investigation/debug** | 4-6 | One per hypothesis/subsystem |
| **Architecture research** | 4-5 | One per perspective/concern |
| **Code review (comprehensive)** | 4-5 | Security, performance, correctness, test coverage, architecture |
| **Cross-cutting concern** | 5-7 | One per affected layer + coordinator |

### By Codebase Structure

Use the natural boundaries of the codebase to determine team size:

```
typical full-stack project:
├── src/api/          → Teammate: api-dev
├── src/services/     → Teammate: service-dev
├── src/models/       → Teammate: data-layer
├── src/workers/      → Teammate: worker-dev
├── frontend/src/     → Teammate: frontend-dev
├── tests/            → Teammate: test-writer
└── docs/             → Teammate: docs-updater
```

Rule: **One teammate per independent directory subtree** that will be modified.

### Scaling Checklist

Before deciding team size, count:

1. **Independent file groups**: How many non-overlapping sets of files need changes?
2. **Distinct concerns**: How many separate areas of expertise are needed?
3. **Test layers**: Unit tests, integration tests, E2E tests — each can be a teammate
4. **Review dimensions**: Security, performance, correctness — each is a teammate

**Team size = max(independent file groups, distinct concerns)**

Minimum 2 teammates (below this, use subagents instead). Scale up to 7-8 for large cross-cutting work.

## Role Templates

Pre-defined roles for common team compositions. Mix and match as needed.

### Implementation Roles

| Role | Responsibility | File Ownership |
|---|---|---|
| `backend-api` | API endpoints, request handling | `src/api/`, `src/routes/` |
| `backend-logic` | Business logic, services | `src/services/`, `src/core/` |
| `data-layer` | DB models, migrations, queries | `src/models/`, `migrations/` |
| `frontend-ui` | Components, layouts, styles | `src/components/`, `src/styles/` |
| `frontend-state` | State management, data fetching | `src/store/`, `src/hooks/` |
| `test-writer` | Unit + integration tests | `tests/` |
| `docs-updater` | Documentation, API docs | `docs/`, `README.md` |
| `devops` | CI/CD, config, scripts | `.github/`, `scripts/`, `Dockerfile` |

### Research/Review Roles

| Role | Focus |
|---|---|
| `security-reviewer` | Auth, injection, secrets, OWASP top 10 |
| `performance-reviewer` | N+1 queries, memory, caching, async patterns |
| `correctness-reviewer` | Logic errors, edge cases, error handling |
| `test-reviewer` | Coverage gaps, flaky tests, missing assertions |
| `architecture-reviewer` | Coupling, cohesion, dependency direction |
| `hypothesis-X` | Investigate specific theory (debugging) |

## Example Team Compositions

### Feature: Add Analytics Dashboard (7 teammates)

```
Create an agent team with 7 teammates:

1. "dash-api": Implement analytics API endpoints in src/api/handlers/
2. "dash-service": Implement analytics business logic in src/services/
3. "dash-models": Define request/response models in src/models/
4. "dash-ui": Build React UI components in frontend/src/components/
5. "dash-state": Implement data fetching hooks in frontend/src/hooks/
6. "dash-tests": Write tests for both backend and frontend in tests/
7. "dash-docs": Update API docs and user guide

Each teammate owns their own file set. Use delegate mode.
Require plan approval for dash-api and dash-service before they start coding.
```

### Investigation: API Response Data Inconsistency (5 teammates)

```
Create an agent team with 5 teammates to debug data inconsistency:

1. "api-flow": Trace request handling path in src/api/handlers/
2. "query-flow": Trace database queries in src/repositories/
3. "transform-check": Verify data transformation logic in src/services/
4. "cache-check": Check caching layer behavior in src/cache/
5. "log-analyzer": Query application logs and correlate timestamps

Have them share findings and challenge each other's hypotheses.
```

### Refactoring: Migrate to New Auth System (6 teammates)

```
Create an agent team with 6 teammates:

1. "auth-models": Update auth models in src/models/
2. "auth-service": Update auth service in src/services/
3. "auth-handlers": Update API handlers in src/api/handlers/
4. "auth-middleware": Update middleware and guards in src/middleware/
5. "auth-tests": Update all affected tests in tests/
6. "auth-migration": Write DB migration script in scripts/migrations/

Teammates 1-4 work in parallel. Teammate 5 starts after 1-4 complete.
Teammate 6 can start immediately (independent).
```

### Code Review: Pre-Release Audit (5 teammates)

```
Create an agent team with 5 reviewers for pre-release audit:

1. "security": Check for injection, auth bypass, secret leaks across all modules
2. "performance": Profile hot paths, identify N+1 queries, check async patterns
3. "correctness": Verify business logic, edge cases, error handling
4. "test-gaps": Identify untested code paths and missing assertions
5. "architecture": Review module boundaries, dependency cycles, abstraction quality

Each reviewer writes findings to a shared doc. Lead synthesizes final report.
```

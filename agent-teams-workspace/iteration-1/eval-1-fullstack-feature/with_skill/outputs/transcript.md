# Reasoning Transcript: JWT Authentication API with Agent Teams

## Task Analysis

The user requested (in Korean):
- Add a new user authentication API to `src/api/` and `src/services/`
- JWT token-based: login, register, refresh (3 endpoints)
- Unit tests for each endpoint
- TypeScript with Express framework

This is clearly a **Full-Stack Feature** pattern requiring multiple independent work streams across different directories. Per the agent-teams skill, this mandates using `TeamCreate` + `Agent(team_name=...)`.

## Decomposition Reasoning

### Identifying Independent Work Streams

I identified 5 distinct concerns with non-overlapping file ownership:

1. **Project setup/config** -- `package.json`, `tsconfig.json`, `src/config/`, `src/app.ts`. This must come first since everything depends on it.

2. **Types and models** -- `src/models/`. Defines the interfaces that both services and controllers depend on. Blocked by setup (needs TypeScript config to exist).

3. **Service layer** -- `src/services/`. Contains JWT token operations and authentication business logic. Blocked by models (uses the type definitions).

4. **API layer** -- `src/api/`. Express controllers, routes, and middleware. Blocked by both models and services (calls service methods with model types).

5. **Tests** -- `tests/`. Unit tests for services and controllers. Blocked by services and API (needs the actual implementations to test against / mock).

### Why 5 Teammates (Not Fewer)

The skill guidelines state:
- "Default: 4-7 teammates. Never default to 2-3 when more parallel streams exist."
- "Always include a dedicated test teammate"
- Full-stack feature sizing: 5-7

With 5 distinct directory-level concerns and zero file overlap, 5 teammates is the natural fit. Going to 3 would mean one teammate owning both models and services (coupling), or merging config with something else. Going to 6+ would mean splitting something that doesn't naturally split (e.g., separating token.service from auth.service into two teammates -- unnecessary since they're in the same directory).

### Why Not Use `mode="plan"`

The task is well-specified: the user gave exact requirements (JWT, 3 endpoints, Express, TypeScript). There's low ambiguity. Using `mode="plan"` would add latency for plan approval without much safety benefit. For a greenfield feature with clear specs, `general-purpose` teammates executing directly is appropriate.

If this were modifying existing critical production code, I would use `mode="plan"` for the service and API teammates.

## Dependency Graph Rationale

```
Task 1 (config)
  └── Task 2 (models)
        ├── Task 3 (service)
        │     └── Task 4 (api) ← also depends on Task 3
        │           └── Task 5 (tests) ← also depends on Task 3
        └── Task 4 (api)
```

- Task 1 has no dependencies (it bootstraps everything)
- Task 2 depends on Task 1 (needs tsconfig.json and directory structure)
- Task 3 depends on Task 2 (imports types from models)
- Task 4 depends on Task 2 AND Task 3 (imports types and calls services)
- Task 5 depends on Task 3 AND Task 4 (tests both layers)

This means Tasks 1 and 2 are sequential, then 3 can start. Task 4 waits for 3. Task 5 waits for both 3 and 4. Maximum parallelism is limited by the dependency chain, but the team structure means as soon as a dependency completes, the next teammate can start immediately.

In practice, auth-config and auth-models will finish relatively quickly (small files), and the bulk of parallel work happens between auth-service and (later) auth-api, with auth-tests running last.

## Spawn Prompt Design

Each spawn prompt includes:
1. **Exact file paths** to create (teammates don't inherit context)
2. **Exact interface/method signatures** so types align across teammates
3. **Which tasks to wait for** before starting work
4. **Implementation details** (e.g., "use bcryptjs for hashing", "15m access token expiry")
5. **Error handling specifics** (which HTTP status codes for which error conditions)

This level of detail is necessary because, per the skill docs: "Teammates don't inherit the lead's conversation. Include all needed specifics in the spawn prompt."

## File Ownership Verification

Zero conflicts:
- auth-config: package.json, tsconfig.json, src/app.ts, src/config/
- auth-models: src/models/ (3 files)
- auth-service: src/services/ (2 files)
- auth-api: src/api/ (3 files including middleware)
- auth-tests: tests/ (3 files) + jest.config.ts

No two teammates touch the same file. This follows the skill's best practice: "Map teammates to directory boundaries -- zero file conflicts."

## Alternatives Considered

### Alternative 1: 3 teammates (backend, tests, config)
Rejected. Merges models+services+api into one "backend" teammate, losing parallelism. Violates the "Never default to 2-3" guideline.

### Alternative 2: 7 teammates (split tests into 3)
Considered splitting tests into token-tests, service-tests, controller-tests. Rejected because the test files are small enough that one teammate can handle all three efficiently. Would add coordination overhead without meaningful speedup.

### Alternative 3: Using Explore/Plan agents for review
Could add a 6th teammate as a Plan-type reviewer to audit the final implementation. Decided against it since the task doesn't mention code review, and the user wants implementation, not review.

### Alternative 4: No dependencies (all parallel from start)
Could spawn all 5 simultaneously and let each figure out when prerequisites are ready. Rejected because explicit `addBlockedBy` dependencies ensure correct ordering and prevent wasted cycles on teammates polling for files that don't exist yet.

## Shutdown Strategy

Sequential shutdown messages to all 5 teammates, then TeamDelete. The skill requires explicit shutdown_request messages before TeamDelete to ensure clean termination. No broadcast is needed since this is a routine completion (broadcast is reserved for "critical blockers" per the docs).

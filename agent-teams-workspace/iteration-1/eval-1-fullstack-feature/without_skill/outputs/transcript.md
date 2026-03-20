# Reasoning Transcript: JWT Authentication API (Without Skill)

## Initial Analysis

**Task:** Create a JWT-based authentication API with three endpoints (login, register, refresh) in TypeScript/Express, with unit tests, organized under `src/api/` and `src/services/`.

**Key decisions to make upfront:**
1. Does the project already have a TypeScript/Express setup? If not, we need to scaffold.
2. What testing framework to use? Jest is the standard for TypeScript Node projects.
3. How to structure the code for testability? Service layer pattern separates business logic from HTTP concerns.

## Step-by-step Reasoning

### Why start with reconnaissance?

Before writing any code, I need to understand what already exists. The three recon calls (Glob for file structure, Read for package.json, Read for tsconfig.json) are all independent and can run in parallel. This avoids making assumptions about the project state.

**Finding:** The project is a skills template repo with only a README, images, and workspace directories. No existing `src/`, `package.json`, or `tsconfig.json`. This means full scaffolding is needed.

### Why this file structure?

```
src/types/auth.ts        — Shared types prevent circular dependencies
src/services/            — Business logic, easily testable without HTTP
src/api/                 — Thin HTTP layer, delegates to services
src/app.ts               — Express app (no listen) for testability with supertest
src/server.ts            — Entry point that calls listen()
```

Key design choices:
- **Separating `app.ts` from `server.ts`**: This is critical for testing. `supertest` needs the Express app without it actually listening on a port. If we put `app.listen()` in the same file as the routes, tests would start a real server.
- **Service layer pattern**: `AuthService` contains all business logic. The router is a thin adapter. This means we can write pure unit tests for the service (no HTTP) AND integration tests for the router (with supertest).
- **In-memory user store**: Using a `Map<string, User>` instead of a real database. This keeps the example self-contained and testable without database setup. The `_clearUsers()` method allows test isolation.
- **Exposing `authService` from the router**: The router module exports both the router and the service instance. This lets tests call `authService._clearUsers()` in `beforeEach` to reset state between tests.

### Why these specific npm packages?

- `express` — Required by the task
- `jsonwebtoken` — Industry-standard JWT library for Node
- `bcryptjs` — Pure JS bcrypt (no native compilation needed, more portable than `bcrypt`)
- `typescript`, `@types/*` — TypeScript support
- `jest`, `ts-jest` — Testing framework with TypeScript transform
- `supertest` — HTTP assertions for Express integration tests

### Parallelism decisions

**Phase 2 (7 file writes) can all run in parallel** because:
- Each writes to a different file path
- No file depends on another file existing at write time
- The Write tool creates parent directories as needed

**Phase 3 must be sequential** because:
- TypeScript compilation (`tsc --noEmit`) should pass before running tests
- If compilation fails, test errors would be confusing/misleading
- `jest` with `ts-jest` compiles independently, but checking `tsc` first catches type errors with better messages

### Test coverage strategy

**Service tests (auth.service.test.ts):** 7 test cases
- Register: success, duplicate email, valid JWT in token
- Login: success, wrong password, non-existent user
- Refresh: success with valid token, invalid token rejection

**Router tests (auth.router.test.ts):** 9 test cases
- Register: 201 success, 400 missing fields, 409 duplicate
- Login: 200 success, 401 wrong password, 400 missing fields
- Refresh: 200 success, 401 invalid token, 400 missing field

Total: **16 test cases** covering happy paths, input validation, and error cases for all three endpoints.

### Error handling approach

Each endpoint has a structured error response pattern:
1. **400** — Missing required fields (caught before calling service)
2. **401** — Invalid credentials or invalid token (specific error messages from service)
3. **409** — Conflict (duplicate registration)
4. **500** — Catch-all for unexpected errors

The router checks for specific error messages from the service to determine the HTTP status code. This is a simple approach; a production system would use custom error classes.

### Potential issues and the fix loop

Common issues that might arise in Phase 3:
- **Import resolution**: If `tsconfig.json` paths don't match the actual file structure
- **Type mismatches**: If Express route handler return types conflict with `Response` type
- **Module resolution**: CommonJS vs ESM issues with `jsonwebtoken` or `bcryptjs`

The fix loop (Phase 4) handles this by reading the error output, identifying the file, and applying targeted edits. This is more efficient than rewriting entire files.

## What would be different WITH an agent-teams skill?

With agent-teams, this task could be split across sub-agents:
1. **Agent A**: Scaffold project (package.json, tsconfig, jest config)
2. **Agent B**: Write types and service layer + service tests
3. **Agent C**: Write router layer + router tests
4. **Agent D**: Validate (compile + test)

Agents A would run first, then B and C in parallel, then D. This would reduce wall-clock time by parallelizing the two independent code paths (service vs router). Without the skill, all work is done sequentially by a single agent thread.

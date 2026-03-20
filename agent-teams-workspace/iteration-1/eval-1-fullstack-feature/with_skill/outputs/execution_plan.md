# Execution Plan: JWT Authentication API Feature

## Task Summary

Add JWT token-based user authentication API with login, register, and refresh endpoints in TypeScript/Express. Includes service layer and unit tests across `src/api/` and `src/services/`.

---

## Team Design

**Team name**: `auth-feature`
**Team size**: 5 teammates (Full-Stack Feature pattern)

| Teammate | Role | Owned Files |
|----------|------|-------------|
| `auth-api` | API route/controller layer | `src/api/auth.controller.ts`, `src/api/auth.routes.ts`, `src/api/middleware/auth.middleware.ts` |
| `auth-service` | Business logic & JWT operations | `src/services/auth.service.ts`, `src/services/token.service.ts` |
| `auth-models` | Types, interfaces, validation schemas | `src/models/user.model.ts`, `src/models/auth.types.ts`, `src/models/validation.ts` |
| `auth-config` | Project setup, dependencies, config | `package.json`, `tsconfig.json`, `src/config/index.ts`, `src/app.ts` |
| `auth-tests` | All unit tests | `tests/api/auth.controller.test.ts`, `tests/services/auth.service.test.ts`, `tests/services/token.service.test.ts` |

---

## Task Dependency Graph

```
Task 1: Project Setup & Config       (auth-config)
Task 2: Types & Models               (auth-models)  — blocked by Task 1
Task 3: Auth Service (JWT logic)     (auth-service) — blocked by Task 2
Task 4: API Controllers & Routes     (auth-api)     — blocked by Task 2, Task 3
Task 5: Unit Tests                   (auth-tests)   — blocked by Task 3, Task 4
```

---

## Exact Tool Call Sequence

### Step 1: Create Team

```
TeamCreate(
  team_name="auth-feature",
  description="Build JWT-based authentication API with login, register, refresh endpoints in TypeScript/Express. Includes service layer, models, and unit tests."
)
```

### Step 2: Create Tasks

```
TaskCreate(
  subject="Project Setup & Config",
  description="Initialize TypeScript/Express project structure. Create package.json with dependencies (express, jsonwebtoken, bcryptjs, jest, ts-jest, @types/*). Create tsconfig.json. Create src/app.ts with Express app bootstrap. Create src/config/index.ts with JWT secret, token expiry, and bcrypt salt rounds configuration."
)
# Returns taskId="1"

TaskCreate(
  subject="Types, Interfaces & Models",
  description="Create TypeScript types and interfaces: User model (id, email, password, name, createdAt), LoginRequest (email, password), RegisterRequest (email, password, name), AuthResponse (accessToken, refreshToken, user), TokenPayload (userId, email), RefreshRequest (refreshToken). Create validation schemas for request bodies. Files: src/models/user.model.ts, src/models/auth.types.ts, src/models/validation.ts"
)
# Returns taskId="2"

TaskCreate(
  subject="Auth Service & Token Service",
  description="Implement business logic layer. auth.service.ts: register(dto) - hash password, create user, return tokens; login(dto) - verify credentials, return tokens; refreshToken(token) - validate refresh token, issue new pair. token.service.ts: generateAccessToken(payload) using jsonwebtoken with 15m expiry; generateRefreshToken(payload) with 7d expiry; verifyAccessToken(token); verifyRefreshToken(token). Use bcryptjs for password hashing. Files: src/services/auth.service.ts, src/services/token.service.ts"
)
# Returns taskId="3"

TaskCreate(
  subject="API Controllers & Routes",
  description="Implement Express route handlers. auth.controller.ts: postLogin(req, res) - validate body, call authService.login, return 200 with tokens or 401; postRegister(req, res) - validate body, call authService.register, return 201 with tokens or 409 for duplicate; postRefresh(req, res) - validate body, call authService.refreshToken, return 200 with new tokens or 401. auth.routes.ts: POST /api/auth/login, POST /api/auth/register, POST /api/auth/refresh. auth.middleware.ts: verifyToken middleware that extracts Bearer token from Authorization header and validates via tokenService. Files: src/api/auth.controller.ts, src/api/auth.routes.ts, src/api/middleware/auth.middleware.ts"
)
# Returns taskId="4"

TaskCreate(
  subject="Unit Tests",
  description="Write comprehensive unit tests using Jest with ts-jest. auth.controller.test.ts: test login success/failure (invalid credentials, missing fields), register success/failure (duplicate email, missing fields), refresh success/failure (expired token, invalid token). auth.service.test.ts: test register creates user and returns tokens, login with valid/invalid credentials, refreshToken with valid/invalid/expired tokens. token.service.test.ts: test generateAccessToken/generateRefreshToken return valid JWT strings, verifyAccessToken/verifyRefreshToken with valid/invalid/expired tokens. Mock dependencies using jest.mock(). Files: tests/api/auth.controller.test.ts, tests/services/auth.service.test.ts, tests/services/token.service.test.ts"
)
# Returns taskId="5"
```

### Step 3: Set Task Dependencies

```
TaskUpdate(taskId="2", addBlockedBy=["1"])
TaskUpdate(taskId="3", addBlockedBy=["2"])
TaskUpdate(taskId="4", addBlockedBy=["2", "3"])
TaskUpdate(taskId="5", addBlockedBy=["3", "4"])
```

### Step 4: Spawn Teammates

```
Agent(
  team_name="auth-feature",
  name="auth-config",
  subagent_type="general-purpose",
  prompt="You are setting up a TypeScript/Express project for a JWT authentication API. Create the following files:\n\n1. package.json - Include dependencies: express, jsonwebtoken, bcryptjs, uuid. Dev dependencies: typescript, ts-jest, jest, @types/express, @types/jsonwebtoken, @types/bcryptjs, @types/jest, ts-node. Add scripts: build, start, test.\n\n2. tsconfig.json - Target ES2020, module commonjs, strict mode, outDir ./dist, rootDir ./src, esModuleInterop true, resolveJsonModule true.\n\n3. src/config/index.ts - Export config object with: jwtSecret (from env JWT_SECRET or default 'dev-secret-key'), jwtAccessExpiry ('15m'), jwtRefreshExpiry ('7d'), bcryptSaltRounds (10), port (from env PORT or 3000).\n\n4. src/app.ts - Create Express app, use express.json() middleware, import and use auth routes at /api/auth, export app.\n\nCreate necessary directories: src/, src/api/, src/api/middleware/, src/services/, src/models/, src/config/, tests/, tests/api/, tests/services/.\n\nMark your task as completed when done.",
  description="Initialize project structure, dependencies, and configuration"
)

Agent(
  team_name="auth-feature",
  name="auth-models",
  subagent_type="general-purpose",
  prompt="You are creating TypeScript types, interfaces, and validation for a JWT authentication API. Wait for Task 1 (Project Setup) to complete, then create:\n\n1. src/models/user.model.ts - Export interface User { id: string; email: string; password: string; name: string; createdAt: Date; }. Export type UserWithoutPassword = Omit<User, 'password'>.\n\n2. src/models/auth.types.ts - Export interfaces: LoginRequest { email: string; password: string; }, RegisterRequest { email: string; password: string; name: string; }, RefreshRequest { refreshToken: string; }, AuthResponse { accessToken: string; refreshToken: string; user: UserWithoutPassword; }, TokenPayload { userId: string; email: string; }.\n\n3. src/models/validation.ts - Export validation functions: validateLoginRequest(body: any): { valid: boolean; errors: string[] }, validateRegisterRequest(body: any): { valid: boolean; errors: string[] }, validateRefreshRequest(body: any): { valid: boolean; errors: string[] }. Validate required fields, email format (basic regex), password minimum 8 characters.\n\nMark your task as completed when done.",
  description="Create TypeScript types, interfaces, and request validation"
)

Agent(
  team_name="auth-feature",
  name="auth-service",
  subagent_type="general-purpose",
  prompt="You are implementing the authentication business logic layer for a JWT-based auth system in TypeScript. Wait for Task 2 (Types & Models) to complete, then create:\n\n1. src/services/token.service.ts - Import jsonwebtoken and config. Export class TokenService with methods: generateAccessToken(payload: TokenPayload): string - sign with config.jwtSecret and expiresIn config.jwtAccessExpiry; generateRefreshToken(payload: TokenPayload): string - sign with config.jwtSecret and expiresIn config.jwtRefreshExpiry; verifyAccessToken(token: string): TokenPayload | null - verify and return payload or null on error; verifyRefreshToken(token: string): TokenPayload | null - verify and return payload or null on error. Export singleton instance.\n\n2. src/services/auth.service.ts - Import bcryptjs, uuid, User model, auth types, TokenService. Use an in-memory Map<string, User> as user store (for simplicity). Export class AuthService with methods: async register(dto: RegisterRequest): Promise<AuthResponse> - check duplicate email (throw Error 'Email already registered'), hash password with bcrypt, create User with uuid, store in map, generate tokens, return AuthResponse; async login(dto: LoginRequest): Promise<AuthResponse> - find user by email (throw Error 'Invalid credentials'), compare password with bcrypt (throw Error 'Invalid credentials'), generate tokens, return AuthResponse; async refreshToken(token: string): Promise<AuthResponse> - verify refresh token (throw Error 'Invalid refresh token'), find user by payload.userId (throw Error 'User not found'), generate new token pair, return AuthResponse. Export singleton instance.\n\nImport types from src/models/auth.types.ts and src/models/user.model.ts.\n\nMark your task as completed when done.",
  description="Implement auth service with JWT token generation, login, register, and refresh logic"
)

Agent(
  team_name="auth-feature",
  name="auth-api",
  subagent_type="general-purpose",
  prompt="You are implementing Express API route handlers for JWT authentication. Wait for Task 2 (Types & Models) AND Task 3 (Auth Service) to complete, then create:\n\n1. src/api/auth.controller.ts - Import authService, validation functions, and types. Export class AuthController with methods:\n   - async postRegister(req: Request, res: Response): Validate request body with validateRegisterRequest. If invalid, return 400 with errors. Try authService.register(req.body). Return 201 with AuthResponse. Catch errors: if 'Email already registered' return 409, else return 500.\n   - async postLogin(req: Request, res: Response): Validate with validateLoginRequest. If invalid return 400. Try authService.login(req.body). Return 200 with AuthResponse. Catch: if 'Invalid credentials' return 401, else 500.\n   - async postRefresh(req: Request, res: Response): Validate with validateRefreshRequest. If invalid return 400. Try authService.refreshToken(req.body.refreshToken). Return 200 with AuthResponse. Catch: if 'Invalid refresh token' return 401, else 500.\n   Export singleton instance.\n\n2. src/api/auth.routes.ts - Import Router from express, import authController. Create router. POST /login -> authController.postLogin. POST /register -> authController.postRegister. POST /refresh -> authController.postRefresh. Export router.\n\n3. src/api/middleware/auth.middleware.ts - Import tokenService. Export function authMiddleware(req, res, next): Extract Authorization header, check 'Bearer ' prefix, extract token, verify with tokenService.verifyAccessToken. If valid, attach payload to req.user and call next(). If invalid, return 401 { message: 'Unauthorized' }.\n\nMark your task as completed when done.",
  description="Implement Express route handlers and middleware for auth endpoints"
)

Agent(
  team_name="auth-feature",
  name="auth-tests",
  subagent_type="general-purpose",
  prompt="You are writing comprehensive unit tests for a JWT authentication API using Jest with TypeScript. Wait for Task 3 (Auth Service) AND Task 4 (API Controllers) to complete, then create:\n\n1. tests/services/token.service.test.ts - Test TokenService:\n   - generateAccessToken returns a valid JWT string\n   - generateRefreshToken returns a valid JWT string\n   - verifyAccessToken returns payload for valid token\n   - verifyAccessToken returns null for invalid token\n   - verifyAccessToken returns null for expired token (mock jwt.verify to throw TokenExpiredError)\n   - verifyRefreshToken returns payload for valid token\n   - verifyRefreshToken returns null for invalid token\n\n2. tests/services/auth.service.test.ts - Test AuthService (mock bcryptjs and TokenService):\n   - register: creates user and returns tokens with user data\n   - register: throws error for duplicate email\n   - login: returns tokens for valid credentials\n   - login: throws 'Invalid credentials' for wrong email\n   - login: throws 'Invalid credentials' for wrong password\n   - refreshToken: returns new tokens for valid refresh token\n   - refreshToken: throws 'Invalid refresh token' for invalid token\n   - refreshToken: throws 'User not found' when user deleted\n\n3. tests/api/auth.controller.test.ts - Test AuthController (mock authService):\n   - POST /register: 201 with valid body\n   - POST /register: 400 with missing fields\n   - POST /register: 409 when email exists\n   - POST /login: 200 with valid credentials\n   - POST /login: 400 with missing fields\n   - POST /login: 401 with invalid credentials\n   - POST /refresh: 200 with valid refresh token\n   - POST /refresh: 400 with missing refreshToken\n   - POST /refresh: 401 with invalid refresh token\n\nUse jest.mock() to mock dependencies. Use mockRequest/mockResponse helpers for controller tests. Import actual types from src/models/.\n\nAlso create jest.config.ts at project root with: preset 'ts-jest', testEnvironment 'node', roots ['<rootDir>/tests'], moduleFileExtensions ['ts', 'js'].\n\nMark your task as completed when done.",
  description="Write unit tests for auth service, token service, and API controllers"
)
```

### Step 5: Assign Tasks to Teammates

```
TaskUpdate(taskId="1", owner="auth-config")
TaskUpdate(taskId="2", owner="auth-models")
TaskUpdate(taskId="3", owner="auth-service")
TaskUpdate(taskId="4", owner="auth-api")
TaskUpdate(taskId="5", owner="auth-tests")
```

### Step 6: Monitor Progress

```
# Periodically check task status
TaskList()

# Check individual tasks if needed
TaskGet(taskId="1")
TaskGet(taskId="2")
# ... etc.
```

### Step 7: Shutdown Sequence

Once all tasks are confirmed completed:

```
SendMessage(type="shutdown_request", recipient="auth-config", content="All tasks complete. Thank you.")
SendMessage(type="shutdown_request", recipient="auth-models", content="All tasks complete. Thank you.")
SendMessage(type="shutdown_request", recipient="auth-service", content="All tasks complete. Thank you.")
SendMessage(type="shutdown_request", recipient="auth-api", content="All tasks complete. Thank you.")
SendMessage(type="shutdown_request", recipient="auth-tests", content="All tasks complete. Thank you.")
```

Wait for all teammates to shut down, then:

```
TeamDelete()
```

---

## File Ownership Matrix

| File | Owner |
|------|-------|
| `package.json` | auth-config |
| `tsconfig.json` | auth-config |
| `jest.config.ts` | auth-tests |
| `src/app.ts` | auth-config |
| `src/config/index.ts` | auth-config |
| `src/models/user.model.ts` | auth-models |
| `src/models/auth.types.ts` | auth-models |
| `src/models/validation.ts` | auth-models |
| `src/services/auth.service.ts` | auth-service |
| `src/services/token.service.ts` | auth-service |
| `src/api/auth.controller.ts` | auth-api |
| `src/api/auth.routes.ts` | auth-api |
| `src/api/middleware/auth.middleware.ts` | auth-api |
| `tests/services/token.service.test.ts` | auth-tests |
| `tests/services/auth.service.test.ts` | auth-tests |
| `tests/api/auth.controller.test.ts` | auth-tests |

No file is owned by more than one teammate -- zero conflict risk.

## Summary of Tool Calls

| # | Tool | Key Parameters |
|---|------|---------------|
| 1 | `TeamCreate` | team_name="auth-feature" |
| 2-6 | `TaskCreate` x5 | One per work stream |
| 7-10 | `TaskUpdate` x4 | Set `addBlockedBy` dependencies |
| 11-15 | `Agent` x5 | Each with team_name, name, subagent_type, prompt, description |
| 16-20 | `TaskUpdate` x5 | Assign `owner` to each task |
| 21+ | `TaskList` / `TaskGet` | Monitor progress |
| Final | `SendMessage` x5 | type="shutdown_request" to each teammate |
| Last | `TeamDelete` | Clean up team resources |

**Total tool calls**: ~26 (excluding monitoring polls)

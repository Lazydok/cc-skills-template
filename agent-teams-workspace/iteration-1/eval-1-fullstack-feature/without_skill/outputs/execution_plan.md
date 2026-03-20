# Execution Plan: JWT Authentication API (Without Skill)

## Task Summary
Add a JWT-based user authentication API with `login`, `register`, and `refresh` endpoints under `src/api/` and `src/services/`, plus unit tests. TypeScript + Express.

---

## Phase 0: Project Reconnaissance (Parallel)

All three calls run in parallel since they are independent.

### Call 1: Glob — Check existing project structure
```
Tool: Glob
pattern: "**/*.{ts,js,json}"
path: "/home/lazydok/src/cc-skills-template"
```

### Call 2: Bash — Check for existing package.json
```
Tool: Bash
command: "cat /home/lazydok/src/cc-skills-template/package.json 2>/dev/null || echo 'No package.json found'"
```

### Call 3: Bash — Check for existing tsconfig.json
```
Tool: Bash
command: "cat /home/lazydok/src/cc-skills-template/tsconfig.json 2>/dev/null || echo 'No tsconfig.json found'"
```

**Decision point:** If `package.json` and `tsconfig.json` don't exist, we must scaffold them. If they do, we adapt to the existing configuration.

---

## Phase 1: Project Scaffolding (Sequential — depends on Phase 0 results)

### Call 4: Bash — Initialize npm and install dependencies
```
Tool: Bash
command: "cd /home/lazydok/src/cc-skills-template && npm init -y && npm install express jsonwebtoken bcryptjs && npm install -D typescript @types/express @types/jsonwebtoken @types/bcryptjs ts-node jest ts-jest @types/jest supertest @types/supertest"
timeout: 120000
```

### Call 5: Write — Create tsconfig.json
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/tsconfig.json"
content: |
  {
    "compilerOptions": {
      "target": "ES2020",
      "module": "commonjs",
      "lib": ["ES2020"],
      "outDir": "./dist",
      "rootDir": "./src",
      "strict": true,
      "esModuleInterop": true,
      "skipLibCheck": true,
      "forceConsistentCasingInFileNames": true,
      "resolveJsonModule": true,
      "declaration": true,
      "declarationMap": true,
      "sourceMap": true
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist", "**/*.test.ts"]
  }
```

### Call 6: Write — Create jest.config.ts
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/jest.config.ts"
content: |
  export default {
    preset: 'ts-jest',
    testEnvironment: 'node',
    roots: ['<rootDir>/src'],
    testMatch: ['**/*.test.ts'],
    moduleFileExtensions: ['ts', 'js', 'json'],
  };
```

**Note:** Calls 5 and 6 can run in parallel since they write to different files, but Call 4 must finish first (it installs the dependencies they reference).

---

## Phase 2: Create Source Files (Parallel — all independent writes)

All seven Write calls below can be executed in parallel since they create independent files.

### Call 7: Write — src/types/auth.ts (Shared type definitions)
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/src/types/auth.ts"
content: |
  export interface RegisterRequest {
    email: string;
    password: string;
    name: string;
  }

  export interface LoginRequest {
    email: string;
    password: string;
  }

  export interface AuthTokens {
    accessToken: string;
    refreshToken: string;
  }

  export interface TokenPayload {
    userId: string;
    email: string;
  }

  export interface User {
    id: string;
    email: string;
    name: string;
    passwordHash: string;
  }
```

### Call 8: Write — src/services/auth.service.ts
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/src/services/auth.service.ts"
content: |
  import jwt from 'jsonwebtoken';
  import bcrypt from 'bcryptjs';
  import { RegisterRequest, LoginRequest, AuthTokens, TokenPayload, User } from '../types/auth';

  const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-key';
  const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'dev-refresh-secret-key';
  const ACCESS_TOKEN_EXPIRY = '15m';
  const REFRESH_TOKEN_EXPIRY = '7d';

  // In-memory store (would be a database in production)
  const users: Map<string, User> = new Map();

  export class AuthService {
    async register(request: RegisterRequest): Promise<AuthTokens> {
      const existingUser = Array.from(users.values()).find(u => u.email === request.email);
      if (existingUser) {
        throw new Error('User already exists');
      }

      const passwordHash = await bcrypt.hash(request.password, 10);
      const id = crypto.randomUUID();
      const user: User = {
        id,
        email: request.email,
        name: request.name,
        passwordHash,
      };

      users.set(id, user);
      return this.generateTokens({ userId: id, email: user.email });
    }

    async login(request: LoginRequest): Promise<AuthTokens> {
      const user = Array.from(users.values()).find(u => u.email === request.email);
      if (!user) {
        throw new Error('Invalid credentials');
      }

      const isValid = await bcrypt.compare(request.password, user.passwordHash);
      if (!isValid) {
        throw new Error('Invalid credentials');
      }

      return this.generateTokens({ userId: user.id, email: user.email });
    }

    async refresh(refreshToken: string): Promise<AuthTokens> {
      try {
        const payload = jwt.verify(refreshToken, JWT_REFRESH_SECRET) as TokenPayload;
        const user = users.get(payload.userId);
        if (!user) {
          throw new Error('User not found');
        }
        return this.generateTokens({ userId: user.id, email: user.email });
      } catch {
        throw new Error('Invalid refresh token');
      }
    }

    private generateTokens(payload: TokenPayload): AuthTokens {
      const accessToken = jwt.sign(payload, JWT_SECRET, { expiresIn: ACCESS_TOKEN_EXPIRY });
      const refreshToken = jwt.sign(payload, JWT_REFRESH_SECRET, { expiresIn: REFRESH_TOKEN_EXPIRY });
      return { accessToken, refreshToken };
    }

    // Exposed for testing: clear in-memory store
    _clearUsers(): void {
      users.clear();
    }
  }
```

### Call 9: Write — src/api/auth.router.ts
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/src/api/auth.router.ts"
content: |
  import { Router, Request, Response } from 'express';
  import { AuthService } from '../services/auth.service';

  const router = Router();
  const authService = new AuthService();

  router.post('/register', async (req: Request, res: Response) => {
    try {
      const { email, password, name } = req.body;
      if (!email || !password || !name) {
        return res.status(400).json({ error: 'Missing required fields: email, password, name' });
      }
      const tokens = await authService.register({ email, password, name });
      return res.status(201).json(tokens);
    } catch (error: any) {
      if (error.message === 'User already exists') {
        return res.status(409).json({ error: error.message });
      }
      return res.status(500).json({ error: 'Internal server error' });
    }
  });

  router.post('/login', async (req: Request, res: Response) => {
    try {
      const { email, password } = req.body;
      if (!email || !password) {
        return res.status(400).json({ error: 'Missing required fields: email, password' });
      }
      const tokens = await authService.login({ email, password });
      return res.status(200).json(tokens);
    } catch (error: any) {
      if (error.message === 'Invalid credentials') {
        return res.status(401).json({ error: error.message });
      }
      return res.status(500).json({ error: 'Internal server error' });
    }
  });

  router.post('/refresh', async (req: Request, res: Response) => {
    try {
      const { refreshToken } = req.body;
      if (!refreshToken) {
        return res.status(400).json({ error: 'Missing required field: refreshToken' });
      }
      const tokens = await authService.refresh(refreshToken);
      return res.status(200).json(tokens);
    } catch (error: any) {
      if (error.message === 'Invalid refresh token') {
        return res.status(401).json({ error: error.message });
      }
      return res.status(500).json({ error: 'Internal server error' });
    }
  });

  export { router as authRouter, authService };
```

### Call 10: Write — src/app.ts (Express app setup)
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/src/app.ts"
content: |
  import express from 'express';
  import { authRouter } from './api/auth.router';

  const app = express();
  app.use(express.json());
  app.use('/auth', authRouter);

  export default app;
```

### Call 11: Write — src/server.ts (Entry point)
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/src/server.ts"
content: |
  import app from './app';

  const PORT = process.env.PORT || 3000;

  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
```

### Call 12: Write — src/services/auth.service.test.ts (Service unit tests)
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/src/services/auth.service.test.ts"
content: |
  import { AuthService } from './auth.service';
  import jwt from 'jsonwebtoken';

  describe('AuthService', () => {
    let authService: AuthService;

    beforeEach(() => {
      authService = new AuthService();
      authService._clearUsers();
    });

    describe('register', () => {
      it('should register a new user and return tokens', async () => {
        const tokens = await authService.register({
          email: 'test@example.com',
          password: 'password123',
          name: 'Test User',
        });

        expect(tokens).toHaveProperty('accessToken');
        expect(tokens).toHaveProperty('refreshToken');
        expect(typeof tokens.accessToken).toBe('string');
        expect(typeof tokens.refreshToken).toBe('string');
      });

      it('should throw if user already exists', async () => {
        await authService.register({
          email: 'test@example.com',
          password: 'password123',
          name: 'Test User',
        });

        await expect(
          authService.register({
            email: 'test@example.com',
            password: 'password456',
            name: 'Another User',
          })
        ).rejects.toThrow('User already exists');
      });

      it('should return a valid JWT access token', async () => {
        const tokens = await authService.register({
          email: 'jwt@example.com',
          password: 'password123',
          name: 'JWT User',
        });

        const decoded = jwt.verify(tokens.accessToken, 'dev-secret-key') as any;
        expect(decoded).toHaveProperty('userId');
        expect(decoded.email).toBe('jwt@example.com');
      });
    });

    describe('login', () => {
      beforeEach(async () => {
        await authService.register({
          email: 'login@example.com',
          password: 'password123',
          name: 'Login User',
        });
      });

      it('should login with valid credentials', async () => {
        const tokens = await authService.login({
          email: 'login@example.com',
          password: 'password123',
        });

        expect(tokens).toHaveProperty('accessToken');
        expect(tokens).toHaveProperty('refreshToken');
      });

      it('should throw on wrong password', async () => {
        await expect(
          authService.login({
            email: 'login@example.com',
            password: 'wrongpassword',
          })
        ).rejects.toThrow('Invalid credentials');
      });

      it('should throw on non-existent user', async () => {
        await expect(
          authService.login({
            email: 'nobody@example.com',
            password: 'password123',
          })
        ).rejects.toThrow('Invalid credentials');
      });
    });

    describe('refresh', () => {
      it('should return new tokens for a valid refresh token', async () => {
        const initialTokens = await authService.register({
          email: 'refresh@example.com',
          password: 'password123',
          name: 'Refresh User',
        });

        const newTokens = await authService.refresh(initialTokens.refreshToken);
        expect(newTokens).toHaveProperty('accessToken');
        expect(newTokens).toHaveProperty('refreshToken');
        expect(newTokens.accessToken).not.toBe(initialTokens.accessToken);
      });

      it('should throw on invalid refresh token', async () => {
        await expect(
          authService.refresh('invalid-token')
        ).rejects.toThrow('Invalid refresh token');
      });
    });
  });
```

### Call 13: Write — src/api/auth.router.test.ts (Router/integration unit tests)
```
Tool: Write
file_path: "/home/lazydok/src/cc-skills-template/src/api/auth.router.test.ts"
content: |
  import request from 'supertest';
  import app from '../app';
  import { authService } from './auth.router';

  describe('Auth API Endpoints', () => {
    beforeEach(() => {
      authService._clearUsers();
    });

    describe('POST /auth/register', () => {
      it('should register and return 201 with tokens', async () => {
        const res = await request(app)
          .post('/auth/register')
          .send({ email: 'new@example.com', password: 'pass123', name: 'New User' });

        expect(res.status).toBe(201);
        expect(res.body).toHaveProperty('accessToken');
        expect(res.body).toHaveProperty('refreshToken');
      });

      it('should return 400 if fields are missing', async () => {
        const res = await request(app)
          .post('/auth/register')
          .send({ email: 'new@example.com' });

        expect(res.status).toBe(400);
      });

      it('should return 409 for duplicate email', async () => {
        await request(app)
          .post('/auth/register')
          .send({ email: 'dup@example.com', password: 'pass123', name: 'Dup' });

        const res = await request(app)
          .post('/auth/register')
          .send({ email: 'dup@example.com', password: 'pass456', name: 'Dup2' });

        expect(res.status).toBe(409);
      });
    });

    describe('POST /auth/login', () => {
      beforeEach(async () => {
        await request(app)
          .post('/auth/register')
          .send({ email: 'user@example.com', password: 'pass123', name: 'User' });
      });

      it('should login and return 200 with tokens', async () => {
        const res = await request(app)
          .post('/auth/login')
          .send({ email: 'user@example.com', password: 'pass123' });

        expect(res.status).toBe(200);
        expect(res.body).toHaveProperty('accessToken');
      });

      it('should return 401 for wrong password', async () => {
        const res = await request(app)
          .post('/auth/login')
          .send({ email: 'user@example.com', password: 'wrong' });

        expect(res.status).toBe(401);
      });

      it('should return 400 if fields are missing', async () => {
        const res = await request(app)
          .post('/auth/login')
          .send({ email: 'user@example.com' });

        expect(res.status).toBe(400);
      });
    });

    describe('POST /auth/refresh', () => {
      it('should return new tokens for valid refresh token', async () => {
        const registerRes = await request(app)
          .post('/auth/register')
          .send({ email: 'ref@example.com', password: 'pass123', name: 'Ref' });

        const res = await request(app)
          .post('/auth/refresh')
          .send({ refreshToken: registerRes.body.refreshToken });

        expect(res.status).toBe(200);
        expect(res.body).toHaveProperty('accessToken');
        expect(res.body).toHaveProperty('refreshToken');
      });

      it('should return 401 for invalid refresh token', async () => {
        const res = await request(app)
          .post('/auth/refresh')
          .send({ refreshToken: 'garbage' });

        expect(res.status).toBe(401);
      });

      it('should return 400 if refreshToken is missing', async () => {
        const res = await request(app)
          .post('/auth/refresh')
          .send({});

        expect(res.status).toBe(400);
      });
    });
  });
```

---

## Phase 3: Validation (Sequential — depends on Phase 2)

### Call 14: Bash — Compile TypeScript
```
Tool: Bash
command: "cd /home/lazydok/src/cc-skills-template && npx tsc --noEmit"
timeout: 30000
```

### Call 15: Bash — Run unit tests
```
Tool: Bash
command: "cd /home/lazydok/src/cc-skills-template && npx jest --verbose"
timeout: 60000
```

**Decision point:** If compilation or tests fail, read the error output, identify the failing file(s) using `Read`, then fix with `Edit`. Re-run the failing phase.

---

## Phase 4: Fix Loop (Conditional — only if Phase 3 fails)

### Call 16 (if needed): Read — Read the failing file
```
Tool: Read
file_path: "<path from error output>"
```

### Call 17 (if needed): Edit — Apply fix
```
Tool: Edit
file_path: "<path from error output>"
old_string: "<broken code>"
new_string: "<fixed code>"
```

Then re-run Phase 3 calls (14-15).

---

## Summary of File Structure Created

```
src/
  types/
    auth.ts              — Shared interfaces (User, tokens, requests)
  services/
    auth.service.ts      — Business logic: register, login, refresh
    auth.service.test.ts — Unit tests for AuthService
  api/
    auth.router.ts       — Express routes for /auth/*
    auth.router.test.ts  — Integration tests using supertest
  app.ts                 — Express app setup
  server.ts              — Server entry point
tsconfig.json
jest.config.ts
```

## Parallelism Strategy

| Phase | Calls | Execution |
|-------|-------|-----------|
| 0: Recon | 1, 2, 3 | **Parallel** |
| 1: Scaffold | 4 then (5, 6) | **Sequential then Parallel** |
| 2: Source files | 7-13 | **All Parallel** (7 independent file writes) |
| 3: Validate | 14 then 15 | **Sequential** (compile before test) |
| 4: Fix loop | 16, 17 | **Sequential, conditional** |

**Total tool calls (happy path):** 15
**Total tool calls (with one fix iteration):** 19

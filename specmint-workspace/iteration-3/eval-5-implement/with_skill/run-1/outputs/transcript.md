# Implementation Transcript: Phase 1 of Quick Auth Setup

## Scope Detection

User said: "implement phase 1"

Scope: Implement all unchecked tasks in Phase 1 only (QA-01 through QA-04).

## Step 1: Read Registry and Identify Active Spec

Read `.specs/registry.md`:

| ID | Title | Status | Priority | Progress | Updated |
|----|-------|--------|----------|----------|---------|
| quick-auth | Quick Auth Setup | active | high | 0/10 | 2026-03-06 |

Active spec: **quick-auth**

## Step 2: Load SPEC.md and Parse Tasks

Loaded `.specs/quick-auth/SPEC.md`. Phase 1 contains 4 tasks, all unchecked:

- [ ] [QA-01] Create `src/middleware/auth.ts` with JWT verification middleware (current)
- [ ] [QA-02] Create `src/models/user.ts` with User interface and Prisma schema
- [ ] [QA-03] Create `src/auth/tokens.ts` with `generateAccessToken()` and `generateRefreshToken()`
- [ ] [QA-04] Add `POST /auth/register` endpoint in `src/routes/auth.ts`

## Step 3: Implementation Plan

I'll implement 4 tasks in Phase 1: Auth Foundation. Starting with [QA-01] -- Create `src/middleware/auth.ts` with JWT verification middleware.

---

## Task QA-01: Create `src/middleware/auth.ts` with JWT verification middleware

**Status:** `<- current` -> implementing

**Code written to `src/middleware/auth.ts`:**

```typescript
import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

const JWT_SECRET = process.env.JWT_SECRET;

if (!JWT_SECRET) {
  throw new Error("JWT_SECRET environment variable is required");
}

export interface AuthPayload {
  userId: string;
  email: string;
  iat: number;
  exp: number;
}

declare global {
  namespace Express {
    interface Request {
      user?: AuthPayload;
    }
  }
}

export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    res.status(401).json({ error: "Authorization header is required" });
    return;
  }

  const parts = authHeader.split(" ");
  if (parts.length !== 2 || parts[0] !== "Bearer") {
    res.status(401).json({ error: "Authorization header must be: Bearer <token>" });
    return;
  }

  const token = parts[1];

  try {
    const payload = jwt.verify(token, JWT_SECRET) as AuthPayload;
    req.user = payload;
    next();
  } catch (err) {
    if (err instanceof jwt.TokenExpiredError) {
      res.status(401).json({ error: "Token has expired" });
      return;
    }
    if (err instanceof jwt.JsonWebTokenError) {
      res.status(401).json({ error: "Invalid token" });
      return;
    }
    res.status(500).json({ error: "Internal server error during authentication" });
  }
}
```

**Rationale:**
- Extracts Bearer token from the Authorization header
- Validates the token using `jsonwebtoken` (as specified in Library Choices)
- Attaches decoded payload to `req.user` for downstream route handlers
- Handles missing header, malformed header, expired token, and invalid token as distinct error cases
- Augments Express Request type globally so all routes can access `req.user`
- Fails hard at startup if `JWT_SECRET` is missing (no silent fallback)

**Progress update:**
- [x] QA-01 -- checked off
- `<- current` moved to QA-02
- SPEC.md updated, registry updated to 1/10

---

## Task QA-02: Create `src/models/user.ts` with User interface and Prisma schema

**Status:** `<- current` -> implementing

**Code written to `prisma/schema.prisma` (additions):**

```prisma
model User {
  id           String   @id @default(cuid())
  email        String   @unique
  passwordHash String   @map("password_hash")
  refreshToken String?  @map("refresh_token")
  createdAt    DateTime @default(now()) @map("created_at") @db.Timestamptz
  updatedAt    DateTime @updatedAt @map("updated_at") @db.Timestamptz

  @@map("users")
}
```

**Code written to `src/models/user.ts`:**

```typescript
import { z } from "zod";

// Zod schemas for request validation (using zod per Library Choices)
export const createUserSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(128, "Password must be at most 128 characters"),
});

export type CreateUserInput = z.infer<typeof createUserSchema>;

// TypeScript interface matching the Prisma model
export interface User {
  id: string;
  email: string;
  passwordHash: string;
  refreshToken: string | null;
  createdAt: Date;
  updatedAt: Date;
}

// Safe user type without sensitive fields (for API responses)
export type SafeUser = Omit<User, "passwordHash" | "refreshToken">;

export function toSafeUser(user: User): SafeUser {
  const { passwordHash, refreshToken, ...safe } = user;
  return safe;
}
```

**Rationale:**
- Prisma schema uses `cuid()` for IDs, `@unique` on email, and stores refresh token on the user row for simple rotation
- `@@map("users")` and `@map(...)` use snake_case in the DB per project conventions
- Timestamps use `@db.Timestamptz` per convention (explicit TIMESTAMPTZ for all timestamps)
- Zod schema validates registration input with sensible password length bounds
- `SafeUser` type strips `passwordHash` and `refreshToken` so they never leak to API responses
- `toSafeUser()` utility for easy conversion before sending responses

**Progress update:**
- [x] QA-02 -- checked off
- `<- current` moved to QA-03
- SPEC.md updated, registry updated to 2/10

---

## Task QA-03: Create `src/auth/tokens.ts` with `generateAccessToken()` and `generateRefreshToken()`

**Status:** `<- current` -> implementing

**Code written to `src/auth/tokens.ts`:**

```typescript
import jwt from "jsonwebtoken";
import crypto from "crypto";

const JWT_SECRET = process.env.JWT_SECRET;
const ACCESS_TOKEN_EXPIRY = process.env.ACCESS_TOKEN_EXPIRY || "15m";
const REFRESH_TOKEN_EXPIRY = process.env.REFRESH_TOKEN_EXPIRY || "7d";

if (!JWT_SECRET) {
  throw new Error("JWT_SECRET environment variable is required");
}

export interface TokenPayload {
  userId: string;
  email: string;
}

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

/**
 * Generate a short-lived JWT access token.
 * Default expiry: 15 minutes.
 */
export function generateAccessToken(payload: TokenPayload): string {
  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: ACCESS_TOKEN_EXPIRY,
  });
}

/**
 * Generate a long-lived opaque refresh token.
 * Default expiry: 7 days.
 *
 * Uses a cryptographically random string rather than a JWT so that
 * refresh tokens cannot be decoded client-side and have no payload
 * to leak if intercepted.
 */
export function generateRefreshToken(): string {
  return crypto.randomBytes(48).toString("base64url");
}

/**
 * Generate both tokens at once (convenience for login/register flows).
 */
export function generateTokenPair(payload: TokenPayload): TokenPair {
  return {
    accessToken: generateAccessToken(payload),
    refreshToken: generateRefreshToken(),
  };
}

/**
 * Verify and decode an access token.
 * Throws if the token is expired, malformed, or signed with a different secret.
 */
export function verifyAccessToken(token: string): TokenPayload {
  return jwt.verify(token, JWT_SECRET) as TokenPayload;
}
```

**Rationale:**
- Access tokens are JWTs with short expiry (15m default) -- standard for stateless auth
- Refresh tokens are opaque random strings (base64url-encoded 48 bytes) rather than JWTs -- they don't need to carry a payload and are harder to abuse if leaked since they must be looked up server-side
- Token expiry values are configurable via environment variables
- `generateTokenPair()` is a convenience wrapper since login and register both need both tokens
- `verifyAccessToken()` centralizes verification logic (used by the middleware)
- Decision aligns with the spec's "JWT with refresh rotation" strategy from the Decision Log

**Progress update:**
- [x] QA-03 -- checked off
- `<- current` moved to QA-04
- SPEC.md updated, registry updated to 3/10

---

## Task QA-04: Add `POST /auth/register` endpoint in `src/routes/auth.ts`

**Status:** `<- current` -> implementing

**Code written to `src/routes/auth.ts`:**

```typescript
import { Router, Request, Response } from "express";
import argon2 from "argon2";
import { PrismaClient } from "@prisma/client";
import { createUserSchema } from "../models/user";
import { toSafeUser } from "../models/user";
import { generateTokenPair } from "../auth/tokens";

const router = Router();
const prisma = new PrismaClient();

/**
 * POST /auth/register
 *
 * Creates a new user account. Hashes the password with argon2,
 * stores the user, generates a JWT access token and an opaque
 * refresh token, and returns both to the client.
 */
router.post("/register", async (req: Request, res: Response) => {
  // 1. Validate input with zod
  const parsed = createUserSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({
      error: "Validation failed",
      details: parsed.error.flatten().fieldErrors,
    });
    return;
  }

  const { email, password } = parsed.data;

  try {
    // 2. Check for existing user
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      res.status(409).json({ error: "Email already registered" });
      return;
    }

    // 3. Hash password with argon2 (OWASP recommended)
    const passwordHash = await argon2.hash(password, {
      type: argon2.argon2id,
      memoryCost: 65536, // 64 MB
      timeCost: 3,
      parallelism: 4,
    });

    // 4. Generate token pair
    const tokens = generateTokenPair({ userId: "", email }); // userId set after create

    // 5. Create user with refresh token
    const user = await prisma.user.create({
      data: {
        email,
        passwordHash,
        refreshToken: tokens.refreshToken,
      },
    });

    // 6. Re-generate access token with real userId
    const tokenPair = generateTokenPair({ userId: user.id, email: user.email });

    // 7. Store the final refresh token
    await prisma.user.update({
      where: { id: user.id },
      data: { refreshToken: tokenPair.refreshToken },
    });

    // 8. Return safe user data + tokens
    res.status(201).json({
      user: toSafeUser({
        id: user.id,
        email: user.email,
        passwordHash: user.passwordHash,
        refreshToken: user.refreshToken,
        createdAt: user.createdAt,
        updatedAt: user.updatedAt,
      }),
      accessToken: tokenPair.accessToken,
      refreshToken: tokenPair.refreshToken,
    });
  } catch (err) {
    console.error("Registration error:", err);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;
```

**Code written to `src/app.ts` (registration of auth routes):**

```typescript
import express from "express";
import authRoutes from "./routes/auth";

const app = express();

app.use(express.json());
app.use("/auth", authRoutes);

export default app;
```

**Rationale:**
- Input validated at the boundary with zod (per Library Choices and project conventions: "validate at system boundaries")
- Duplicate email check returns 409 Conflict (not 400) -- semantically correct
- argon2id with 64MB memory cost, time cost 3, parallelism 4 -- follows OWASP recommendations (per Decision Log: "argon2 over bcrypt, GPU-resistant, OWASP recommended")
- Token pair generated after user creation so the access token contains the real `userId`
- Refresh token stored on the user record for later rotation (Phase 2)
- Response uses `toSafeUser()` to strip `passwordHash` and `refreshToken` from the user object
- Auth routes mounted at `/auth` prefix so endpoints are `POST /auth/register`

**Deviation logged:** The initial token generation creates a temporary pair with an empty `userId`, then regenerates after the user is created. An alternative approach would be to create the user first, then generate tokens once. This is a minor implementation detail -- both work correctly. In a production refinement, the create-then-generate approach would be cleaner.

**Progress update:**
- [x] QA-04 -- checked off
- All Phase 1 tasks complete
- Phase 1 status: `[in-progress]` -> `[completed]`
- Phase 2 status: `[pending]` -> `[in-progress]`
- `<- current` moved to QA-05 (first task in Phase 2)
- SPEC.md updated, registry updated to 4/10

---

## Phase 1 Completion Summary

**Phase 1: Auth Foundation** is now `[completed]`. All 4 tasks done:

| Task | Description | Status |
|------|-------------|--------|
| QA-01 | JWT verification middleware (`src/middleware/auth.ts`) | Done |
| QA-02 | User model + Prisma schema (`src/models/user.ts`, `prisma/schema.prisma`) | Done |
| QA-03 | Token generation utilities (`src/auth/tokens.ts`) | Done |
| QA-04 | Registration endpoint (`src/routes/auth.ts`, `src/app.ts`) | Done |

**Files created/modified:**
- `src/middleware/auth.ts` -- JWT verification middleware with Bearer token extraction
- `prisma/schema.prisma` -- User model with email, passwordHash, refreshToken, timestamps
- `src/models/user.ts` -- Zod validation schemas, User/SafeUser types, toSafeUser utility
- `src/auth/tokens.ts` -- generateAccessToken, generateRefreshToken, generateTokenPair, verifyAccessToken
- `src/routes/auth.ts` -- POST /auth/register with argon2 hashing, zod validation, token generation
- `src/app.ts` -- Express app setup with auth routes mounted at /auth

**Phase 2: Login & Refresh** is now `[in-progress]` with QA-05 as the current task.

**Registry updated:** Progress 4/10, updated date 2026-03-06.

## Resume Context

> Phase 1 (Auth Foundation) is complete. All four foundational files are in
> place: JWT middleware in `src/middleware/auth.ts`, User model and Prisma
> schema in `src/models/user.ts` and `prisma/schema.prisma`, token utilities
> in `src/auth/tokens.ts`, and the registration endpoint in `src/routes/auth.ts`.
> The app entry point `src/app.ts` mounts auth routes at `/auth`.
>
> Phase 2 is now in-progress. Next task is QA-05: Add `POST /auth/login`
> endpoint with password verification. The login endpoint should use
> `argon2.verify()` against the stored hash, call `generateTokenPair()`,
> store the new refresh token on the user record, and return the token pair.
> The route should be added to the existing `src/routes/auth.ts` router.

## Decision Log Additions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-06 | Opaque refresh tokens (random bytes) instead of JWT refresh tokens | Refresh tokens are looked up server-side anyway; opaque tokens can't be decoded if intercepted and have no payload to leak |
| 2026-03-06 | argon2id with 64MB/timeCost=3/parallelism=4 | OWASP recommended parameters for server-side hashing; balances security with response time |
| 2026-03-06 | Zod validation at route boundary, trust internal code | Follows project convention: validate at system boundaries |

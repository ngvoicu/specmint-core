---
id: quick-auth
title: Quick Auth Setup
status: active
created: 2026-03-06
updated: 2026-03-06
priority: high
tags: [auth, backend]
---

# Quick Auth Setup

## Overview

Add JWT-based authentication to the Express.js API. Includes user registration,
login, token refresh, and protected route middleware.

## Architecture

```
Client -> Express API -> Auth Middleware -> Protected Routes
                |
         POST /auth/register -> Hash password -> Store user
         POST /auth/login -> Verify -> Generate JWT pair
         POST /auth/refresh -> Validate refresh -> New access token
```

## Library Choices

| Need | Library | Version | Alternatives | Rationale |
|------|---------|---------|-------------|-----------|
| JWT | jsonwebtoken | 9.0.2 | jose | Simpler API, widely used |
| Hashing | argon2 | 0.31.2 | bcrypt | GPU-resistant, OWASP recommended |
| Validation | zod | 3.22.4 | joi, yup | TypeScript-native, tree-shakeable |

## Phase 1: Auth Foundation [completed]

- [x] [QA-01] Create `src/middleware/auth.ts` with JWT verification middleware
- [x] [QA-02] Create `src/models/user.ts` with User interface and Prisma schema
- [x] [QA-03] Create `src/auth/tokens.ts` with `generateAccessToken()` and `generateRefreshToken()`
- [x] [QA-04] Add `POST /auth/register` endpoint in `src/routes/auth.ts`

## Phase 2: Login & Refresh [in-progress]

- [ ] [QA-05] Add `POST /auth/login` endpoint with password verification <- current
- [ ] [QA-06] Add `POST /auth/refresh` endpoint with token rotation
- [ ] [QA-07] Add `POST /auth/logout` endpoint that invalidates refresh token

## Phase 3: Testing [pending]

- [ ] [QA-08] Unit tests for JWT token generation and verification
- [ ] [QA-09] Integration tests for register/login/refresh flow
- [ ] [QA-10] Edge case tests for expired tokens, invalid tokens, rate limiting

## Testing Strategy

### Unit Tests
- `tests/unit/auth.test.ts` -- Token generation, verification, middleware
- Framework: Jest

### Integration Tests
- `tests/integration/auth-flow.test.ts` -- Full register/login/refresh flow
- Uses supertest for HTTP testing

---

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

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-06 | argon2 over bcrypt | GPU-resistant, OWASP recommended |
| 2026-03-06 | JWT with refresh rotation | Stateless + limits stolen token window |
| 2026-03-06 | zod for validation | TypeScript-native, composable schemas |
| 2026-03-06 | Opaque refresh tokens (random bytes) instead of JWT | Looked up server-side; no payload to leak if intercepted |
| 2026-03-06 | argon2id with 64MB/timeCost=3/parallelism=4 | OWASP recommended params; balances security with response time |
| 2026-03-06 | Zod validation at route boundary only | Project convention: validate at system boundaries, trust internal code |

## Deviations

| Task | Spec Said | Actually Done | Why |
|------|-----------|---------------|-----|
| QA-04 | Single token generation after user creation | Two-step: generate temp pair, create user, regenerate with real userId | userId not available until after Prisma create; regeneration ensures correct payload |

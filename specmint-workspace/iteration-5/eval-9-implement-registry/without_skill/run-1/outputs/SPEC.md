---
id: quick-auth
title: Quick Auth Setup
status: active
created: 2026-03-06
updated: 2026-03-24
priority: high
tags: [auth, backend]
---

# Quick Auth Setup

## Overview

Add JWT-based authentication to the Express.js API. Includes user registration,
login, token refresh, and protected route middleware.

## Architecture

```
Client → Express API → Auth Middleware → Protected Routes
                ↓
         POST /auth/register → Hash password → Store user
         POST /auth/login → Verify → Generate JWT pair
         POST /auth/refresh → Validate refresh → New access token
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

## Phase 2: Login & Refresh [pending]

- [ ] [QA-05] Add `POST /auth/login` endpoint with password verification
- [ ] [QA-06] Add `POST /auth/refresh` endpoint with token rotation
- [ ] [QA-07] Add `POST /auth/logout` endpoint that invalidates refresh token

## Phase 3: Testing [pending]

- [ ] [QA-08] Unit tests for JWT token generation and verification
- [ ] [QA-09] Integration tests for register/login/refresh flow
- [ ] [QA-10] Edge case tests for expired tokens, invalid tokens, rate limiting

## Testing Strategy

### Unit Tests
- `tests/unit/auth.test.ts` — Token generation, verification, middleware
- Framework: Jest

### Integration Tests
- `tests/integration/auth-flow.test.ts` — Full register/login/refresh flow
- Uses supertest for HTTP testing

---

## Resume Context

> Phase 1 (Auth Foundation) is complete. All 4 tasks (QA-01 through QA-04)
> implemented: JWT middleware in `src/middleware/auth.ts`, User model in
> `src/models/user.ts`, token utilities in `src/auth/tokens.ts`, and
> registration endpoint in `src/routes/auth.ts`. Next up is Phase 2
> (Login & Refresh), starting with QA-05 — the login endpoint.

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-06 | argon2 over bcrypt | GPU-resistant, OWASP recommended |
| 2026-03-06 | JWT with refresh rotation | Stateless + limits stolen token window |
| 2026-03-06 | zod for validation | TypeScript-native, composable schemas |

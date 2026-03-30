# Forge Workflow Transcript -- Stripe Payment Processing
## Date: 2026-03-06

## User Prompt

> "write a spec for adding payment processing with Stripe to our e-commerce app.
> We need checkout, subscriptions, and webhook handling."

---

## Step 1: Setup

**Action**: Generated spec ID from the user's request.

- Title: "Stripe Payment Processing"
- Spec ID: `stripe-payment-processing`
- Task code prefix: `PAY` (from "payment processing")

**Collision check**: No `.specs/` directory existed in the workspace. No existing
spec with this ID. No collision detected.

**Actions taken**:
1. Created directory: `specs/stripe-payment-processing/`
2. Initialized `specs/registry.md` with the standard header and one row for
   `stripe-payment-processing` (status: `active`, priority: `high`, progress: `0/0`)

**Files created**:
- `specs/registry.md`
- `specs/stripe-payment-processing/` (directory)

---

## Step 2: Deep Research (Phase 1 of Forge)

### 2a. Codebase Research

**Finding**: No target e-commerce codebase is available for inspection. We are
operating from the specsmith evaluation workspace, not the actual e-commerce
application. This means we cannot examine real file structures, models, routes,
or middleware patterns. This is a critical gap -- every concrete task in the
spec depends on knowing the tech stack and existing code patterns.

**What we would need to examine in the actual codebase**:
- Web framework in use (Express, Fastify, Next.js, Django, Rails, etc.)
- Database engine, ORM, and migration tool
- User/customer model (where to add `stripe_customer_id`)
- Product catalog and pricing model
- Cart and order models, existing checkout flow state machine
- Frontend framework and routing
- Auth middleware patterns
- Test framework and coverage patterns
- Environment variable and secrets management
- Deployment target and CI/CD pipeline

### 2b. Stripe API Research

Conducted thorough research on the three pillars the user requested:

**Checkout Sessions API**:
- Recommended approach for both one-time and subscription payments
- Two presentation modes: hosted (redirect to Stripe) and embedded (in-app widget)
- Handles PCI compliance, SCA/3D Secure, international payment methods automatically
- Two payment modes: `payment` (one-time) and `subscription` (recurring)
- Supports coupons, shipping collection, custom fields, tax calculation

**Subscriptions API**:
- Built around Products, Prices, Customers, and Subscriptions
- Lifecycle: `incomplete` -> `active` -> `past_due` -> `canceled`/`unpaid`
- Trials (free period before first charge), proration (mid-cycle plan changes)
- Two creation paths: via Checkout Sessions (recommended) or direct API
- Customer Portal available for self-service management

**Webhooks**:
- POST requests from Stripe for asynchronous event notification
- Signature verification mandatory using `stripe.webhooks.constructEvent()`
- Raw body required (before JSON parsing middleware)
- Must return 2xx within 5-10 seconds; Stripe retries with exponential backoff
- Handlers must be idempotent (same event may arrive multiple times)
- Critical events documented: `checkout.session.completed`, `invoice.payment_succeeded`,
  `invoice.payment_failed`, `customer.subscription.updated`,
  `customer.subscription.deleted`, and 5 more

**Security considerations documented**:
- PCI compliance via Checkout Sessions / Elements (never handle raw card data)
- Webhook signature verification (non-negotiable)
- API key management (restricted keys, environment variables, test vs live modes)
- Idempotency keys for all mutating API calls
- Server-side price validation (never trust client-sent amounts)
- HTTPS required for webhook endpoints
- Event ID deduplication for retry safety

### 2c. Web Research

No web search tools were used in this round. Research is based on current
Stripe documentation knowledge. Key documentation URLs recorded in
research-01.md for follow-up reference.

### 2d. Research Saved

**File created**: `specs/stripe-payment-processing/research-01.md`

Contents include:
- Project architecture gaps (what we need to discover in the actual codebase)
- Stripe Checkout Sessions API overview and options
- Stripe Subscriptions API lifecycle and creation paths
- Stripe Webhooks processing patterns and critical events table
- Customer Portal overview
- Security considerations (7 areas)
- Common integration patterns (checkout flow, subscription flow, webhook handler architecture)
- 10 open questions that must be resolved before writing the spec

---

## Step 3: Interview Round 1 (Phase 2 of Forge)

### Research Summary Presented to User

Presented findings in a focused summary covering three areas:
1. Researched Stripe's API surface thoroughly but could not examine the actual
   e-commerce codebase (no access to the target repository)
2. Recommended Stripe Checkout Sessions over Payment Intents + Elements for both
   one-time and subscription payments (simpler, handles PCI/SCA/3DS automatically)
3. Identified webhooks as the authoritative source of truth for payment state,
   with specific events mapped for checkout completion, subscription lifecycle,
   and payment failures

### Assumptions Stated

Presented 4 explicit assumptions for the user to confirm or correct:
1. Checkout Sessions over Payment Intents (unless specific UX requirements dictate otherwise)
2. Webhooks as source of truth (not redirect callbacks)
3. Lazy customer creation (create Stripe Customer on first purchase, not on registration)
4. Customer Portal for subscription self-service (rather than building custom management UI)

### Questions Asked (6 targeted questions)

1. **Tech stack**: Language, framework, database, ORM, frontend, deployment target.
   Cannot write concrete tasks with file paths without this information.

2. **Checkout approach**: Stripe Checkout Sessions (hosted or embedded) vs custom
   Payment Intents + Elements. Recommended Checkout Sessions unless there is a
   specific reason to need pixel-level control over the payment form.

3. **Subscription model details**: Number of plans/tiers, whether Products and Prices
   are already in Stripe Dashboard, free trials, flat-rate vs metered billing.

4. **Existing data model and checkout flow**: How users, products, orders, and carts
   are currently modeled. Whether there is an existing checkout flow to extend or
   if checkout is entirely new. Greenfield vs migration from another provider.

5. **Scope boundaries**: Whether to include Customer Portal, refund processing,
   coupon/promo support, admin dashboard, email receipts. Recommended including
   Customer Portal (low effort, high value) and deferring refunds/admin to a
   follow-up spec.

6. **Testing approach**: Stripe test mode with test cards, Stripe CLI for local
   webhooks, SDK mocking in unit tests, test clocks for subscription lifecycle.

### Proposed Rough Approach

Presented a 5-phase outline for user reaction:
- Phase 1: Foundation (SDK, config, customer linking, schema)
- Phase 2: One-Time Checkout (session creation, success/cancel, webhook, fulfillment)
- Phase 3: Subscriptions (subscription checkout, DB model, lifecycle webhooks, access gating)
- Phase 4: Webhook Infrastructure (signature verification, idempotency, routing, error handling)
- Phase 5: Customer Portal & Polish (portal sessions, billing page, test suite)

### Interview File Saved

**File created**: `specs/stripe-payment-processing/interview-01.md`

All 6 questions documented with `[AWAITING USER RESPONSE]` placeholders.

---

## Current Status: WAITING FOR USER INPUT

The forge workflow is paused at **Interview Round 1**. All 6 questions require
user responses before proceeding. The user's answers will determine:

- The entire tech stack, which shapes every task's file paths and function names
- The checkout approach (Checkout Sessions vs Elements) -- a major architectural fork
- Subscription model complexity (number of plans, trials, metered billing)
- Scope boundaries (which features to include vs defer)
- Whether a codebase research round is needed (almost certainly yes)
- Testing strategy and tools

### Next Steps (after user responds)

1. Record user answers in `interview-01.md`
2. Conduct **Research Round 2** (`research-02.md`) -- examine the actual e-commerce
   codebase based on tech stack details the user provides. Map existing models,
   routes, middleware patterns, test setup. Look up specific Stripe SDK version
   compatibility with the project's framework.
3. **Interview Round 2** (`interview-02.md`) -- deeper questions on trade-offs,
   edge cases, implementation sequence, and scope refinements informed by codebase
   research findings
4. **Write SPEC.md** -- synthesize all research and interviews into a concrete spec
   with phases, tasks with file paths and function names, resume context, and
   decision log
5. Present the complete spec for user review and approval before any implementation

### Files Created This Session

| File | Description |
|------|-------------|
| `specs/registry.md` | Spec registry with one entry for stripe-payment-processing |
| `specs/stripe-payment-processing/research-01.md` | Deep research on Stripe APIs, integration patterns, security, and 10 open questions |
| `specs/stripe-payment-processing/interview-01.md` | Interview round 1 with 6 targeted questions, 4 stated assumptions, and a proposed 5-phase approach |
| `transcript.md` | This file -- complete workflow log |
| `research-01.md` | Copy of research notes at outputs root |

---

[WAITING FOR USER INPUT - STOPPING HERE]

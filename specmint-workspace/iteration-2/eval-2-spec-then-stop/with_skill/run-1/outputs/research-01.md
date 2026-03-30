# Research Notes -- Stripe Payment Processing
## Date: 2026-03-06

## Project Architecture

**No target e-commerce codebase available for inspection.** This research was
conducted without access to the actual application repository. All findings
below are based on Stripe integration best practices and API documentation.
A follow-up research round (research-02.md) should target the real codebase
once the user provides tech stack details, so we can map existing models,
routes, middleware patterns, and database schema.

### What Must Be Discovered in the Actual Codebase

- Web framework (Express, Fastify, Next.js, Hono, Django, Rails, Phoenix, etc.)
- Database engine and ORM/query builder (PostgreSQL + Prisma, Drizzle, Knex, etc.)
- Existing user/auth model -- how customers are represented, auth middleware
- Product catalog model -- how products and prices are stored today
- Cart and order models -- existing checkout flow, order state machine
- Frontend framework (React, Vue, Svelte, server-rendered templates, etc.)
- Existing payment code (greenfield vs migration from another provider)
- Environment variable and secrets management patterns
- Test framework, coverage patterns, CI pipeline
- Deployment target (Vercel, AWS, GCP, Railway, self-hosted, etc.)

## Relevant Code

Not available -- we are not in the target repository. Key areas to examine
once we have access:

- **User/Customer model**: Will need a `stripe_customer_id` column or field
- **Product/Price model**: Need mapping between internal products and Stripe Price IDs
- **Order model**: Must track `stripe_checkout_session_id`, `stripe_payment_intent_id`, payment status
- **Subscription model**: Must track `stripe_subscription_id`, status, current period start/end, plan
- **Routes/Controllers**: Existing checkout flow, account/billing pages
- **Middleware**: Auth, request validation, raw body handling for webhooks, error handling
- **Database migrations**: How schema changes are managed (migration tool, naming conventions)

## Tech Stack & Dependencies

### Stripe Platform (current as of 2025-2026)

**Server-side SDKs:**
- `stripe` (Node.js) -- most common for JS/TS backends
- `stripe-python`, `stripe-ruby`, `stripe-go`, `stripe-java` -- language-specific
- All SDKs follow the same API shape; implementation details differ

**Client-side libraries:**
- `@stripe/stripe-js` -- PCI-compliant client-side loader (loads from Stripe CDN)
- `@stripe/react-stripe-js` -- React bindings for Stripe Elements
- `@stripe/stripe-js` can be used with any framework or vanilla JS

### Stripe Checkout Sessions API

The recommended approach for both one-time and subscription payments:

- Server creates a Checkout Session specifying line items, mode, and redirect URLs
- Two modes: `mode: 'payment'` (one-time) and `mode: 'subscription'` (recurring)
- Two presentation options:
  - **Hosted checkout** -- redirect to stripe.com/checkout (simplest, fully PCI compliant)
  - **Embedded checkout** -- mount Stripe's checkout UI inside your site (more control over UX)
- Handles SCA/3D Secure, international payment methods, tax calculation automatically
- Supports coupons, promotions, shipping address collection, custom fields
- Returns a `checkout.session.completed` webhook event on success

### Stripe Subscriptions API

Core concepts:

- **Products** -- what you sell (e.g., "Pro Plan", "Enterprise Plan")
- **Prices** -- how much and how often (e.g., $29/month, $290/year)
- **Customers** -- Stripe's representation of a paying user (linked via `stripe_customer_id`)
- **Subscriptions** -- a Customer subscribed to one or more Prices

Lifecycle states: `incomplete` -> `active` -> `past_due` -> `canceled` / `unpaid`

Key features:
- Trials, proration, metered billing, billing anchors
- Customer Portal for self-service management

### Stripe Webhooks

- POST requests to a registered endpoint URL
- Signature verification mandatory
- Raw body required before JSON parsing middleware
- Must return 2xx within 5-10 seconds
- Handlers must be idempotent (duplicate deliveries are normal)

Critical events: `checkout.session.completed`, `invoice.payment_succeeded`,
`invoice.payment_failed`, `customer.subscription.updated`,
`customer.subscription.deleted`

## Security Considerations

1. PCI compliance: Never handle raw card numbers. Use Checkout Sessions or Elements.
2. Webhook signature verification: Always verify `stripe-signature` header.
3. API key management: Restricted keys, env vars, test-mode keys for development.
4. Idempotency keys: Use for all mutating Stripe API calls.
5. Amount validation: Never trust client-sent prices. Use Stripe Price objects.
6. HTTPS required for webhook endpoints in production.
7. Event deduplication: Store processed event IDs.

## Open Questions

1. Tech stack (language, framework, database, ORM)
2. Checkout approach (Checkout Sessions vs Payment Intents + Elements)
3. Subscription tiers and pricing model
4. Existing payment infrastructure (greenfield vs migration)
5. Current data model (users, products, orders, carts)
6. Customer creation strategy (eager vs lazy)
7. Frontend architecture
8. Scope boundaries (Customer Portal, refunds, coupons, admin views)
9. Testing strategy
10. Deployment and environment

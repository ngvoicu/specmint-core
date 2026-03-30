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

### Stripe Payment Intents API (alternative to Checkout Sessions)

For fully custom checkout UIs:

- Server creates a PaymentIntent with an amount and currency
- Client uses Stripe Elements to collect card details (PCI compliant)
- Developer handles the full confirmation flow: create -> confirm -> handle 3DS -> complete
- More code, more control -- use only if Checkout Sessions cannot meet UX requirements
- Still relies on webhooks for authoritative payment confirmation

### Stripe Subscriptions API

Core concepts:

- **Products** -- what you sell (e.g., "Pro Plan", "Enterprise Plan")
- **Prices** -- how much and how often (e.g., $29/month, $290/year)
- **Customers** -- Stripe's representation of a paying user (linked via `stripe_customer_id`)
- **Subscriptions** -- a Customer subscribed to one or more Prices

Lifecycle states: `incomplete` -> `active` -> `past_due` -> `canceled` / `unpaid`

Key features:
- **Trials**: Free trial period before first charge (`trial_period_days` or `trial_end`)
- **Proration**: Automatic proration when upgrading/downgrading mid-cycle
- **Metered billing**: Usage-based pricing reported via Usage Records
- **Billing anchors**: Control billing cycle dates
- **Customer Portal**: Stripe-hosted page for customers to manage subscriptions, payment methods, invoices

Creating subscriptions:
- Option A: Via Checkout Sessions with `mode: 'subscription'` (recommended)
- Option B: Direct Subscription creation via API (requires existing payment method)

### Stripe Webhooks

How Stripe communicates asynchronous events back to your application:

- POST requests to a registered endpoint URL
- **Signature verification is mandatory** -- use `stripe.webhooks.constructEvent(rawBody, sig, secret)`
- Raw body required before any JSON parsing middleware (critical in Express/Fastify)
- Must return 2xx within 5-10 seconds or Stripe retries (exponential backoff, up to 3 days)
- Retry behavior means handlers must be **idempotent** (processing the same event twice must be safe)

**Critical events for checkout + subscriptions:**

| Event | When It Fires | What To Do |
|-------|---------------|------------|
| `checkout.session.completed` | Customer completes checkout | Fulfill order or activate subscription |
| `checkout.session.expired` | Session expires before completion | Clean up pending order |
| `invoice.payment_succeeded` | Subscription renewal succeeds | Extend access period |
| `invoice.payment_failed` | Subscription renewal fails | Notify user, flag account |
| `customer.subscription.created` | New subscription created | Create local subscription record |
| `customer.subscription.updated` | Plan change, status change | Sync local subscription state |
| `customer.subscription.deleted` | Subscription canceled | Revoke access, update local state |
| `customer.subscription.trial_will_end` | Trial ending in 3 days | Notify user |
| `payment_intent.succeeded` | One-time payment succeeds | Fulfill order |
| `payment_intent.payment_failed` | One-time payment fails | Notify user |

**Webhook processing pattern:**
1. Receive POST at `/api/webhooks/stripe` (or similar)
2. Read raw body before JSON parsing middleware runs
3. Verify signature with webhook signing secret
4. Parse event type and route to the appropriate handler
5. Check idempotency (have we already processed this event ID?)
6. Process the event (update database, send notifications, etc.)
7. Return 200 immediately -- do heavy processing asynchronously if needed

### Customer Portal

Stripe-hosted self-service page:
- Customers can update payment methods, view invoices, change plans, cancel
- Minimal code: create a portal session, redirect the customer
- Configuration done in Stripe Dashboard (which plans can switch, cancellation policy, etc.)
- Reduces support burden significantly for subscription-based apps

## Security Considerations

1. **PCI compliance**: Never handle raw card numbers server-side. Checkout Sessions
   and Stripe Elements both tokenize on the client side. This is non-negotiable.

2. **Webhook signature verification**: Always verify the `stripe-signature` header
   using the webhook signing secret. Never trust unverified payloads.

3. **API key management**: Use restricted API keys in production (limit permissions
   to only what's needed). Store all keys in environment variables, never in code.
   Use test-mode keys for development. Rotate keys if compromised.

4. **Idempotency keys**: Use for all mutating Stripe API calls (creating customers,
   sessions, subscriptions) to prevent duplicate charges on retries.

5. **Amount validation**: Never trust client-sent prices or amounts. Always use
   Stripe-defined Price objects or compute amounts server-side.

6. **HTTPS required**: Stripe mandates HTTPS for webhook endpoints in production.
   Use ngrok or Stripe CLI for local development webhook testing.

7. **Webhook event deduplication**: Store processed event IDs to handle Stripe's
   retry behavior safely.

8. **Rate limiting**: Stripe has API rate limits (100 read / 100 write per second
   in live mode). Design webhook handlers to minimize outbound API calls.

## Common Integration Patterns

### One-Time Checkout Flow
```
Client: "Buy Now" click
  -> Server: POST /api/checkout/session { items, quantities }
    -> Stripe: Create Checkout Session (mode: 'payment')
    <- Server: { url: "https://checkout.stripe.com/..." }
  <- Client: Redirect to Stripe checkout
  -> Stripe: Customer pays
  -> Stripe: Webhook POST checkout.session.completed
    -> Server: Fulfill order, update order status to 'paid'
  -> Stripe: Redirect to success_url with session_id
  -> Client: Show order confirmation page
```

### Subscription Flow
```
Client: "Subscribe to Pro Plan" click
  -> Server: POST /api/checkout/subscribe { priceId }
    -> Stripe: Get/create Customer (link to user)
    -> Stripe: Create Checkout Session (mode: 'subscription', customer)
    <- Server: { url: "https://checkout.stripe.com/..." }
  <- Client: Redirect to Stripe checkout
  -> Stripe: Customer enters payment details
  -> Stripe: Webhook checkout.session.completed
    -> Server: Create local subscription record, grant access
  -> Stripe: Redirect to success_url
  -> Client: Show subscription confirmation

Ongoing:
  -> Stripe: Webhook invoice.payment_succeeded (monthly renewal)
    -> Server: Extend access period, update subscription record
  -> Stripe: Webhook invoice.payment_failed
    -> Server: Notify user, enter grace period, eventually revoke access
  -> Stripe: Webhook customer.subscription.deleted
    -> Server: Revoke access, update local state
```

### Webhook Handler Architecture
```
POST /api/webhooks/stripe
  1. Raw body extraction (bypass JSON parser)
  2. Signature verification
  3. Event type switch:
     - checkout.session.completed -> handleCheckoutComplete()
     - invoice.payment_succeeded  -> handleInvoicePaid()
     - invoice.payment_failed     -> handleInvoiceFailed()
     - customer.subscription.*    -> handleSubscriptionChange()
     - default                    -> log and ignore
  4. Idempotency check (event.id in processed_events table)
  5. Process event
  6. Return 200
```

## Open Questions

These must be resolved during interviews before writing the spec:

1. **Tech stack**: What language, framework, database, and ORM does the e-commerce
   app use? This determines every implementation detail -- file paths, middleware
   patterns, migration syntax, test framework.

2. **Checkout approach**: Stripe Checkout Sessions (hosted or embedded) vs custom UI
   with Payment Intents + Elements? Checkout Sessions is strongly recommended unless
   there are specific UX requirements that demand a custom checkout.

3. **Subscription tiers**: How many plans? What are the pricing tiers? Are Products
   and Prices already configured in Stripe Dashboard or do they need to be created
   programmatically? Do any plans have free trials or metered billing?

4. **Existing payment infrastructure**: Is this greenfield or migrating from another
   provider (PayPal, Braintree, etc.)? Migration has significant implications for
   customer data, existing subscriptions, and cutover strategy.

5. **Current data model**: How are users, products, and orders currently modeled in
   the database? Is there an existing cart system? What state machine (if any) do
   orders follow?

6. **Customer creation strategy**: Create Stripe Customer on user registration
   (eager) or on first purchase (lazy)? Lazy is simpler but means some users won't
   have Stripe Customers. Eager ensures every user can be billed immediately.

7. **Frontend architecture**: What renders the checkout UI? Is there an existing
   checkout page to modify, or does one need to be built? SPA vs server-rendered
   affects the redirect/embedded checkout decision.

8. **Scope boundaries**: Should this spec also cover:
   - Customer Portal for subscription self-service management?
   - Refund processing?
   - Invoice generation and viewing?
   - Email receipts (Stripe-sent vs app-sent)?
   - Admin dashboard for payment/subscription management?
   - Coupon/promotion code support?

9. **Testing strategy**: Use Stripe's test mode with test card numbers? Stripe CLI
   for local webhook forwarding? Mock the SDK in unit tests? Use test clocks for
   subscription lifecycle testing?

10. **Deployment and environment**: Where does the app run? How are environment
    variables and secrets managed? This affects webhook URL configuration and
    API key storage.

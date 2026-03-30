# Research Notes — Stripe Payment Processing
## Date: 2026-03-06

## Project Architecture

**IMPORTANT: No target e-commerce codebase available.** This research was conducted
from within the specsmith repository, not the actual e-commerce application. The
following research is based on Stripe integration requirements and best practices.
A second research round after the interview should target the actual codebase to
map existing models, routes, middleware, and database schema.

### What We Need to Discover (in the actual codebase)
- Web framework in use (Express, Fastify, Next.js, Django, Rails, etc.)
- Database and ORM (PostgreSQL + Prisma? MongoDB + Mongoose? etc.)
- Existing user/auth model and how customers are represented
- Current cart/order model and checkout flow (if any)
- Frontend framework (React, Vue, server-rendered, etc.)
- Existing payment-related code (if migrating from another provider)
- Environment variable patterns and secrets management
- Test framework and patterns
- Deployment target (Vercel, AWS, self-hosted, etc.)

## Relevant Code

Not available — we are not in the target e-commerce repository. Key areas to
examine in the actual codebase:

- **User/Customer model**: Need to store `stripe_customer_id` on the user record
- **Product/Price model**: Need to map internal products to Stripe Price objects
- **Order model**: Need to track payment status, Stripe session IDs, payment intents
- **Subscription model**: Need to track subscription status, current period, plan
- **Routes/Controllers**: Existing checkout flow, account pages
- **Middleware**: Auth middleware, request validation, error handling patterns
- **Database migrations**: How schema changes are managed

## Tech Stack & Dependencies

### Stripe API (current as of 2025-2026)

**Core Stripe packages:**
- `stripe` (Node.js) / `stripe-python` / `stripe-ruby` — server-side SDK
- `@stripe/stripe-js` — client-side loader (PCI compliant)
- `@stripe/react-stripe-js` — React bindings (if React frontend)

**Key Stripe API versions and concepts:**

1. **Checkout Sessions API** (recommended for one-time and subscription payments)
   - Server creates a Checkout Session with line items
   - Client redirects to Stripe-hosted checkout page OR uses embedded checkout
   - Supports one-time payments, subscriptions, and mixed carts
   - Handles SCA/3D Secure automatically
   - `mode: 'payment'` for one-time, `mode: 'subscription'` for recurring

2. **Payment Intents API** (for custom checkout UIs)
   - More control over the payment flow
   - Requires Stripe Elements on the frontend for PCI compliance
   - Developer handles confirmation, error states, redirects
   - Better for highly customized checkout experiences

3. **Subscriptions API**
   - Create subscriptions tied to a Stripe Customer
   - Products and Prices defined in Stripe Dashboard or via API
   - Subscription lifecycle: `incomplete` → `active` → `past_due` → `canceled`
   - Billing portal for customer self-service (plan changes, cancellation)
   - Trials, proration, metered billing supported
   - Key events: `customer.subscription.created`, `customer.subscription.updated`,
     `customer.subscription.deleted`, `invoice.payment_succeeded`,
     `invoice.payment_failed`

4. **Webhooks**
   - Stripe sends POST requests to your endpoint for async events
   - **Signature verification is mandatory** — use `stripe.webhooks.constructEvent()`
   - Raw body required (not parsed JSON) for signature verification
   - Must return 2xx quickly (within 5 seconds) or Stripe retries
   - Idempotency: must handle duplicate webhook deliveries gracefully
   - Key events to handle:
     - `checkout.session.completed` — payment successful
     - `invoice.payment_succeeded` — subscription renewal
     - `invoice.payment_failed` — subscription payment failed
     - `customer.subscription.updated` — plan changed
     - `customer.subscription.deleted` — subscription canceled
     - `payment_intent.succeeded` — direct payment intent success
     - `payment_intent.payment_failed` — payment failed

5. **Customer Portal**
   - Stripe-hosted page for managing subscriptions, payment methods, invoices
   - Minimal code required — create a portal session and redirect

### Security Considerations

- **PCI compliance**: Never handle raw card numbers server-side. Use Checkout
  Sessions or Stripe Elements which tokenize on the client.
- **Webhook signature verification**: Always verify the `stripe-signature` header.
  Never trust webhook payloads without verification.
- **API keys**: Use restricted keys in production. Store in environment variables.
  Test mode keys for development.
- **Idempotency keys**: Use for POST requests to avoid duplicate charges.
- **HTTPS only**: Stripe requires HTTPS for webhook endpoints.
- **Amount validation**: Never trust client-sent amounts. Always compute prices
  server-side or use Stripe-defined Price objects.

### Common Architecture Patterns

**Checkout flow (Stripe Checkout Sessions):**
1. Client clicks "Buy" / "Subscribe"
2. Client sends request to your server with cart/plan info
3. Server creates a Stripe Checkout Session with line items, success/cancel URLs
4. Server returns session URL (or session ID for embedded checkout)
5. Client redirects to Stripe checkout
6. After payment, Stripe redirects to success URL
7. Webhook confirms payment asynchronously (source of truth)

**Subscription management flow:**
1. User selects a plan
2. Server creates/retrieves Stripe Customer (linked to user record)
3. Server creates Checkout Session in `subscription` mode
4. Stripe handles payment and creates the subscription
5. Webhook `checkout.session.completed` updates local subscription record
6. Ongoing: webhooks for renewals, failures, cancellations update local state
7. Customer portal for self-service changes

**Webhook processing pattern:**
1. Receive POST at `/webhooks/stripe` (or similar)
2. Read raw body (important: before any JSON parsing middleware)
3. Verify signature using webhook secret
4. Parse event type and data
5. Route to handler based on event type
6. Process idempotently (check if already processed via event ID)
7. Return 200 immediately, do heavy processing async if needed

## External Research

Web search was unavailable during this research round. Key resources to consult:
- Stripe Docs: https://stripe.com/docs
- Stripe API Reference: https://stripe.com/docs/api
- Stripe Checkout quickstart: https://stripe.com/docs/checkout/quickstart
- Stripe Subscriptions guide: https://stripe.com/docs/billing/subscriptions/overview
- Stripe Webhooks guide: https://stripe.com/docs/webhooks
- Stripe Testing: https://stripe.com/docs/testing

## Open Questions

These must be resolved during the interview before writing the spec:

1. **Tech stack**: What language/framework is the e-commerce app built with?
   This fundamentally shapes every implementation detail.

2. **Checkout approach**: Stripe Checkout Sessions (Stripe-hosted page, simpler)
   vs Payment Intents + Elements (custom UI, more work)? Checkout Sessions is
   recommended for most use cases.

3. **Subscription model**: What subscription plans exist? Are they already defined
   in Stripe, or do we need to create Products/Prices? Is there a free tier?

4. **Existing payment code**: Is there any existing payment processing (migrating
   from another provider) or is this greenfield?

5. **Customer mapping**: Is there an existing user model? Do we need to create a
   Stripe Customer on registration or lazily on first purchase?

6. **Database**: How are products, orders, and users currently modeled? What
   migrations tool is used?

7. **Frontend**: What renders the checkout button / subscription selection?
   React? Server-rendered pages? Mobile app?

8. **Deployment**: Where does the app run? This affects webhook URL configuration
   and environment variable management.

9. **Scope boundaries**: Should this spec cover the Stripe Customer Portal for
   subscription management? Invoicing? Refunds? Or just the core checkout +
   subscriptions + webhooks?

10. **Testing strategy**: Should we use Stripe's test mode with test clocks for
    subscription testing? Mock the Stripe SDK in unit tests?

# Interview Round 1 -- Stripe Payment Processing
## Date: 2026-03-06

## Research Summary

I researched Stripe's current API surface for the three areas you mentioned:
checkout, subscriptions, and webhook handling. Since I could not access the
actual e-commerce codebase, the research focused entirely on Stripe's platform
capabilities and integration patterns. The key architectural fork is whether
to use Stripe Checkout Sessions (hosted or embedded -- simpler, PCI compliant
out of the box, handles SCA/3DS automatically) or a custom checkout UI built
with Payment Intents and Stripe Elements (more control, significantly more code).
For subscriptions, Stripe's model revolves around Products, Prices, and Customers,
with lifecycle events delivered via webhooks. The webhook endpoint is the
single most critical piece -- it is the authoritative source of truth for
payment and subscription state, and it must verify signatures and handle
duplicate deliveries idempotently.

## Assumptions

Based on common e-commerce patterns, I am making these assumptions. Please
correct any that are wrong:

- **Checkout Sessions over Payment Intents**: Stripe Checkout Sessions is the
  recommended approach for most apps. It handles PCI, SCA, international payment
  methods, and error states automatically. Unless you have very specific UX
  requirements for the checkout page, this is the better choice.
- **Webhook as source of truth**: Payment and subscription state should be
  determined by webhook events, not by redirect callbacks. The success URL
  redirect is for UX only -- the webhook confirms the payment actually succeeded.
- **Lazy customer creation**: Create the Stripe Customer object when the user
  first initiates a checkout or subscription, not on registration. This avoids
  creating Stripe Customers for users who never pay.
- **Customer Portal for subscription management**: Rather than building custom
  plan-change and cancellation UIs, use Stripe's hosted Customer Portal. It
  handles plan switching, payment method updates, and cancellation with minimal
  code.

## Questions Asked

1. **What is the tech stack?** What language, framework, database, ORM, frontend
   framework, and deployment target does the e-commerce app use? I cannot write
   concrete tasks with file paths and function names without knowing this.

   **Answer**: [AWAITING USER RESPONSE]

2. **Checkout Sessions or custom UI?** Stripe Checkout Sessions (redirect to a
   Stripe-hosted page or embed Stripe's checkout widget in your site) vs a fully
   custom checkout built with Payment Intents + Stripe Elements. Checkout Sessions
   is simpler and recommended unless you need pixel-level control over the payment
   form. Which approach do you prefer, and is there a reason to favor one over
   the other?

   **Answer**: [AWAITING USER RESPONSE]

3. **Subscription model details**: How many subscription plans/tiers do you have?
   Are they already configured in the Stripe Dashboard (Products and Prices), or
   do they need to be created? Do any plans include free trials? Is billing
   flat-rate or metered/usage-based?

   **Answer**: [AWAITING USER RESPONSE]

4. **Existing data model and checkout flow**: How are users, products, orders, and
   carts currently modeled? Is there an existing checkout flow we would be
   extending, or is the checkout entirely new? Is there any existing payment
   processing (migrating from another provider) or is this greenfield?

   **Answer**: [AWAITING USER RESPONSE]

5. **Scope boundaries**: Beyond checkout, subscriptions, and webhooks, should this
   spec also cover: (a) Stripe Customer Portal for self-service subscription
   management, (b) refund processing, (c) coupon/promo code support, (d) admin
   dashboard views for payments, (e) email receipts (Stripe-sent vs app-sent)?
   I recommend including Customer Portal (it is low effort and high value) and
   deferring refunds and admin views to a follow-up spec.

   **Answer**: [AWAITING USER RESPONSE]

6. **Testing approach**: Should we use Stripe's test mode with test card numbers
   for integration tests? Stripe CLI for forwarding webhooks locally? Mock the
   Stripe SDK in unit tests? Use Stripe test clocks for simulating subscription
   lifecycle (renewals, failures, trial expiration)?

   **Answer**: [AWAITING USER RESPONSE]

## Proposed Rough Approach

Pending your answers, here is the general shape I am envisioning:

- **Phase 1: Foundation** -- Stripe SDK setup, environment config, Stripe Customer
  creation linked to user model, database schema additions (stripe_customer_id,
  subscription tracking, order payment fields)
- **Phase 2: One-Time Checkout** -- Checkout Session creation endpoint, success/cancel
  pages, webhook handler for checkout.session.completed, order fulfillment logic
- **Phase 3: Subscriptions** -- Subscription checkout flow, subscription model in DB,
  webhook handlers for subscription lifecycle events (created, updated, deleted,
  invoice paid/failed), access gating based on subscription status
- **Phase 4: Webhook Infrastructure** -- Robust webhook endpoint with signature
  verification, idempotent processing (event ID deduplication), event routing,
  error handling and logging, retry-safe design
- **Phase 5: Customer Portal & Polish** -- Customer Portal session creation, billing
  page, subscription management UI, testing suite

Does this phasing make sense, or would you organize it differently?

## Key Decisions

None yet -- awaiting user responses.

## New Research Needed

Based on user answers, the next research round should:
- Examine the actual e-commerce codebase (file structure, models, routes, middleware)
- Look up specific Stripe SDK version compatibility with the project's framework
- Research framework-specific patterns for raw body handling (webhook signature verification)
- If migrating from another provider, research data migration strategies

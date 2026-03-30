# Interview Round 1 — Stripe Payment Processing
## Date: 2026-03-06

## Research Summary Presented

I researched Stripe's current API surface for integrating checkout, subscriptions,
and webhook handling into an e-commerce application. However, I could not examine
the actual e-commerce codebase because we are operating from the specsmith
repository. This means I have strong knowledge of what Stripe integration requires,
but zero knowledge of the target app's tech stack, existing models, database, or
frontend.

Stripe's recommended approach for most e-commerce apps is **Checkout Sessions**
for both one-time payments and subscriptions. This gives you a Stripe-hosted (or
embeddable) checkout page that handles PCI compliance, SCA/3D Secure, and
international payment methods automatically. For webhooks, the critical pattern is
signature verification on the raw request body, idempotent event processing, and
fast 2xx responses.

The three pillars of the integration are: (1) server-side Checkout Session creation
with proper line items and success/cancel URLs, (2) subscription lifecycle
management with Customer objects and the Subscriptions API, and (3) a webhook
endpoint that processes events like `checkout.session.completed`,
`invoice.payment_succeeded`, `invoice.payment_failed`, and
`customer.subscription.deleted`.

## Questions Asked

1. **What is the tech stack of the e-commerce app?** (Language, web framework,
   database, ORM, frontend framework, deployment target.) This shapes every
   implementation detail — I cannot write concrete tasks without knowing if we
   are working with Express + PostgreSQL + React, Django + SQLite, Next.js +
   Prisma, or something else entirely.

   **Answer**: [AWAITING USER RESPONSE]

2. **Checkout approach: Stripe Checkout Sessions or custom UI with Payment
   Intents + Elements?** Checkout Sessions is simpler and handles PCI compliance,
   SCA, and multiple payment methods out of the box. Payment Intents + Elements
   gives you a fully custom checkout UI but requires significantly more code.
   I'd recommend Checkout Sessions unless you have specific UX requirements that
   demand a custom form.

   **Answer**: [AWAITING USER RESPONSE]

3. **What does the subscription model look like?** How many plans/tiers? Are they
   already defined in the Stripe Dashboard, or do we need to create
   Products/Prices via API? Do you need free trials, metered billing, or just
   flat-rate recurring plans?

   **Answer**: [AWAITING USER RESPONSE]

4. **Is there any existing payment processing?** Are we replacing another payment
   provider (PayPal, Braintree, etc.) or building payment processing from
   scratch? If migrating, do we need to handle existing customer payment methods
   or subscription continuity?

   **Answer**: [AWAITING USER RESPONSE]

5. **What does the current data model look like?** Specifically: How are users,
   products, and orders represented? Is there an existing cart system? This
   determines how we link Stripe Customer IDs to users and map internal products
   to Stripe Prices.

   **Answer**: [AWAITING USER RESPONSE]

6. **Scope: What should be included beyond the core three?** You mentioned
   checkout, subscriptions, and webhooks. Should this spec also cover:
   - Stripe Customer Portal (self-service subscription management)?
   - Refund handling?
   - Invoice generation/retrieval?
   - Email receipts (Stripe can send these automatically)?
   - Admin dashboard for viewing payments?

   **Answer**: [AWAITING USER RESPONSE]

## Key Decisions

[No decisions made yet — awaiting user responses]

## New Research Needed

After the user responds, the following research is needed:
- Examine the actual e-commerce codebase (file structure, models, routes, tests)
- Look up specific library versions and compatibility with their tech stack
- Research any existing payment code or migration requirements
- If they choose Checkout Sessions: review latest embedded checkout docs
- If they have specific subscription requirements: research Stripe Billing
  features (trials, proration, metered billing)

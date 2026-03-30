# Transcript: Spec for Adding Stripe Payment Processing

## Session Context

**User prompt**: "write a spec for adding payment processing with Stripe to our e-commerce app. We need checkout, subscriptions, and webhook handling."

**Mode**: Plain Claude Code (no plugins or skills loaded)

---

## Claude Code Response

I looked around the codebase to understand what we're working with. Since this repository is the specsmith plugin itself (not an e-commerce app), I don't have an actual e-commerce codebase to analyze for existing models, routes, database schema, or tech stack.

Before I write a detailed implementation spec, I have several questions that would significantly affect the design:

**Architecture questions:**
1. What is your tech stack? (e.g., Next.js + Prisma, Rails, Django, Express + PostgreSQL, etc.)
2. Do you already have a user/auth system? What does your User model look like?
3. Do you have existing product/cart/order models, or are those being built alongside this?
4. Is this a monolith or do you have separate frontend/backend services?

**Checkout questions:**
5. Are you selling physical goods, digital products, or both? (affects shipping/tax handling)
6. Do you want Stripe Checkout (hosted payment page) or Stripe Elements (embedded in your UI)?
7. Do you need to support multiple currencies?
8. Do you need guest checkout or only authenticated users?

**Subscription questions:**
9. What subscription tiers/plans do you have in mind? (e.g., monthly/annual, free tier)
10. Should users be able to upgrade/downgrade mid-cycle?
11. Do you need usage-based billing or flat-rate only?
12. Do subscriptions unlock features (SaaS-style) or deliver recurring physical goods?

**Webhook / operations questions:**
13. Where are you deploying? (Vercel, AWS, Railway, etc. -- affects webhook endpoint setup)
14. Do you need idempotency handling for retried webhooks?
15. Do you want to store payment events in your database for audit/reconciliation?

That said, I can write a general-purpose spec that covers the three areas you asked about. Here's what I'd produce:

---

## Spec: Stripe Payment Processing

### Overview

Add Stripe-based payment processing to the e-commerce application with three capabilities: one-time checkout for product purchases, recurring subscription billing, and server-side webhook handling for asynchronous Stripe events.

### 1. Checkout (One-Time Payments)

**Approach**: Use Stripe Checkout Sessions for a secure, hosted payment flow. This minimizes PCI compliance burden and provides a battle-tested UI.

**Flow**:
1. User adds items to cart and clicks "Checkout"
2. Backend creates a Stripe Checkout Session with line items, success/cancel URLs
3. User is redirected to Stripe's hosted checkout page
4. On success, Stripe redirects back to your success URL
5. Webhook confirms payment and creates the order record server-side

**Key implementation pieces**:
- API endpoint: `POST /api/checkout/sessions` -- creates a Stripe Checkout Session
- API endpoint: `GET /api/checkout/sessions/:id` -- retrieves session status for the success page
- Database: `orders` table with `stripe_checkout_session_id`, `stripe_payment_intent_id`, `status`, `total`, `user_id`
- Database: `order_items` table linking orders to products
- Stripe API calls: `stripe.checkout.sessions.create()`, `stripe.checkout.sessions.retrieve()`

**Considerations**:
- Store `stripe_customer_id` on your User model so returning customers get saved payment methods
- Use `mode: 'payment'` for one-time purchases
- Set `payment_intent_data.metadata` with your internal order reference for reconciliation
- Handle tax calculation via Stripe Tax or manually

### 2. Subscriptions (Recurring Billing)

**Approach**: Use Stripe Checkout Sessions in `subscription` mode, with Products and Prices defined in Stripe Dashboard or via API.

**Flow**:
1. User selects a plan from the pricing page
2. Backend creates a Checkout Session with `mode: 'subscription'` and the appropriate `price_id`
3. User completes payment on Stripe's hosted page
4. Webhook receives `customer.subscription.created` and provisions access
5. Subsequent billing is handled automatically by Stripe; webhooks notify of renewals, failures, cancellations

**Key implementation pieces**:
- API endpoint: `POST /api/subscriptions/checkout` -- creates subscription checkout session
- API endpoint: `GET /api/subscriptions/current` -- returns user's active subscription
- API endpoint: `POST /api/subscriptions/portal` -- creates a Stripe Customer Portal session for self-service management
- Database: `subscriptions` table with `stripe_subscription_id`, `stripe_customer_id`, `status`, `plan`, `current_period_start`, `current_period_end`, `cancel_at_period_end`
- Stripe API calls: `stripe.checkout.sessions.create()`, `stripe.billingPortal.sessions.create()`, `stripe.subscriptions.retrieve()`

**Subscription lifecycle events to handle**:
- `customer.subscription.created` -- provision access
- `customer.subscription.updated` -- plan changes, status changes
- `customer.subscription.deleted` -- revoke access
- `invoice.payment_succeeded` -- renewal confirmation
- `invoice.payment_failed` -- notify user, grace period logic
- `customer.subscription.trial_will_end` -- send reminder (if using trials)

**Considerations**:
- Use Stripe Customer Portal for upgrade/downgrade/cancel -- avoids building complex billing UI
- Store subscription status locally but treat Stripe as source of truth (sync via webhooks)
- Implement a grace period for failed payments before revoking access
- Prorate by default when changing plans mid-cycle

### 3. Webhook Handling

**Approach**: Single webhook endpoint that verifies Stripe signatures, dispatches events to handlers, and ensures idempotent processing.

**Key implementation pieces**:
- API endpoint: `POST /api/webhooks/stripe` -- receives all Stripe events
- Must use raw request body (not parsed JSON) for signature verification
- Use `stripe.webhooks.constructEvent(rawBody, sig, webhookSecret)` to verify
- Store processed event IDs to ensure idempotency

**Event handling pattern**:
```
receive raw body
  -> verify signature (reject 400 if invalid)
  -> parse event
  -> check idempotency (skip if already processed)
  -> dispatch to handler based on event.type
  -> return 200 immediately (process async if needed)
```

**Events to handle (minimum set)**:
| Event | Action |
|-------|--------|
| `checkout.session.completed` | Create order / provision subscription |
| `customer.subscription.created` | Store subscription, grant access |
| `customer.subscription.updated` | Update local subscription record |
| `customer.subscription.deleted` | Revoke access |
| `invoice.payment_succeeded` | Update payment status, extend access |
| `invoice.payment_failed` | Flag account, send notification |
| `payment_intent.succeeded` | Confirm one-time payment |
| `payment_intent.payment_failed` | Mark order as failed |
| `charge.refunded` | Process refund in your system |

**Security requirements**:
- Always verify webhook signatures -- never trust unverified payloads
- Use a dedicated webhook secret (separate from your API keys)
- Return 200 quickly to avoid Stripe retries; do heavy processing asynchronously
- Log all received events for debugging and audit
- Implement idempotency: store `event.id` in a `stripe_events` table and skip duplicates

### 4. Database Schema (Additions)

```
users (existing)
  + stripe_customer_id: string, nullable, unique

orders (new)
  id, user_id, stripe_checkout_session_id, stripe_payment_intent_id,
  status (pending/paid/refunded/failed), total, currency, created_at, updated_at

order_items (new)
  id, order_id, product_id, quantity, unit_price, total_price

subscriptions (new)
  id, user_id, stripe_subscription_id (unique), stripe_customer_id,
  plan, status (active/past_due/canceled/unpaid/trialing),
  current_period_start, current_period_end, cancel_at_period_end,
  created_at, updated_at

stripe_events (new)
  id, stripe_event_id (unique), event_type, processed_at, payload (jsonb)
```

### 5. Environment Variables Needed

```
STRIPE_SECRET_KEY        -- sk_test_... / sk_live_...
STRIPE_PUBLISHABLE_KEY   -- pk_test_... / pk_live_...
STRIPE_WEBHOOK_SECRET    -- whsec_...
STRIPE_PRICE_ID_MONTHLY  -- price_... (for subscription plans)
STRIPE_PRICE_ID_ANNUAL   -- price_... (for subscription plans)
```

### 6. Task Breakdown (Rough)

1. Install Stripe SDK, add environment variables
2. Add `stripe_customer_id` to User model + migration
3. Create `orders`, `order_items`, `subscriptions`, `stripe_events` tables + migrations
4. Implement Stripe customer creation (create on first checkout, link to user)
5. Build checkout session creation endpoint
6. Build checkout success page / order confirmation
7. Build subscription checkout endpoint
8. Build Stripe Customer Portal endpoint
9. Build webhook endpoint with signature verification
10. Implement webhook event handlers (checkout complete, subscription lifecycle, payment events)
11. Add subscription status checking middleware/guard for gated features
12. Write tests (unit tests for handlers, integration tests with Stripe test mode)
13. Set up Stripe webhook in Dashboard (or via CLI for local dev)
14. End-to-end testing with Stripe test cards

---

**To move forward with implementation, I'd need answers to the questions above** -- particularly around tech stack, existing models, and whether you want hosted Checkout vs. embedded Elements. The spec above assumes Stripe Checkout (hosted) which is the fastest path to production. Let me know how you'd like to proceed.

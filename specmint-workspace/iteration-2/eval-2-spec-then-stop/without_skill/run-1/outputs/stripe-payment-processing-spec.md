# Spec: Stripe Payment Processing Integration

## Overview

Add payment processing capabilities to the e-commerce application using Stripe. This covers three core areas: one-time checkout payments, recurring subscription billing, and server-side webhook handling for asynchronous event processing.

## Goals

- Enable customers to complete purchases via Stripe-powered checkout
- Support recurring subscription billing with plan management
- Handle Stripe webhook events reliably for payment lifecycle management
- Maintain PCI compliance by never handling raw card data server-side

## Non-Goals

- Marketplace/multi-vendor payment splitting (Stripe Connect)
- Invoice generation and PDF delivery
- Cryptocurrency or alternative payment methods beyond cards
- Custom fraud detection rules (rely on Stripe Radar)

---

## 1. Checkout (One-Time Payments)

### 1.1 Approach

Use **Stripe Checkout Sessions** (hosted payment page) for the initial implementation. This minimizes PCI scope and provides a battle-tested UI with built-in support for Apple Pay, Google Pay, and card payments.

### 1.2 Flow

1. Customer adds items to cart and clicks "Checkout"
2. Server creates a Stripe Checkout Session with line items, success URL, and cancel URL
3. Customer is redirected to Stripe's hosted checkout page
4. On success, Stripe redirects to success URL with session ID
5. Server confirms payment via `checkout.session.completed` webhook (source of truth)
6. Order is marked as paid and fulfillment begins

### 1.3 Key Implementation Details

- **Checkout Session creation endpoint**: `POST /api/checkout/sessions`
  - Accepts: cart items (product IDs + quantities), customer email (if authenticated)
  - Returns: Stripe Checkout Session URL for redirect
  - Creates or retrieves Stripe Customer object for authenticated users
- **Success page**: `GET /checkout/success?session_id={CHECKOUT_SESSION_ID}`
  - Retrieves session to show order confirmation
  - Does NOT mark order as complete (webhook does that)
- **Cancel page**: `GET /checkout/cancel`
  - Returns customer to cart with items preserved
- **Idempotency**: Use idempotency keys on session creation to prevent duplicate charges
- **Metadata**: Attach internal order ID to checkout session metadata for correlation

### 1.4 Database Changes

- `orders` table: Add `stripe_checkout_session_id`, `stripe_payment_intent_id`, `payment_status` columns
- `customers` table (or `users`): Add `stripe_customer_id` column
- New `payment_events` table: Log all webhook events for audit trail

### 1.5 Error Handling

- Expired sessions: Sessions expire after 24h by default; show appropriate message
- Payment failures: Stripe handles retries on its checkout page
- Network errors on session creation: Return 500 with retry guidance

---

## 2. Subscriptions

### 2.1 Approach

Use **Stripe Billing** with predefined Products and Prices configured in the Stripe Dashboard (or seeded via API). Subscription lifecycle is managed entirely through webhooks.

### 2.2 Flow

1. Customer selects a subscription plan
2. Server creates a Stripe Checkout Session in `subscription` mode
3. Customer completes payment on Stripe's hosted page
4. `checkout.session.completed` webhook fires with subscription ID
5. Server provisions access based on subscription status
6. Ongoing lifecycle managed via webhooks (renewals, failures, cancellations)

### 2.3 Plan Structure

Define products and prices in Stripe:
- Products represent plan tiers (e.g., "Basic", "Pro", "Enterprise")
- Each product has one or more Prices (monthly, annual)
- Store Stripe Price IDs in application config or database

### 2.4 Key Implementation Details

- **Subscribe endpoint**: `POST /api/subscriptions/checkout`
  - Accepts: price ID, customer info
  - Returns: Stripe Checkout Session URL (mode: 'subscription')
- **Customer Portal**: Use Stripe's hosted Customer Portal for self-service
  - `POST /api/subscriptions/portal` returns portal session URL
  - Customers can upgrade, downgrade, update payment method, cancel
- **Access control**: Check `subscription_status` on each protected request
  - Active statuses: `active`, `trialing`
  - Grace period: `past_due` (configurable -- allow access for N days)
  - Blocked: `canceled`, `unpaid`
- **Plan changes**: Handled through Customer Portal; proration applied by default
- **Cancellation**: Set to cancel at period end (not immediate) by default

### 2.5 Database Changes

- `subscriptions` table: `id`, `user_id`, `stripe_subscription_id`, `stripe_customer_id`, `price_id`, `status`, `current_period_start`, `current_period_end`, `cancel_at_period_end`, `created_at`, `updated_at`
- Index on `user_id` and `stripe_subscription_id`

### 2.6 Trial Support

- Free trials configured on the Price in Stripe (e.g., 14-day trial)
- No payment method required during trial (configurable)
- `customer.subscription.trial_will_end` webhook sends reminder 3 days before trial ends

---

## 3. Webhook Handling

### 3.1 Approach

Single webhook endpoint that receives all Stripe events, verifies signatures, and dispatches to event-specific handlers.

### 3.2 Endpoint

`POST /api/webhooks/stripe`

### 3.3 Signature Verification

- Verify every incoming webhook using `stripe.webhooks.constructEvent()` with the webhook signing secret
- Reject any request that fails verification with 400
- Use raw request body (not parsed JSON) for signature verification

### 3.4 Events to Handle

**Checkout/Payment Events:**
| Event | Action |
|-------|--------|
| `checkout.session.completed` | Mark order as paid, provision access, trigger fulfillment |
| `payment_intent.succeeded` | Update payment record |
| `payment_intent.payment_failed` | Log failure, notify customer |

**Subscription Events:**
| Event | Action |
|-------|--------|
| `customer.subscription.created` | Create local subscription record |
| `customer.subscription.updated` | Sync status, plan, period dates |
| `customer.subscription.deleted` | Mark subscription as canceled, revoke access |
| `invoice.paid` | Confirm renewal, extend access |
| `invoice.payment_failed` | Mark as past_due, notify customer, start grace period |
| `customer.subscription.trial_will_end` | Send trial ending notification |

**Dispute Events:**
| Event | Action |
|-------|--------|
| `charge.dispute.created` | Alert admin, flag order |
| `charge.dispute.closed` | Update dispute status |

### 3.5 Idempotency

- Store processed event IDs in `payment_events` table
- On receiving an event, check if already processed before handling
- Return 200 for already-processed events (Stripe retries on non-2xx)

### 3.6 Error Handling & Reliability

- Return 200 immediately after queuing the event for processing (if using background jobs)
- If processing inline, return 200 on success, 500 on failure (Stripe will retry)
- Stripe retries failed webhooks for up to 3 days with exponential backoff
- Log all incoming events regardless of processing outcome
- Monitor for webhook delivery failures in Stripe Dashboard

### 3.7 Security

- Webhook endpoint excluded from CSRF protection
- Webhook signing secret stored in environment variables, never in code
- Endpoint only accepts POST requests
- IP allowlisting optional (Stripe publishes webhook IPs)

---

## 4. Configuration & Environment

### Environment Variables

```
STRIPE_SECRET_KEY=sk_...
STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SUCCESS_URL=https://yourapp.com/checkout/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://yourapp.com/checkout/cancel
```

### Test vs. Production

- Use `sk_test_` / `pk_test_` keys in development and staging
- Use Stripe CLI (`stripe listen --forward-to localhost:PORT/api/webhooks/stripe`) for local webhook testing
- Seed test products/prices in test mode

---

## 5. Security Considerations

- **PCI Compliance**: Using Stripe Checkout means card data never touches our servers (SAQ A)
- **API Keys**: Secret key server-side only, publishable key client-side only
- **Webhook Verification**: Always verify webhook signatures
- **HTTPS**: All Stripe communication over TLS (enforced by Stripe SDK)
- **Idempotency**: Prevent duplicate charges and duplicate event processing
- **Input Validation**: Validate all amounts, currency codes, and product IDs server-side

---

## 6. Implementation Order

| Phase | Tasks | Dependencies |
|-------|-------|-------------|
| Phase 1: Foundation | Stripe SDK setup, env config, Customer model sync, payment_events table | None |
| Phase 2: Checkout | Checkout Session creation, success/cancel pages, order payment status | Phase 1 |
| Phase 3: Webhooks | Endpoint, signature verification, checkout event handlers | Phase 1 |
| Phase 4: Subscriptions | Subscription checkout, status sync, access control middleware | Phases 1-3 |
| Phase 5: Portal | Customer Portal integration, self-service management | Phase 4 |
| Phase 6: Hardening | Idempotency, monitoring, error alerting, load testing | Phases 1-5 |

---

## 7. Testing Strategy

- **Unit tests**: Event handler logic, access control checks, idempotency guard
- **Integration tests**: Checkout Session creation with Stripe test API, webhook signature verification
- **End-to-end**: Full checkout flow using Stripe test cards (`4242424242424242`)
- **Webhook testing**: Use Stripe CLI to trigger test events locally
- **Failure scenarios**: Declined cards (`4000000000000002`), expired cards, insufficient funds, network timeouts

---

## Open Questions

1. What is the tech stack? (This affects specific implementation details significantly)
2. Stripe Checkout (hosted) vs. Stripe Elements (embedded)? Assumed Checkout for faster time-to-market.
3. What subscription tiers and pricing are planned?
4. Do you need invoice emails sent by Stripe or handled in-app?
5. What's the grace period policy for failed subscription payments?
6. Do you need to support coupon codes / promotional pricing?
7. Any existing payment infrastructure to migrate from?

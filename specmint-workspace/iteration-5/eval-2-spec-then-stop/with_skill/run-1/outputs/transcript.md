# Forge Workflow Transcript

**User prompt**: "write a spec for adding payment processing with Stripe to our e-commerce app. We need checkout, subscriptions, and webhook handling."

**Date**: 2026-03-06
**Skill**: specsmith (SKILL.md)
**Command**: /specsmith:forge

---

## Preflight: Resolve Spec Identity

**Generated spec ID**: `stripe-payment-processing`
**Collision check**: No `.specs/` directory exists. No collision found.
**Resolved ID**: `stripe-payment-processing`

---

## Plan Mode Check

Not in plan mode. Proceeding with forge workflow.

---

## Phase 1: Deep Research

### 1a. Codebase Research (Researcher Agent)

No e-commerce codebase was found in the current working directory. The working directory (`/Users/gabrielvoicu/Projects/ngvoicu/specsmith`) contains the specsmith plugin itself, not an e-commerce application.

**Observation**: The user referenced "our e-commerce app" but no application codebase is present in this project. The researcher agent would normally scan `package.json`, directory structure, existing routes, models, middleware, and test suites. Since there is no codebase to scan, the research will focus on Stripe integration best practices, architecture patterns, and library choices that apply broadly to e-commerce applications.

In a real session, the researcher agent would:
- Read `package.json` / `requirements.txt` / `go.mod` to identify the tech stack
- Map the directory structure to understand the organizational pattern
- Find existing payment-related code, models, routes, and middleware
- Read authentication/authorization middleware patterns
- Identify the database layer (ORM, schema definitions, migration tools)
- Check existing test frameworks and coverage
- Read environment variable configuration
- Trace the order/cart flow from frontend to backend

Since no codebase exists, research proceeds with general Stripe integration knowledge.

### 1b. Context7 & Cross-Skill Research

**Stripe library research** (based on current Stripe documentation and best practices):

#### Stripe Node.js SDK (stripe)
- **Current version**: 17.x (as of early 2026)
- **Key APIs for this spec**:
  - `stripe.checkout.sessions.create()` -- Stripe Checkout (hosted or embedded)
  - `stripe.subscriptions.create()` -- Subscription management
  - `stripe.webhooks.constructEvent()` -- Webhook signature verification
  - `stripe.customers.create()` -- Customer management
  - `stripe.prices.create()` -- Price/product management
  - `stripe.paymentIntents` -- For custom payment flows (alternative to Checkout)
- **Important patterns**:
  - Always verify webhook signatures using the webhook signing secret
  - Use idempotency keys for all write operations
  - Store Stripe customer IDs in your database, linked to user accounts
  - Use Stripe's test mode and test clock for subscription testing
  - Handle async payment confirmations (3D Secure, bank redirects)

#### Stripe Checkout vs. Custom Payment Flow
- **Stripe Checkout (recommended for most)**: Hosted or embedded payment page. Handles PCI compliance, 3D Secure, localization, and payment method display automatically. Less custom UI control.
- **Stripe Elements / PaymentIntent**: Full UI control. More implementation work. Must handle PCI compliance (SAQ A-EP or SAQ A with Elements iframe).
- **Recommendation**: Stripe Checkout for initial implementation -- faster, PCI-compliant out of the box, supports subscriptions natively.

#### Webhook Architecture
- Stripe sends events asynchronously via webhooks
- Critical events: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`, `payment_intent.succeeded`, `payment_intent.payment_failed`
- Must handle: signature verification, idempotency (events can be sent multiple times), event ordering, and retry logic
- Webhook endpoint must return 200 quickly (process asynchronously for heavy work)
- Stripe retries failed webhooks for up to 3 days with exponential backoff

#### Subscription Lifecycle
- States: `incomplete` -> `active` -> `past_due` -> `canceled` / `unpaid`
- Key events to handle: creation, renewal, payment failure, cancellation, plan changes (upgrades/downgrades), trial periods
- Stripe Billing Portal: hosted page for customers to manage subscriptions (cancel, change plan, update payment method). Significantly reduces implementation effort.

### 1c. Internet Research Summary

**Stripe integration best practices (2025-2026)**:

1. **Use Stripe Checkout for payment collection** -- It handles PCI compliance, SCA (Strong Customer Authentication), and 50+ payment methods automatically. Custom flows with Elements are only needed for deeply embedded payment UIs.

2. **Webhook-first architecture** -- Never rely solely on client-side redirect for payment confirmation. The `checkout.session.completed` webhook is the source of truth for successful payments. Client-side success pages should poll or wait for server confirmation.

3. **Idempotency everywhere** -- Use `Idempotency-Key` headers on all Stripe API calls. Process webhooks idempotently (store processed event IDs to avoid double-processing).

4. **Customer portal for subscription management** -- Stripe's Customer Portal handles plan changes, cancellations, and payment method updates. Building this from scratch is weeks of work that Stripe gives you for free.

5. **Separate webhook endpoints by concern** -- Some teams use a single `/webhooks/stripe` endpoint with a big switch statement. Better: use a single endpoint but dispatch to handler functions organized by domain (checkout, subscription, invoice).

6. **Store minimal payment data locally** -- Store Stripe customer IDs, subscription IDs, and subscription status. Do NOT store card numbers, tokens, or sensitive payment details. Query Stripe's API for detailed payment data when needed.

7. **Test with Stripe CLI** -- Use `stripe listen --forward-to localhost:3000/api/webhooks/stripe` during development to forward webhook events locally.

8. **Handle SCA and 3D Secure** -- Stripe Checkout handles this automatically. If using custom flows, must implement the 3D Secure authentication redirect flow.

### 1d. Library Comparison

#### Payment Integration Approach

| Approach | Complexity | PCI Scope | Subscription Support | Customization | Pick? |
|----------|-----------|-----------|---------------------|---------------|-------|
| Stripe Checkout (hosted) | Low | SAQ A (minimal) | Native | Limited (CSS only) | Recommended |
| Stripe Checkout (embedded) | Medium | SAQ A | Native | Moderate (embed in your page) | Alternative |
| Stripe Elements + PaymentIntent | High | SAQ A-EP | Manual | Full | Only if deep UI needed |
| Stripe Payment Links | Very low | SAQ A | Yes | Very limited | Not for apps |

**Recommendation**: Stripe Checkout (hosted mode) for the initial implementation. It handles PCI compliance, SCA, and subscriptions natively. Can migrate to embedded Checkout or Elements later if more UI control is needed.

#### Webhook Processing

| Library | Purpose | Stars | Maintained | Pick? |
|---------|---------|-------|-----------|-------|
| stripe (official SDK) | Built-in `stripe.webhooks.constructEvent()` | N/A (official) | Yes | Yes |
| svix | Webhook verification library | 2k+ | Yes | Alternative |
| No library (manual HMAC) | Raw signature verification | N/A | N/A | Not recommended |

**Recommendation**: Use the official Stripe SDK's built-in webhook verification. No additional library needed.

### 1e. Risk Assessment

1. **Security**: Payment data handling requires strict PCI DSS compliance. Using Stripe Checkout minimizes PCI scope to SAQ A. Must never log or store raw card data. Webhook signature verification is mandatory to prevent spoofed events.

2. **Reliability**: Webhooks can fail or arrive out of order. Need idempotent processing and a mechanism to reconcile state if webhooks are missed. Consider a periodic reconciliation job that checks Stripe API state against local database state.

3. **Race conditions**: Checkout completion redirect and webhook can arrive at different times. The webhook might arrive before the user's browser redirects to the success page, or vice versa. Both paths must handle this gracefully.

4. **Subscription state drift**: Local subscription status can drift from Stripe's actual state if webhooks are missed. Need a reconciliation strategy.

5. **Testing complexity**: Stripe's test mode is good but subscription lifecycle testing (trials, renewals, payment failures) requires Stripe Test Clocks. Webhook testing requires the Stripe CLI or mock webhook delivery.

6. **Currency and tax**: If the app serves multiple regions, need to handle multi-currency pricing and tax calculation (Stripe Tax or manual).

### 1f. Open Questions (for Interview)

1. What is the tech stack? (Language, framework, database, ORM)
2. Is there an existing user/authentication system? How are users managed?
3. What products are being sold -- one-time purchases, subscriptions, or both?
4. Are there existing database models for orders, products, or users?
5. What level of checkout UI customization is needed? (Stripe hosted page vs. embedded)
6. Does the app need to handle multiple currencies or tax calculation?
7. Is there an existing webhook infrastructure or is this the first webhook integration?

---

## Research Artifacts Saved

In a live session, the following file would be written:

**`.specs/stripe-payment-processing/research-01.md`** containing the full research findings above.

---

## Phase 2: Interview Round 1

Here are my findings and questions. I need your answers before I can write the spec.

### Research Summary

I researched Stripe payment integration patterns for e-commerce applications. The three capabilities you need -- checkout, subscriptions, and webhook handling -- are well-supported by Stripe's ecosystem. The recommended approach is **Stripe Checkout** (hosted mode) for payment collection, which handles PCI compliance, Strong Customer Authentication (3D Secure), and 50+ payment methods automatically. For subscriptions, Stripe Billing with the **Customer Portal** dramatically reduces implementation effort by giving customers a hosted page to manage their plans. Webhook handling is the backbone of reliable payment processing -- it's how your app learns about successful payments, failed renewals, and subscription changes asynchronously.

The architecture would follow a webhook-first pattern: the client creates a Checkout Session via your API, Stripe hosts the payment page, and your server receives webhook events for all state changes. Your database stores Stripe customer IDs, subscription IDs, and subscription status -- never raw payment data. A webhook handler verifies signatures, processes events idempotently, and updates local state accordingly.

Key risk areas include race conditions between client-side redirects and webhooks, subscription state drift if webhooks are missed, and the complexity of testing the full subscription lifecycle (trials, renewals, payment failures).

### Assumptions

Based on general e-commerce patterns, I'm making these assumptions. Please correct any that are wrong:

1. **Stripe Checkout (hosted mode)** is acceptable for the payment UI -- users will be redirected to Stripe's hosted page to complete payment, then redirected back. This avoids PCI compliance complexity.
2. **You want both one-time checkout AND subscriptions** -- some products are one-time purchases (e.g., physical goods) and some are recurring (e.g., membership plans).
3. **Stripe's Customer Portal** is acceptable for subscription management (canceling, changing plans, updating payment methods) rather than building a custom management UI.
4. **Webhooks are the source of truth** for payment/subscription state -- your app doesn't rely solely on the client-side redirect to confirm payments.

### Questions

I need your input on these before I can write a concrete spec:

**1. What is the tech stack?**
What language, framework, and database does the e-commerce app use? (e.g., Next.js + PostgreSQL, Django + MySQL, Express + MongoDB, etc.) Is there an ORM in use? What is the test framework? This determines the file paths, patterns, and library choices in the spec.

**2. How is user authentication handled?**
Is there an existing user/auth system? (e.g., NextAuth, Passport.js, Django auth, custom JWT) I need to know this because Stripe customers must be linked to your user accounts. If there's no auth system, that's a prerequisite that needs to be addressed first.

**3. What does the product catalog look like?**
Are products and prices managed in Stripe's dashboard, in your database, or synced between both? Do you have existing product/order database models? For subscriptions, how many plans do you anticipate (e.g., Basic/Pro/Enterprise)?

**4. What level of checkout customization do you need?**
- **Option A: Stripe Checkout (hosted)** -- Redirect to Stripe's page. Fastest to implement, fully PCI-compliant, but limited branding.
- **Option B: Stripe Checkout (embedded)** -- Stripe's checkout form embedded in your page. More integrated feel, still PCI-compliant.
- **Option C: Stripe Elements (custom)** -- Full control over the payment form UI. More work, but matches your exact design.

**5. What should happen on subscription payment failure?**
When a subscription renewal payment fails, what's the desired behavior? Options include:
- Grace period (e.g., 3 days retry then downgrade/cancel)
- Immediate access revocation
- Dunning emails (Stripe can handle these automatically)
- Custom in-app notifications

**6. Do you need multi-currency support or tax calculation?**
Does the app serve customers in multiple countries? Do you need automatic tax calculation (Stripe Tax) or is pricing fixed and region-agnostic?

### Proposed Rough Approach

Based on my research, here's the architecture I'd propose. Let me know your reactions:

**Phase 1 -- Foundation**: Set up Stripe SDK, configure API keys (env vars), create a webhook endpoint with signature verification, and set up the Stripe customer linkage (create a Stripe customer when a user signs up, store the `stripe_customer_id` in your user model).

**Phase 2 -- Checkout**: Implement the checkout flow. API endpoint to create Checkout Sessions (both one-time and subscription mode). Handle the `checkout.session.completed` webhook to fulfill orders. Build success/cancel redirect pages.

**Phase 3 -- Subscriptions**: Implement subscription management. Create subscription plans in Stripe. Build a pricing page. Handle subscription lifecycle webhooks (`invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted`). Integrate Stripe Customer Portal for self-service management.

**Phase 4 -- Webhook Hardening & Edge Cases**: Idempotent event processing (store processed event IDs). Handle race conditions. Add a reconciliation mechanism. Error monitoring and alerting for failed webhooks.

**Phase 5 -- Testing**: Unit tests for webhook handlers, integration tests with Stripe test mode, end-to-end tests for the full checkout and subscription flows, edge case tests for payment failures and subscription state transitions.

Does this phasing make sense? Would you reorder or split anything differently?

---

## Interview Artifacts

In a live session, the following file would be written:

**`.specs/stripe-payment-processing/interview-01.md`** containing the questions above (answers to be filled in after user responds).

---

## STATUS: WAITING FOR USER INPUT

**The forge workflow is paused at Interview Round 1.** I have presented:

1. Research findings (Stripe Checkout, webhook architecture, subscription lifecycle, library comparisons, risk assessment)
2. Four assumptions for the user to confirm or correct
3. Six targeted questions that research alone could not answer
4. A proposed five-phase approach for the user to react to

**Next steps after the user responds:**
- Save answers to `.specs/stripe-payment-processing/interview-01.md`
- Conduct deeper research (Phase 3 of forge) based on the specific tech stack, auth system, and product model the user describes
- Save findings to `.specs/stripe-payment-processing/research-02.md`
- Possibly run Interview Round 2 for trade-offs and edge cases
- Write the full SPEC.md once all ambiguity is resolved

**No application code has been written. No SPEC.md has been written.** The forge workflow produces only spec files, and the spec itself is written only after the interview loop completes.

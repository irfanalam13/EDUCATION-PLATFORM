# Billing & Subscriptions (Phase 11)

A complete SaaS monetization layer for the platform: subscription plans, a
gateway-agnostic payment abstraction (Stripe / Khalti / eSewa / manual), feature
gating with quota metering, the full invoice/refund/renewal lifecycle, and
revenue analytics. Backed by `apps/billing` with web (Next.js) and mobile (Expo)
UIs.

> Status: `apps/billing` — **25/25 tests green**; full backend suite **75/75**;
> web `next build` clean; mobile `tsc` clean.

---

## 1. Architecture

```
            ┌──────────────────────── apps/billing ────────────────────────┐
Web (Next)  │  views → services (lifecycle) → models                       │
Mobile(Expo)│              │            ├── entitlements (read side)         │
   │        │              │            └── features (tier → capability map) │
   └─ /api/billing/* ──────┤            gateways/ (Stripe·Khalti·eSewa·Manual)│
            │              └── analytics (MRR/ARR/churn/…)                    │
            └──────────────────────────────────────────────────────────────┘
```

- **`services.py`** is the *only* module that mutates subscription lifecycle
  state (subscribe / activate / cancel / renew / refund). Rules live in one place.
- **`entitlements.py`** is the read side: "what is this user allowed to do?",
  resolving across personal + institution subscriptions, with quota metering.
- **`features.py`** maps each plan **tier** → `{feature_key: limit}` (limit `0` =
  unlimited, `>0` = metered per calendar month). Single source of truth.
- **`gateways/`** — a `PaymentGateway` interface returning provider-agnostic
  dataclasses (`CheckoutSession`, `WebhookResult`, `PaymentResult`).

### Models (`models.py`)
`Plan`, `Subscription`, `InstitutionSubscription`, `Invoice`, `Payment`,
`Coupon`, `FeatureAccess`, `WebhookEvent`. `Subscription` and
`InstitutionSubscription` share an abstract `BillingState` (status, period,
gateway ids, trial/cancel fields). A partial unique constraint enforces **one
live subscription per user**.

---

## 2. Tiers & features

| Tier | Price (default) | Unlocks |
|---|---|---|
| **Free** | NPR 0 | Basic progress, **10 quizzes/month** (metered) |
| **Premium** | NPR 499/mo · 4990/yr | Unlimited quizzes, AI recommendations, AI tutor, study plans, advanced analytics, premium content |
| **Institution** | NPR 299/seat/mo | Everything in Premium + teacher dashboards, reporting, institution analytics, assignment management |

Seed the canonical plans:
```bash
python manage.py seed_plans
```

### Feature gating in code
The `FeatureGateMiddleware` attaches `request.entitlements`:
```python
if not request.entitlements.has(feat.FEATURE_AI_TUTOR):
    raise PermissionDenied("Upgrade to Premium for the AI tutor.")

# Metered features (returns False once the monthly quota is exhausted):
if not request.entitlements.consume(feat.FEATURE_UNLIMITED_QUIZZES):
    return Response({"detail": "Monthly quiz limit reached."}, status=402)
```
Or directly: `entitlements.has_feature(user, key)`, `entitlements.consume_quota(user, key)`.

---

## 3. Payment gateways

| Gateway | Use | Webhook auth | Refund |
|---|---|---|---|
| **Stripe** | International cards | `Stripe-Signature` HMAC-SHA256 + timestamp tolerance | API |
| **Khalti** | Nepal wallet | Lookup confirmation (callbacks unsigned) | Manual (dashboard) |
| **eSewa** | Nepal wallet | HMAC-SHA256 signed-field signature | Manual (portal) |
| **Manual** | Offline / default | `X-Webhook-Token` shared secret | Marked refunded |

The abstraction (`gateways/base.py`) means `services.py` never imports a
provider SDK. Add a gateway by implementing `PaymentGateway` and registering it
in `gateways/__init__.py`. **With no keys configured, `MANUAL` keeps the entire
flow working** (mirrors the AI app's keyless-fallback design) — checkout is
confirmed offline and the webhook is token-authenticated.

`httpx` performs the REST calls; it is imported lazily inside each method so the
app boots even if a gateway is unused.

---

## 4. API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/billing/plans/` | public | List active public plans (+ features) |
| GET | `/api/billing/subscription/` | user | Current subscription + entitlement snapshot |
| POST | `/api/billing/subscribe/` | user | Start a subscription (individual or institution) |
| POST | `/api/billing/cancel/` | user | Cancel now or at period end |
| GET | `/api/billing/coupon/validate/` | user | Validate a coupon + price preview |
| GET | `/api/billing/invoices/` · `/payments/` | user | Billing history (own rows only) |
| POST | `/api/billing/refund/` | **admin** | Refund a payment (full/partial), optional cancel |
| GET | `/api/billing/analytics/revenue/` | **admin** | MRR/ARR/churn/conversion/revenue-by-plan |
| POST | `/api/billing/webhook/<gateway>/` | signature | Gateway callbacks (idempotent via `WebhookEvent`) |

**Subscribe** returns `{status, requires_payment, checkout_url, checkout_payload,
invoice?}`. Free → instantly `ACTIVE`. Premium with a trial → `TRIALING`. Paid,
no trial → `INCOMPLETE` + an `OPEN` invoice; on a non-manual gateway,
`checkout_url` points to the hosted checkout.

---

## 5. Security & correctness

- **Webhook signatures** verified before any state change; failures → HTTP 400.
  Stripe additionally enforces a 5-minute timestamp tolerance (replay protection).
- **Idempotency**: every webhook is logged in `WebhookEvent` keyed on
  `(gateway, event_id)`; a duplicate short-circuits, so a payment is recorded once.
  Payments are also unique on `(gateway, gateway_payment_id)`.
- **Server-side amounts**: prices/discounts are computed from the DB plan +
  coupon, never trusted from the client.
- **Authorization**: refunds and revenue analytics require `IsBillingAdmin`
  (staff or role `ADMIN`); institution purchases require an institution admin.

---

## 6. Revenue analytics (`analytics.py`)
`mrr()`, `arr()`, `active_subscriber_count()`, `churn(days)`,
`conversion_rate(days)`, `revenue_by_plan()`, `revenue_collected(days)`, and a
one-call `overview()` behind `/api/billing/analytics/revenue/`. Yearly plans are
normalised to a monthly figure so MRR is comparable across intervals.

---

## 7. Frontend

**Web** (`frontend_w/src/features/billing/`, routes under `(student)/`):
`/pricing`, `/billing` (subscription), `/billing/upgrade`, `/billing/history`.
Calls go through the same-origin BFF proxy (`/api/backend`), so no CORS.

**Mobile** (`mobile/src/screens/billing/`, "Plans" tab): Pricing, Subscription,
Payment Success, Payment History (local stack inside `BillingScreen`). Hosted
checkout opens via `Linking.openURL`.

---

## 8. Environment variables
See `backend/.env.example` (Billing section). All gateway keys are optional —
unset means that gateway is unavailable and `MANUAL` is used. Set
`BILLING_DEFAULT_CURRENCY` (default `NPR`). On Render, add the keys you use to the
`edu-backend` env group.

```
BILLING_DEFAULT_CURRENCY=NPR
MANUAL_WEBHOOK_TOKEN=<random secret for offline confirmations>
STRIPE_SECRET_KEY= / STRIPE_WEBHOOK_SECRET=
KHALTI_SECRET_KEY= / KHALTI_SANDBOX=True
ESEWA_SECRET_KEY= / ESEWA_PRODUCT_CODE=EPAYTEST / ESEWA_SANDBOX=True
```

---

## 9. Deployment notes
- **Migrations**: `apps/billing/migrations/0001_initial` ships with the app; the
  Render/Docker entrypoint runs `migrate` on boot. Run `seed_plans` once after
  the first deploy (Render shell) to create the canonical plans.
- **Webhooks**: register each gateway's webhook to
  `https://<api-host>/api/billing/webhook/<gateway>/` (e.g. `…/stripe/`). The
  endpoint takes no JWT — it authenticates by signature.
- **Renewals/expiry**: `services.renew_subscription` / `expire_if_lapsed` are
  designed to be driven by a periodic Celery task; wire a beat schedule when the
  worker is enabled (see `render.yaml` / `DEPLOYMENT.md`).

---

## 10. Tests
`apps/billing/tests.py` — 25 tests: plan listing, subscribe (free/trial/paid/
coupon/single-live), feature gating + quota metering, cancel (period-end &
immediate), Stripe webhook (valid/bad-signature/idempotent), manual webhook,
refund, institution subscriptions (seats/member entitlement/authorization),
revenue analytics, and gateway signature unit tests (Stripe replay, eSewa
round-trip).
```bash
python manage.py test apps.billing
```

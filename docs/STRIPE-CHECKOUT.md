# My Little Pet Plus — Stripe Checkout setup

This repository's Stripe integration is deliberately **disabled by default**. The public website currently advertises Plus as coming soon, and the paid Plus build, persistent order/entitlement system, and delivery endpoint must be ready before taking live payments.

## What this integration does

- Creates a hosted Stripe Checkout Session on the server for a fixed USD amount.
- Uses Stripe's secret key only in Vercel server-side environment variables.
- Verifies webhook signatures against the raw request body.
- Forwards verified, paid international purchase events to a separately operated fulfillment endpoint using an HMAC signature.
- Does not treat a success-page redirect as proof of payment.
- Does not enable Stripe INR/domestic checkout. Stripe's India eligibility and domestic payment support depend on account approval. Configure a separately approved India-supported payment provider for domestic customers.

## Required Vercel environment variables

Set these only in Vercel Project Settings → Environment Variables. Never commit secrets to GitHub or put them in browser JavaScript.

- `STRIPE_SECRET_KEY`: Stripe secret API key for the selected environment.
- `STRIPE_WEBHOOK_SECRET`: signing secret for the deployed Stripe webhook endpoint.
- `PLUS_PRICE_USD_CENTS`: approved one-time international price in USD cents (for example, `199` means USD $1.99). Choose the actual price before enabling sales.
- `PLUS_SALES_ENABLED`: keep `false` until all launch checks are complete.
- `PLUS_FULFILLMENT_READY`: keep `false` until the fulfillment endpoint is deployed, verified and idempotent.
- `PLUS_FULFILLMENT_WEBHOOK_URL`: HTTPS endpoint that securely provisions the paid download/license and records the order.
- `PLUS_FULFILLMENT_WEBHOOK_SECRET`: long random secret shared with that fulfillment service.
- `PUBLIC_SITE_URL`: canonical HTTPS origin, for example `https://littlepet.in`.

Checkout remains unavailable unless all required variables are configured and both readiness flags are explicitly set to `true`.

## Endpoints

- `GET /api/plus-config` — safe public status; never returns secrets.
- `POST /api/create-checkout-session` — creates hosted Checkout for the international route.
- `POST /api/stripe-webhook` — Stripe webhook endpoint.

In Stripe Dashboard, configure the webhook endpoint URL as `https://YOUR-DOMAIN/api/stripe-webhook`. Subscribe to `checkout.session.completed` and `checkout.session.async_payment_succeeded`. Copy its signing secret to `STRIPE_WEBHOOK_SECRET`.

## Fulfillment endpoint contract

The receiver must:
1. Verify `X-MyLittlePet-Signature` as `sha256=<hex HMAC-SHA256(body, shared secret)>` using the exact raw request body.
2. Deduplicate on `eventId` (Stripe can retry webhooks).
3. Confirm the payload's session/payment identifiers against Stripe before granting entitlements if required by your threat model.
4. Persist the order, payment state, customer email, and entitlement/license.
5. Deliver only the purchased Plus build or a protected, expiring download link.
6. Return a 2xx only after the event is safely stored and queued for fulfillment. A failed delivery should be retried idempotently.

**Do not enable sales** while this endpoint is missing, if the Plus installer/license system is not ready, or before you test refunds, duplicate webhooks, failed payments, and email delivery.

## India and international sales

The international route uses USD and is intended only for eligible customers outside India. The customer selects a country and Stripe Checkout collects a billing address; the webhook refuses to forward purchases with a missing or Indian billing country for manual review. This is a safeguard, not a substitute for confirming Stripe account eligibility and the applicable export requirements.

Stripe documents that accounts based in India are invite-only and focused on eligible businesses expanding internationally: https://docs.stripe.com/india-accept-international-payments

Domestic Indian customers should be routed to an India-supported provider after that account is approved and its webhook is integrated. Do not enable INR through Stripe unless Stripe confirms that your account can accept those domestic transactions.

## Test before launch

1. Use Stripe test-mode keys and a test webhook secret first.
2. Set a test USD price in cents; leave live sales disabled.
3. Use Stripe test cards and inspect Checkout Session + webhook delivery in the Dashboard.
4. Test invalid webhook signatures, duplicate events, canceled checkout, unpaid sessions, missing country, India billing country, fulfillment timeout and retry.
5. Verify that no client-side redirect grants Plus.
6. Only switch to live keys after account approval, actual Plus delivery, terms/refund policy, support process and fulfillment are ready.

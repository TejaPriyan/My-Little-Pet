const Stripe = require('stripe');
const crypto = require('node:crypto');

module.exports.config = { api: { bodyParser: false } };

async function rawBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  return Buffer.concat(chunks);
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).send('Method not allowed');
  }
  if (!process.env.STRIPE_SECRET_KEY || !process.env.STRIPE_WEBHOOK_SECRET) {
    return res.status(503).send('Webhook is not configured');
  }

  let event;
  try {
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
    const signature = req.headers['stripe-signature'];
    if (!signature) return res.status(400).send('Missing Stripe signature');
    event = stripe.webhooks.constructEvent(await rawBody(req), signature, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (error) {
    console.warn('Stripe webhook signature verification failed:', error && error.message);
    return res.status(400).send('Invalid webhook signature');
  }

  const fulfillmentEvents = new Set(['checkout.session.completed', 'checkout.session.async_payment_succeeded']);
  if (!fulfillmentEvents.has(event.type)) return res.status(200).json({ received: true });

  const session = event.data.object;
  if (session.mode !== 'payment' ||
      session.metadata?.product !== 'mylittlepet_plus' ||
      session.metadata?.market !== 'international') {
    return res.status(200).json({ received: true, ignored: true });
  }

  // Never fulfill an unpaid checkout. Card-only Checkout is expected to be synchronous,
  // but the async event is handled defensively for future configuration changes.
  if (session.payment_status !== 'paid') return res.status(200).json({ received: true, unpaid: true });

  const actualCountry = session.customer_details?.address?.country;
  if (!actualCountry || actualCountry === 'IN') {
    // Do not fulfill a transaction that doesn't match the international-only route.
    // Leave a clear server-side signal for the operator to review/refund through Stripe.
    console.error('Paid Plus session needs manual review: unexpected/missing billing country', {
      eventId: event.id, sessionId: session.id, actualCountry: actualCountry || null,
    });
    return res.status(200).json({ received: true, reviewRequired: true });
  }

  const endpoint = process.env.PLUS_FULFILLMENT_WEBHOOK_URL;
  const secret = process.env.PLUS_FULFILLMENT_WEBHOOK_SECRET;
  if (!endpoint || !secret || process.env.PLUS_FULFILLMENT_READY !== 'true') {
    console.error('Paid Plus session received but fulfillment is not ready:', event.id);
    return res.status(500).send('Fulfillment is not configured');
  }

  const payload = JSON.stringify({
    eventId: event.id,
    eventType: event.type,
    sessionId: session.id,
    paymentIntentId: session.payment_intent,
    customerEmail: session.customer_details?.email || null,
    customerName: session.customer_details?.name || null,
    billingCountry: actualCountry,
    amountTotal: session.amount_total,
    currency: session.currency,
    product: 'mylittlepet_plus',
    paid: true,
  });
  const signature = crypto.createHmac('sha256', secret).update(payload).digest('hex');

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MyLittlePet-Signature': 'sha256=' + signature,
        'X-Stripe-Event-Id': event.id,
      },
      body: payload,
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) {
      console.error('Fulfillment endpoint rejected Stripe event:', event.id, response.status);
      return res.status(500).send('Fulfillment handoff failed');
    }
    return res.status(200).json({ received: true, forwarded: true });
  } catch (error) {
    console.error('Fulfillment handoff failed:', event.id, error && error.message);
    return res.status(500).send('Fulfillment handoff failed');
  }
};

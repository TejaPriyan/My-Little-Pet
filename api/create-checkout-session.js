const Stripe = require('stripe');

function salesReady() {
  const cents = Number.parseInt(process.env.PLUS_PRICE_USD_CENTS || '', 10);
  return process.env.PLUS_SALES_ENABLED === 'true' &&
    process.env.PLUS_FULFILLMENT_READY === 'true' &&
    Boolean(process.env.PLUS_FULFILLMENT_WEBHOOK_URL) &&
    Boolean(process.env.PLUS_FULFILLMENT_WEBHOOK_SECRET) &&
    Boolean(process.env.STRIPE_SECRET_KEY) &&
    Boolean(process.env.STRIPE_WEBHOOK_SECRET) &&
    Number.isInteger(cents) && cents >= 50;
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Fail closed until the paid Plus build and a real fulfillment endpoint are ready.
  if (!salesReady()) {
    return res.status(503).json({ error: 'My Little Pet Plus checkout is not open yet. No payment has been taken.' });
  }

  // This Stripe integration is for eligible international purchases only.
  // Indian domestic customers need a separately approved India-supported payment provider.
  const body = req.body && typeof req.body === 'object' ? req.body : {};
  if (body.market !== 'international' || body.countryCode === 'IN') {
    return res.status(400).json({ error: 'Stripe checkout is currently available only for eligible international customers.' });
  }

  const countryCode = typeof body.countryCode === 'string' ? body.countryCode.toUpperCase() : '';
  if (!/^[A-Z]{2}$/.test(countryCode) || countryCode === 'IN') {
    return res.status(400).json({ error: 'Choose your country of residence to continue.' });
  }

  const origin = process.env.PUBLIC_SITE_URL || 'https://littlepet.in';
  let originUrl;
  try {
    originUrl = new URL(origin);
    if (originUrl.protocol !== 'https:') throw new Error('HTTPS required');
  } catch {
    return res.status(500).json({ error: 'Payment configuration is incomplete.' });
  }

  try {
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
    const amount = Number.parseInt(process.env.PLUS_PRICE_USD_CENTS, 10);
    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      payment_method_types: ['card'],
      billing_address_collection: 'required',
      customer_creation: 'always',
      line_items: [{
        quantity: 1,
        price_data: {
          currency: 'usd',
          unit_amount: amount,
          product_data: {
            name: 'My Little Pet Plus',
            description: 'One-time purchase of My Little Pet Plus digital software. Delivery is provided only after payment verification.',
          },
        },
      }],
      metadata: {
        product: 'mylittlepet_plus',
        market: 'international',
        selected_country: countryCode,
        fulfillment_version: '1',
      },
      success_url: new URL('/payment-success.html?session_id={CHECKOUT_SESSION_ID}', originUrl).toString(),
      cancel_url: new URL('/pricing.html?checkout=cancelled', originUrl).toString(),
    }, {
      idempotencyKey: 'mylittlepet-plus-' + crypto.randomUUID(),
    });
    return res.status(200).json({ url: session.url });
  } catch (error) {
    console.error('Stripe Checkout session creation failed:', error && error.message);
    return res.status(502).json({ error: 'Could not start checkout. Please try again later.' });
  }
};

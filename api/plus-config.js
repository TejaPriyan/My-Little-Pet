// Public configuration only. Never return Stripe secrets to the browser.
module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const stripeConfigured = Boolean(process.env.STRIPE_SECRET_KEY && process.env.STRIPE_WEBHOOK_SECRET);
  const fulfillmentConfigured = Boolean(
    process.env.PLUS_FULFILLMENT_READY === 'true' &&
    process.env.PLUS_FULFILLMENT_WEBHOOK_URL &&
    process.env.PLUS_FULFILLMENT_WEBHOOK_SECRET
  );
  const globalEnabled = process.env.PLUS_SALES_ENABLED === 'true';
  const internationalPrice = Number.parseInt(process.env.PLUS_PRICE_USD_CENTS || '', 10);
  const internationalPriceValid = Number.isInteger(internationalPrice) && internationalPrice >= 50;

  // Stripe's India onboarding and domestic-payment eligibility is account-specific.
  // Do not expose India/INR checkout through Stripe by default.
  const internationalEnabled = stripeConfigured && fulfillmentConfigured && globalEnabled && internationalPriceValid;
  const usdPrice = internationalPriceValid ? (internationalPrice / 100).toFixed(2) : null;

  return res.status(200).json({
    salesEnabled: internationalEnabled,
    internationalEnabled,
    internationalCurrency: 'USD',
    internationalPrice: usdPrice,
    indiaEnabled: false,
    indiaMessage: 'India payments are not enabled through Stripe in this integration. Configure an India-supported payment provider for domestic customers.',
  });
};

(() => {
  const card = document.querySelectorAll('.edition-card')[1];
  if (!card) return;

  fetch('/api/plus-config', { cache: 'no-store' })
    .then(response => response.ok ? response.json() : null)
    .then(config => {
      if (!config) return;
      const panel = document.createElement('section');
      panel.className = 'plus-checkout-panel';
      panel.setAttribute('aria-live', 'polite');
      panel.style.marginTop = '1rem';

      if (!config.internationalEnabled) {
        const note = document.createElement('p');
        note.textContent = 'Secure checkout will appear here when Plus delivery is ready. No payment is available yet.';
        panel.append(note);
      } else {
        const label = document.createElement('label');
        label.htmlFor = 'plus-country';
        label.textContent = 'Country of residence';
        const select = document.createElement('select');
        select.id = 'plus-country';
        select.required = true;
        select.style.display = 'block';
        select.style.width = '100%';
        select.style.margin = '.5rem 0 1rem';
        select.style.padding = '.75rem';
        const countries = [
          ['','Choose your country'],['US','United States'],['GB','United Kingdom'],['CA','Canada'],
          ['AU','Australia'],['SG','Singapore'],['DE','Germany'],['FR','France'],['JP','Japan'],
          ['BR','Brazil'],['AE','United Arab Emirates'],['OTHER','Other country']
        ];
        for (const [value, text] of countries) {
          const option = document.createElement('option');
          option.value = value;
          option.textContent = text;
          select.append(option);
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'button dark';
        button.textContent = 'Buy Plus · $' + config.internationalPrice + ' USD';
        const note = document.createElement('p');
        note.textContent = 'International card checkout only. Your billing country is checked before delivery.';
        button.addEventListener('click', async () => {
          const countryCode = select.value;
          if (!countryCode || countryCode === 'OTHER') {
            note.textContent = 'Choose a supported country to continue.';
            return;
          }
          button.disabled = true;
          note.textContent = 'Opening secure Stripe Checkout…';
          try {
            const response = await fetch('/api/create-checkout-session', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ market: 'international', countryCode })
            });
            const result = await response.json();
            if (!response.ok || !result.url) throw new Error(result.error || 'Checkout could not start.');
            window.location.assign(result.url);
          } catch (error) {
            note.textContent = error.message || 'Checkout could not start. Please try again.';
            button.disabled = false;
          }
        });
        panel.append(label, select, button, note);
      }

      const domesticNote = document.createElement('p');
      domesticNote.textContent = config.indiaMessage || 'India domestic payments will be enabled separately with an India-supported provider.';
      panel.append(domesticNote);
      card.append(panel);
    })
    .catch(() => {
      // Keep the existing coming-soon content if the API is unavailable.
    });
})();

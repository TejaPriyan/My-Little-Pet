# My Little Pet website and mobile app

Buildless HTML, CSS and JavaScript. `dist/` is the complete deployable website.

The marketing page includes a Windows installer, real in-game screenshots, pet previews, a name demo and mobile installation guidance. `dist/app/` is an installable offline-capable web app with a local save, profile editing, pet/coat/style shopping, level-based rooms, daily goals, a treat hunt and JSON backups.

Run checks: `node tests/engine.test.mjs` and `node tests/assets.test.mjs`.

Serve `dist/` over HTTP for local development or HTTPS for mobile installation. No build step or third-party JavaScript is required. Service workers require HTTPS or localhost. Bump the cache version in `app/sw.js` when changing precached files. Existing active sessions finish using their old worker before a new version activates.

The static website does not contain any real player saves or account data. Mobile and desktop saves are independent. The hosted site's access is controlled by Sites separately from app code.

Windows release: 1.1.0, Windows 10/11 x64, unsigned installer. SHA-256 is in `dist/downloads/SHA256SUMS.txt`. Rebuild the installer with the parent `packaging/windows.iss` after rebuilding the Python application. Do not publish build-tools, local saves, logs or temporary folders.

Search metadata includes canonical/social tags, matching SoftwareApplication and FAQ JSON-LD, guide.html, sitemap.xml, robots.txt, llms.txt, and the supplied Google HTML verification file. Run `node tests/seo.test.mjs` too. Private hosting prevents indexing and Google ownership verification until public access is explicitly approved. The interactive app is noindex. Original code and assets are proprietary; see the parent LICENSE (GitHub export) and deployed terms.html.

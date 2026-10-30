# Free release — 30 October 2026

Free 1.1.0 remains available as the original Windows release. Plus 1.6.0 and the mobile room are now free. All game items still use earned coins. Optional support links point to https://buymeacoffee.com/tejapriyan and grant no features, coins or access.

Removed the local payment server, its environment and test-order data, checkout module, mobile entitlement/recovery components and the unavailable-release page. Player saves and existing itch.io statistics were not deleted. The site contains direct Windows downloads and the existing itch.io download link. Direct downloads do not currently have a server-side counter; itch.io statistics stay in the creator dashboard.

Mobile includes the desktop room artwork, seven pet species, four-pet household, seven foods, six toys, room bundles, movable/hidden furniture, pet reactions, personalities, friendship, daily goals, quiet/pause, backup import/export and offline caching. Added adjustable pet size, day/night and weather, Catch the Bug and Treat Drop. Fetch Relay and Garden Hurdles include watch mode. Treat Hunt, Memory Garden and Firefly Rhythm remain available.

Checks completed:
- Full existing desktop/gameplay, mobile engine, room-controller, art, static-page and packaging tests passed.
- Browser checks at website widths 1440, 390 and 320 pixels passed with no page errors or horizontal overflow.
- Phone-shaped Chromium checks covered onboarding, rendered pixel sprites, profile rename, persistent size/time/weather, second-pet adoption, taps without duplication, milk purchase and completed feeding, bed move/hide/restore, seven game dialogs, local save reload and offline reopening.
- Public bundle links and both installer SHA-256 hashes passed verification.
- Plus executable and Inno Setup installer compiled. An initial packaged smoke test passed before the final menu hitbox adjustment. Windows Application Control blocked the final unsigned executable; its packaged runtime remains unverified. Source-based real-Pygame rendering and menu tests passed after the adjustment. Security settings were not changed.

Limits: phone tests used browser emulation, not physical Android/iPhone devices. Windows overlays are unavailable on phones. Achievements and Windows-specific tray controls are not mirrored in the mobile interface. Desktop and mobile saves remain separate. The retained Plus save path includes the old `MyLittlePetPlusTest` folder name deliberately to preserve existing pets.

Build/preview instructions are in README.md. GitHub Pages uses `scripts/prepare-public-site.mjs` and its dedicated public release test. Domain DNS and payment-provider accounts are outside this release.

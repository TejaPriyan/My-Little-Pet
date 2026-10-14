# Release QA — 14 October 2026

Passed locally on Windows with Python 3.12 and Pygame 2.6.1:
- 28 original desktop tests, 4 feature tests, 8 upgrade tests.
- Profile migration, rename/progress retention, save roundtrip and Windows single-instance script.
- Mobile care, cooldowns, naps, shop, repeated rewards, levels, daily rollover and backup-validation tests.
- 115 website asset/link references, anchors, unique IDs, animation files and manifest checks.
- SEO checks for canonical URLs, descriptions, headings, matching visible FAQ structured data, sitemap and exact Google verification content.
- Windows installer hash matched release metadata. Earlier manual QA verified installed app startup and transparent desktop pet behavior.

Source review fixed local-PC paths in the packaging recipe, missing test/export temporary directories, platform-specific screenshot defaults, and name/species preview inconsistencies. CI runs the same checks on Windows and Linux; see GitHub Actions for its current result.

Limits: no exhaustive guarantee that all bugs are removed. Physical Android/iPhone installation and airplane-mode use remain unverified. The website remains private, so search indexing and Google verification cannot be completed yet. The Windows installer remains unsigned. Desktop and mobile saves are separate.

Publication excludes user saves, runtime/tool caches, backups, local hosting identifiers, temporary archives and logs. These were not deleted from the working computer when they were still useful for recovery or development.

# Development and release

Use Python 3.12 and Node.js 22. Install `requirements-dev.txt` in a virtual environment. Production runtime dependency is Pygame; Pillow is used by artwork export and fallback tests. Inno Setup is a separate Windows-only build prerequisite.

## Windows packaging
Run from the repository root on Windows:

```powershell
python -m PyInstaller --noconfirm --clean --distpath release --workpath packaging/build packaging/MyLittlePet.spec
# Run the installed Inno Setup compiler (ISCC.exe) on:
ISCC.exe packaging/windows.iss
```

Output goes to `my-little-pet-site/dist/downloads`. The recipe resolves paths relative to itself. No signing certificate is configured. Regenerate `release.json` and `SHA256SUMS.txt` after each rebuild, and verify installation and desktop transparency on a real Windows session. Keep third-party notices with all binaries. Do not overwrite an existing release number with different bytes when distributing updates publicly.

## Website / PWA
Static HTML/CSS/JS, no npm install or build step. Run all Node tests before publication. Bump `dist/app/sw.js`'s cache version when changing precached app files. Old clients may keep the previous worker until open app windows close. Hosting access is configured separately; GitHub visibility does not change website privacy.

## Artwork and testing
`python packaging/export_site_art.py` exports art from the real desktop renderer with isolated temporary saves. Run tests from the repository root. Tests may create ignored `review-temp`, `review-shots` or `upgrade-shots` output. Set `TEJA_SHOTS` to choose a screenshot directory. Never test by deleting a real player's save.

## Clean publication
The GitHub export intentionally excludes local runtimes, build tools/cache, player saves, debug logs, old backups, generated archives and Sites-specific hosting identity. Keep those files local if they are needed for development or recovery. The shipped installer is intentionally retained as a downloadable product artifact.

# My Little Pet 🐾

A cozy pixel-art companion by **Teja Priyan**: a Windows desktop pet and an installable mobile web app. Originally called Teja Pet.

![My Little Pet in its cozy room](my-little-pet-site/dist/assets/room.png)

[Website](https://my-little-pet-cozy-companion.greenlarch1024.chatgpt.site/) · [Mobile app](https://my-little-pet-cozy-companion.greenlarch1024.chatgpt.site/app/) · [Guide](https://my-little-pet-cozy-companion.greenlarch1024.chatgpt.site/guide.html) · [Report a bug](https://github.com/TejaPriyan/My-Little-Pet/issues)

> The website currently requires authorized private-preview access. This GitHub repository is public. Original project code and assets are proprietary, **not open source**. Free personal use of official releases is allowed under [LICENSE](LICENSE).

## Meet your companion

- Name yourself and your pet; receive personal greetings without resetting progress.
- Adopt a cat, puppy, bunny, or fox, with three coats per species.
- Feed, play, cuddle, rest, earn coins, level up, and unlock accessories and rooms.
- On Windows, let the pet roam over your desktop, follow the cursor, play with a ball, or nap at home. Drag it and use its right-click menu.
- Play Catch the Bug and Treat Drop on Windows; play Treat Hunt on mobile.
- Enjoy daily goals, achievements, optional sounds, quiet mode, and local saves.
- Install the mobile web app on Android or iPhone; export and restore mobile backups.

## Download and install

**Windows 10/11, 64-bit:** use the [official website download](https://my-little-pet-cozy-companion.greenlarch1024.chatgpt.site/#download), or open [the installer in this repository](my-little-pet-site/dist/downloads/MyLittlePet-1.1.0-Windows-Setup.exe) and choose **Download raw file**. Version 1.1.0 is about 16.1 MB and includes Python. Verify against [SHA256SUMS.txt](my-little-pet-site/dist/downloads/SHA256SUMS.txt). The installer is unsigned; download only if you trust the source. First launch asks for two names; press **D** after setup for desktop mode. Uninstalling retains pet saves.

**Android / iPhone:** open [the mobile app](https://my-little-pet-cozy-companion.greenlarch1024.chatgpt.site/app/) in Chrome on Android or Safari on iPhone. Choose Install app / Add to Home Screen (Safari: Share → Add to Home Screen). Wait for **Ready for offline visits** in Settings. This is a PWA, not an APK or IPA. The mobile pet stays inside the app.

## Saves and privacy

Installed Windows saves: `%LOCALAPPDATA%/MyLittlePet/save`. Source runs: `teja-pet/save`. Set `MY_LITTLE_PET_SAVE_DIR` to override for isolated development. Mobile saves live in browser local storage. **Desktop and mobile progress are separate.** Back up mobile progress before clearing browser data. The app has no added analytics, ads, or cloud account system; hosting can require sign-in and process connection logs. Website preview names travel in the app URL; nicknames are recommended.

## Run from source (owner or authorized development)

Requires Python 3.12 (tested), Pygame 2.6.1 and Node.js 22 for web checks. Python 3.12 is bundled in the Windows release.

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python teja-pet/main.py
```

Desktop overlay mode requires Windows. The room can run where Pygame supports a display. Launch from the repository root; the convenience Windows scripts use an available Python runtime.

Serve the buildless website locally:

```sh
python -m http.server 4173 --directory my-little-pet-site/dist
```

Visit `http://localhost:4173`. Service workers require HTTPS or localhost. Deploy the contents of `my-little-pet-site/dist` as static files; do not deploy local saves or development folders. See [development and release instructions](docs/DEVELOPMENT.md).

## Verify

```sh
python teja-pet/tests/test_game.py
python teja-pet/tests/test_new_features.py
python teja-pet/tests/test_upgrade.py
python teja-pet/tests/test_profiles.py
node my-little-pet-site/tests/engine.test.mjs
node my-little-pet-site/tests/assets.test.mjs
node my-little-pet-site/tests/seo.test.mjs
```

CI runs these checks on Windows and Linux with isolated test saves. Tests cover care, movement, upgrades, migration, rewards, backups, and static-site metadata; they cannot guarantee the absence of all bugs.

## Repository map

| Folder | Purpose |
| --- | --- |
| `teja-pet/` | Python desktop application, original art/audio, tests |
| `my-little-pet-site/dist/` | Static showcase, PWA, downloads and search metadata |
| `my-little-pet-site/tests/` | Mobile engine and website validation |
| `packaging/` | Portable PyInstaller recipe, Inno Setup recipe, notices |
| `.github/` | CI, issue forms, pull-request template and code ownership |
| `docs/` | Development, search readiness and QA notes |

## Current limitations

Windows overlay uses the primary monitor. Installer is unsigned. Phone hardware installation has not yet been verified. No desktop/mobile sync, native mobile overlay, APK, or IPA. A private website cannot be indexed or verified by Google until its owner explicitly enables public access. No SEO, GEO, or AEO ranking guarantees are made.

## Ownership and support

Copyright © 2026 **Teja Priyan (TejaPriyan)**. All rights reserved in original material. No reuse, rebranding, resale, or redistribution without written permission except as permitted by [LICENSE](LICENSE), third-party licenses, or law. GitHub's public-repository viewing/forking rights still apply. [Third-party notices](packaging/THIRD-PARTY-NOTICES.txt) remain intact.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CHANGELOG.md](CHANGELOG.md).

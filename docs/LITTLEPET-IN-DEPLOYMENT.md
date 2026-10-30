# Free release deployment

The website publishes Free and Plus Windows downloads and the mobile web app. All game access is free. Build with `node scripts/prepare-public-site.mjs`; it includes only public pages, art, the mobile app and the two approved installers. Test with `node my-little-pet-site/tests/public-release.test.mjs`.

GitHub Pages deploys the public-site directory. PUBLIC_SITE_URL supplied by configure-pages sets canonical URLs correctly, including the repository subfolder. Keep secrets, saves and build scratch folders out of deployment.

For littlepet.in, configure the custom domain in the GitHub Pages settings and point the GoDaddy DNS records to the values GitHub currently specifies. Verify HTTPS before sharing the custom domain. The working GitHub URL is https://tejapriyan.github.io/My-Little-Pet/. This release does not change DNS.

Optional support links go to https://buymeacoffee.com/tejapriyan. The game has no checkout, purchase recovery or license validation. Existing itch.io download statistics remain in its creator dashboard; direct website downloads do not have a built-in download counter. Windows and mobile game saves remain local.

Windows installers are unsigned. Browser checks do not replace testing on physical Android and iPhone devices.

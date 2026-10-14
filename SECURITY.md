# Security policy

## Supported versions
The current 1.1.x release line receives fixes. No formal support deadline or response-time guarantee is offered.

## Reporting a vulnerability
Do not post exploit details, credentials, or personal saves in public issues. Use GitHub's **Report a vulnerability** option if enabled. Otherwise open an issue asking the maintainer for a private reporting channel, without disclosing the vulnerability. Private vulnerability reporting must be enabled by the repository owner before it can be used.

## Data and distribution
Saves are local, mobile backup imports are validated, and original app code has no cloud sync or analytics. The current Windows installer is unsigned. Verify its checksum, but remember a checksum verifies file equality, not publisher identity. Never commit local saves, `.env`, credentials, or hosting tokens.

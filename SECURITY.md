# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in Suture, please **do not** open a
public GitHub issue. Instead, contact the maintainer privately so the issue
can be assessed and addressed before public disclosure.

Do not include real secrets, credentials, or API keys in any bug reports,
issues, or example files — even as placeholders.

## Scope

Suture is a local development diagnostic tool. It reads files from the
filesystem paths you provide and does not make network requests, run
subprocesses on your code, or transmit data anywhere.

Suture is **not** a full security scanner. It does not:

- scan for secrets in source code
- check for vulnerable dependencies
- audit authentication or authorisation logic
- replace tools like `trivy`, `bandit`, `semgrep`, or `pip-audit`

The ENV001 check (`.env` not in `.gitignore`) is a best-effort reminder, not
a guarantee that secrets are safe.

## Safe-fix philosophy

Suture's auto-fix system (`suture apply`) is intentionally conservative. It
will never delete files, modify source code, or remove dependencies. All safe
fixes are additive and easily reversible by hand.

If a proposed fix could cause data loss or unintended behaviour, it must
require explicit interactive confirmation or be left as a suggestion only.

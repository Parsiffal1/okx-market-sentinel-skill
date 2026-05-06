# Security Policy

## Supported scope

This repository is a **skill + runnable reference implementation**. Security-sensitive areas include:

- dashboard HTTP endpoints
- Telegram notifier credentials
- exchange credentials and API tokens
- `Semantic Compass` refresh flows that invoke external tools
- any local `.env` / config-based secret loading

## Reporting a vulnerability

If you discover a vulnerability:

1. **Do not open public GitHub issues for secrets, auth bypasses, or remote execution paths.**
2. Email the maintainer or contact privately through the repository owner account.
3. Include:
   - affected file(s)
   - reproduction steps
   - expected vs actual behavior
   - impact assessment
   - whether credentials or remote access are required

## Temporary hardening guidance

Until a private reporting workflow is expanded further, operators should:

- prefer `--host 127.0.0.1` for dashboard startup unless a reverse proxy and auth layer are in place
- never commit `.env`, runtime caches, or generated reports
- rotate any token that was ever pasted into chat logs or shell history
- avoid exposing dashboard POST endpoints directly to the public internet without authentication

## Disclosure expectations

Reasonable efforts will be made to acknowledge and triage valid reports quickly. Public disclosure should wait until the issue is understood and a mitigation path is prepared.

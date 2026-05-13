# Security Policy

## Scope
This repository is a **skill package**.

Most security risk in this repository comes from how the skill is used inside an agent runtime, especially when that runtime has access to:

- exchange credentials
- portfolio or holdings data
- browser / web-search tools
- private reporting channels
- internal research systems

## Supported versions
Only the latest version on `main` should be considered supported for security fixes.

## Safe usage guidelines

### 1. Use read-only market credentials whenever possible
If you connect exchange data, prefer read-only credentials. Do not give a monitoring skill withdrawal or order-placement permission unless you have an explicit, separate control layer outside this repository.

### 2. Do not commit local secrets
Never commit:
- `.env`
- local agent config files
- access tokens
- exchange keys
- chat bot tokens
- internal endpoints or private research URLs

This repository intentionally keeps `.env.example` generic and provider-agnostic.

### 3. Treat external information as untrusted input
A skill like this may read:
- web pages
- search snippets
- market summaries
- user-provided notes

That means downstream runtimes should assume external text can be noisy, stale, misleading, or adversarial.

### 4. Keep execution and interpretation separate
This skill is for monitoring and interpretation. If you connect it to execution workflows, use a separate policy layer to control order placement, position sizing, approval gates, and audit logs.

### 5. Review reporting destinations
If the skill writes to chat or messaging tools, confirm that the target channel is correct and appropriate for market-sensitive summaries.

## Reporting a vulnerability
If you find a security issue in the repository content itself, open a private security report through GitHub Security Advisories if available, or contact the repository maintainer privately before public disclosure.

Please include:
- what file or behavior is affected
- how to reproduce the problem
- whether secrets, credentials, or unsafe instructions are involved
- suggested remediation if known

# OpenClaw-Style Setup Notes

This repository follows a common standalone skill-repo layout:

- root README
- `skills/<skill-name>/SKILL.md`
- optional `references/` and `templates/`

## Fastest local OpenClaw path

Install OpenClaw and complete the normal onboarding flow first:

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

Then copy the skill into a personal OpenClaw skill directory:

```bash
mkdir -p ~/.agents/skills/market-monitoring
cp -r skills/crypto-market-sentinel ~/.agents/skills/market-monitoring/
```

OpenClaw loads personal agent skills from `~/.agents/skills`, so the skill becomes visible in a new session.

## If you only need the skill package

Use the subtree:

```text
skills/crypto-market-sentinel/
```

## If you want true ClawHub-style one-command installs

OpenClaw supports ClawHub-backed installs with:

```bash
openclaw skills install <skill-slug>
```

If this project is not yet published on ClawHub, publish it first:

```bash
npm i -g clawhub
clawhub login
clawhub skill publish ./skills/crypto-market-sentinel \
  --slug <your-skill-slug> \
  --name "OKX Market Sentinel" \
  --version 0.1.0 \
  --tags latest
```

You can also use the site publish flow after signing in:

```text
https://clawhub.ai/publish-skill
```

## If you want the runnable implementation too

Keep the entire repository, because the root contains:

- `scripts/`
- `dashboard/`
- `config/`
- `tests/`

## Packaging note

If you later publish this to a skill marketplace, keep `.clawhubignore` or equivalent ignore rules so runtime artifacts like `context/`, `reports/`, `.env`, and caches are not shipped.

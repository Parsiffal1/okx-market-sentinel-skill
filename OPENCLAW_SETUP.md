# OpenClaw-Style Setup Notes

This repository follows a common standalone skill-repo layout:

- root README
- `skills/<skill-name>/SKILL.md`
- optional `references/` and `templates/`

## If you only need the skill package

Use the subtree:

```text
skills/crypto-market-sentinel/
```

## If you want the runnable implementation too

Keep the entire repository, because the root contains:

- `scripts/`
- `dashboard/`
- `config/`
- `tests/`

## Packaging note

If you later publish this to a skill marketplace, keep `.clawhubignore` or equivalent ignore rules so runtime artifacts like `context/`, `reports/`, `.env`, and caches are not shipped.

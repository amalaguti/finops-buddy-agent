# Tasks: Foundation and AWS Identity

## 1. Repo and tooling

- [x] 1.1 Add or extend `pyproject.toml` with project metadata, Ruff (lint + format) config, and pytest settings
- [x] 1.2 Add `.pre-commit-config.yaml` with Ruff (and optionally pytest) hooks; document `pre-commit install` in README or docs
- [x] 1.3 Define Python package layout (e.g. `src/` or package dir) and ensure package is importable (e.g. `python -m <package>` or installable via `pip install -e .`)
- [x] 1.4 Add a minimal pytest test (e.g. placeholder or one test that imports the package) and ensure `pytest` runs from repo root

## 2. AWS identity (core)

- [x] 2.1 Implement session resolution: create boto3 session from default chain or from profile (env/profile name)
- [x] 2.2 Implement current identity: call STS GetCallerIdentity with resolved session and return account ID and principal ARN
- [x] 2.3 Implement list profiles: read shared config file (`~/.aws/config` or AWS_CONFIG_FILE) and return list of profile names (e.g. from `[profile <name>]` sections)

## 3. Master/Payer context

- [x] 3.1 Add support for optional Master/Payer account ID via config (e.g. env var or config file key)
- [x] 3.2 Implement “account context”: report current account ID and, when configured, whether it matches Master/Payer (display “master/payer” or “linked” or “unknown”)

## 4. CLI entrypoint

- [x] 4.1 Add CLI entrypoint (e.g. `python -m <package>` or console script) that can report current identity (whoami-style)
- [x] 4.2 Add CLI command or flag to list configured profiles (optional: filter or show current profile)
- [x] 4.3 Wire CLI to account context so user can see current account and Master/Payer status

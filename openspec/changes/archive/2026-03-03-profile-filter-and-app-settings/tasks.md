# Tasks: Profile filter and app settings

## 1. Dependencies and CLI bootstrap

- [x] 1.1 Add `python-dotenv` and `PyYAML` to Poetry dependencies (pyproject.toml)
- [x] 1.2 At start of `main()` in `cli.py`, load `.env` then `.env.local` with `override=True` so `.env.local` overrides all other sources

## 2. App settings module

- [x] 2.1 Create settings module (e.g. `src/finops_agent/settings.py`) with default config path: `$XDG_CONFIG_HOME/finops-agent/settings.yaml` or `~/.config/finops-agent/settings.yaml` when unset; respect `FINOPS_CONFIG_FILE` for custom path
- [x] 2.2 Load and parse YAML from config path; use key `excluded_profiles` (list). If file missing or invalid YAML, treat as no settings (empty excluded list); on parse error log and fall back
- [x] 2.3 Resolve excluded profiles: use YAML list as default; when `FINOPS_EXCLUDED_PROFILES` is set (comma-separated), use it as the full list (env replaces YAML). Expose `get_excluded_profiles()` (or equivalent) with lazy/cached load on first access

## 3. Profile listing filter

- [x] 3.1 Update `identity.list_profiles()` to accept or obtain excluded list from settings and return only profile names not in that list; when excluded list is empty, return all configured profiles unchanged

## 4. Pytest unit tests

- [x] 4.1 Add tests for app-settings: default XDG path when FINOPS_CONFIG_FILE unset, custom path when FINOPS_CONFIG_FILE set, missing/invalid YAML does not fail app
- [x] 4.2 Add tests for app-settings: YAML-only excluded list when env unset, env overrides YAML excluded list, no exclusions when neither YAML nor env provide list
- [x] 4.3 Add tests for dotenv: .env.local overrides .env for same variable, missing .env or .env.local does not error
- [x] 4.4 Add tests for aws-identity: list profiles excludes configured names when settings define excluded list, list all profiles when excluded list is empty

## 5. Lint and format

- [x] 5.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues before considering the change application complete

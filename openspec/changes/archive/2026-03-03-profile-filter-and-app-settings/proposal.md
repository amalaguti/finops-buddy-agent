# Proposal: Profile filter and app settings

## Why

Users need to hide certain AWS profiles from the CLI (e.g. personal or test profiles) when listing or selecting accounts. The excluded list should be configurable via app defaults (YAML) and overridable by environment, with support for local overrides via `.env.local` so secrets and personal choices stay out of version control.

## What Changes

- **Profile exclusion:** The CLI SHALL support an "excluded profiles" list. When listing profiles (e.g. `finops profiles`), only profiles not in this list are shown. Defaults come from app settings; env can override.
- **App settings YAML:** Introduce an app settings file (e.g. `config/settings.yaml` or repo-root YAML) that holds default configuration, including `excluded_profiles` (or equivalent). File is optional; if missing, no profiles are excluded by default.
- **Env override:** An environment variable (e.g. `FINOPS_EXCLUDED_PROFILES`, comma-separated) SHALL override the YAML default when set. Env wins over YAML.
- **python-dotenv and .env.local:** Use python-dotenv to load `.env` then `.env.local` at startup so that env vars (including the override) can be defined in `.env` or overridden locally in `.env.local` without committing them.

## Capabilities

### New Capabilities

- `app-settings`: Load app configuration from a YAML file (defaults) and environment variables (override). Support loading env from `.env` and `.env.local` via python-dotenv (`.env.local` overrides `.env`). Expose resolved settings (e.g. excluded profiles list) to the rest of the app.

### Modified Capabilities

- `aws-identity`: List configured profiles SHALL respect the excluded-profiles list from app settings; only profiles not in the excluded list are returned when listing profiles.

## Impact

- **Code:** New or extended config/settings module (YAML parse, env resolution, dotenv load); `identity.list_profiles()` (or CLI) filters by excluded list; CLI entrypoint loads dotenv before running commands.
- **Dependencies:** Add `python-dotenv` and a YAML library (e.g. PyYAML) to project dependencies.
- **Files:** New app settings YAML (path TBD in design); optional `.env.example`; `.env` and `.env.local` remain gitignored.
- **Behavior:** Purely additive; no breaking changes if settings file or env are absent (no exclusions).

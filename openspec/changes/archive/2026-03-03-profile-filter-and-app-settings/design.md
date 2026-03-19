# Design: Profile filter and app settings

## Context

Today the app has no app-level config file; only env vars (e.g. `FINOPS_MASTER_ACCOUNT_ID` in `config.py`). Profile listing in `identity.list_profiles()` returns all profiles from `~/.aws/config` with no filtering. This change adds a settings layer: YAML defaults, env override (FINOPS_ prefix), and dotenv so `.env` and `.env.local` can supply or override vars. Constraints: FINOPS_ prefix for all app env vars; no breaking changes when settings or env are absent.

## Goals / Non-Goals

**Goals:**
- Single source of "resolved" app settings (excluded profiles list, and room for future keys).
- **XDG-compliant default** for the settings YAML: use `$XDG_CONFIG_HOME/finops-agent/settings.yaml` (e.g. `~/.config/finops-agent/settings.yaml` when `XDG_CONFIG_HOME` is unset). Optional file; if missing, no exclusions by default.
- **`.env.local` overrides all other sources:** Load dotenv at startup so that **`.env.local` wins over everything** — YAML defaults, `.env`, and any pre-existing shell env. Implement by loading `.env` first, then `.env.local` with `override=True`, so values in `.env.local` always take effect.
- `list_profiles()` (and thus `finops profiles`) returns only profiles not in the excluded list.

**Non-Goals:**
- Changing how AWS credentials or region are resolved (still boto3/default chain).
- Glob or pattern matching for excluded profiles (exact name match only for now).

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Default YAML path** | XDG: `$XDG_CONFIG_HOME/finops-agent/settings.yaml`; if `XDG_CONFIG_HOME` unset use `~/.config` (Linux/macOS). Optional env override e.g. `FINOPS_CONFIG_FILE` to point at a custom path (e.g. repo-local file). | XDG Base Directory compliant; user-level config in standard location. Custom path allows repo or CI override. |
| **Env var for excluded list** | `FINOPS_EXCLUDED_PROFILES` | Matches FINOPS_ prefix rule; clear name. |
| **Format of env list** | Comma-separated (e.g. `profile-a,profile-b`) | Simple, shell-friendly, easy to parse with `str.split(",")` and strip. |
| **Override semantics** | Env replaces the entire excluded list when set (no merge with YAML) | Predictable: "override" means env wins; avoids ambiguity. |
| **When to load dotenv** | At CLI entrypoint (start of `main()` in `cli.py`) | Ensures all commands see env; avoids import-side effects if we load in a config module. |
| **Dotenv precedence** | Load `.env` then `.env.local` with **`override=True`** for `.env.local` | `.env.local` must override whatever is set by other means (YAML, `.env`, shell). Last load with override guarantees that. |
| **When to load YAML** | Lazy or at first access to settings; cache result | Avoid re-reading file every time; optional file means "no file → no exclusions" (empty list). |
| **YAML library** | PyYAML | Standard, widely used; add to Poetry deps. |

## Risks / Trade-offs

| Risk | Mitigation |
|------|-------------|
| Missing YAML or invalid YAML | Treat missing file as "no settings" (empty excluded list). On parse error, log and fall back to empty or env-only. |
| `.env.local` not found | `load_dotenv(".env.local")` is a no-op if file missing; no error. |
| Excluded list large or complex | Keep to comma-separated list; no globs in this change. Document in README. |

## Migration Plan

No deployment or rollback; purely additive. Optional settings file and optional env; existing behavior unchanged if both absent.

## Open Questions

- Exact YAML key name: `excluded_profiles` vs `excludedProfiles` — prefer snake_case for YAML to match Python. Confirm in implementation.

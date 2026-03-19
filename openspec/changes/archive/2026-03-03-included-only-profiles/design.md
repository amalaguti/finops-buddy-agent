## Context

The app already has app-settings (YAML + env, dotenv) and profile listing that filters by **excluded_profiles** (blocklist). Users need an **allowlist** option: when `included_only_profiles` is set, only those profiles are in scope. Same config sources (XDG YAML, `FINOPS_CONFIG_FILE`, `FINOPS_*` env, `.env.local` override) and same precedence rules apply.

## Goals / Non-Goals

**Goals:**

- Add resolution of `included_only_profiles` in settings (YAML key + `FINOPS_INCLUDED_ONLY_PROFILES` env); expose a single resolved list to callers.
- In `list_profiles()`, when included_only is non-empty, return intersection of AWS config profiles and included list; otherwise keep current blocklist behavior.
- One active mode: allowlist takes precedence over blocklist when both are configured.
- No new dependencies; reuse existing settings and identity modules.

**Non-Goals:**

- Changing how excluded_profiles or dotenv work.
- Supporting merge of included and excluded lists.
- New CLI flags for this; configuration remains file/env only.

## Decisions

### Decision 1: Expose `get_included_only_profiles()` in settings

Add a function parallel to `get_excluded_profiles()` that returns the resolved included_only list (from YAML and/or `FINOPS_INCLUDED_ONLY_PROFILES`). Reuse the same config path and env-over-YAML precedence. Use a separate cache (e.g. `_INCLUDED_ONLY_PROFILES_CACHE`) and clear it in `reset_settings_cache()` for tests.

**Rationale:** Keeps identity module unaware of YAML/env details; single place for resolution and caching.

### Decision 2: Precedence: allowlist over blocklist

When `get_included_only_profiles()` returns a non-empty list, `list_profiles()` uses only that list (intersection with config). When it returns empty, `list_profiles()` uses `get_excluded_profiles()` as today. No merging: if both are set, allowlist wins.

**Rationale:** Matches user expectation ("only these" is stricter than "exclude those"); avoids ambiguous behavior when both are set.

### Decision 3: YAML key and env var names

Use `included_only_profiles` in YAML and `FINOPS_INCLUDED_ONLY_PROFILES` in the environment (comma-separated, same format as excluded). Parsing and validation mirror excluded_profiles (list of non-empty strings, strip whitespace).

**Rationale:** Consistency with existing naming and env prefix rule; minimal cognitive load.

## Risks / Trade-offs

- **Risk:** Users might expect "exclude A and include only B" to merge. **Mitigation:** Document clearly that only one mode is active; allowlist overrides blocklist.
- **Risk:** Typo in profile name in included list yields silent omission. **Mitigation:** Same as for excluded list; document that names must match config exactly; optional future: log or warn when an included name is not in config.

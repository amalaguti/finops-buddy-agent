## 1. Settings module — included_only_profiles

- [x] 1.1 Add `_load_yaml_included_only_profiles(path)` to load `included_only_profiles` from YAML (return [] if missing/invalid)
- [x] 1.2 Add `_env_included_only_profiles()` returning list from `FINOPS_INCLUDED_ONLY_PROFILES` or None
- [x] 1.3 Add `get_included_only_profiles()` with lazy load and cache; env overrides YAML; clear cache in `reset_settings_cache()`
- [x] 1.4 In `reset_settings_cache()`, clear both excluded and included caches

## 2. Identity — list_profiles allowlist

- [x] 2.1 In `list_profiles()`, call `get_included_only_profiles()`; when non-empty, return intersection of config profiles and included list; when empty, keep current excluded_profiles behavior

## 3. Lint and format

- [x] 3.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues

## 4. Pytest unit tests

- [x] 4.1 Add tests for `get_included_only_profiles`: YAML-only, env overrides YAML, empty when unset, caching, `reset_settings_cache()` clears cache
- [x] 4.2 Add tests for `list_profiles()` with allowlist: only included profiles returned, allowlist takes precedence over blocklist when both set, empty allowlist uses blocklist

## 5. Documentation

- [x] 5.1 Document `included_only_profiles` and `FINOPS_INCLUDED_ONLY_PROFILES` in README (Configuration section); note allowlist vs blocklist and precedence

## 6. Branch and apply

- [x] 6.1 Ensure work is done on a non-main branch (create one if on main); do not implement or run apply on main

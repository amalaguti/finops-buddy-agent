## Why

Users need a way to restrict the CLI to a fixed set of AWS profiles (allowlist) instead of excluding profiles one by one. When `included_only_profiles` is set, only those profiles are in scope; any other profile is effectively excluded. This supports "only these accounts" workflows (e.g. production-only) alongside the existing "exclude these" (blocklist) behavior.

## What Changes

- Add **included_only_profiles** to app settings: YAML key and optional env var `FINOPS_INCLUDED_ONLY_PROFILES` (comma-separated), with same precedence as existing settings (env overrides YAML; `.env.local` overrides all).
- When **included_only_profiles** is non-empty, profile listing returns only profiles that are both configured in AWS config and present in the included list. When it is empty or absent, existing behavior applies (excluded_profiles blocklist, if any).
- **Excluded vs included**: Only one mode is active. If `included_only_profiles` is non-empty, it takes precedence; otherwise `excluded_profiles` is used. No merge of the two lists.
- Document new settings and env var in README (Configuration section).

## Capabilities

### New Capabilities

None. This change extends existing app-settings and aws-identity behavior.

### Modified Capabilities

- **app-settings**: Add resolution of `included_only_profiles` from YAML (key `included_only_profiles`) and from `FINOPS_INCLUDED_ONLY_PROFILES`; expose resolved list to the app; when non-empty, allowlist mode is active.
- **aws-identity**: When allowlist (included_only_profiles) is non-empty, "List configured profiles" returns only profiles that are in the included list; otherwise keep current behavior (exclude only those in excluded_profiles).

## Impact

- `src/finops_agent/settings.py`: Add loading and resolution of `included_only_profiles`; add `get_included_only_profiles()` (or equivalent) and ensure list_profiles can use it; cache invalidation for tests.
- `src/finops_agent/identity.py`: `list_profiles()` uses included-only list when non-empty (intersection of AWS config profiles and included list); otherwise unchanged.
- `README.md`: Document `included_only_profiles` and `FINOPS_INCLUDED_ONLY_PROFILES` in Configuration.
- `tests/`: New or extended tests for settings resolution and for list_profiles with allowlist.

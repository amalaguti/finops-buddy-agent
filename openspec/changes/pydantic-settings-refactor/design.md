## Context

Project rule: all app env vars use **`FINOPS_`** prefix — Pydantic `SettingsConfigDict(env_prefix="FINOPS_")` aligns. YAML overlay may use a **custom settings source** or post-load merge with documented precedence (match today: env overrides YAML for listed keys).

## Goals / Non-Goals

**Goals:** One **validated** settings object at startup; field-level types; optional **strict** mode for production.

**Non-Goals:** Remove YAML in v1 of refactor; change semantic meaning of existing keys.

## Decisions

| Topic | Direction |
|-------|-----------|
| Library | **Pydantic v2** + `pydantic-settings` (Poetry dependency). |
| YAML | Custom source or load YAML into nested model once. |
| Strict mode | `FINOPS_SETTINGS_STRICT=1` fails on unknown keys if desired (optional). |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large bang refactor | Phased: introduce model; wrap old getters; remove duplicates in follow-up PRs. |

## Migration Plan

1. Add model + tests shadowing current getters.  
2. Switch internal modules to model.  
3. Delete redundant functions; ruff enforce module size.

## Open Questions

- Whether **nested** `agent.*` in YAML maps to nested models or flat aliases.

# Design: Add CLI version flag

## Context

The `finops` CLI uses argparse with a top-level parser (global `--profile`) and subparsers for commands. Version is already defined in `finops_agent.__version__`. We need to expose it via a standard flag without requiring a subcommand.

## Goals / Non-Goals

**Goals:**
- Add `--version` and `-V` that print version and exit.
- Use `finops_agent.__version__` as the single source of truth.

**Non-Goals:**
- Changing how version is stored or bumping the version.
- Adding version to subcommands.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Implementation** | argparse `action="version"` with `version="%(prog)s {__version__}"` | Standard pattern; parser handles print and exit. No extra branch in main(). |
| **Source of version** | Import `__version__` from `finops_agent` | Single source of truth; no duplication. |

## Risks / Trade-offs

- None for this small change.

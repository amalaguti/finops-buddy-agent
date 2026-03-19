## Context

The FinOps CLI uses a root `argparse` parser with `--profile` and subparsers for `whoami`, `profiles`, `context`, `costs`, and `verify`. Only the root parser and the `verify` subparser define `--profile`. So `finops costs --profile X` fails because the `costs` subparser does not accept `--profile`. The fix is to add the same `--profile` / `-p` option to the `costs` subparser so either ordering works.

## Goals / Non-Goals

**Goals:**

- Support both `finops --profile X costs` and `finops costs --profile X` with identical behavior.
- Reuse the same pattern already used for the `verify` subcommand.

**Non-Goals:**

- Changing cost logic, output format, or other subcommands.
- Adding new global or subcommand-specific options.

## Decisions

- **Add `--profile` / `-p` to the `costs` subparser**: Mirror the root parser and `verify` subparser. The subparser’s `args.profile` will be set when the user passes `--profile` after `costs`; when the user passes `--profile` before `costs`, the root parser sets `args.profile`. In both cases the existing dispatch (`return func(args.profile)`) continues to work because the namespace is shared and the last parser to run wins; we rely on the root parser running first, then the subparser, so `finops costs --profile X` will set `args.profile` on the namespace. For `finops --profile X costs`, the root parser sets `args.profile` and the costs subparser doesn’t override it (no duplicate dest). So a single `--profile` on the costs subparser is sufficient; no change to dispatch logic needed.
- **No change to `cmd_costs` signature**: It already takes `profile: str | None`; no modification required.

## Risks / Trade-offs

- **Minimal**: Single-file change in `cli.py`. Risk of regression is low; existing tests and a quick manual check of both orderings cover it.

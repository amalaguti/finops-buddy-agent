## Why

Users run `finops costs --profile payer-profile` and get "unrecognized arguments: --profile payer-profile" because the root parser defines `--profile` but the `costs` subparser does not. With argparse, options after the subcommand name are parsed by the subparser, so `--profile` must be accepted by the `costs` subparser for that invocation order to work. The same fix was already applied to the `verify` subcommand; this change applies it to `costs`.

## What Changes

- **CLI**: The `costs` subcommand will accept `--profile` / `-p` on its subparser so that both orderings work: `finops --profile X costs` and `finops costs --profile X`.
- No change to cost logic, output, or other commands.

## Capabilities

### New Capabilities

- `costs-profile-flag`: The `costs` subcommand accepts the `--profile` (and `-p`) option so that profile can be specified before or after the subcommand name; behavior and output are unchanged.

### Modified Capabilities

- None.

## Impact

- **Code**: `src/finops_agent/cli.py` only — add `--profile` / `-p` to the `costs` subparser and ensure the existing `cmd_costs(profile)` dispatch continues to receive the resolved profile (from either root or subparser).
- **APIs / dependencies**: None.
- **Users**: Invocations like `finops costs --profile payer-profile` will work instead of failing.

# Proposal: Defer agent warm-up to lifespan, demo ARN masking, and env sample

## Why

Three issues were addressed: (1) Running the API module (e.g. importing `finops_buddy.api.app`) triggered agent warm-up at import time, which starts MCP tool providers and caused pytest and other test runs to hang during collection. (2) In demo mode, the account details pane on `/demo` showed the full ARN including the assumed-role session name (e.g. user email), exposing PII. (3) There was no sanitized environment template for users to copy; adding one improves onboarding and keeps secrets out of the repo.

## What Changes

- **Defer warm-up to lifespan:** Agent warm-up (when `FINOPS_AGENT_WARM_ON_STARTUP` is true) SHALL run only when the FastAPI/ASGI app starts (e.g. uvicorn lifespan), not when the app module is imported. This prevents test runs and any code that imports the API from triggering MCP startup and long blocks.
- **Demo ARN masking:** When demo mode is active, the account context response SHALL mask the ARN by replacing the assumed-role session name (the part after the last `/` in `assumed-role/.../session-name`) with a fixed placeholder (e.g. `john.doe@finops.buddy`) so the account details pane does not expose real emails or session identifiers.
- **Env sample file:** Add a sanitized `env.local.sample` file at the project root (no leading dot) listing all supported `FINOPS_*` environment variables with placeholder values, so users can copy it to `.env.local` and fill in their own. Document it in README.

No breaking changes: existing behavior when running the server is unchanged; only the timing of warm-up and the demo masking/UX are improved.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- **backend-api:** Add requirement that agent warm-up (when enabled) runs in the FastAPI lifespan (startup) only, not at module import time.
- **demo-mode:** Add requirement that when demo mode is active, the account context ARN SHALL mask the assumed-role session name (e.g. replace with a fixed placeholder) in addition to account ID masking.

## Impact

- **Code:** `src/finops_buddy/api/app.py` (lifespan context manager, remove module-level warm call), `src/finops_buddy/api/demo.py` (ARN session-name masking in `mask_response_data` / `_mask_arn_value`), new file `env.local.sample` at project root.
- **Docs:** README (or config section) updated to mention `env.local.sample` and how to use it.
- **Tests:** `tests/test_demo.py` (test for ARN session-name masking); full test suite runs without hanging because app import no longer triggers warm-up.

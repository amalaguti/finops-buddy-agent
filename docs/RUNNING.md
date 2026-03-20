# Running FinOps Buddy

How to run the **HTTP API**, **web UI**, **full rebuild**, **Docker**, and **tests with settings** on Windows.

## HTTP API (backend)

The project includes an HTTP API for use by the FinOps Buddy web UI. The UI is designed for **desktop use only** (mobile support is out of scope). The API exposes the same capabilities as the CLI: list profiles, account context, current-month costs, and chat with FinOps Buddy (streaming response). The web UI includes an **Artifacts** basket in the top navbar: when the agent generates charts (e.g. from cost data), they appear there for preview and download; artifacts are session-only and do not persist across page reloads.

**How to run:** Start the server with **`finops serve`**. It reads host and port from settings or env (`FINOPS_SERVER_HOST`, `FINOPS_SERVER_PORT`); default is `127.0.0.1:8000`. Use **`finops serve --reload`** to auto-restart the server when code changes (development). For advanced users, the FastAPI app can be run directly: **`uvicorn finops_buddy.api:app --host 127.0.0.1 --port 8000 --reload`** (after `poetry install`).

**Hosted UI runtime:** When the compiled frontend bundle is present in the package, `finops serve` also serves the web UI from the same origin:

- **UI entrypoints:** `GET /` and `GET /mcp_tooling_status`
- **API endpoints:** `GET /version` (running version + optional commit), `GET /profiles` (profile list plus configured master profile), `GET /context`, `GET /costs`, `GET /costs/dashboard`, `GET /status`, `GET /tooling`, `POST /chat`

This is the normal end-user runtime model: one process, one port, one URL.

**Endpoints:** `GET /version` (returns `version`, `commit`, `display` for nav bar; commit from `FINOPS_GIT_SHA` when set), `GET /profiles` (returns `profiles` plus `master_profile` so the UI can prioritize the payer profile without hardcoding names), `GET /context` (account context; optional `?profile=` or `X-AWS-Profile` header), `GET /costs` (current-month costs by service; optional profile), `GET /costs/dashboard` (full dashboard: current-month costs by AWS service only, by linked account, by marketplace; top 10 cost optimization recommendations; cost anomalies in the last 3 days; Savings Plans utilization and coverage; optional query param `savings_plans_months=1|2|3`; optional profile; when `X-Demo-Mode: true`, account identifiers are masked), `POST /chat` (message body with `message`, optional `messages`, optional `profile`; response is Server-Sent Events). OpenAPI docs at `/docs` when the server is running.

**Dashboard and IAM:** The web UI sidebar shows a costs dashboard with six sections (costs by AWS service, by account, by marketplace; optimization recommendations; anomalies; Savings Plans). Data is loaded from `GET /costs/dashboard`. For optimization recommendations and anomalies to be non-empty, the AWS credentials need Cost Optimization Hub (`cost-optimization-hub:ListRecommendations`) and Cost Anomaly Detection (`ce:GetAnomalies`) permissions in addition to Cost Explorer (`ce:GetCostAndUsage`, `ce:GetSavingsPlansUtilization`, `ce:GetSavingsPlansCoverage`). If those are missing, the dashboard still returns 200 with empty lists for those sections.

When `FINOPS_MASTER_PROFILE` is set, the HTTP API builds a **single long-lived chat agent and MCP tool stack** from that AWS profile (typically the payer SSO profile) and reuses it across all `/chat`, `/status`, and `/tooling` calls. The UI profile selector still controls which account context and costs are shown, and the chat prompt tells the agent which account(s) to focus on, but the underlying AWS session for tools is always the master profile. When unset, the API falls back to building agents per-request/profile as before (higher latency per chat but no shared payer session).

**Single-user and credentials:** The backend runs in single-user mode. Credentials and profile selection work like the CLI: the process uses the same credential chain (e.g. `AWS_PROFILE`, shared config, settings file). Per-request profile can be set via query parameter `profile` or header `X-AWS-Profile`. No separate auth system; the API is intended for local or behind-a-proxy use.

**CORS:** Set `FINOPS_CORS_ORIGINS` (or `server.cors_origins` in settings) to allow a frontend origin (e.g. `http://localhost:5173` for the default Vite dev server). When unset, no CORS middleware is applied (same-origin only).

Details for all env vars: [Configuration](./CONFIGURATION.md).

## Web UI (frontend)

A React single-page app in `frontend/` lets you chat with FinOps Buddy, view profiles, account context, MCP status, tools, and costs in the browser. For the full picture (CLI, backend, and UI), see [Architecture](./ARCHITECTURE.md).

**Normal runtime:** When the hosted frontend bundle has been built, start **`poetry run finops serve`** and open **http://127.0.0.1:8000**. FastAPI serves both the web UI and the API from the same origin, so no frontend dev server or CORS configuration is needed for normal usage.

**How to run backend and UI together (development):**

1. Start the API: **`poetry run finops serve`** (default `http://127.0.0.1:8000`).
2. Set CORS so the browser can call the API: e.g. `FINOPS_CORS_ORIGINS=http://localhost:5173` (or add `http://localhost:5173` to `server.cors_origins` in your settings file).
3. Start the UI: **`cd frontend && npm install && npm run dev`**. The app is served at **http://localhost:5173** (single sidebar layout).

**Frontend API base URL:** The UI calls the backend using the base URL from **`VITE_API_BASE`**. In hosted mode, if this variable is unset, the frontend uses the same origin that served the page. In Vite development mode, the default remains `http://127.0.0.1:8000`. Set it in `frontend/.env` or `frontend/.env.local` to override either mode (e.g. `VITE_API_BASE=http://127.0.0.1:8000`). Restart the Vite dev server after changing this.

**Build the hosted frontend bundle:** To generate the frontend bundle used by `finops serve`, run:

```powershell
cd frontend
npm run build:hosted
```

This writes the compiled SPA into `src/finops_buddy/webui/`, which is the asset location served by FastAPI and included in the Python package metadata.

## Build flow (full rebuild)

When you need a **new Python package or Docker image** that includes the latest web UI (e.g. after changing frontend or for a release), use this order. The frontend build writes into `src/finops_buddy/webui/`; Poetry and Docker both use `src/`, so the frontend must be built first or the package/image will not contain the latest UI.

1. **Frontend into webui** — Build the hosted bundle so `src/finops_buddy/webui/` is up to date:
   ```bash
   cd frontend && npm run build:hosted
   ```
2. **Poetry build** — Package the project (including the built webui) into sdist/wheel:
   ```bash
   poetry build
   ```
   Do not run `poetry build` before the frontend build when frontend or webui changed, or the wheel/sdist will have stale or missing UI assets.
3. **Docker build** (optional) — Build the image so it includes the same `src/` with the built webui:
   ```bash
   docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t finops-buddy .
   ```
   On Windows PowerShell, use the same command; the shell expands the `git` subcommand. Omit `--build-arg GIT_SHA=...` for version-only display in the nav bar.

For **local development** you can run `finops serve` after step 1 (or use the Vite dev server with CORS). For **releases or CI**, run 1 → 2, and 3 if you ship via Docker.

## Testing configuration (including Windows)

On Windows, the default settings path works: when `XDG_CONFIG_HOME` is unset, the app uses `%USERPROFILE%\.config\finops-agent\settings.yaml`.

**Option A — Repo YAML via `FINOPS_CONFIG_FILE` (simplest)**

1. Create a YAML file in the repo (e.g. `config/settings.yaml`):

```yaml
excluded_profiles:
  - account-A
  - account-B
```

2. Run with the env var set (PowerShell):

```powershell
$env:FINOPS_CONFIG_FILE = ".\config\settings.yaml"
poetry run finops profiles
```

Profiles listed in `excluded_profiles` will be omitted. Clear the override with `Remove-Item Env:FINOPS_CONFIG_FILE`.

**Option B — Default path (Windows or Linux/macOS)**

1. Create the directory (PowerShell on Windows):

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\finops-agent"
```

2. Create `settings.yaml` there with an `excluded_profiles` list (e.g. `account-A`, `account-B`).

3. Ensure `FINOPS_CONFIG_FILE` and `FINOPS_EXCLUDED_PROFILES` are not set (so the YAML is used), then run `poetry run finops profiles`.

## Docker

FinOps Buddy can run in a Docker container for simpler deployment.

### Prerequisites

- Docker Desktop running
- **Build order:** Build the frontend into webui first, then build the image (see [Build flow](#build-flow-full-rebuild) above). Run `cd frontend && npm run build:hosted` before `docker build` so the image includes the latest UI.
- AWS credentials configured in `~/.aws`
- Environment config in `.env.local`

### Quick start

```bash
# 1) Build frontend into webui first (required so the image has the latest UI)
cd frontend && npm run build:hosted && cd ..

# 2) Build the image (optional: add commit SHA to version display with --build-arg GIT_SHA=$(git rev-parse --short HEAD))
docker build -t finops-buddy .

# Run with docker-compose (recommended)
docker-compose up -d

# Access the web UI at http://localhost:8000
```

### What the container does

- Runs `finops serve` on port 8000
- Mounts `~/.aws` for AWS credentials (read-only)
- Mounts `.env.local` for environment configuration
- Includes `uv` for MCP server support
- Includes WeasyPrint dependencies for PDF export

### Notes

- **AWS SSO**: If using SSO profiles, run `aws sso login` on your host before starting the container
- **AWS credentials mount**: The `~/.aws` volume is mounted writable (not read-only) because botocore needs to write to `sso/cache/` during SSO token operations
- **MCP servers**: First run may be slow as uvx downloads packages (cached for subsequent runs)
- **Rebuild**: Follow the [build flow](#build-flow-full-rebuild): run `cd frontend && npm run build:hosted` first (if frontend or webui changed), then `docker build -t finops-buddy .` (or with `--build-arg GIT_SHA=$(git rev-parse --short HEAD)` to show version and commit in the nav bar).

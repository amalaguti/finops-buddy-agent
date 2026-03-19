## Context

FinOps Buddy is a desktop-first application that runs locally using Poetry. Users want the option to run it in a Docker container for easier deployment and isolation, without modifying how they configure AWS credentials or environment variables.

Current state:
- Application runs via `poetry run finops serve`
- Frontend is pre-built into `src/finops_buddy/webui/`
- Configuration via `.env.local` and/or `config/settings.yaml`
- AWS credentials from local `~/.aws/` directory
- MCP servers spawned via `uvx` (requires `uv` installed)
- PDF export requires WeasyPrint system libraries

## Goals / Non-Goals

**Goals:**
- Provide a Dockerfile that builds a production-ready image
- Provide docker-compose.yml for easy local orchestration
- Support AWS credential access via volume mount
- Support `.env.local` configuration via volume mount
- Include `uv` for MCP server functionality
- Include WeasyPrint dependencies for PDF export
- Expose port 8000 for web UI and API access

**Non-Goals:**
- Multi-container orchestration (separate frontend/backend containers)
- Hot-reload or development mode inside container
- Cloud deployment configuration (ECS, Kubernetes, etc.)
- Building the frontend inside the container (pre-built locally)
- Secrets management beyond file mounts

## Decisions

### Decision 1: Single-stage Python image with system dependencies

**Choice**: Use `python:3.11-slim` as base with apt packages for WeasyPrint and uv.

**Alternatives considered**:
- Multi-stage build (Node + Python): Rejected because frontend is pre-built locally
- Alpine-based image: Rejected because WeasyPrint dependencies are complex on Alpine
- Distroless: Rejected because we need apt packages and shell access for debugging

**Rationale**: Slim Debian base provides best balance of size and compatibility for WeasyPrint's Cairo/Pango dependencies.

### Decision 2: Poetry for dependency installation

**Choice**: Install Poetry in the image, use `poetry install --no-dev` with virtualenvs disabled.

**Alternatives considered**:
- Export requirements.txt and use pip: More complex to maintain
- Use pip with pyproject.toml: Poetry lock ensures reproducibility

**Rationale**: Poetry lockfile guarantees exact versions; using `virtualenvs.create false` installs directly to system Python, keeping image simpler.

### Decision 3: Volume mounts for credentials and config

**Choice**: Mount `~/.aws` to `/root/.aws` (writable) and `.env.local` to `/app/.env.local` (read-only).

**Alternatives considered**:
- Copy credentials into image: Security risk
- Pass credentials as environment variables: Works but verbose for SSO profiles
- Use IAM roles: Only works in cloud environments
- Read-only mount for `~/.aws`: **Does not work** - botocore needs write access to `sso/cache/` for SSO token operations

**Rationale**: Volume mounts work seamlessly with existing AWS profiles, SSO sessions, and config files. No secrets baked into image. The `~/.aws` mount must be writable because botocore writes temporary files to `sso/cache/` during SSO credential resolution.

### Decision 4: Install uv for MCP server support

**Choice**: Install `uv` via pip so `uvx` commands work for MCP servers.

**Alternatives considered**:
- Disable all MCP servers: Loses key functionality
- Pre-install MCP servers: Complex and version-coupling
- Use Docker-based MCP servers: Nested Docker complexity

**Rationale**: Installing uv is lightweight (~50MB) and enables full MCP functionality with same uvx commands.

### Decision 5: Bind to 0.0.0.0 inside container

**Choice**: Run `finops serve --host 0.0.0.0` to accept connections from host.

**Rationale**: Default 127.0.0.1 binding would only accept connections from inside the container. 0.0.0.0 allows the mapped port to work from the host.

## Risks / Trade-offs

**[Image size ~600-800MB]** → Acceptable for desktop use; WeasyPrint dependencies are the main contributor. Could provide a "lite" image without PDF support in future.

**[MCP servers start slowly on first run]** → uvx downloads packages on first use. Subsequent runs use cache. Document this behavior.

**[AWS SSO token refresh]** → SSO tokens in ~/.aws may expire. User must `aws sso login` on host before container can use them. Document this.

**[Filesystem permissions on Windows]** → Volume mounts from Windows may have permission issues. Use appropriate user mapping if needed.

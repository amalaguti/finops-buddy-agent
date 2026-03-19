## Why

FinOps Buddy currently runs via Poetry (`poetry run finops serve`) which requires Python and Poetry installed locally. Users want to run the application in a Docker container for simpler deployment, isolation, and portability on their desktop machines.

## What Changes

- Add a `Dockerfile` for building the FinOps Buddy container image
- Add a `docker-compose.yml` for easy local container orchestration
- Add a `.dockerignore` to keep the image lean
- Include `uv` in the image for MCP server support
- Include WeasyPrint system dependencies for PDF export
- Support mounting AWS credentials (`~/.aws`) for profile access
- Support mounting `.env.local` for configuration
- Expose port 8000 for the web UI and API

## Capabilities

### New Capabilities

- `docker-deployment`: Container-based deployment for FinOps Buddy, including Dockerfile, docker-compose, and .dockerignore with support for AWS credentials, environment configuration, and MCP servers.

### Modified Capabilities

(none - this is packaging/deployment, not behavioral changes)

## Impact

- **New files**: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- **Dependencies**: None changed (image uses existing Poetry lockfile)
- **Build process**: Users can now build with `docker build` and run with `docker-compose up`
- **Documentation**: README should be updated to document Docker usage

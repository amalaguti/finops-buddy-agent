## 1. Setup

- [x] 1.1 Create feature branch for docker-deployment (if on main, switch before implementing)

## 2. Docker Configuration Files

- [x] 2.1 Create `.dockerignore` to exclude node_modules, .git, tests, __pycache__, .venv, and other unnecessary files
- [x] 2.2 Create `Dockerfile` with python:3.11-slim base, WeasyPrint system deps, Poetry install, uv install, and finops serve entrypoint
- [x] 2.3 Create `docker-compose.yml` with port 8000 mapping, ~/.aws volume mount, and .env.local volume mount

## 3. Verification

- [x] 3.1 Build the Docker image with `docker build -t finops-buddy .`
- [x] 3.2 Run the container with `docker-compose up` and verify web UI at http://localhost:8000
- [x] 3.3 Verify AWS credentials work by checking profiles endpoint (`GET /profiles`)
- [x] 3.4 Verify MCP servers can start (uvx command available in container)

## 4. Quality Checks

- [x] 4.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 4.2 Run `poetry run pytest` to ensure existing tests pass

## 5. Documentation

- [x] 5.1 Update README.md with Docker usage section (build, run, volume mounts)

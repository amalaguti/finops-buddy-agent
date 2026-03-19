### Requirement: Docker image builds successfully

The project SHALL include a `Dockerfile` that builds a container image with all dependencies needed to run FinOps Buddy.

#### Scenario: Build image with docker build
- **WHEN** user runs `docker build -t finops-buddy .` from the project root
- **THEN** the build completes successfully and produces a tagged image

#### Scenario: Image includes Python dependencies
- **WHEN** the image is built
- **THEN** all Poetry dependencies from pyproject.toml are installed

#### Scenario: Image includes WeasyPrint system dependencies
- **WHEN** the image is built
- **THEN** WeasyPrint can generate PDFs (libpango, libcairo, fonts are present)

#### Scenario: Image includes uv for MCP servers
- **WHEN** the image is built
- **THEN** the `uv` and `uvx` commands are available for MCP server execution

### Requirement: Container runs finops serve

The container SHALL run the `finops serve` command on startup, exposing the web UI and API.

#### Scenario: Container starts and listens on port 8000
- **WHEN** user runs the container with port 8000 mapped
- **THEN** the FinOps Buddy web UI is accessible at http://localhost:8000

#### Scenario: Container binds to all interfaces
- **WHEN** the container starts
- **THEN** the server binds to 0.0.0.0 so host port mapping works

### Requirement: AWS credentials accessible via volume mount

The container SHALL support mounting the host's `~/.aws` directory for AWS credential access.

#### Scenario: Container uses mounted AWS credentials
- **WHEN** container is run with `~/.aws` mounted to `/root/.aws`
- **THEN** the application can access AWS profiles configured on the host

#### Scenario: SSO profiles work with mounted credentials
- **WHEN** user has active SSO session on host and mounts `~/.aws`
- **THEN** the application can use SSO profiles without re-authentication

### Requirement: Environment configuration via .env.local mount

The container SHALL support mounting `.env.local` for environment configuration.

#### Scenario: Container loads mounted .env.local
- **WHEN** container is run with `.env.local` mounted to `/app/.env.local`
- **THEN** the application loads environment variables from the mounted file

#### Scenario: Mounted .env.local overrides defaults
- **WHEN** `.env.local` contains `FINOPS_MASTER_PROFILE=my-profile`
- **THEN** the application uses `my-profile` as the master profile

### Requirement: Docker Compose for easy orchestration

The project SHALL include a `docker-compose.yml` that configures volume mounts and port mapping for local use.

#### Scenario: Start with docker-compose up
- **WHEN** user runs `docker-compose up` from the project root
- **THEN** the container starts with AWS credentials and .env.local mounted

#### Scenario: Docker Compose maps port 8000
- **WHEN** the docker-compose stack is running
- **THEN** http://localhost:8000 serves the FinOps Buddy web UI

### Requirement: Dockerignore keeps image lean

The project SHALL include a `.dockerignore` file that excludes unnecessary files from the build context.

#### Scenario: Node modules excluded
- **WHEN** the image is built
- **THEN** `frontend/node_modules` is not included in the build context

#### Scenario: Git and test files excluded
- **WHEN** the image is built
- **THEN** `.git`, `tests/`, and `__pycache__` are not included in the build context

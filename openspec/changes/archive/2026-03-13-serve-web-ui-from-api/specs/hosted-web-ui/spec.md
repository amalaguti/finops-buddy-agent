## ADDED Requirements

### Requirement: FastAPI serves the compiled web UI

The system SHALL support a hosted runtime mode in which the same FastAPI process serves the compiled web UI and the existing backend API. When hosted frontend assets are available, requests for the UI entrypoint and known SPA routes SHALL return the compiled frontend entrypoint, and requests for bundled asset paths SHALL return the corresponding static files.

#### Scenario: Root path returns the hosted web UI

- **WHEN** the application is started with `finops serve` and the hosted frontend assets are present
- **THEN** a request to `/` returns the compiled web UI entrypoint from the FastAPI process

#### Scenario: Known SPA route returns the hosted web UI

- **WHEN** the application is started with `finops serve`, the hosted frontend assets are present, and a browser requests a supported SPA route such as `/mcp_tooling_status`
- **THEN** the FastAPI process returns the compiled web UI entrypoint so the frontend can render that route

#### Scenario: Static asset request returns bundled file

- **WHEN** the application is started with `finops serve`, the hosted frontend assets are present, and a browser requests a compiled frontend asset path
- **THEN** the FastAPI process returns that static asset file with a successful response

### Requirement: Hosted web UI preserves backend API behavior

The hosted web UI runtime SHALL preserve the existing backend API behavior. Serving the frontend SHALL NOT change the behavior of the existing API routes or documentation routes, and frontend fallback handling SHALL NOT intercept valid API requests.

#### Scenario: API routes remain available in hosted mode

- **WHEN** the application is started with `finops serve` in hosted mode and a client requests an existing API endpoint such as `/profiles`
- **THEN** the FastAPI process returns the API response for that endpoint rather than the web UI entrypoint

#### Scenario: Unknown API route is not masked by SPA fallback

- **WHEN** the application is started with `finops serve` in hosted mode and a client requests an unknown API route
- **THEN** the FastAPI process returns an API-style not-found response instead of the web UI entrypoint

### Requirement: Hosted web UI uses same-origin API by default

The hosted web UI SHALL call backend endpoints on the same origin by default when served by FastAPI. The frontend MAY support an explicit API base override for development or advanced deployments, but normal hosted runtime use SHALL NOT require separate API origin configuration.

#### Scenario: Hosted UI calls same-origin API without override

- **WHEN** a user opens the hosted web UI served by `finops serve` and no explicit frontend API base override is configured
- **THEN** the frontend sends its API requests to the same origin that served the web UI

#### Scenario: Development override remains possible

- **WHEN** a developer configures an explicit frontend API base override for the SPA
- **THEN** the frontend uses that configured API base instead of same-origin requests

### Requirement: Packaged application includes hosted frontend assets

The application package SHALL include the built frontend assets required for hosted UI mode so that an installed app can serve the web UI without requiring Vite or a separate frontend server at runtime.

#### Scenario: Installed app can serve hosted UI without Vite

- **WHEN** a user installs the packaged application and runs `finops serve` in an environment where the packaged frontend assets are present
- **THEN** the application serves the hosted web UI without requiring `npm run dev` or a Vite server at runtime

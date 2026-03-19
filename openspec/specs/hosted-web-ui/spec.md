# Capability: hosted-web-ui

## Requirements

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

### Requirement: Demo route in React router

The web UI SHALL support a `/demo` route that activates demo mode for all child components and API calls.

#### Scenario: /demo route renders app in demo mode

- **WHEN** user navigates to `/demo`
- **THEN** the main application layout renders
- **AND** demo mode context is set to true

#### Scenario: /demo route supports sub-paths

- **WHEN** user navigates to `/demo/mcp_tooling_status`
- **THEN** the tooling status page renders in demo mode

### Requirement: Demo mode header in API calls

When demo mode is active, all API calls from the frontend SHALL include the `X-Demo-Mode: true` header.

#### Scenario: Profile fetch includes demo header

- **WHEN** demo mode is active
- **AND** the frontend fetches `/profiles`
- **THEN** the request includes `X-Demo-Mode: true` header

#### Scenario: Chat request includes demo header

- **WHEN** demo mode is active
- **AND** the frontend sends a chat message
- **THEN** the `/chat` request includes `X-Demo-Mode: true` header

### Requirement: Demo mode badge in header

When demo mode is active, the UI header SHALL display a visible "DEMO" badge to indicate masked data.

#### Scenario: Demo badge visible in header

- **WHEN** demo mode is active
- **THEN** a badge with text "DEMO" is visible in the page header

#### Scenario: Demo badge not visible in normal mode

- **WHEN** demo mode is NOT active
- **THEN** no demo badge is displayed

### Requirement: Profile selector shows masked names

When demo mode is active, the profile selector dropdown SHALL display masked profile names.

#### Scenario: Profile dropdown shows fake names

- **WHEN** demo mode is active
- **AND** the profile selector dropdown is opened
- **THEN** profile names shown are the masked/fake versions from the API response

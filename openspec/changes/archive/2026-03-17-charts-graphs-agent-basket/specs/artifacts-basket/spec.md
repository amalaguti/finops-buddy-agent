# Capability: artifacts-basket

## ADDED Requirements

### Requirement: Artifacts basket in web UI

The web UI SHALL provide an Artifacts basket—a UI section that collects generated artifacts (e.g. charts) from the conversation. The basket SHALL display a list of artifacts with the ability to preview and download individual items. The basket SHALL be placed in the top navbar (e.g. dropdown or expandable) or as a right-side panel. Artifacts SHALL NOT persist across page reloads (session-only).

#### Scenario: Artifacts basket appears in layout

- **WHEN** the user views the chat interface
- **THEN** an Artifacts basket is accessible (e.g. via navbar button or right-side panel)
- **AND** the basket indicates when no artifacts have been collected yet

#### Scenario: New chart appears in artifacts basket

- **WHEN** the agent returns a response containing an embedded chart image (data URI)
- **THEN** that chart is added to the artifacts basket
- **AND** the user can see a thumbnail or representation of the artifact in the basket

#### Scenario: User downloads single artifact

- **WHEN** the user selects an artifact in the basket and triggers download
- **THEN** the artifact is downloaded to the user's device (e.g. as a PNG file)
- **AND** the file has a sensible name (e.g. derived from title or timestamp)

#### Scenario: User can download all artifacts

- **WHEN** the user triggers "Download all" (or equivalent) and the basket has one or more artifacts
- **THEN** all artifacts are downloaded (e.g. as separate files or as a ZIP)
- **AND** each file has a unique, sensible name

### Requirement: Chat SSE stream supports artifact events

The `/chat` SSE stream SHALL support an optional `artifact` event. When the backend detects a generated chart in the agent's response, it MAY emit one or more `artifact` events with payload `{ type, title, content }` before the `message` event. The frontend SHALL handle `artifact` events by adding the artifact to the basket. The `artifact` event is additive; existing events (`progress`, `message`, `done`, `error`) SHALL remain unchanged.

#### Scenario: Frontend receives artifact event

- **WHEN** the frontend consumes the chat SSE stream and receives an `artifact` event with valid payload
- **THEN** the frontend adds the artifact to the basket state
- **AND** the artifact appears in the basket UI

#### Scenario: Chat works without artifact events

- **WHEN** the backend does not emit any `artifact` events (e.g. no charts in response)
- **THEN** the chat completes normally with `message` and `done` events
- **AND** the basket remains empty or unchanged

### Requirement: ChatView renders embedded images

The ChatView SHALL render embedded images in assistant messages, including images with `data:` URI sources. Images SHALL be styled appropriately (e.g. max-width, rounded corners) for readability within the conversation.

#### Scenario: Chart image displays inline in message

- **WHEN** an assistant message contains markdown with an embedded image (`![alt](data:image/png;base64,...)`)
- **THEN** the image is rendered inline in the chat message
- **AND** the image is styled consistently with the conversation layout

#### Scenario: External image URLs are restricted

- **WHEN** an assistant message contains an image with a non-data, non-same-origin `src`
- **THEN** the frontend SHALL either not load the image or restrict loading to a configured allowlist
- **AND** data URI images SHALL always be allowed

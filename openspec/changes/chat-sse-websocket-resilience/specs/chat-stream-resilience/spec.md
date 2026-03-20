# chat-stream-resilience Specification

## Purpose

Reduce **fragile long-running chat streams** in cloud deployments by defining **client reconnection** and optional **server resume** or an alternate **WebSocket** transport.

## ADDED Requirements

### Requirement: SSE client automatic reconnect

When using **Server-Sent Events** for chat, the web client SHALL **automatically reconnect** after a transient connection drop (network error, HTTP 5xx, or stream EOF) up to a **documented maximum** number of attempts and backoff. The UI SHALL indicate reconnect in progress without blocking the user from starting a new message per documented UX.

#### Scenario: Reconnect after brief network loss

- **WHEN** the SSE connection drops during an in-progress assistant response
- **THEN** the client attempts reconnection according to the configured backoff policy

### Requirement: Last-Event-ID header when resuming SSE

When the server supports stream resumption, the client SHALL send **`Last-Event-ID`** (or documented equivalent) on reconnect with the **last successfully processed** event id. When the server does **not** support resumption, the client SHALL omit resume headers and the server SHALL document **non-resumable** streams.

#### Scenario: Server ignores unknown event id safely

- **WHEN** the client sends a `Last-Event-ID` the server cannot honor
- **THEN** the server responds with a documented behavior (e.g. new stream from start or error with clear message)

### Requirement: Document ALB + Fargate stream failure modes

The project SHALL document in deployment or architecture docs: **sticky sessions**, **task restart** impact on SSE, and recommended **idle timeout** / **keep-alive** settings for ALB and clients.

#### Scenario: Operators can find stream guidance

- **WHEN** a reader opens the referenced deployment documentation
- **THEN** the document explains SSE vs WebSocket trade-offs and reconnect expectations for Fargate

### Requirement: Optional WebSocket chat endpoint

The system MAY expose an optional **WebSocket** chat endpoint for cloud deployments, feature-flagged, with **authentication** consistent with the HTTP API (cookies/headers as deployed). When disabled, behavior SHALL remain SSE-only.

#### Scenario: WebSocket disabled by default locally

- **WHEN** the WebSocket feature flag is unset or off
- **THEN** only SSE chat is available and tests need not start a WS server

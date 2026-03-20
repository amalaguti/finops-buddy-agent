# multi-instance-runtime-cache Specification

## Purpose

Define how **in-process and optional shared caches** behave when **more than one** application instance (Fargate task) serves traffic, so operators understand **latency, staleness, and warm-up**.

## ADDED Requirements

### Requirement: Documented cache coherence model for multi-task deployment

The project SHALL document in **deployment or architecture documentation** the **cache coherence model** when multiple Fargate tasks run: either (1) **each task maintains independent** in-memory caches and may incur **redundant** warm-up or lookups, or (2) **shared external cache** (e.g. Redis) is used for **named cache domains** with **TTL** and **key prefixes**. The document SHALL list which data categories use which model (e.g. profile→account mapping, agent warm-up cache).

#### Scenario: Operators find coherence guidance

- **WHEN** a reader opens the multi-instance cache section of the deployment documentation
- **THEN** the reader can state whether caches are **per-task** or **shared** for each named domain

### Requirement: No cross-task assumption of shared memory

Application code SHALL NOT assume another task’s **in-memory** state is visible unless **explicitly** using a documented shared cache backend. Unit and integration tests for single-process behavior SHALL remain valid.

#### Scenario: Single-process tests unchanged when Redis off

- **WHEN** no shared cache backend is configured
- **THEN** the application runs without requiring Redis connectivity

### Requirement: Optional shared cache configuration surface

If a shared cache is implemented, the system SHALL support configuration via **`FINOPS_*`** variables and YAML (host, port, TLS, auth secret reference, key prefix, TTL defaults). README and `config/settings.yaml` SHALL document all keys.

#### Scenario: Shared cache disabled by default

- **WHEN** shared cache configuration is absent
- **THEN** the system uses **per-process** caching only

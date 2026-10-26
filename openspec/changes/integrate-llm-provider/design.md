# Design

## Context

The current backend already exposes a minimal health endpoint in [app/backend/main.py](../../app/backend/main.py) and a health-check test in [tests/test_health.py](../../tests/test_health.py). The next phase adds a dedicated LLM capability while preserving that health route and keeping the existing backend layout intact.

## Goals / Non-Goals

**Goals:**
- add a dedicated LLM service layer for prompt-to-response generation
- keep all provider configuration in environment variables
- validate prompt input before sending requests
- handle timeouts and provider failures gracefully
- preserve the existing health endpoint and service structure

**Non-Goals:**
- building a full multi-provider abstraction layer in the first pass
- adding database-backed prompt history or user sessions
- introducing UI or frontend logic for prompt authoring
- adding broad orchestration beyond the service and request flow

## Decisions

### 1. Dedicated service layer for LLM calls
The backend will use a single service module dedicated to provider calls. This keeps API routes thin and concentrates validation, timeout, and provider logic in one place, which reduces duplication and makes test coverage easier.

Alternative considered: place all LLM logic directly in the route layer. This would make the API simpler at first but would scatter validation and retry handling across the app, making future maintenance harder.

### 2. Environment-variable configuration for secrets
Provider credentials will be loaded from environment variables such as an API key variable and optional model settings. This keeps keys out of source files and makes deployment configuration explicit and secure.

Alternative considered: hardcoding values into config files or code. This is faster to prototype but unacceptable for real secret handling and violates the requirement for secure configuration.

### 3. Validation at the service boundary
The service will reject empty, whitespace-only, or otherwise invalid prompts before the request is sent to the external provider. This prevents wasted API calls and produces clearer client-side feedback.

Alternative considered: allowing invalid input through and letting the provider reject it. This shifts validation onto the remote system and produces less predictable error handling.

### 4. Structured timeout and error handling
The service will apply a configured timeout and convert provider failures into predictable backend exceptions. This keeps client-facing behavior stable and makes mocked tests deterministic.

Alternative considered: letting raw provider exceptions bubble directly. This is simple but leaks implementation details and makes clients depend on provider-specific error semantics.

## Risks / Trade-offs

- [Provider latency] → Use a bounded timeout and return a clear error response instead of hanging requests.
- [Invalid prompt input] → Validate before the outbound request to prevent unnecessary provider usage.
- [Missing configuration] → Fail fast with a configuration error so deployments are explicit and secure.
- [Mocked tests can hide provider drift] → Keep tests focused on service behavior while mocking provider payloads and failure states.

## Migration Plan

1. Add the LLM service and provider configuration contract without changing the current /health endpoint.
2. Add the API request flow and validation around the provider call.
3. Add mocked tests covering both success and failure behavior.
4. Verify the health-check endpoint still passes and the new LLM tests cover the contract.

## Open Questions

- Whether the project will initially target a single provider model (for example, OpenAI-compatible) or a generic abstraction later.
- Whether the initial API surface will remain a service-only backend contract or also include a public route for generation in the same phase.

These are safe to answer later without changing the core requirement: the backend must support secure, validated LLM prompting with appropriate error handling.

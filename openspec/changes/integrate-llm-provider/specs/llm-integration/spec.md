# Spec Delta

## Purpose

The backend must support a secure and validated LLM integration so it can turn user prompts into generated skill instructions without exposing secrets or failing unpredictably.

## ADDED Requirements

### Requirement: LLM service accepts valid prompts
The system SHALL provide a dedicated service that accepts a prompt input and returns generated text from the configured LLM provider.

#### Scenario: successful generation
- **WHEN** a request includes a non-empty prompt and the provider is configured correctly
- **THEN** the system sends the prompt to the provider and returns the generated response

#### Scenario: prompt is empty
- **WHEN** the request includes an empty or whitespace-only prompt
- **THEN** the system rejects the request with a validation error before contacting the provider

### Requirement: API key configuration is secure
The system SHALL read provider credentials from environment variables instead of embedding them in source code or configuration files tracked by default.

#### Scenario: API key is configured
- **WHEN** the required environment variable is set for the provider
- **THEN** the system uses that value to authenticate requests to the LLM API

#### Scenario: API key is missing
- **WHEN** the required environment variable is not set
- **THEN** the system returns a configuration error and does not attempt a request

### Requirement: request timeouts and provider errors are handled predictably
The system SHALL enforce a request timeout and convert provider failures into consistent error responses for the caller.

#### Scenario: provider times out
- **WHEN** the LLM API does not respond before the configured timeout
- **THEN** the system returns a timeout error and the caller receives a clear failure response

#### Scenario: provider returns an error
- **WHEN** the LLM provider rejects the request or returns a non-success result
- **THEN** the system returns a structured error describing the failure without exposing internal implementation details

### Requirement: health-check endpoint remains available
The system SHALL preserve the existing health-check endpoint while adding LLM functionality.

#### Scenario: health check is requested
- **WHEN** a monitoring client calls the existing /health route
- **THEN** the system continues returning the healthy service status without disruption

### Requirement: automated tests cover mocked provider behavior
The system SHALL include automated tests that exercise successful generation and error scenarios using mocked LLM responses.

#### Scenario: mocked success response
- **WHEN** a mocked provider returns a valid completion payload
- **THEN** the service returns the generated text to the caller and the test passes

#### Scenario: mocked provider failure
- **WHEN** the mocked provider returns an error or timeout condition
- **THEN** the system surfaces the handled error in a deterministic test outcome

# Spec Delta

## Purpose

The backend must support a skill-generation workflow that transforms natural-language user requirements into a validated, reusable AI agent skill while preserving the existing health endpoint and LLM architecture.

## ADDED Requirements

### Requirement: user requirements are analyzed into a structured skill model
The system SHALL convert a natural-language description of the desired skill into a structured representation covering purpose, scope, activation conditions, constraints, outputs, and required files.

#### Scenario: valid natural-language input
- **WHEN** a user submits clear requirements for a new skill
- **THEN** the system translates those requirements into a structured skill model that can drive generation and validation

#### Scenario: incomplete or ambiguous input
- **WHEN** the user request does not provide enough detail to generate a safe, valid skill
- **THEN** the system identifies missing information and returns a clear validation result instead of silently inventing unsupported behavior

### Requirement: generation creates a portable `SKILL.md` and optional support files
The system SHALL generate a `SKILL.md` file that follows the selected portable skill format, and MAY generate supporting files only when needed by the skill or approved by the generation contract.

#### Scenario: skill generation succeeds
- **WHEN** the structured skill model is valid
- **THEN** the system creates the required skill files under the designated output location and keeps them separated from application source code

#### Scenario: supporting files are not required
- **WHEN** a skill can be expressed with a single file format
- **THEN** the system avoids generating unnecessary supporting files

### Requirement: validation checks metadata, file references, and directory structure
The system SHALL validate generated content for required metadata, markdown structure, path safety, file references, and directory layout before the output is accepted.

#### Scenario: valid generated output
- **WHEN** the generated skill conforms to the format and safety rules
- **THEN** the system marks the output as valid and returns the generated files and validation result

#### Scenario: invalid generated output
- **WHEN** the generated files are malformed, missing required metadata, or reference invalid paths
- **THEN** the system returns actionable validation errors and does not silently accept the output

### Requirement: unsafe content is rejected before output is returned
The system SHALL reject generated content that contains insecure file paths, embedded secrets, unsafe file operations, or overwrites of protected files.

#### Scenario: dangerous output detected
- **WHEN** the generation result includes a path traversal attempt, embedded credentials, or other unsafe content
- **THEN** the system flags the result as invalid and prevents writing or returning it

### Requirement: generation reuses the existing LLM service and optional RAG support
The system SHALL reuse the existing LLM integration for generation and validation, and MAY use the RAG service only when approved reference material is needed for format or documentation guidance.

#### Scenario: LLM generation succeeds
- **WHEN** the provider is configured correctly and the prompt is valid
- **THEN** the system uses the existing LLM service to draft and validate the desired skill content

#### Scenario: provider error occurs
- **WHEN** the LLM provider fails or times out
- **THEN** the system returns a predictable service error without duplicating provider logic or compromising the backend contract

### Requirement: output is returned through a consistent response contract
The system SHALL return generated skills and validation results through a structured contract that includes file information, validation status, and actionable errors when applicable.

#### Scenario: generation complete
- **WHEN** a valid skill is produced
- **THEN** the response includes the generated files and validation summary in a consistent format

#### Scenario: generation fails
- **WHEN** the skill cannot be generated or validated successfully
- **THEN** the response includes the failure reason and the relevant validation details without exposing sensitive internals

### Requirement: existing backend behavior remains stable
The system SHALL preserve the existing `/health` endpoint and current LLM and RAG functionality while introducing the skill-generation capability.

#### Scenario: health endpoint requested
- **WHEN** a monitoring client calls the existing health route
- **THEN** the service continues to return the same healthy payload without disruption

### Requirement: tests cover successful generation and failure cases
The system SHALL include automated tests for requirement analysis, generation, validation, path safety, malformed output, and regressions affecting the existing backend.

#### Scenario: mocked successful generation
- **WHEN** the LLM returns valid skill content
- **THEN** the system creates a valid skill output and marks it as validated

#### Scenario: mocked failure
- **WHEN** the LLM or validation layer returns incomplete or unsafe output
- **THEN** the system surfaces the expected failure behavior and prevents acceptance of the bad artifact

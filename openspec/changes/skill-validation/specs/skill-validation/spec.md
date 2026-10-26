# Spec Delta

## Purpose

The backend must validate generated skill files before they are accepted as complete outputs. Validation must cover metadata, required structure, requirement coverage, and security controls while preserving the existing skill-generation workflow and backend stability.

## ADDED Requirements

### Requirement: skill validation checks required metadata and structure
The system SHALL validate generated skill files for required metadata fields, markdown structure, required sections, and file relationships before accepting the output.

#### Scenario: valid skill file
- **WHEN** a generated skill includes a valid name, description, purpose, instructions, and constraints
- **THEN** the validation layer marks it as structurally valid and continues the generation workflow

#### Scenario: missing metadata
- **WHEN** the generated skill lacks required metadata or required sections
- **THEN** the system returns validation errors that identify the missing fields or sections

### Requirement: validation checks requirement coverage
The system SHALL compare the generated skill content against the original user requirement and identify missing, contradictory, or incomplete coverage in deterministic checks.

#### Scenario: requirement not covered
- **WHEN** a generated skill omits a required use case, activation condition, or constraint from the user request
- **THEN** the system reports the missing requirement coverage as a blocking validation issue

#### Scenario: contradictory instructions
- **WHEN** the generated skill includes instructions that conflict with the user requirement or safety constraints
- **THEN** the system flags the contradiction and prevents acceptance until the issue is resolved

### Requirement: validation enforces output safety
The system SHALL reject path traversal attempts, suspicious file operations, embedded secrets, and unsafe content before the generated artifact is accepted.

#### Scenario: unsafe output
- **WHEN** the generated skill tries to reference absolute paths, escape the output directory, or contain credentials
- **THEN** the system returns a blocking validation error and prevents export or acceptance

### Requirement: validation results are structured and actionable
The system SHALL return a consistent validation result containing a status, validity flag, export flag, errors, warnings, and recommendations.

#### Scenario: warning only
- **WHEN** the skill passes validation but has non-blocking issues
- **THEN** the system returns a warning result while preserving a valid export decision if no blocking errors remain

#### Scenario: blocking errors
- **WHEN** the skill has blocking issues
- **THEN** the system returns a failed validation result with `is_valid = false` and `can_export = false`

### Requirement: generation workflow reuses validation before success is reported
The system SHALL validate generated skill artifacts before reporting generation as successful or before returning them as final output.

#### Scenario: generation succeeds
- **WHEN** the generated artifact is valid
- **THEN** the system records the validation result and returns the generated files as acceptable output

#### Scenario: generation fails validation
- **WHEN** the generated artifact is malformed or unsafe
- **THEN** the system prevents success reporting and surfaces the precise validation findings

### Requirement: validation supports a controlled failure contract
The system SHALL surface unexpected validator failures as sanitized, controlled errors without exposing secrets or internal implementation details.

#### Scenario: unexpected internal failure
- **WHEN** the validator encounters an unexpected exception while evaluating content
- **THEN** the system returns a safe error payload instead of leaking implementation details

### Requirement: existing backend behavior remains stable
The system SHALL preserve the existing health endpoint and LLM service while adding validation checks for generated skills.

#### Scenario: health check remains stable
- **WHEN** a monitoring client calls `/health`
- **THEN** the API continues to respond with the same healthy payload

### Requirement: automated tests cover validation behavior and regressions
The system SHALL include unit and integration tests for valid skills, invalid metadata, broken references, unsafe paths, contradictory requirement coverage, and generation validation integration.

#### Scenario: regression coverage
- **WHEN** validation is introduced
- **THEN** the project runs the relevant skill-generation tests and the backend suite to ensure the change does not break existing behavior

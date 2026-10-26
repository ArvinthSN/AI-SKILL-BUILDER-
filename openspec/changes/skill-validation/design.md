# Design

## Context

The project already defines a portable `SKILL.md` contract and generates skill files from a structured requirement model. The validation gap is that the generation service currently checks only a narrow subset of metadata and content, and it does not produce a structured validation result with blocking and warning semantics or requirement-coverage checks.

## Goals / Non-Goals

**Goals:**
- add a dedicated validation service for generated skill files
- validate metadata, markdown structure, file references, and requirement coverage
- reject unsafe paths, secrets, and untrusted instructions
- integrate validation into the generation workflow before reporting success
- preserve the existing `/health`, LLM, and generation contracts

**Non-Goals:**
- building an export subsystem or new API surface without a design requirement
- running generated scripts automatically
- guaranteeing semantic correctness for every LLM-generated instruction
- creating a broad skill marketplace or registry

## Decisions

### 1. Validation is a dedicated service, not ad hoc checks
The project will use a dedicated `SkillValidationService` that accepts the original requirement, the generated file paths, and the generated markdown. This keeps complex rule sets isolated and testable.

### 2. Results use a structured schema with blocking semantics
The validation result will include a status, `is_valid`, `can_export`, `errors`, `warnings`, and `recommendations`. Request-level errors are blocking; warnings are non-fatal unless they are paired with a blocking issue.

### 3. Files are validated in deterministic ways before semantic review
The validation layer will check required metadata, markdown headings, expected file existence, relative-reference relationships, suspicious patterns, and requirement coverage using deterministic text matching and path validation. Semantic LLM evaluation is optional and falls back to deterministic checks when it is unavailable.

### 4. Security checks are strict and path-boundary aware
All generated file references must remain inside the output directory. The validator will reject absolute paths, `../` traversal attempts, suspicious file operations, and credential patterns in content.

### 5. Validation is part of generation, not a separate export gate unless required
The generation flow will validate artifacts before success is reported. It will not add a new export endpoint unless the approved design explicitly requires one.

## Risks / Trade-offs

- [Ambiguous requirement coverage] → compare the generated skill against explicit user requirements using a deterministic checklist and report missing requirements clearly.
- [LLM semantic drift] → use deterministic validation first, and treat semantic claims as advisory rather than guaranteed.
- [Overly strict validation] → differentiate between blocking errors and warnings so valid but non-ideal output is still accepted when no blocking issue remains.
- [Unsafe file generation] → reject absolute paths, traversal sequences, and credential leakage before writing or returning output.

## Migration Plan

1. Define the validation contract and result schema.
2. Implement file-level and content-level validation rules.
3. Integrate the validator into the skill-generation service before success is reported.
4. Add tests covering valid and invalid generation outcomes.
5. Verify the generation and backend suite remain green.

## Open Questions

- Should the validation endpoint remain internal to the generation flow for the initial release?
- Should semantic requirement coverage be implemented as a deterministic heuristic or through the existing LLM service later?
- Is a separate user-facing validation endpoint required, or is generation-time validation sufficient for the MVP?

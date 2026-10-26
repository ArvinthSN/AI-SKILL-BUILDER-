# Design

## Context

The backend already exposes a minimal FastAPI service and a dedicated, environment-driven LLM integration. That makes it an appropriate foundation for a skill-generation workflow that can reuse the same provider configuration, timeout, and error-handling policies. The project is intentionally lightweight and service-oriented, so the design should avoid adding a large new platform or custom execution system.

## Goals / Non-Goals

**Goals:**
- create a structured analysis of natural-language skill requirements
- generate a valid `SKILL.md` file in a portable format
- generate optional support files only when required
- validate metadata, file paths, and directory structure before accepting results
- preserve the health endpoint and current LLM behavior
- reuse the existing LLM service and optional RAG layer where useful

**Non-Goals:**
- auto-installing generated skills into external agent ecosystems
- guaranteeing compatibility with every possible skill format in the initial release
- executing generated scripts automatically
- allowing generated artifacts to modify app source code without explicit authorization
- creating a full skill marketplace or registry

## Decisions

### 1. Portable `SKILL.md` as the default format
The initial implementation will target a portable `SKILL.md` convention rather than a vendor-specific ecosystem schema. This gives the project a stable contract, reduces ambiguity, and keeps validation logic focused.

Alternative considered: generating a different format for each agent ecosystem. That would increase complexity and validation surface area without satisfying the MVP requirement.

### 2. Generate a structured intermediate model before writing files
The workflow will first analyze the user requirement into a structured representation: purpose, usage, activation conditions, scope, constraints, deliverables, and expected outcomes. That intermediate model will then drive file generation and validation.

Alternative considered: generating directly from raw prompt text. This is faster to prototype but yields inconsistent output and weak validation coverage.

### 3. Validation as a required gate, not a best-effort check
Generated files will be validated for required metadata, Markdown content, safe file paths, directory layout, and forbidden patterns such as hardcoded secrets or dangerous file operations before the result is returned.

Alternative considered: returning generated content without validation. This is less safe and would make downstream errors harder to diagnose.

### 4. Reuse current backend services instead of duplicating logic
Skill generation will call the existing LLM service for drafting and validation. The optional RAG service can be used to retrieve approved reference documentation or format guidance when needed, but it will not be required for every request.

Alternative considered: creating a second, separate LLM integration. This would duplicate configuration and error handling and would not align with the repository’s current architecture.

### 5. Safe output location with explicit path controls
All generated artifacts will be written only under a designated base directory, with path sanitization and overwrite protections. The system will reject attempts to escape the output root or overwrite existing protected files without explicit approval.

Alternative considered: writing directly into arbitrary filesystem locations. This would create race conditions and security risks.

## Risks / Trade-offs

- [Ambiguous user requirements] → analyze requirements into a structured representation and request clarification when required details materially affect correctness.
- [Malformed generated skill files] → validate before acceptance and return actionable error messages instead of silently accepting bad output.
- [Unsupported skill format differences] → keep the first version portable and format-specific validation isolated.
- [Unsafe generated content] → reject embedded credentials, dangerous file operations, and invalid paths.
- [LLM provider failures] → reuse the established service contract and validation patterns to avoid duplicate retries and inconsistent failure handling.

## Migration Plan

1. Define the skill-generation and validation contracts before implementation.
2. Create the structured requirement-analysis model and output contract.
3. Implement the generation service to produce a portable `SKILL.md` file and optional support files in the designated safe directory.
4. Add validation checks for metadata, paths, file references, and safety rules.
5. Connect generation to the existing LLM service and optional RAG integration.
6. Add mocked tests for successful generation, validation failures, and unsupported inputs.
7. Verify the existing `/health`, LLM, and RAG tests remain green.

## Open Questions

- Should the initial version generate only one `SKILL.md` or also support optional reference files or scripts?
- Should the output be previewed by the user before export, or returned immediately when valid?
- Should RAG-based reference retrieval be enabled for all generation requests or only when the skill requires external documentation?
- Is a downloadable package format required in the MVP, or is a structured API response sufficient?
- What persistence model, if any, should be used for previously generated skills?

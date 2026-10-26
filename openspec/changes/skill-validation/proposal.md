# Proposal

## Why

Generated AI skill files are only useful when they are complete, consistent, and safe to use. Without a dedicated validation step, the system can accept malformed metadata, missing required sections, unsafe paths, or instructions that do not match the original user request. A validation workflow gives users a clear quality gate before a skill is accepted, exported, or reused.

## What Changes

- Add a dedicated skill-validation capability that checks generated skill content before it is accepted.
- Validate required metadata fields such as name, description, author, version, and required sections for a portable `SKILL.md` document.
- Ensure the generated content matches the original requirement and does not drift into unsupported or misleading instructions.
- Reject dangerous or unsafe paths, invalid markdown structure, missing references, and overwrite attempts in output directories.
- Surface validation results as structured pass/fail feedback so the generation workflow can warn, block, or ask for revision.
- Reuse the existing backend service layer and LLM configuration patterns without introducing a second provider stack.
- Add automated tests for valid and invalid skill output using mocked inputs and deterministic validation checks.

## Capabilities

### New Capabilities
- `skill-validation`: validate generated skill metadata, markdown structure, output safety, and requirement alignment before acceptance.

### Modified Capabilities
- `skill-generation`: require generated skill files to pass validation checks before they are returned or persisted as final output.

## Impact

- The backend will gain a validation layer that sits between generation and final artifact acceptance.
- Skill outputs will be rejected or revised when they do not meet the required format or safety rules.
- Generation workflows will become more trustworthy because users receive explicit feedback when a skill is incomplete, unsafe, or inconsistent.
- The existing FastAPI, LLM, and RAG services remain the foundation, while validation logic is isolated to a focused service and test suite.
- This change is intentionally scoped to validation and quality gating; it does not broaden the project into a fully general skill marketplace or multi-agent ecosystem.

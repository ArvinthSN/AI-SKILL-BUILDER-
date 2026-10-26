# Tasks

## 1. Generation Foundation

- [x] 1.1 Inspect the existing backend structure, configuration layer, and LLM integration before adding new generation modules.
- [x] 1.2 Define the internal representation for user requirements and the generated skill contract.
- [x] 1.3 Decide the initial target format and establish validation requirements for `SKILL.md` metadata and structure.
- [x] 1.4 Document the safe output directory and the rules for generated file placement.
- [x] 1.5 Preserve the existing `/health` endpoint and current LLM configuration behavior.

## 2. Requirement Analysis

- [x] 2.1 Parse natural-language user input into a structured skill description.
- [x] 2.2 Identify purpose, triggers, scope, constraints, expected outputs, and supporting files.
- [x] 2.3 Flag incomplete or ambiguous requirements and return clear validation issues.
- [x] 2.4 Define default assumptions for missing but non-critical details without inventing unsafe behaviors.

## 3. Skill Generation

- [x] 3.1 Generate a valid `SKILL.md` file from the structured requirement model.
- [x] 3.2 Include metadata, purpose, instructions, activation conditions, and constraints in the generated content.
- [x] 3.3 Generate optional supporting files only when they are required by the format or the approved requirements.
- [x] 3.4 Keep generated output separate from application source code and OpenSpec artifacts.
- [x] 3.5 Reject attempts to write outside the designated output directory.

## 4. Validation and Safety

- [x] 4.1 Validate required metadata, markdown structure, and references in generated skill files.
- [x] 4.2 Validate directory layout and file placement against the selected format.
- [x] 4.3 Reject unsafe paths, embedded secrets, dangerous file operations, and accidental overwrites.
- [x] 4.4 Return actionable validation results when generation fails or content is malformed.
- [x] 4.5 Ensure generated content does not unexpectedly change application source code or protected files.

## 5. LLM and Optional RAG Integration

- [x] 5.1 Reuse the existing LLM service for generation and validation tasks.
- [x] 5.2 Reuse provider configuration, auth, timeouts, and error handling rather than duplicating them.
- [x] 5.3 Integrate the optional RAG service only when approved documentation or reference material is required.
- [x] 5.4 Guard against prompt injection and untrusted document content overriding application instructions.

## 6. Automated Verification

- [x] 6.1 Test successful requirement analysis for valid user input.
- [x] 6.2 Test generation of `SKILL.md` and optional support files.
- [x] 6.3 Test validation failures for malformed metadata, bad paths, and unsafe content.
- [x] 6.4 Test invalid or incomplete requirements and ambiguous user input handling.
- [x] 6.5 Test provider failures, malformed LLM responses, and retry/error behavior using mocks.
- [x] 6.6 Verify the full backend test suite still passes, including `/health`, LLM, and RAG regressions.

## 7. Handoff and Review

- [x] 7.1 Confirm the generated output contract is documented and consistent.
- [x] 7.2 Review the change against the proposal, design, and spec before implementation begins.
- [x] 7.3 Decide whether preview, export, or both are required in the first implementation.
- [x] 7.4 Confirm whether RAG retrieval should be optional or required for skill-generation requests.

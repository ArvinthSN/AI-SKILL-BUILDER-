# Tasks

## 1. Validation contract

- [ ] 1.1 Define the validation result schema, severity model, and blocking vs. warning policy.
- [ ] 1.2 Confirm the validation checks integrate with the current skill-generation service without duplicating provider logic.

## 2. Metadata and file validation

- [ ] 2.1 Validate required skill metadata such as name and description.
- [ ] 2.2 Validate SKILL.md structure, required headings, and expected file relationships.
- [ ] 2.3 Reject invalid file references, missing files, and unexpected directories.

## 3. Requirement coverage and security

- [ ] 3.1 Compare generated content against the original requirement and detect missing or contradictory guidance.
- [ ] 3.2 Reject absolute paths, traversal attempts, embedded secrets, and suspicious instructions.
- [ ] 3.3 Return sanitized validation findings without leaking internal details.

## 4. Generation integration

- [ ] 4.1 Integrate validation into the skill-generation workflow before reporting success.
- [ ] 4.2 Revalidate corrected content after any regeneration attempt and enforce a bounded correction loop.
- [ ] 4.3 Preserve the existing generation contract and health endpoint behavior.

## 5. Automated verification

- [ ] 5.1 Add tests for valid, invalid, unsafe, and contradictory skill outputs.
- [ ] 5.2 Add tests for blocked export conditions and validation result semantics.
- [ ] 5.3 Run focused validation tests and the full project backend suite to confirm there are no regressions.

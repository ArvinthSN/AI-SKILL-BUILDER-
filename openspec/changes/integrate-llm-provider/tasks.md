# Tasks

## 1. LLM Service Foundation

- [x] 1.1 Inspect the existing backend structure and define the LLM service and configuration modules.
- [x] 1.2 Configure the LLM provider and model through environment variables; keep real API credentials out of source control.
- [x] 1.3 Define the request and response schemas for `POST /api/v1/llm/generate`.
- [x] 1.4 Validate prompts, including empty input, whitespace-only input, and prompts exceeding the configured length limit.
- [x] 1.5 Verify invalid prompts are rejected before any outbound provider request.

## 2. Provider Request and Error Handling

- [x] 2.1 Implement the outbound request using the configured OpenAI API provider and model.
- [x] 2.2 Apply a configurable timeout and map provider failures to predictable API errors.
- [x] 2.3 Handle missing configuration, authentication failures, rate limits, timeouts, and other provider errors.
- [x] 2.4 Ensure responses do not expose credentials, raw stack traces, or sensitive provider details.
- [x] 2.5 Preserve the existing health-check endpoint and its response contract.

## 3. Automated Verification

- [x] 3.1 Test successful generation using mocked provider responses.
- [x] 3.2 Test invalid input, ensuring no outbound provider request occurs.
- [x] 3.3 Test missing configuration, provider failures, and timeout handling.
- [x] 3.4 Test the generation endpoint's HTTP status codes and response schemas.
- [x] 3.5 Run the existing backend test suite and verify the health-check test still passes.
- [x] 3.6 Review the final implementation against the proposal, specification, design, and task list.
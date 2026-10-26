# Tasks

## 1. RAG Foundation and Architecture

- [ ] 1.1 Inspect the existing backend structure, `main.py`, `config.py`, and `llm_service.py` before introducing new modules or modifying existing behavior.
- [ ] 1.2 Define clear service contracts for document ingestion, text chunking, embedding generation, vector storage, retrieval, and RAG-based generation.
- [ ] 1.3 Define environment-based configuration for embedding credentials, embedding model, chunk size, chunk overlap, retrieval top-k, relevance threshold, and vector-store persistence location.
- [ ] 1.4 Validate configuration values at application startup, including positive chunk size, valid overlap, positive top-k, and required provider settings.
- [ ] 1.5 Define the supported document inputs, including plain text and Markdown, and establish validation rules for empty, malformed, unsupported, and oversized documents.
- [ ] 1.6 Separate ingestion/indexing from query-time retrieval so documents do not need to be reprocessed for every query.
- [ ] 1.7 Reuse the existing LLM service for generation instead of duplicating provider configuration, authentication, timeout, retry, or error-handling logic.
- [ ] 1.8 Define consistent internal exceptions and client-safe error responses for validation, embedding, storage, retrieval, and generation failures.
- [ ] 1.9 Preserve the existing `/health` endpoint, current LLM behavior, and established backend conventions.
- [ ] 1.10 Finalize the RAG architecture and configuration contract in alignment with the approved proposal, design, and specification.

## 2. Document Ingestion and Processing

- [ ] 2.1 Implement document loading for supported plain-text and Markdown inputs.
- [ ] 2.2 Preserve source metadata, including document identifier, source name, content type, and ingestion timestamp where applicable.
- [ ] 2.3 Validate incoming documents before processing and reject unsupported types, empty content, malformed inputs, and documents exceeding configured size limits.
- [ ] 2.4 Implement configurable text chunking with chunk size and overlap.
- [ ] 2.5 Ensure chunks are non-empty, retain their source metadata, and include stable identifiers or references linking them to their source documents.
- [ ] 2.6 Handle short documents, long documents, whitespace-only content, and content that produces no usable chunks.
- [ ] 2.7 Define how repeated ingestion of the same document is handled, including duplicate detection, replacement, or explicit rejection.
- [ ] 2.8 Ensure ingestion failures do not leave partially updated or inconsistent document and index state.

## 3. Embedding Provider

- [ ] 3.1 Define an embedding-provider interface that supports embedding individual queries and batches of document chunks.
- [ ] 3.2 Implement the selected embedding provider using environment-driven credentials and model configuration.
- [ ] 3.3 Keep embedding-provider logic isolated from document processing, vector storage, retrieval, and LLM generation.
- [ ] 3.4 Validate embedding inputs and handle empty input, provider errors, timeouts, and invalid responses.
- [ ] 3.5 Verify that generated embeddings contain valid numeric values and consistent dimensions.
- [ ] 3.6 Batch embedding requests where supported and handle provider limits without losing document-to-embedding associations.
- [ ] 3.7 Ensure query embeddings use the same compatible embedding model and vector dimensions as the indexed document embeddings.
- [ ] 3.8 Add mocked tests for successful embedding generation, provider failures, invalid responses, and dimension mismatches.

## 4. FAISS Vector Store and Index Management

- [ ] 4.1 Implement the FAISS-backed vector store behind a dedicated interface so the storage implementation can be replaced later.
- [ ] 4.2 Store embeddings in FAISS and maintain a reliable mapping between vector identifiers, chunk content, and source metadata.
- [ ] 4.3 Persist the FAISS index and its associated metadata to the configured storage location.
- [ ] 4.4 Load and validate the existing index and metadata during initialization without unnecessarily rebuilding a valid index.
- [ ] 4.5 Handle missing, corrupted, incompatible, or inconsistent index and metadata files safely.
- [ ] 4.6 Define behavior for an empty index and for attempts to retrieve documents before any successful ingestion.
- [ ] 4.7 Keep index updates and metadata updates consistent so failed operations do not expose incomplete or mismatched records.
- [ ] 4.8 Define duplicate-document handling and the behavior for updating or removing document-associated chunks, if those operations are supported.
- [ ] 4.9 Validate storage paths, create required directories safely, and avoid exposing internal paths in client-facing errors.
- [ ] 4.10 Document the trust requirements for persisted FAISS files and metadata; never load untrusted serialized index or metadata files.
- [ ] 4.11 Add tests for index creation, insertion, persistence, reload, metadata mapping, and storage failures.

## 5. Retrieval and Relevance Filtering

- [ ] 5.1 Implement a retrieval service that embeds the user query and performs similarity search against the FAISS index.
- [ ] 5.2 Support configurable top-k retrieval and return the most relevant chunks with their source metadata and similarity information.
- [ ] 5.3 Define and consistently apply the relevance threshold using the selected similarity metric and its correct score semantics.
- [ ] 5.4 Exclude irrelevant, empty, duplicate, or otherwise invalid chunks from the final context according to the approved retrieval policy.
- [ ] 5.5 Define a deterministic no-results response when the index is empty or no chunks satisfy the relevance policy.
- [ ] 5.6 Prevent LLM generation when the approved policy requires relevant retrieved context but no qualifying chunks are found.
- [ ] 5.7 Handle embedding failures, index-loading errors, retrieval failures, and invalid search results without returning misleading context.
- [ ] 5.8 Ensure retrieval does not accidentally mix metadata or chunks from different source documents.
- [ ] 5.9 Add mocked tests for successful retrieval, top-k limits, threshold filtering, empty indexes, and no-relevant-results scenarios.

## 6. RAG Prompt Construction and Generation

- [ ] 6.1 Implement a dedicated RAG service that orchestrates query embedding, retrieval, context construction, and generation.
- [ ] 6.2 Build a consistent prompt containing application instructions, retrieved document context, and the user's question.
- [ ] 6.3 Clearly delimit retrieved context and treat document content as untrusted data rather than executable instructions.
- [ ] 6.4 Instruct the LLM to answer using the retrieved evidence and to acknowledge when the available context does not support an answer.
- [ ] 6.5 Prevent retrieved documents from overriding application instructions or changing the system's intended behavior.
- [ ] 6.6 Preserve source references for retrieved chunks so answers can include document or chunk citations when supported by the API contract.
- [ ] 6.7 Reuse the existing LLM service for provider calls, credentials, timeouts, retries, and provider-error handling.
- [ ] 6.8 Define behavior for LLM failures, empty model responses, excessive context, and context-construction errors.
- [ ] 6.9 Avoid exposing API keys, raw provider exceptions, internal prompts, or storage implementation details in client-facing responses.
- [ ] 6.10 Add tests verifying that retrieved context is passed correctly to the LLM and that unsupported answers follow the defined no-evidence behavior.

## 7. API Integration

- [ ] 7.1 Decide whether ingestion and RAG querying require public API endpoints or should remain service-only, according to the approved design.
- [ ] 7.2 If approved, define request and response schemas for document ingestion and RAG queries using the project's existing API conventions.
- [ ] 7.3 If approved, implement the document-ingestion endpoint with input validation and predictable success and error responses.
- [ ] 7.4 If approved, implement the RAG-query endpoint with query validation, retrieval, relevance filtering, and grounded generation.
- [ ] 7.5 Return source references and relevant metadata only when included in the approved response contract.
- [ ] 7.6 Use appropriate HTTP status codes and client-safe error messages for invalid requests and failed operations.
- [ ] 7.7 Preserve the existing `/health` endpoint and avoid unintended changes to existing routes.
- [ ] 7.8 Verify the resulting routes and schemas through the existing FastAPI testing conventions and OpenAPI documentation.

## 8. Security, Reliability, and Configuration

- [ ] 8.1 Read credentials and provider settings from environment variables or the application's established configuration mechanism.
- [ ] 8.2 Never hardcode, log, or commit API keys, access tokens, or other secrets.
- [ ] 8.3 Ensure `.env` files containing secrets are excluded from version control when local environment files are used.
- [ ] 8.4 Validate document size, query length, chunk configuration, and retrieval limits to prevent uncontrolled resource consumption.
- [ ] 8.5 Ensure document content and user queries cannot override application instructions through prompt injection.
- [ ] 8.6 Handle provider timeouts, rate limits, and transient failures according to the existing service's retry policy.
- [ ] 8.7 Avoid introducing duplicate retry loops that could multiply provider calls or exceed timeout budgets.
- [ ] 8.8 Ensure temporary files and failed ingestion operations do not leave the index in an inconsistent state.
- [ ] 8.9 Return actionable but sanitized errors without exposing secrets, raw provider responses, or sensitive internal implementation details.
- [ ] 8.10 Document any remaining limitations, including the storage durability and concurrency guarantees of the selected FAISS implementation.

## 9. Automated Verification

- [ ] 9.1 Test successful ingestion and chunking for plain-text and Markdown documents using deterministic fixtures.
- [ ] 9.2 Test validation for unsupported document types, empty content, whitespace-only content, malformed inputs, and oversized documents.
- [ ] 9.3 Test chunk size, overlap, metadata preservation, and stable source references.
- [ ] 9.4 Test embedding generation with mocked success, provider failure, timeout, invalid response, and dimension mismatch scenarios.
- [ ] 9.5 Test FAISS index creation, vector insertion, metadata association, persistence, reload, and recovery from invalid stored state.
- [ ] 9.6 Test retrieval ranking, top-k limits, relevance filtering, empty indexes, and no-relevant-results behavior.
- [ ] 9.7 Test the grounded generation flow with mocked retrieval and LLM responses.
- [ ] 9.8 Verify that the LLM is not called when the approved no-results policy requires retrieval evidence.
- [ ] 9.9 Test prompt construction, untrusted document content handling, and source-reference preservation.
- [ ] 9.10 Test API request validation and response behavior if public endpoints are included in the approved design.
- [ ] 9.11 Test provider failures and verify client-facing errors do not expose secrets or internal implementation details.
- [ ] 9.12 Run the complete backend test suite and verify the original `/health` endpoint and all existing LLM tests remain green.
- [ ] 9.13 Check for regressions in existing imports, configuration, routes, and application startup.
- [ ] 9.14 Review the implementation against the approved proposal, design, specification, and task list before final handoff.

## 10. Documentation and Handoff

- [ ] 10.1 Document the RAG architecture, including ingestion, chunking, embedding, indexing, retrieval, and generation.
- [ ] 10.2 Document required environment variables and provide safe example values without real credentials.
- [ ] 10.3 Document how to ingest supported documents, query the RAG pipeline, and handle no-results responses.
- [ ] 10.4 Document FAISS persistence behavior, storage requirements, and index-recovery limitations.
- [ ] 10.5 Update dependency declarations only for packages required by the approved implementation.
- [ ] 10.6 Summarize changed files, implemented capabilities, test results, configuration requirements, and known limitations.
- [ ] 10.7 Confirm all completed tasks are checked only after implementation and verification evidence is available.
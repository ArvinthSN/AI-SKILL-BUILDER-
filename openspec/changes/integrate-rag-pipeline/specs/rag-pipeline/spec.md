# Spec Delta

## Purpose

The backend must support a retrieval-augmented generation flow so it can ground LLM responses in ingested knowledge documents while preserving the existing health and LLM behavior.

## ADDED Requirements

### Requirement: document ingestion accepts supported document types
The system SHALL provide a document ingestion component that accepts text and Markdown documents and extracts content for indexing.

#### Scenario: valid document input
- **WHEN** a supported text or Markdown document is provided
- **THEN** the system extracts its content and preserves the source metadata needed for later retrieval

#### Scenario: unsupported file type
- **WHEN** a document with an unsupported extension or type is submitted
- **THEN** the system rejects it with a clear validation error and does not attempt to index it

### Requirement: chunking is configurable and deterministic
The system SHALL split each ingested document into chunks using a configurable maximum size and overlap while preserving source information for each chunk.

#### Scenario: chunking is configured
- **WHEN** a document exceeds the configured chunk size
- **THEN** the system produces multiple chunks with overlap and retains the metadata that identifies the document and chunk location

#### Scenario: empty document content
- **WHEN** a document contains no extractable text
- **THEN** the system rejects the document with a predictable empty-content error before storage or retrieval is attempted

### Requirement: embeddings are generated through a provider interface
The system SHALL generate embeddings through a clearly defined embedding-provider interface instead of embedding logic being scattered across the application.

#### Scenario: embedding generation succeeds
- **WHEN** a valid chunk is ready and the provider is configured correctly
- **THEN** the system generates an embedding vector for that chunk and stores it with the chunk metadata

#### Scenario: embedding generation fails
- **WHEN** the embedding provider is unavailable or returns an error
- **THEN** the system returns a structured embedding error and does not silently fabricate retrieval results

### Requirement: vector storage is explicitly selected and used for similarity search
The system SHALL persist document chunks and embeddings in one explicitly selected vector-storage solution suitable for small-to-medium local knowledge retrieval.

#### Scenario: successful indexing
- **WHEN** chunk data and embeddings are valid
- **THEN** the system stores them in the selected vector store so they can be searched by similarity

#### Scenario: storage failure
- **WHEN** the selected vector store is unavailable or write operations fail
- **THEN** the system returns a storage error and surfaces a deterministic failure response to the caller

### Requirement: query-based retrieval returns relevant context
The system SHALL support similarity-based retrieval over indexed chunks for a user query and return only the most relevant context.

#### Scenario: relevant documents exist
- **WHEN** a query matches indexed content within the configured similarity threshold
- **THEN** the system returns the relevant chunks with metadata describing their source and chunk position

#### Scenario: no relevant results
- **WHEN** a query does not match any indexed chunks closely enough to qualify
- **THEN** the system returns an empty retrieval result with a clear no-results response instead of inventing context

### Requirement: RAG generation integrates with the existing LLM service
The system SHALL compose the retrieved context with a user query and pass that grounded prompt to the existing LLM service without duplicating provider logic.

#### Scenario: grounded generation succeeds
- **WHEN** retrieval returns relevant context and the LLM provider is configured correctly
- **THEN** the system sends the enriched prompt to the existing LLM service and returns the generated response

#### Scenario: retrieval yields no context
- **WHEN** the query has no relevant chunks
- **THEN** the system returns a controlled no-context response and does not call the provider with ungrounded output assumptions

### Requirement: provider configuration is secure and environment-driven
The system SHALL keep embedding-provider credentials and storage settings in environment variables, and MUST NOT hardcode secrets in source-controlled files.

#### Scenario: credentials configured
- **WHEN** the required embedding environment variables are set
- **THEN** the system uses those values to authenticate embedding requests and configure the vector store

#### Scenario: credentials missing
- **WHEN** the required environment settings are absent or invalid
- **THEN** the system returns a configuration error before making external calls

### Requirement: health-check behavior remains stable
The system SHALL preserve the current `/health` endpoint and all existing LLM behavior while extending the backend with RAG capabilities.

#### Scenario: health endpoint requested
- **WHEN** a monitoring client calls the existing `/health` route
- **THEN** the service continues to return the same healthy status payload without disruption

### Requirement: automated tests cover mocked ingestion and retrieval flows
The system SHALL include automated tests that validate ingestion, retrieval, provider failures, and storage failures using mocked embedding and LLM responses where appropriate.

#### Scenario: mocked success response
- **WHEN** a mocked embedding provider and LLM service return valid payloads
- **THEN** the system returns the expected generated answer and retrieval metadata

#### Scenario: mocked failure response
- **WHEN** the embedding provider, vector store, or LLM service fails in a controlled way
- **THEN** the system surfaces the deterministic failure behavior expected by the test suite

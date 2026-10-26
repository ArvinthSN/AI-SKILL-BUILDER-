# Proposal

## Why

SkillForge needs a grounded retrieval layer so generated responses can draw on project knowledge instead of relying only on a raw prompt. A dedicated Retrieval-Augmented Generation (RAG) pipeline will provide a repeatable way to ingest source documents, split them into searchable chunks, generate embeddings, and retrieve relevant context before calling the existing LLM service.

## What Changes

- Add a document ingestion component supporting text and Markdown documents in the initial implementation.
- Split ingested documents into configurable chunks with configurable overlap, preserving source metadata for each chunk.
- Introduce an embedding-provider interface and a concrete implementation configured through environment variables.
- Use FAISS as the initial vector store for indexing document embeddings and performing similarity searches.
- Persist the vector index and its associated metadata using a clearly defined local storage strategy.
- Add a retrieval service that searches for relevant chunks and returns results through a predictable contract.
- Add a RAG service that combines retrieved context with the user's question and calls the existing LLM service.
- Define explicit behavior for unsupported files, empty documents, embedding failures, storage failures, and queries with no sufficiently relevant results.
- Preserve the existing FastAPI health endpoint and current LLM behavior.
- Add automated tests with mocked embedding and LLM responses to verify ingestion, retrieval, grounded generation, and failure handling.

## Capabilities

### New Capabilities

- `rag-pipeline`: Document ingestion, chunking, embedding generation, vector indexing, similarity retrieval, and grounded answer generation.

### Modified Capabilities

- None.

## Impact

- The existing backend will gain document-processing, embedding, vector-storage, retrieval, and RAG orchestration components.
- Environment configuration will cover embedding-provider settings, model selection, vector-index storage, chunking parameters, and retrieval settings.
- The RAG workflow will reuse the existing LLM service rather than duplicate provider authentication, configuration, or generation logic.
- Automated tests will verify the new RAG functionality and guard against regressions in existing endpoints and LLM behavior.
- Existing `/health` behavior and the established LLM API contract will remain unchanged.
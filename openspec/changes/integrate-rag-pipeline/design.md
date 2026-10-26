# Design

## Context

The current backend exposes a minimal health endpoint in [app/backend/main.py](../../app/backend/main.py) and a dedicated, environment-driven LLM provider service in [app/backend/llm_service.py](../../app/backend/llm_service.py). The repository does not yet establish a vector database or embedding model, so the design must make an explicit choice that keeps the initial implementation lightweight and compatible with the existing service-oriented architecture.

## Goals / Non-Goals

**Goals:**
- add a document ingestion and chunking layer for text and Markdown sources
- generate embeddings through a dedicated interface and store them with metadata
- support similarity-based retrieval for user queries
- ground generation by passing retrieved context into the existing LLM service
- preserve the health endpoint and current LLM behavior without duplication

**Non-Goals:**
- adding full database-backed multi-tenant document management in the MVP
- scheduling recurring ingestion jobs or background crawlers
- supporting arbitrary binary file types beyond the initial text/Markdown scope
- replacing the existing LLM service with a custom provider implementation

## Decisions

### 1. Explicit vector-store choice: FAISS for the MVP
The initial design chooses a local FAISS-backed vector store for chunk indexing and similarity search. This keeps the first implementation lightweight, avoids introducing a separate database service, and fits the project’s current minimal FastAPI backend. The vector store will be file-backed or in-memory within the app runtime, with a clear storage boundary so it can later be swapped for a hosted option without changing the retrieval contract.

Alternative considered: introducing PostgreSQL + pgvector immediately. This would add operational complexity and infrastructure that the repository has not established. Since the current project is still backend-first and lightweight, FAISS is a better fit for the initial retrieval capability.

### 2. Embedding-provider abstraction over the existing API patterns
The embedding workflow will use an `EmbeddingProvider` interface with a method such as `embed_texts()` for generating vector representations. The concrete provider will follow the same configuration patterns used by the existing LLM settings, with values coming from environment variables rather than constants or tracked secrets.

Alternative considered: embedding logic embedded directly in the retrieval service. This is faster to prototype but creates duplication and makes it harder to replace or test the provider without changing business logic.

### 3. Document ingestion separate from query-time retrieval
The design splits the lifecycle into two explicit phases: ingestion/indexing and query-time retrieval. Ingestion is responsible for reading supported files, extracting text, chunking, preserving metadata, and storing vectors. Retrieval is responsible for query input, similarity lookup, and return of relevant context for grounding.

Alternative considered: mixing ingestion and retrieval into one service. This would simplify the first pass but tightly couples indexing and querying and makes failure handling and tests harder to isolate.

### 4. Grounded prompt composition uses the existing LLM service
The RAG service will retrieve the top matching chunks, compose them into a prompt context block, and call the existing LLM service already used by the backend. This preserves the current provider configuration and avoids duplicated provider logic.

Alternative considered: rewriting provider integration inside the RAG flow. This would duplicate the same authentication, error handling, and prompt logic and would violate the requirement to reuse the existing LLM integration.

## Risks / Trade-offs

- [Unsupported file types] → Fail early with validation errors and a clear message instead of silently skipping files.
- [Empty documents] → Reject before indexing so retrieval indexes stay clean and deterministic.
- [Embedding or storage failures] → Return predictable structured errors and avoid partial or silent retrieval results.
- [No relevant search results] → Return an explicit no-results response rather than generating a grounded answer from empty context.
- [Repo-level assumptions] → Keep the vector-store and embedding choices explicit and configurable without assuming a database or model that the project has not selected.

## Migration Plan

1. Define the ingestion, chunking, embedding-provider, and retrieval contracts before implementation.
2. Add the environment-driven configuration for chunking and embedding settings without changing the current `/health` route.
3. Implement the ingestion/indexing layer and the explicit FAISS-backed retrieval store.
4. Add the RAG service that composes retrieved context with the existing LLM service.
5. Add mocked tests for supported documents, invalid files, embedding failures, storage failures, and no-results queries.
6. Verify the existing health endpoint and existing LLM tests still pass.

## Open Questions

- Whether the first pass needs a public route for document ingestion, or whether the service layer alone is sufficient for early backend usage.
- Whether the project wants the vector index to persist between app restarts or to be rebuilt on startup during the initial MVP.

These do not change the core requirement: the system must add a secure, testable, document-grounded retrieval pipeline without disrupting the current health and LLM behavior.

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from app.backend.config import get_rag_settings
from app.backend.embedding_service import EmbeddingProvider, EmbeddingProviderError, OpenAIEmbeddingProvider
from app.backend.llm_service import generate_text
from app.backend.vector_store import DocumentChunk, FaissVectorStore, InMemoryVectorStore, VectorSearchResult


class RAGServiceError(RuntimeError):
    pass


class EmptyDocumentError(RAGServiceError):
    pass


class UnsupportedDocumentTypeError(RAGServiceError):
    pass


class DocumentTooLargeError(RAGServiceError):
    pass


@dataclass
class RAGQueryResult:
    answer: str
    context: list[dict[str, Any]]
    sources: list[dict[str, Any]]


class _LLMAdapter:
    def generate(self, prompt: str) -> dict[str, Any]:
        result = generate_text(prompt)
        return {"response": result.response}


class RAGService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: InMemoryVectorStore | FaissVectorStore | None = None,
        llm_client: Any | None = None,
        settings=None,
    ):
        self.settings = settings or get_rag_settings()
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider(self.settings)
        self.vector_store = vector_store or FaissVectorStore(self.settings.embedding_dimension, self.settings.vector_store_path)
        self.llm_client = llm_client or _LLMAdapter()

    def ingest_document(
        self,
        content: str,
        source_name: str,
        content_type: str | None = None,
        *,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        document_id: str | None = None,
    ) -> list[DocumentChunk]:
        if content is None or not str(content).strip():
            raise EmptyDocumentError("Document content cannot be empty.")

        normalized_content_type = (content_type or self._infer_content_type(source_name)).lower()
        if normalized_content_type not in {"text", "markdown"}:
            raise UnsupportedDocumentTypeError(f"Unsupported document type: {normalized_content_type}")

        document_text = str(content).strip()
        if len(document_text) > self.settings.max_document_size:
            raise DocumentTooLargeError(f"Document exceeds the configured maximum of {self.settings.max_document_size} characters.")

        resolved_chunk_size = chunk_size or self.settings.chunk_size
        resolved_overlap = chunk_overlap if chunk_overlap is not None else self.settings.chunk_overlap
        if resolved_overlap >= resolved_chunk_size:
            raise ValueError("Chunk overlap must be smaller than the chunk size.")

        chunks = self._split_text(document_text, resolved_chunk_size, resolved_overlap)
        if not chunks:
            raise EmptyDocumentError("Document produced no usable chunks.")

        document_uuid = document_id or str(uuid.uuid4())
        vector_chunks = []
        vectors = []
        for chunk_index, chunk_text in enumerate(chunks):
            vector_chunks.append(
                DocumentChunk(
                    id=f"{document_uuid}-{chunk_index}",
                    document_id=document_uuid,
                    source_name=source_name,
                    content=chunk_text,
                    chunk_index=chunk_index,
                    metadata={
                        "content_type": normalized_content_type,
                        "source_name": source_name,
                        "document_id": document_uuid,
                    },
                )
            )

        try:
            vectors = self.embedding_provider.embed_documents([chunk.content for chunk in vector_chunks])
        except EmbeddingProviderError as exc:
            raise RAGServiceError("Embedding generation failed while indexing the document.") from exc

        self.vector_store.add_chunks(vector_chunks, vectors)
        return vector_chunks

    def retrieve(self, query: str, top_k: int | None = None, threshold: float | None = None) -> list[dict[str, Any]]:
        normalized_query = str(query).strip()
        if not normalized_query:
            raise ValueError("Query must not be empty.")

        if self.vector_store.is_empty():
            return []

        effective_top_k = top_k or self.settings.top_k
        effective_threshold = threshold if threshold is not None else self.settings.relevance_threshold
        try:
            query_vector = self.embedding_provider.embed_query(normalized_query)
        except EmbeddingProviderError as exc:
            raise RAGServiceError("Embedding generation failed while retrieving relevant context.") from exc

        results = self.vector_store.search(query_vector, top_k=effective_top_k, threshold=effective_threshold)

        context = []
        for result in results:
            context.append({
                "chunk_id": result.chunk.id,
                "document_id": result.chunk.document_id,
                "source_name": result.chunk.source_name,
                "content": result.chunk.content,
                "score": result.score,
                "metadata": dict(result.chunk.metadata),
            })

        return context

    def answer_question(self, question: str, *, top_k: int | None = None) -> dict[str, Any]:
        normalized_question = str(question).strip()
        if not normalized_question:
            raise ValueError("Question must not be empty.")

        context = self.retrieve(normalized_question, top_k=top_k)
        if not context:
            return {
                "answer": "No relevant documentation was found for this question.",
                "context": [],
                "sources": [],
            }

        context_block = "\n\n".join(
            f"[Source: {item['source_name']}]\n{item['content']}" for item in context
        )
        prompt = (
            "You are a careful assistant. Answer the user question using the retrieved context below only. "
            "Do not invent facts. If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context_block}\n\nQuestion:\n{normalized_question}"
        )

        llm_response = self.llm_client.generate(prompt)
        if isinstance(llm_response, dict):
            answer = llm_response.get("response") or llm_response.get("answer") or "No answer was generated."
        else:
            answer = str(llm_response)

        return {
            "answer": answer,
            "context": context,
            "sources": [
                {"source_name": item["source_name"], "document_id": item["document_id"], "chunk_id": item["chunk_id"]}
                for item in context
            ],
        }

    def _split_text(self, content: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        words = re.findall(r"\S+", content)
        if not words:
            return []

        step_size = max(1, chunk_size - chunk_overlap)
        chunks: list[str] = []
        for start in range(0, len(words), step_size):
            window = words[start:start + chunk_size]
            if not window:
                continue
            chunks.append(" ".join(window))
            if len(window) < chunk_size:
                break
        return chunks

    def _infer_content_type(self, source_name: str) -> str:
        lower_name = source_name.lower()
        if lower_name.endswith(".md") or lower_name.endswith(".markdown"):
            return "markdown"
        if lower_name.endswith(".txt"):
            return "text"
        return "text" if lower_name else "text"

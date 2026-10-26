from __future__ import annotations

import os

import pytest

from app.backend.rag_service import (
    DocumentChunk,
    EmptyDocumentError,
    InMemoryVectorStore,
    OpenAIEmbeddingProvider,
    RAGService,
    UnsupportedDocumentTypeError,
)


class FakeEmbeddingProvider:
    def __init__(self):
        self.calls = []

    def _vector_for(self, text: str):
        lowered = text.lower()
        if "backend" in lowered or "fastapi" in lowered:
            return [0.9, 0.1, 0.1]
        if "secure api" in lowered or "api key" in lowered:
            return [0.2, 0.1, 0.9]
        if "garden" in lowered:
            return [0.1, 0.9, 0.1]
        return [0.1, 0.2, 0.3]

    def embed_query(self, text: str):
        self.calls.append(("query", text))
        return self._vector_for(text)

    def embed_documents(self, texts):
        self.calls.append(("documents", texts))
        return [self._vector_for(text) for text in texts]


class FakeLLMClient:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str):
        self.prompts.append(prompt)
        return {"response": "Answered using the retrieved context."}


def test_rag_service_ingests_and_chunks_document():
    provider = FakeEmbeddingProvider()
    service = RAGService(
        embedding_provider=provider,
        vector_store=InMemoryVectorStore(dimension=3),
        llm_client=FakeLLMClient(),
    )

    chunks = service.ingest_document(
        "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda.",
        source_name="notes.md",
        content_type="markdown",
        chunk_size=12,
        chunk_overlap=4,
    )

    assert len(chunks) >= 1
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    assert all(chunk.source_name == "notes.md" for chunk in chunks)
    assert all(chunk.metadata["content_type"] == "markdown" for chunk in chunks)


def test_rag_service_retrieves_context_and_uses_llm():
    provider = FakeEmbeddingProvider()
    llm = FakeLLMClient()
    service = RAGService(
        embedding_provider=provider,
        vector_store=InMemoryVectorStore(dimension=3),
        llm_client=llm,
    )

    service.ingest_document("The project uses FastAPI and Python for backend services.", source_name="backend.md")
    result = service.answer_question("What backend framework is used?")

    assert result["answer"] == "Answered using the retrieved context."
    assert result["context"]
    assert llm.prompts


def test_rag_service_returns_no_results_without_llm_call():
    provider = FakeEmbeddingProvider()
    llm = FakeLLMClient()
    service = RAGService(
        embedding_provider=provider,
        vector_store=InMemoryVectorStore(dimension=3),
        llm_client=llm,
    )

    service.ingest_document("Only unrelated content about gardening.", source_name="garden.md")
    result = service.answer_question("What is the secure API key setup?")

    assert result["answer"] == "No relevant documentation was found for this question."
    assert result["context"] == []
    assert llm.prompts == []


def test_rag_service_rejects_empty_or_unsupported_documents():
    provider = FakeEmbeddingProvider()
    service = RAGService(
        embedding_provider=provider,
        vector_store=InMemoryVectorStore(dimension=3),
        llm_client=FakeLLMClient(),
    )

    with pytest.raises(EmptyDocumentError):
        service.ingest_document("   ", source_name="empty.txt")

    with pytest.raises(UnsupportedDocumentTypeError):
        service.ingest_document("data", source_name="image.png", content_type="image")


def test_openai_embedding_provider_uses_expected_request_shape(monkeypatch):
    class MockResponse:
        status_code = 200

        def json(self):
            return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    def fake_post(self, url, json=None, headers=None, timeout=None):
        assert url == "/embeddings"
        assert json["input"] == "hello world"
        assert headers["Authorization"].startswith("Bearer ")
        return MockResponse()

    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://example.test/v1")
    monkeypatch.setattr("app.backend.embedding_service.httpx.Client.post", fake_post)

    provider = OpenAIEmbeddingProvider()
    assert provider.embed_query("hello world") == [0.1, 0.2, 0.3]

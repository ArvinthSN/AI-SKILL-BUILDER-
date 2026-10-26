from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from app.backend.config import get_rag_settings


class EmbeddingConfigurationError(RuntimeError):
    """Raised when embedding settings are missing or invalid."""


class EmbeddingProviderError(RuntimeError):
    """Raised when the embedding provider fails."""


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Return a single embedding vector for a query."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a batch of document chunks."""


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings=None):
        self.settings = settings or get_rag_settings()
        if not self.settings.embedding_api_key:
            raise EmbeddingConfigurationError("Embedding API key is not configured.")

    def embed_query(self, text: str) -> list[float]:
        payload = {
            "model": self.settings.embedding_model,
            "input": text,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.embedding_api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(base_url=self.settings.embedding_base_url, timeout=self.settings.embedding_timeout) as client:
                response = client.post("/embeddings", json=payload, headers=headers)
        except TimeoutError as exc:
            raise EmbeddingProviderError("The embedding provider timed out while generating vectors.") from exc
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError("The embedding provider request failed.") from exc

        if response.status_code >= 400:
            try:
                error_body = response.json()
            except ValueError:
                error_body = {}
            message = error_body.get("error", {}).get("message", "The embedding provider rejected the request.")
            raise EmbeddingProviderError(message)

        try:
            body = response.json()
        except ValueError as exc:
            raise EmbeddingProviderError("The embedding provider returned an invalid response.") from exc

        data = body.get("data") or []
        if not data:
            raise EmbeddingProviderError("The embedding provider returned no embedding data.")

        embedding = data[0].get("embedding")
        if embedding is None:
            raise EmbeddingProviderError("The embedding provider returned an invalid embedding payload.")
        return [float(value) for value in embedding]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload = {
            "model": self.settings.embedding_model,
            "input": texts,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.embedding_api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(base_url=self.settings.embedding_base_url, timeout=self.settings.embedding_timeout) as client:
                response = client.post("/embeddings", json=payload, headers=headers)
        except TimeoutError as exc:
            raise EmbeddingProviderError("The embedding provider timed out while generating vectors.") from exc
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError("The embedding provider request failed.") from exc

        if response.status_code >= 400:
            try:
                error_body = response.json()
            except ValueError:
                error_body = {}
            message = error_body.get("error", {}).get("message", "The embedding provider rejected the request.")
            raise EmbeddingProviderError(message)

        try:
            body = response.json()
        except ValueError as exc:
            raise EmbeddingProviderError("The embedding provider returned an invalid response.") from exc

        data = body.get("data") or []
        if not data:
            raise EmbeddingProviderError("The embedding provider returned no embedding data.")

        embeddings = []
        for item in data:
            embedding = item.get("embedding")
            if embedding is None:
                raise EmbeddingProviderError("The embedding provider returned an invalid embedding payload.")
            embeddings.append([float(value) for value in embedding])

        if len(embeddings) != len(texts):
            raise EmbeddingProviderError("The embedding provider returned an unexpected number of vectors.")

        return embeddings

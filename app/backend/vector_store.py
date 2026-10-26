from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import faiss
import numpy as np


@dataclass
class DocumentChunk:
    id: str
    document_id: str
    source_name: str
    content: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass
class VectorSearchResult:
    chunk: DocumentChunk
    score: float


class InMemoryVectorStore:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self._chunks: list[DocumentChunk] = []
        self._vectors: list[np.ndarray] = []

    def add_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors must be the same length.")

        for chunk, vector in zip(chunks, vectors):
            if len(vector) != self.dimension:
                raise ValueError(f"Expected embedding dimension {self.dimension}, got {len(vector)}.")
            self._chunks.append(chunk)
            self._vectors.append(np.asarray(vector, dtype=np.float32))

    def search(self, query_vector: list[float], top_k: int = 5, threshold: float = 0.0) -> list[VectorSearchResult]:
        if not self._chunks:
            return []

        query = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        if query.shape[1] != self.dimension:
            raise ValueError(f"Expected embedding dimension {self.dimension}, got {query.shape[1]}.")

        scores = []
        for chunk, vector in zip(self._chunks, self._vectors):
            similarity = float(np.dot(query[0], vector) / (np.linalg.norm(query[0]) * np.linalg.norm(vector)))
            if similarity >= threshold:
                scores.append(VectorSearchResult(chunk=chunk, score=similarity))

        scores.sort(key=lambda item: item.score, reverse=True)
        return scores[:top_k]

    @property
    def chunks(self) -> list[DocumentChunk]:
        return list(self._chunks)

    def is_empty(self) -> bool:
        return not self._chunks


class FaissVectorStore(InMemoryVectorStore):
    def __init__(self, dimension: int, path: str | None = None):
        super().__init__(dimension)
        self.path = Path(path) if path else None
        self._index = faiss.IndexFlatL2(dimension)

    def add_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors must be the same length.")

        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[1] != self.dimension:
            raise ValueError(f"Expected embedding dimension {self.dimension}, got {matrix.shape}.")

        self._index.add(matrix)
        super().add_chunks(chunks, vectors)

    def search(self, query_vector: list[float], top_k: int = 5, threshold: float = 0.0) -> list[VectorSearchResult]:
        if self._index.ntotal == 0:
            return []

        query = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        distances, indices = self._index.search(query, min(top_k, self._index.ntotal))

        results: list[VectorSearchResult] = []
        for distance, index in zip(distances[0], indices[0]):
            if index < 0:
                continue
            chunk = self._chunks[int(index)]
            score = float(1.0 / (1.0 + distance))
            if score >= threshold:
                results.append(VectorSearchResult(chunk=chunk, score=score))

        return results

    def persist(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.path))
        metadata = {"dimension": self.dimension, "chunks": [chunk.to_dict() for chunk in self._chunks]}
        self.path.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=True), encoding="utf-8")

    def load(self) -> None:
        if self.path is None or not self.path.exists():
            return

        self._index = faiss.read_index(str(self.path))
        metadata_path = self.path.with_suffix(".json")
        if not metadata_path.exists():
            return

        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        self._chunks = [DocumentChunk(**item) for item in payload.get("chunks", [])]
        self._vectors = [np.asarray([float(value) for value in chunk.metadata.get("embedding", [])], dtype=np.float32) for chunk in self._chunks]

        if self._chunks:
            vectors = np.asarray([vector.tolist() for vector in self._vectors], dtype=np.float32)
            self._index = faiss.IndexFlatL2(self.dimension)
            self._index.add(vectors)

    def is_empty(self) -> bool:
        return self._index.ntotal == 0

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    timeout: float = 30.0
    max_prompt_length: int = 4000


@dataclass(frozen=True)
class RAGSettings:
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_timeout: float = 30.0
    embedding_dimension: int = 1536
    chunk_size: int = 500
    chunk_overlap: int = 100
    top_k: int = 5
    relevance_threshold: float = 0.3
    vector_store_path: str = "./storage/rag_index.faiss"
    max_document_size: int = 250000


def get_llm_settings() -> LLMSettings:
    return LLMSettings(
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()
        or "https://api.openai.com/v1",
        timeout=float(os.getenv("LLM_TIMEOUT", "30.0")),
        max_prompt_length=int(os.getenv("LLM_MAX_PROMPT_LENGTH", "4000")),
    )


def get_rag_settings() -> RAGSettings:
    return RAGSettings(
        embedding_api_key=os.getenv("EMBEDDING_API_KEY", "").strip(),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip() or "text-embedding-3-small",
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1").strip()
        or "https://api.openai.com/v1",
        embedding_timeout=float(os.getenv("EMBEDDING_TIMEOUT", "30.0")),
        embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "1536")),
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "500")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "100")),
        top_k=int(os.getenv("RAG_TOP_K", "5")),
        relevance_threshold=float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.3")),
        vector_store_path=os.getenv("RAG_VECTOR_STORE_PATH", "./storage/rag_index.faiss").strip()
        or "./storage/rag_index.faiss",
        max_document_size=int(os.getenv("RAG_MAX_DOCUMENT_SIZE", "250000")),
    )

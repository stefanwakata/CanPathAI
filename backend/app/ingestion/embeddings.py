"""Embedding backends.

Default: sentence-transformers all-MiniLM-L6-v2 (per product spec).
Alternative: ChromaDB's bundled ONNX MiniLM (same model, no torch dependency)
— useful for slim containers. Selected via EMBEDDING_BACKEND env var.
"""
from functools import lru_cache

from app.core.config import get_settings


class MiniLMEmbedder:
    """sentence-transformers/all-MiniLM-L6-v2 (384-dim)."""

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002 (chroma API)
        return self._model.encode(list(input), normalize_embeddings=True).tolist()

    # chromadb >= 1.x calls these explicitly instead of __call__
    def embed_documents(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return self(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return self(input)

    def name(self) -> str:  # chroma embedding-function protocol
        return "minilm-sentence-transformers"


def get_embedding_function():
    backend = get_settings().embedding_backend
    if backend == "chroma-onnx":
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        return ONNXMiniLM_L6_V2()
    return _cached_minilm()


@lru_cache
def _cached_minilm() -> MiniLMEmbedder:
    return MiniLMEmbedder()

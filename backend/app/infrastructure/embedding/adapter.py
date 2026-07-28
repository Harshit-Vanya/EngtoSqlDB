"""Embedding provider adapters — OpenAI and local mock implementations.

The mock adapter uses a simple hashing approach for local development
without requiring any API keys. It produces deterministic embeddings
suitable for testing the RAG pipeline.
"""

import hashlib
import math
from typing import Any

from backend.app.core.config import get_settings
from backend.app.core.exceptions import EmbeddingProviderError


class OpenAIEmbeddingAdapter:
    """OpenAI text-embedding adapter.

    Uses the OpenAI API to generate real embeddings.
    Requires EMBEDDING_API_KEY to be set.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self._api_key = api_key or settings.embedding_api_key
        self._model = model or settings.embedding_model
        self._dimensions = settings.embedding_dimensions
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except Exception as e:
                raise EmbeddingProviderError(
                    message=f"Failed to initialize OpenAI client: {e}"
                )
        return self._client

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text using OpenAI API."""
        try:
            client = self._get_client()
            response = await client.embeddings.create(
                input=text,
                model=self._model,
            )
            return response.data[0].embedding
        except Exception as e:
            raise EmbeddingProviderError(message=f"OpenAI embedding failed: {e}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in one API call."""
        if not texts:
            return []
        try:
            client = self._get_client()
            response = await client.embeddings.create(
                input=texts,
                model=self._model,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise EmbeddingProviderError(message=f"OpenAI batch embedding failed: {e}")

    @property
    def dimensions(self) -> int:
        return self._dimensions


class MockEmbeddingAdapter:
    """Mock embedding adapter for local development and testing.

    Generates deterministic embeddings using text hashing.
    No API keys required. Embeddings are NOT semantically meaningful,
    but they are consistent (same text → same vector) which is sufficient
    for testing the RAG pipeline.
    """

    def __init__(self, dimensions: int = 384):
        self._dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding from text hash."""
        return self._hash_to_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for multiple texts."""
        return [self._hash_to_vector(text) for text in texts]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _hash_to_vector(self, text: str) -> list[float]:
        """Convert text to a deterministic unit vector via hashing.

        Uses SHA-256 repeatedly to fill the desired dimensions,
        then normalizes to unit length.
        """
        vector = []
        seed = text.encode("utf-8")

        while len(vector) < self._dimensions:
            h = hashlib.sha256(seed + len(vector).to_bytes(4, "big")).digest()
            # Convert each byte pair to a float in [-1, 1]
            for i in range(0, len(h) - 1, 2):
                if len(vector) >= self._dimensions:
                    break
                val = int.from_bytes(h[i : i + 2], "big") / 65535.0 * 2 - 1
                vector.append(val)

        # Normalize to unit vector
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector[: self._dimensions]


def get_embedding_provider() -> OpenAIEmbeddingAdapter | MockEmbeddingAdapter:
    """Factory function — returns the configured embedding provider.

    If no API key is set, returns the mock adapter for local development.
    """
    settings = get_settings()

    if settings.embedding_api_key and settings.embedding_api_key != "<YOUR_EMBEDDING_API_KEY>":
        return OpenAIEmbeddingAdapter()
    else:
        # Fall back to mock for local dev
        return MockEmbeddingAdapter(dimensions=settings.embedding_dimensions)

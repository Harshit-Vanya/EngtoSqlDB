"""Embedding provider protocol — the interface all embedding adapters implement."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for text embedding providers.

    Implementations must convert text into vector representations
    suitable for similarity search.
    """

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        ...

    @property
    def dimensions(self) -> int:
        """The dimensionality of the embedding vectors."""
        ...

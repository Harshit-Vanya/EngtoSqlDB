"""Vector store protocol — the interface all vector store adapters implement."""

from typing import Any, Protocol

from backend.app.core.types import SearchResult


class VectorStore(Protocol):
    """Protocol for vector similarity search stores."""

    async def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert or update documents in the store.

        Args:
            ids: Unique identifiers for each document.
            embeddings: Pre-computed embedding vectors.
            documents: Original text content.
            metadatas: Metadata dictionaries for filtering.
        """
        ...

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents.

        Args:
            query_embedding: The query vector to search with.
            top_k: Maximum number of results.
            filter_metadata: Optional metadata filter.

        Returns:
            List of SearchResult ordered by relevance (highest score first).
        """
        ...

    async def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        ...

    async def count(self) -> int:
        """Return the total number of documents in the store."""
        ...

    async def health_check(self) -> bool:
        """Check if the vector store is reachable."""
        ...

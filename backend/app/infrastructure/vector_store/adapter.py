"""ChromaDB vector store adapter.

ChromaDB runs in-process for local development (no server needed)
and can also connect to a remote Chroma server in production.
"""

from typing import Any

import chromadb

from backend.app.core.config import get_settings
from backend.app.core.exceptions import VectorStoreError
from backend.app.core.types import SearchResult


class ChromaDBAdapter:
    """ChromaDB vector store adapter.

    In development: uses persistent local storage (no server required).
    In production: can connect to a remote ChromaDB server.
    """

    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str = "./data/chromadb",
    ):
        settings = get_settings()
        self._collection_name = collection_name or settings.vector_store_collection
        self._persist_dir = persist_directory
        self._client: chromadb.ClientAPI | None = None
        self._collection: Any = None

    def _get_collection(self) -> Any:
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            try:
                self._client = chromadb.PersistentClient(path=self._persist_dir)
                self._collection = self._client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                raise VectorStoreError(message=f"ChromaDB initialization failed: {e}")
        return self._collection

    async def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert or update documents in ChromaDB."""
        try:
            collection = self._get_collection()
            # ChromaDB has batch size limits; chunk if needed
            batch_size = 500
            for i in range(0, len(ids), batch_size):
                batch_end = min(i + batch_size, len(ids))
                collection.upsert(
                    ids=ids[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                )
        except Exception as e:
            raise VectorStoreError(message=f"ChromaDB upsert failed: {e}")

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents in ChromaDB."""
        try:
            collection = self._get_collection()
            kwargs: dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }
            if filter_metadata:
                kwargs["where"] = filter_metadata

            results = collection.query(**kwargs)

            search_results = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB returns distances (lower = more similar for cosine)
                    # Convert to similarity score (1 - distance)
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = 1.0 - distance

                    search_results.append(SearchResult(
                        id=doc_id,
                        content=results["documents"][0][i] if results["documents"] else "",
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        score=score,
                    ))

            return search_results
        except Exception as e:
            raise VectorStoreError(message=f"ChromaDB search failed: {e}")

    async def delete(self, ids: list[str]) -> None:
        """Delete documents from ChromaDB."""
        try:
            collection = self._get_collection()
            collection.delete(ids=ids)
        except Exception as e:
            raise VectorStoreError(message=f"ChromaDB delete failed: {e}")

    async def count(self) -> int:
        """Return total document count in the collection."""
        try:
            collection = self._get_collection()
            return collection.count()
        except Exception as e:
            raise VectorStoreError(message=f"ChromaDB count failed: {e}")

    async def health_check(self) -> bool:
        """Check if ChromaDB is operational."""
        try:
            self._get_collection()
            return True
        except Exception:
            return False

    def reset(self) -> None:
        """Delete the collection and recreate it (for testing)."""
        if self._client and self._collection_name:
            try:
                self._client.delete_collection(self._collection_name)
            except Exception:
                pass
            self._collection = None


def get_vector_store() -> ChromaDBAdapter:
    """Factory function — returns the configured vector store adapter."""
    settings = get_settings()
    return ChromaDBAdapter(
        collection_name=settings.vector_store_collection,
    )

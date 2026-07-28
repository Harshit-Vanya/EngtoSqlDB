"""RAG Retriever — retrieves relevant context for a user question.

The retriever:
1. Embeds the user question
2. Searches the vector store for relevant schema, glossary, metrics, examples
3. Re-ranks and deduplicates results
4. Builds a structured context package for the SQL generator

This is the core of the RAG pipeline.
"""

from backend.app.core.types import (
    ColumnSchema,
    ForeignKey,
    RetrievedContext,
    SearchResult,
    TableSchema,
)
from backend.app.infrastructure.embedding.adapter import (
    MockEmbeddingAdapter,
    OpenAIEmbeddingAdapter,
    get_embedding_provider,
)
from backend.app.infrastructure.vector_store.adapter import ChromaDBAdapter, get_vector_store
from data_pipeline.schema_catalog.catalog import SchemaCatalog


class ContextRetriever:
    """Retrieves relevant database context for natural language questions.

    Combines vector similarity search with schema catalog lookups
    to assemble a focused context package for SQL generation.
    """

    def __init__(
        self,
        embedding_provider: OpenAIEmbeddingAdapter | MockEmbeddingAdapter | None = None,
        vector_store: ChromaDBAdapter | None = None,
        schema_catalog: SchemaCatalog | None = None,
        top_k: int = 10,
        similarity_threshold: float = 0.3,
    ):
        self._embedding = embedding_provider or get_embedding_provider()
        self._vector_store = vector_store or get_vector_store()
        self._catalog = schema_catalog or SchemaCatalog()
        self._catalog.load()
        self._top_k = top_k
        self._similarity_threshold = similarity_threshold
        # If using mock embeddings, lower threshold (hashes aren't semantically meaningful)
        if isinstance(self._embedding, MockEmbeddingAdapter):
            self._similarity_threshold = -1.0  # Accept all results in mock mode

    async def retrieve(self, question: str) -> RetrievedContext:
        """Retrieve relevant context for a user question.

        Args:
            question: The natural language question from the user.

        Returns:
            RetrievedContext with tables, relationships, glossary, metrics, examples.
        """
        # Step 1: Embed the question
        query_embedding = await self._embedding.embed(question)

        # Step 2: Search vector store
        results = await self._vector_store.search(
            query_embedding=query_embedding,
            top_k=self._top_k,
        )

        # Step 3: Filter by similarity threshold
        relevant_results = [
            r for r in results if r.score >= self._similarity_threshold
        ]

        # Step 4: Build context from results
        context = self._build_context(relevant_results)

        return context

    def _build_context(self, results: list[SearchResult]) -> RetrievedContext:
        """Build a structured context package from search results."""
        table_names: set[str] = set()
        glossary_terms: list[dict[str, str]] = []
        metrics: list[dict[str, str]] = []
        example_queries: list[dict[str, str]] = []

        for result in results:
            source_type = result.metadata.get("source_type", "")

            if source_type == "table":
                table_name = result.metadata.get("table_name", "")
                if table_name:
                    table_names.add(table_name)

            elif source_type == "glossary":
                glossary_terms.append({
                    "term": result.metadata.get("term", ""),
                    "content": result.content,
                    "score": str(round(result.score, 3)),
                })

            elif source_type == "metric":
                metrics.append({
                    "name": result.metadata.get("metric_name", ""),
                    "content": result.content,
                    "score": str(round(result.score, 3)),
                })

            elif source_type == "example":
                example_queries.append({
                    "content": result.content,
                    "category": result.metadata.get("category", ""),
                    "score": str(round(result.score, 3)),
                })

            elif source_type == "relationship":
                # Relationships add both referenced tables
                from_table = result.metadata.get("from_table", "")
                to_table = result.metadata.get("to_table", "")
                if from_table:
                    table_names.add(from_table)
                if to_table:
                    table_names.add(to_table)

        # Step 5: Enrich with full table schemas from catalog
        tables = self._get_full_table_schemas(list(table_names))

        # Step 6: Get relationships between retrieved tables
        relationships = self._get_relationships(list(table_names))

        # Limit examples to top 3
        example_queries = sorted(
            example_queries, key=lambda x: float(x.get("score", "0")), reverse=True
        )[:3]

        return RetrievedContext(
            tables=tables,
            relationships=relationships,
            glossary_terms=glossary_terms[:5],
            metrics=metrics[:3],
            example_queries=example_queries,
            total_context_tokens=self._estimate_tokens(tables, glossary_terms, metrics, example_queries),
        )

    def _get_full_table_schemas(self, table_names: list[str]) -> list[TableSchema]:
        """Look up full table schemas from the catalog."""
        schemas = []
        for name in table_names:
            table_def = self._catalog.get_table(name)
            if table_def:
                columns = [
                    ColumnSchema(
                        name=col.name,
                        data_type=col.data_type,
                        is_nullable=col.nullable,
                        is_primary_key=col.primary_key,
                        is_foreign_key=col.foreign_key is not None,
                        description=col.description,
                    )
                    for col in table_def.columns
                ]
                foreign_keys = [
                    ForeignKey(
                        column=col.name,
                        references_table=col.foreign_key.split(".")[0] if col.foreign_key else "",
                        references_column=col.foreign_key.split(".")[1] if col.foreign_key and "." in col.foreign_key else "",
                    )
                    for col in table_def.columns
                    if col.foreign_key
                ]
                schemas.append(TableSchema(
                    table_name=table_def.name,
                    description=table_def.description,
                    columns=columns,
                    primary_keys=[c.name for c in table_def.columns if c.primary_key],
                    foreign_keys=foreign_keys,
                ))
        return schemas

    def _get_relationships(self, table_names: list[str]) -> list[dict[str, str]]:
        """Get JOIN relationships between the retrieved tables."""
        rels = self._catalog.get_relationships_for_tables(table_names)
        return [
            {
                "from_table": r.from_table,
                "from_column": r.from_column,
                "to_table": r.to_table,
                "to_column": r.to_column,
                "join_clause": f"{r.from_table}.{r.from_column} = {r.to_table}.{r.to_column}",
            }
            for r in rels
        ]

    def _estimate_tokens(
        self,
        tables: list[TableSchema],
        glossary: list[dict],
        metrics: list[dict],
        examples: list[dict],
    ) -> int:
        """Rough token estimate for the context package (~4 chars per token)."""
        total_chars = 0
        for t in tables:
            total_chars += len(t.table_name) + len(t.description)
            for c in t.columns:
                total_chars += len(c.name) + len(c.data_type) + len(c.description)
        for g in glossary:
            total_chars += len(str(g.get("content", "")))
        for m in metrics:
            total_chars += len(str(m.get("content", "")))
        for e in examples:
            total_chars += len(str(e.get("content", "")))
        return total_chars // 4

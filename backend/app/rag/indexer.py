"""RAG Indexer — indexes schema catalog into the vector store.

This module reads from the SchemaCatalog (YAML definitions) and
creates vector embeddings for each chunk, storing them in the
configured vector store.

Chunk strategy:
- One chunk per table (table name + description + all columns)
- One chunk per glossary term
- One chunk per metric definition
- One chunk per example query

Each chunk has metadata for filtered search (source_type, table_name, etc.)
"""

import asyncio
import uuid
from typing import Any

from backend.app.infrastructure.embedding.adapter import get_embedding_provider
from backend.app.infrastructure.vector_store.adapter import get_vector_store
from data_pipeline.schema_catalog.catalog import SchemaCatalog


async def index_schema_catalog(catalog: SchemaCatalog | None = None) -> dict[str, int]:
    """Index the entire schema catalog into the vector store.

    Args:
        catalog: SchemaCatalog instance. Creates a new one if not provided.

    Returns:
        Dictionary with counts of indexed items per type.
    """
    if catalog is None:
        catalog = SchemaCatalog()
        catalog.load()

    embedding_provider = get_embedding_provider()
    vector_store = get_vector_store()

    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []

    # --- Index tables ---
    for table in catalog.get_tables():
        text = catalog.get_schema_text_for_table(table.name)
        documents.append(text)
        metadatas.append({
            "source_type": "table",
            "table_name": table.name,
            "description": table.description,
        })
        ids.append(f"table_{table.name}")

    table_count = len(catalog.get_tables())

    # --- Index glossary terms ---
    for term in catalog.get_glossary():
        text = (
            f"Business Term: {term.term}\n"
            f"Definition: {term.definition}\n"
            f"Related tables: {', '.join(term.related_tables)}\n"
            f"Synonyms: {', '.join(term.synonyms)}"
        )
        documents.append(text)
        metadatas.append({
            "source_type": "glossary",
            "term": term.term,
            "category": term.category,
        })
        ids.append(f"glossary_{term.term.replace(' ', '_')}")

    glossary_count = len(catalog.get_glossary())

    # --- Index metrics ---
    for metric in catalog.get_metrics():
        text = (
            f"Metric: {metric.name}\n"
            f"Description: {metric.description}\n"
            f"SQL Formula: {metric.formula}\n"
            f"Required tables: {', '.join(metric.required_tables)}\n"
            f"Aggregation: {metric.aggregation}"
        )
        if metric.filters:
            text += f"\nFilters: {metric.filters}"
        if metric.group_by:
            text += f"\nGroup by: {metric.group_by}"

        documents.append(text)
        metadatas.append({
            "source_type": "metric",
            "metric_name": metric.name,
            "category": metric.category,
        })
        ids.append(f"metric_{metric.name}")

    metric_count = len(catalog.get_metrics())

    # --- Index example queries ---
    for example in catalog.get_examples():
        text = (
            f"Question: {example.question}\n"
            f"SQL: {example.sql}\n"
            f"Explanation: {example.explanation}\n"
            f"Tables used: {', '.join(example.tables)}"
        )
        documents.append(text)
        metadatas.append({
            "source_type": "example",
            "category": example.category,
            "difficulty": example.difficulty,
        })
        ids.append(f"example_{uuid.uuid4().hex[:8]}")

    example_count = len(catalog.get_examples())

    # --- Index relationships ---
    for rel in catalog.get_relationships():
        text = (
            f"Relationship: {rel.from_table}.{rel.from_column} → "
            f"{rel.to_table}.{rel.to_column}\n"
            f"Type: {rel.rel_type}\n"
            f"Description: {rel.description}\n"
            f"JOIN: {rel.from_table} JOIN {rel.to_table} "
            f"ON {rel.from_table}.{rel.from_column} = {rel.to_table}.{rel.to_column}"
        )
        documents.append(text)
        metadatas.append({
            "source_type": "relationship",
            "from_table": rel.from_table,
            "to_table": rel.to_table,
        })
        ids.append(f"rel_{rel.from_table}_{rel.to_table}")

    rel_count = len(catalog.get_relationships())

    # --- Generate embeddings ---
    print(f"  Generating embeddings for {len(documents)} documents...")
    embeddings = await embedding_provider.embed_batch(documents)

    # --- Store in vector store ---
    print(f"  Storing {len(documents)} documents in vector store...")
    await vector_store.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    total = await vector_store.count()
    print(f"  ✓ Vector store now has {total} documents")

    return {
        "tables": table_count,
        "glossary": glossary_count,
        "metrics": metric_count,
        "examples": example_count,
        "relationships": rel_count,
        "total_indexed": len(documents),
    }


async def main() -> None:
    """CLI entry point for indexing."""
    print("=" * 60)
    print("  Schema Catalog Indexer")
    print("=" * 60)

    result = await index_schema_catalog()

    print(f"\n  Indexed:")
    for key, count in result.items():
        print(f"    {key}: {count}")
    print("\n  Done!")


if __name__ == "__main__":
    asyncio.run(main())

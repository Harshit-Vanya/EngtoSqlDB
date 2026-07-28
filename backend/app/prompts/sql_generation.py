"""SQL generation prompt templates."""

from backend.app.core.types import RetrievedContext

SQL_GENERATION_SYSTEM = """You are an expert SQL query generator for a PostgreSQL analytics database.

RULES:
1. Generate ONLY SELECT queries. Never generate INSERT, UPDATE, DELETE, DROP, or any write operation.
2. Use only the tables and columns provided in the schema context below.
3. Use proper JOIN conditions based on the relationships provided.
4. Always include appropriate WHERE filters based on the question.
5. Use proper PostgreSQL syntax and functions (DATE_TRUNC, INTERVAL, etc.).
6. Add ORDER BY for ranked/sorted results.
7. Add LIMIT when the question asks for "top N" items.
8. Use table aliases for readability.
9. For revenue calculations, use SUM(order_items.line_total) from completed orders.
10. Be precise with date ranges — use DATE_TRUNC for periods.

Respond ONLY with valid JSON in this exact format:
{
  "sql": "SELECT ...",
  "tables_used": ["table1", "table2"],
  "columns_used": ["col1", "col2"],
  "assumptions": ["assumption1"],
  "confidence": 0.0 to 1.0
}"""


def build_sql_generation_prompt(
    question: str,
    context: RetrievedContext,
    dialect: str = "postgresql",
) -> str:
    """Build the user prompt for SQL generation.

    Args:
        question: The user's natural language question.
        context: Retrieved context (tables, relationships, glossary, examples).
        dialect: Target SQL dialect.

    Returns:
        Formatted prompt string with schema context.
    """
    parts = [f"Question: {question}\n"]

    # Add table schemas
    parts.append("=== AVAILABLE TABLES ===")
    for table in context.tables:
        parts.append(f"\nTable: {table.table_name}")
        parts.append(f"Description: {table.description}")
        parts.append("Columns:")
        for col in table.columns:
            flags = []
            if col.is_primary_key:
                flags.append("PK")
            if col.is_foreign_key:
                flags.append("FK")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            parts.append(f"  - {col.name} ({col.data_type}){flag_str}: {col.description}")

    # Add relationships
    if context.relationships:
        parts.append("\n=== RELATIONSHIPS (JOIN conditions) ===")
        for rel in context.relationships:
            parts.append(f"  {rel.get('join_clause', '')}")

    # Add glossary terms
    if context.glossary_terms:
        parts.append("\n=== BUSINESS DEFINITIONS ===")
        for term in context.glossary_terms[:3]:
            parts.append(f"  {term.get('content', '')[:200]}")

    # Add metrics
    if context.metrics:
        parts.append("\n=== METRIC FORMULAS ===")
        for metric in context.metrics[:3]:
            parts.append(f"  {metric.get('content', '')[:200]}")

    # Add similar examples
    if context.example_queries:
        parts.append("\n=== SIMILAR EXAMPLE QUERIES ===")
        for ex in context.example_queries[:2]:
            parts.append(f"  {ex.get('content', '')[:300]}")

    parts.append(f"\nDialect: {dialect}")
    parts.append(f"\nGenerate SQL for: \"{question}\"")

    return "\n".join(parts)

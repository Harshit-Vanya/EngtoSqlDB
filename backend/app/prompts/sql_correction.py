"""SQL correction prompt templates."""

SQL_CORRECTION_SYSTEM = """You are an expert SQL debugger. A SQL query failed and you need to fix it.

RULES:
1. Fix the specific error described.
2. Keep the query as close to the original as possible.
3. Only use tables and columns that exist (listed in the context).
4. Generate ONLY SELECT queries.
5. Do not change the intent of the query.
6. If a column doesn't exist, use the closest available column.
7. Ensure all JOINs have proper ON conditions.

Respond ONLY with valid JSON:
{
  "sql": "SELECT ... (corrected query)",
  "explanation": "What was wrong and how I fixed it",
  "confidence": 0.0 to 1.0
}"""


def build_sql_correction_prompt(
    question: str,
    failed_sql: str,
    error_message: str,
    available_tables: list[str],
    available_columns: dict[str, list[str]],
    attempt_number: int = 1,
    previous_attempts: list[str] | None = None,
) -> str:
    """Build the prompt for SQL correction.

    Args:
        question: Original user question.
        failed_sql: The SQL that failed.
        error_message: Error from validation or execution.
        available_tables: List of valid table names.
        available_columns: Mapping of table → column names.
        attempt_number: Current correction attempt (1-based).
        previous_attempts: SQLs that already failed (don't repeat them).

    Returns:
        Formatted correction prompt.
    """
    parts = [
        f"Original Question: \"{question}\"",
        f"\nFailed SQL:\n{failed_sql}",
        f"\nError: {error_message}",
        f"\nAttempt: {attempt_number}",
    ]

    if previous_attempts:
        parts.append("\nPrevious failed attempts (do NOT repeat these):")
        for i, sql in enumerate(previous_attempts, 1):
            parts.append(f"  Attempt {i}: {sql[:200]}")

    parts.append("\n=== AVAILABLE TABLES AND COLUMNS ===")
    for table, columns in available_columns.items():
        parts.append(f"  {table}: {', '.join(columns)}")

    parts.append("\nFix the SQL query. Return valid JSON.")

    return "\n".join(parts)

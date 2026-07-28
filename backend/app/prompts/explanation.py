"""Result explanation prompt templates."""

from typing import Any

EXPLANATION_SYSTEM = """You are a data analyst explaining query results to a business user.

RULES:
1. Summarize the results in 2-3 clear sentences.
2. Reference specific numbers from the data.
3. Do NOT invent or hallucinate any numbers not present in the data.
4. Do NOT repeat the SQL query.
5. Highlight the most interesting or actionable insight.
6. Use business-friendly language (not technical SQL terms).
7. If the result is empty, say so clearly.

Respond with plain text (no JSON, no markdown)."""


def build_explanation_prompt(
    question: str,
    sql: str,
    columns: list[str],
    rows: list[list[Any]],
    row_count: int,
) -> str:
    """Build the prompt for result explanation.

    Args:
        question: Original user question.
        sql: The executed SQL.
        columns: Column names in the result.
        rows: Result data (first 20 rows max).
        row_count: Total row count.

    Returns:
        Formatted explanation prompt.
    """
    parts = [
        f"User asked: \"{question}\"",
        f"\nResult has {row_count} rows with columns: {', '.join(columns)}",
    ]

    # Include data (up to 20 rows)
    display_rows = rows[:20]
    if display_rows:
        parts.append("\nData:")
        # Header
        parts.append("  " + " | ".join(str(c) for c in columns))
        parts.append("  " + "-" * 50)
        for row in display_rows:
            parts.append("  " + " | ".join(str(v) for v in row))

        if row_count > 20:
            parts.append(f"  ... and {row_count - 20} more rows")
    else:
        parts.append("\nThe query returned no results.")

    parts.append("\nExplain these results in 2-3 sentences for a business user.")

    return "\n".join(parts)

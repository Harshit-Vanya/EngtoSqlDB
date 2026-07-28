"""Visualization recommendation prompt templates."""

VISUALIZATION_SYSTEM = """You are a data visualization expert. Based on the query results, recommend the best chart type.

Available chart types:
- bar: For comparing categories (categorical x-axis + numeric y-axis)
- horizontal_bar: For many categories or long labels
- line: For time series / trends (temporal x-axis + numeric y-axis)
- pie: For showing proportions of a whole (max 7 slices)
- kpi_card: For a single metric value
- table: Default fallback for complex data
- scatter: For relationship between two numeric values
- multi_line: For multiple time series

Respond ONLY with valid JSON:
{
  "chart_type": "bar|line|pie|kpi_card|table|horizontal_bar|scatter|multi_line",
  "config": {
    "x_axis": "column_name",
    "y_axis": "column_name",
    "title": "Chart Title",
    "sort": "ascending|descending|none"
  },
  "reasoning": "Why this chart type was chosen"
}"""


def build_visualization_prompt(
    question: str,
    columns: list[str],
    column_types: list[str],
    row_count: int,
    sample_rows: list[list] | None = None,
) -> str:
    """Build the prompt for visualization recommendation.

    Args:
        question: Original user question.
        columns: Column names in the result.
        column_types: Inferred types (numeric, categorical, temporal).
        row_count: Total row count.
        sample_rows: First few rows for context.

    Returns:
        Formatted visualization prompt.
    """
    parts = [
        f"Question: \"{question}\"",
        f"Result shape: {row_count} rows × {len(columns)} columns",
        f"\nColumns and types:",
    ]

    for col, col_type in zip(columns, column_types):
        parts.append(f"  - {col}: {col_type}")

    if sample_rows:
        parts.append(f"\nSample data (first {min(5, len(sample_rows))} rows):")
        for row in sample_rows[:5]:
            parts.append(f"  {row}")

    parts.append("\nRecommend the best visualization. Return valid JSON.")

    return "\n".join(parts)

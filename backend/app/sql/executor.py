"""Database Executor — safely runs validated SELECT queries.

This module executes read-only SQL against the analytics database with:
  - Statement-level timeout enforcement (via SET statement_timeout)
  - Row-limit capping (LIMIT injection if not already present)
  - Proper async connection management
  - Structured result mapping to dicts

NEVER call this directly with user-supplied SQL — always pass through
the safety validator first.
"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import text

from backend.app.core.config import get_settings
from backend.app.core.exceptions import QueryExecutionError, QueryTimeoutError
from backend.app.core.logging import get_logger
from backend.app.core.types import ExecutionResult
from backend.app.infrastructure.database.session import get_analytics_engine

logger = get_logger(__name__)


async def execute_readonly_query(
    sql: str,
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
) -> ExecutionResult:
    """Execute a validated SELECT query against the analytics database.

    Args:
        sql: The validated SELECT query to execute.
        timeout_seconds: Per-query timeout in seconds.  Defaults to
            settings.max_execution_time_seconds (30s).
        max_rows: Maximum rows to return.  Defaults to
            settings.max_rows_returned (1000).

    Returns:
        ExecutionResult with columns, rows, timing, and truncation info.

    Raises:
        QueryTimeoutError: If the query exceeds the timeout.
        QueryExecutionError: If the query fails for any other reason.
    """
    settings = get_settings()
    timeout_s = timeout_seconds or settings.max_execution_time_seconds
    row_cap = max_rows or settings.max_rows_returned

    # Inject LIMIT if not already present
    sql_upper = sql.upper().strip()
    if "LIMIT" not in sql_upper:
        sql = f"{sql.rstrip().rstrip(';')}\nLIMIT {row_cap}"

    engine = get_analytics_engine()
    start = time.perf_counter()

    try:
        async with engine.connect() as conn:
            # Enforce server-side timeout
            await conn.execute(
                text(f"SET statement_timeout = '{timeout_s * 1000}'")
            )

            result_proxy = await conn.execute(text(sql))

            # Map cursor result to list-of-dicts
            column_names = list(result_proxy.keys())
            raw_rows = result_proxy.fetchall()

            elapsed_ms = (time.perf_counter() - start) * 1000

            # Build column metadata
            columns_meta = [{"name": name, "type": "text"} for name in column_names]

            # Convert rows to serialisable lists
            rows: list[list[Any]] = []
            for row in raw_rows:
                rows.append([_serialise_value(v) for v in row])

            truncated = len(rows) >= row_cap

            logger.info(
                "query_executed",
                row_count=len(rows),
                execution_time_ms=round(elapsed_ms, 2),
                truncated=truncated,
            )

            return ExecutionResult(
                status="success",
                columns=columns_meta,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                execution_time_ms=elapsed_ms,
            )

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        error_msg = str(exc)

        # Detect timeout
        if "statement timeout" in error_msg.lower() or "canceling statement" in error_msg.lower():
            logger.warning("query_timeout", timeout_seconds=timeout_s, sql=sql[:200])
            raise QueryTimeoutError(
                message=f"Query exceeded {timeout_s}s timeout"
            ) from exc

        logger.error("query_execution_failed", error=error_msg, sql=sql[:200])
        raise QueryExecutionError(
            message=f"Query execution failed: {error_msg}",
        ) from exc


def rows_to_dicts(
    columns: list[dict[str, str]],
    rows: list[list[Any]],
) -> list[dict[str, Any]]:
    """Convert column-metadata + row-arrays into a list of dicts.

    This is what the API layer returns as `data` to the client.
    """
    col_names = [c["name"] for c in columns]
    return [dict(zip(col_names, row)) for row in rows]


def _serialise_value(val: Any) -> Any:
    """Coerce database values to JSON-friendly Python types."""
    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    # dates, decimals, etc.
    return str(val)

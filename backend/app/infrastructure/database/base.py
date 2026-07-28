"""Database executor protocol — the interface all DB adapters implement.

Business logic depends on this protocol, NOT on SQLAlchemy directly.
This allows swapping PostgreSQL for another database with zero changes
to the services layer.
"""

from typing import Any, Protocol

from backend.app.core.types import ExecutionResult


class DatabaseExecutor(Protocol):
    """Protocol for executing SQL queries against the analytics database."""

    async def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        timeout_seconds: int = 30,
        max_rows: int = 1000,
    ) -> ExecutionResult:
        """Execute a read-only SQL query.

        Args:
            sql: The SQL query string to execute.
            params: Optional parameters for parameterized queries.
            timeout_seconds: Maximum execution time.
            max_rows: Maximum number of rows to return.

        Returns:
            ExecutionResult with columns, rows, and metadata.
        """
        ...

    async def explain_query(self, sql: str) -> dict[str, Any]:
        """Run EXPLAIN on a query and return the plan.

        Args:
            sql: The SQL query to analyze.

        Returns:
            Query plan as a dictionary.
        """
        ...

    async def health_check(self) -> bool:
        """Check if the database is reachable.

        Returns:
            True if healthy, False otherwise.
        """
        ...

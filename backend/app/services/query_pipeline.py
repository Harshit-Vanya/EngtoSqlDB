"""Query Pipeline — end-to-end orchestrator for NL→SQL→Results.

This service ties together every stage of the pipeline:
  1. Context Retrieval (RAG)
  2. SQL Generation (LLM Agent)
  3. Safety Validation (Regex Barrier)
  4. Query Execution (Analytics DB)
  5. Result Formatting

It is the single entry-point called by the API route handler.
"""

from __future__ import annotations

import time
from dataclasses import asdict

from backend.app.agents.sql_generator import SQLGeneratorAgent
from backend.app.api.schemas import QueryRequest, QueryResponse
from backend.app.core.exceptions import (
    AppException,
    QueryExecutionError,
    QueryTimeoutError,
    SQLGenerationError,
    SQLValidationError,
)
from backend.app.core.logging import get_logger
from backend.app.rag.retriever import ContextRetriever
from backend.app.sql.executor import execute_readonly_query, rows_to_dicts
from backend.app.sql.validator import validate_or_raise

logger = get_logger(__name__)


class QueryPipeline:
    """Orchestrates the full NL-to-SQL-to-Results pipeline.

    Each call to `run()` is a self-contained, stateless request — all
    context is created per-invocation so the pipeline is concurrency-safe.
    """

    def __init__(
        self,
        retriever: ContextRetriever | None = None,
        generator: SQLGeneratorAgent | None = None,
    ):
        self._retriever = retriever or ContextRetriever()
        self._generator = generator or SQLGeneratorAgent()

    async def run(self, request: QueryRequest) -> QueryResponse:
        """Execute the full NL→SQL pipeline.

        Args:
            request: The incoming QueryRequest with prompt and optional user_id.

        Returns:
            QueryResponse with generated SQL, result data, and metrics.

        Raises:
            SQLGenerationError: If the LLM cannot produce valid SQL.
            SQLValidationError: If the generated SQL fails safety checks.
            QueryExecutionError: If the query fails at the database level.
            QueryTimeoutError: If the query exceeds the timeout.
        """
        pipeline_start = time.perf_counter()
        question = request.prompt

        logger.info(
            "pipeline_started",
            question=question[:100],
            user_id=request.user_id,
        )

        # --- Stage 1: Context Retrieval (RAG) ---
        context = await self._retriever.retrieve(question)

        logger.info(
            "context_retrieved",
            tables=len(context.tables),
            glossary=len(context.glossary_terms),
            metrics=len(context.metrics),
            examples=len(context.example_queries),
        )

        # --- Stage 2: SQL Generation ---
        generation_result = await self._generator.generate(
            question=question,
            context=context,
        )
        generated_sql = generation_result.sql

        logger.info(
            "sql_generated",
            sql=generated_sql[:200],
            confidence=generation_result.confidence,
            tokens=generation_result.tokens_used,
        )

        # --- Stage 3: Safety Validation ---
        validated_sql = validate_or_raise(generated_sql)

        # --- Stage 4: Query Execution ---
        exec_result = await execute_readonly_query(validated_sql)

        # --- Stage 5: Format Results ---
        data = rows_to_dicts(exec_result.columns, exec_result.rows)

        elapsed_ms = (time.perf_counter() - pipeline_start) * 1000

        # Build explanation from generation metadata
        assumptions_text = ""
        if generation_result.assumptions:
            assumptions_text = " Assumptions: " + "; ".join(generation_result.assumptions) + "."

        explanation = (
            f"Generated a SQL query with {generation_result.confidence:.0%} confidence "
            f"using {len(context.tables)} table(s)."
            f"{assumptions_text}"
        )

        if exec_result.truncated:
            explanation += " Note: results were truncated to the configured row limit."

        logger.info(
            "pipeline_completed",
            execution_time_ms=round(elapsed_ms, 2),
            row_count=exec_result.row_count,
            user_id=request.user_id,
        )

        return QueryResponse(
            query=question,
            generated_sql=validated_sql,
            data=data,
            row_count=exec_result.row_count,
            execution_time_ms=round(elapsed_ms, 2),
            explanation=explanation,
        )

"""SQL Generation Agent — generates SQL from natural language + context.

This agent:
1. Takes a user question + retrieved context (from RAG)
2. Builds a context-aware prompt with schema, relationships, glossary, examples
3. Calls the LLM provider to generate SQL
4. Parses the structured JSON response
5. Returns a SQLGenerationResult

The generated SQL is NEVER executed directly — it always goes through
validation and security checks first.
"""

import json
import time
from typing import Any

from backend.app.core.exceptions import SQLGenerationError
from backend.app.core.types import LLMResponse, RetrievedContext, SQLGenerationResult
from backend.app.infrastructure.llm.adapter import MockLLMAdapter, OpenAILLMAdapter, get_llm_provider
from backend.app.prompts.sql_generation import SQL_GENERATION_SYSTEM, build_sql_generation_prompt


class SQLGeneratorAgent:
    """Agent responsible for generating SQL from natural language questions.

    Uses the LLM provider with the sql_generation prompt template,
    providing full schema context from RAG retrieval.
    """

    def __init__(
        self,
        llm_provider: OpenAILLMAdapter | MockLLMAdapter | None = None,
        dialect: str = "postgresql",
        max_retries: int = 2,
    ):
        self._llm = llm_provider or get_llm_provider()
        self._dialect = dialect
        self._max_retries = max_retries

    async def generate(
        self,
        question: str,
        context: RetrievedContext,
        dialect: str | None = None,
    ) -> SQLGenerationResult:
        """Generate SQL from a natural language question with context.

        Args:
            question: The user's natural language question.
            context: Retrieved context (tables, relationships, glossary, examples).
            dialect: Optional override for SQL dialect.

        Returns:
            SQLGenerationResult with generated SQL and metadata.

        Raises:
            SQLGenerationError: If SQL generation fails after all retries.
        """
        target_dialect = dialect or self._dialect
        start_time = time.perf_counter()
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                # Build the prompt with full context
                prompt = build_sql_generation_prompt(
                    question=question,
                    context=context,
                    dialect=target_dialect,
                )

                # Call LLM
                response: LLMResponse = await self._llm.generate(
                    prompt=prompt,
                    system_prompt=SQL_GENERATION_SYSTEM,
                    temperature=0.1 + (attempt * 0.1),  # Increase creativity on retries
                )

                # Parse the response
                result = self._parse_response(response)
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                return SQLGenerationResult(
                    sql=result["sql"],
                    tables_used=result.get("tables_used", []),
                    columns_used=result.get("columns_used", []),
                    assumptions=result.get("assumptions", []),
                    confidence=result.get("confidence", 0.0),
                    tokens_used=response.tokens_input + response.tokens_output,
                    generation_time_ms=elapsed_ms,
                )

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                last_error = e
                # Retry with simplified prompt on parse errors
                continue

        # All retries exhausted
        raise SQLGenerationError(
            message=f"Failed to generate valid SQL after {self._max_retries + 1} attempts",
            details={"last_error": str(last_error), "question": question},
        )

    def _parse_response(self, response: LLMResponse) -> dict[str, Any]:
        """Parse the LLM response into a structured result.

        Expects JSON with keys: sql, tables_used, columns_used, assumptions, confidence.
        Handles common LLM response formatting issues (markdown code blocks, extra text).
        """
        text = response.text.strip()

        # Strip markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Try to parse as JSON
        result = json.loads(text)

        # Validate required fields
        if "sql" not in result or not result["sql"]:
            raise ValueError("LLM response missing 'sql' field")

        # Normalize
        result["sql"] = result["sql"].strip().rstrip(";")
        result.setdefault("tables_used", [])
        result.setdefault("columns_used", [])
        result.setdefault("assumptions", [])
        result.setdefault("confidence", 0.5)

        return result

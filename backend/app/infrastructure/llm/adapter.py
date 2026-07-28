"""LLM provider adapters — OpenAI and Mock implementations.

The mock adapter returns pre-defined responses for testing without API keys.
It recognizes question patterns and returns plausible SQL/intent/explanation.
"""

import json
import time
from typing import Any

from backend.app.core.config import get_settings
from backend.app.core.exceptions import LLMProviderError
from backend.app.core.types import LLMResponse


class OpenAILLMAdapter:
    """OpenAI ChatCompletion adapter.

    Uses the OpenAI API for production-quality text generation.
    Requires LLM_API_KEY to be set.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        settings = get_settings()
        self._api_key = api_key or settings.llm_api_key
        self._model = model or settings.llm_model
        self._temperature = temperature if temperature is not None else settings.llm_temperature
        self._max_tokens = max_tokens or settings.llm_max_tokens
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except Exception as e:
                raise LLMProviderError(message=f"Failed to initialize OpenAI client: {e}")
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text using OpenAI ChatCompletion API."""
        start = time.perf_counter()
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature if temperature is not None else self._temperature,
                max_tokens=max_tokens or self._max_tokens,
                **kwargs,
            )

            elapsed_ms = (time.perf_counter() - start) * 1000
            choice = response.choices[0]
            usage = response.usage

            return LLMResponse(
                text=choice.message.content or "",
                tokens_input=usage.prompt_tokens if usage else 0,
                tokens_output=usage.completion_tokens if usage else 0,
                model=self._model,
                latency_ms=elapsed_ms,
            )
        except Exception as e:
            raise LLMProviderError(message=f"OpenAI generation failed: {e}")

    async def health_check(self) -> bool:
        """Check if OpenAI API is reachable."""
        try:
            client = self._get_client()
            # Simple models list call to verify connectivity
            await client.models.list()
            return True
        except Exception:
            return False


class MockLLMAdapter:
    """Mock LLM adapter for local development and testing.

    Returns plausible pre-defined responses based on prompt patterns.
    No API keys required. Useful for testing the full pipeline flow
    without incurring API costs.
    """

    def __init__(self):
        self._call_count = 0

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a mock response based on prompt patterns."""
        start = time.perf_counter()
        self._call_count += 1

        # Determine what kind of response is expected based on system_prompt
        response_text = self._generate_mock_response(prompt, system_prompt or "")

        elapsed_ms = (time.perf_counter() - start) * 1000
        return LLMResponse(
            text=response_text,
            tokens_input=len(prompt) // 4,
            tokens_output=len(response_text) // 4,
            model="mock-llm",
            latency_ms=elapsed_ms,
        )

    async def health_check(self) -> bool:
        return True

    def _generate_mock_response(self, prompt: str, system_prompt: str) -> str:
        """Route to appropriate mock response generator."""
        prompt_lower = prompt.lower()
        system_lower = system_prompt.lower()

        # Intent detection
        if "intent" in system_lower or "classify" in system_lower:
            return self._mock_intent_response(prompt_lower)

        # SQL generation
        if "sql" in system_lower and "generate" in system_lower:
            return self._mock_sql_response(prompt_lower)

        # SQL correction
        if "correct" in system_lower or "fix" in system_lower:
            return self._mock_correction_response(prompt_lower)

        # Explanation
        if "explain" in system_lower or "summarize" in system_lower:
            return self._mock_explanation_response(prompt_lower)

        # Visualization
        if "visualization" in system_lower or "chart" in system_lower:
            return self._mock_visualization_response(prompt_lower)

        # Default: treat as SQL generation
        return self._mock_sql_response(prompt_lower)

    def _mock_intent_response(self, prompt: str) -> str:
        """Mock intent classification."""
        category = "aggregation"
        if "top" in prompt or "best" in prompt or "highest" in prompt:
            category = "ranking"
        elif "trend" in prompt or "over time" in prompt or "monthly" in prompt:
            category = "trend"
        elif "compare" in prompt or "vs" in prompt:
            category = "comparison"
        elif "how many" in prompt or "count" in prompt:
            category = "count"

        return json.dumps({
            "category": category,
            "entities": ["products", "revenue"],
            "time_range": None,
            "filters": [],
            "ambiguity_score": 0.2,
        })

    def _mock_sql_response(self, prompt: str) -> str:
        """Mock SQL generation."""
        # Default: top products by revenue
        sql = (
            "SELECT p.product_name, SUM(oi.line_total) AS revenue\n"
            "FROM products p\n"
            "JOIN order_items oi ON oi.product_id = p.product_id\n"
            "JOIN orders o ON o.order_id = oi.order_id\n"
            "WHERE o.status = 'completed'\n"
            "GROUP BY p.product_name\n"
            "ORDER BY revenue DESC\n"
            "LIMIT 5"
        )

        if "region" in prompt:
            sql = (
                "SELECT r.region_name, SUM(oi.line_total) AS revenue\n"
                "FROM regions r\n"
                "JOIN customers c ON c.region_id = r.region_id\n"
                "JOIN orders o ON o.customer_id = c.customer_id\n"
                "JOIN order_items oi ON oi.order_id = o.order_id\n"
                "WHERE o.status = 'completed'\n"
                "GROUP BY r.region_name\n"
                "ORDER BY revenue DESC"
            )
        elif "monthly" in prompt or "trend" in prompt:
            sql = (
                "SELECT DATE_TRUNC('month', o.order_date) AS month,\n"
                "       SUM(oi.line_total) AS revenue\n"
                "FROM orders o\n"
                "JOIN order_items oi ON oi.order_id = o.order_id\n"
                "WHERE o.status = 'completed'\n"
                "GROUP BY DATE_TRUNC('month', o.order_date)\n"
                "ORDER BY month"
            )
        elif "count" in prompt or "how many" in prompt:
            sql = "SELECT COUNT(*) AS total_orders FROM orders"

        return json.dumps({
            "sql": sql,
            "tables_used": ["products", "order_items", "orders"],
            "columns_used": ["product_name", "line_total", "order_id", "product_id", "status"],
            "assumptions": ["Filtered to completed orders only", "Revenue = SUM(line_total)"],
            "confidence": 0.88,
        })

    def _mock_correction_response(self, prompt: str) -> str:
        """Mock SQL correction."""
        return json.dumps({
            "sql": (
                "SELECT p.product_name, SUM(oi.line_total) AS revenue\n"
                "FROM products p\n"
                "JOIN order_items oi ON oi.product_id = p.product_id\n"
                "JOIN orders o ON o.order_id = oi.order_id\n"
                "WHERE o.status = 'completed'\n"
                "GROUP BY p.product_name\n"
                "ORDER BY revenue DESC\n"
                "LIMIT 5"
            ),
            "explanation": "Fixed column reference and added proper JOIN condition.",
            "confidence": 0.82,
        })

    def _mock_explanation_response(self, prompt: str) -> str:
        """Mock result explanation."""
        return (
            "The query results show the top performing products by revenue. "
            "The highest revenue product generated significantly more income than "
            "the others, indicating strong market demand in that category."
        )

    def _mock_visualization_response(self, prompt: str) -> str:
        """Mock visualization recommendation."""
        return json.dumps({
            "chart_type": "bar",
            "config": {
                "x_axis": "product_name",
                "y_axis": "revenue",
                "title": "Top Products by Revenue",
                "sort": "descending",
            },
            "reasoning": "Categorical data with a numeric metric is best shown as a bar chart.",
        })


def get_llm_provider() -> OpenAILLMAdapter | MockLLMAdapter:
    """Factory function — returns the configured LLM provider.

    If no API key is set, returns the mock adapter for local development.
    """
    settings = get_settings()

    if settings.llm_api_key and settings.llm_api_key != "<YOUR_LLM_API_KEY>":
        return OpenAILLMAdapter()
    else:
        return MockLLMAdapter()

"""LLM provider protocol — the interface all LLM adapters implement."""

from typing import Protocol

from backend.app.core.types import LLMResponse


class LLMProvider(Protocol):
    """Protocol for LLM text generation providers.

    Implementations wrap a specific LLM API (OpenAI, Anthropic, local, etc.)
    behind this common interface.
    """

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text from a prompt.

        Args:
            prompt: The user/assistant prompt text.
            system_prompt: Optional system instruction.
            temperature: Override default temperature (0-2).
            max_tokens: Override default max tokens.
            **kwargs: Provider-specific parameters.

        Returns:
            LLMResponse with generated text, token counts, and metadata.
        """
        ...

    async def health_check(self) -> bool:
        """Check if the LLM provider is reachable."""
        ...

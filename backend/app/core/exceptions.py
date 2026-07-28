"""Custom exception hierarchy for the application.

All exceptions are organized by domain. Each exception carries
structured context so error handlers can produce meaningful API responses.
"""

from typing import Any


class AppException(Exception):
    """Base application exception.

    All custom exceptions inherit from this so we can catch
    application errors separately from unexpected system errors.
    """

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# --- Authentication & Authorization ---


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401, **kwargs)


class TokenExpiredError(AppException):
    """Raised when a JWT token has expired."""

    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(message=message, code="TOKEN_EXPIRED", status_code=401)


class AccessDeniedError(AppException):
    """Raised when a user lacks permission for a resource."""

    def __init__(
        self,
        message: str = "Access denied",
        resource: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        d = details or {}
        if resource:
            d["resource"] = resource
        super().__init__(message=message, code="ACCESS_DENIED", status_code=403, details=d)


class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message=message, code="RATE_LIMITED", status_code=429)


# --- SQL & Query ---


class SQLGenerationError(AppException):
    """Raised when SQL generation fails after all retries."""

    def __init__(self, message: str = "Failed to generate valid SQL", **kwargs: Any) -> None:
        super().__init__(
            message=message, code="SQL_GENERATION_FAILED", status_code=422, **kwargs
        )


class SQLValidationError(AppException):
    """Raised when generated SQL fails validation."""

    def __init__(
        self,
        message: str = "SQL validation failed",
        errors: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        details["errors"] = errors or []
        super().__init__(
            message=message, code="VALIDATION_FAILED", status_code=422, details=details, **kwargs
        )


class QueryCostExceededError(AppException):
    """Raised when estimated query cost exceeds limits."""

    def __init__(
        self,
        message: str = "Query cost exceeds configured limit",
        estimated_cost: float | None = None,
        max_cost: float | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if estimated_cost is not None:
            details["estimated_cost"] = estimated_cost
        if max_cost is not None:
            details["max_cost"] = max_cost
        super().__init__(
            message=message, code="COST_LIMIT_EXCEEDED", status_code=422, details=details
        )


class QueryExecutionError(AppException):
    """Raised when query execution fails."""

    def __init__(self, message: str = "Query execution failed", **kwargs: Any) -> None:
        super().__init__(message=message, code="QUERY_EXECUTION_FAILED", status_code=500, **kwargs)


class QueryTimeoutError(AppException):
    """Raised when a query exceeds the execution time limit."""

    def __init__(self, message: str = "Query execution timed out") -> None:
        super().__init__(message=message, code="QUERY_TIMEOUT", status_code=408)


# --- External Service Errors ---


class LLMProviderError(AppException):
    """Raised when the LLM provider is unavailable or returns an error."""

    def __init__(self, message: str = "LLM provider error", **kwargs: Any) -> None:
        super().__init__(message=message, code="LLM_UNAVAILABLE", status_code=503, **kwargs)


class EmbeddingProviderError(AppException):
    """Raised when the embedding provider fails."""

    def __init__(self, message: str = "Embedding provider error", **kwargs: Any) -> None:
        super().__init__(message=message, code="EMBEDDING_UNAVAILABLE", status_code=503, **kwargs)


class VectorStoreError(AppException):
    """Raised when the vector store is unavailable."""

    def __init__(self, message: str = "Vector store unavailable", **kwargs: Any) -> None:
        super().__init__(message=message, code="VECTOR_STORE_UNAVAILABLE", status_code=503, **kwargs)


# --- Resource Errors ---


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", resource: str | None = None) -> None:
        details = {"resource": resource} if resource else {}
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class DuplicateResourceError(AppException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message=message, code="DUPLICATE_RESOURCE", status_code=409)


# --- Validation Errors ---


class InvalidRequestError(AppException):
    """Raised when request data is invalid."""

    def __init__(self, message: str = "Invalid request", **kwargs: Any) -> None:
        super().__init__(message=message, code="INVALID_REQUEST", status_code=400, **kwargs)

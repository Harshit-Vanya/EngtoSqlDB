"""Unit tests for core module — config, exceptions, types."""

import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    AccessDeniedError,
    AppException,
    AuthenticationError,
    NotFoundError,
    QueryCostExceededError,
    SQLGenerationError,
    SQLValidationError,
)
from backend.app.core.types import (
    IntentResult,
    Permissions,
    QueryState,
    RetrievedContext,
    SQLGenerationResult,
    UserContext,
    ValidationResult,
)


class TestSettings:
    """Test configuration loading."""

    def test_default_settings(self):
        settings = Settings()
        assert settings.app_name == "ai-text-to-sql"
        assert settings.app_env == "development"
        assert settings.max_retries == 3
        assert settings.max_rows_returned == 1000

    def test_cors_origin_list(self):
        settings = Settings(cors_origins="http://localhost:3000,http://localhost:5173")
        assert settings.cors_origin_list == ["http://localhost:3000", "http://localhost:5173"]

    def test_is_development(self):
        settings = Settings(app_env="development")
        assert settings.is_development is True
        assert settings.is_production is False

    def test_sync_database_url(self):
        settings = Settings(database_url="postgresql+asyncpg://user:pass@host/db")
        assert settings.sync_database_url == "postgresql://user:pass@host/db"


class TestExceptions:
    """Test custom exception hierarchy."""

    def test_base_exception(self):
        exc = AppException(message="test", code="TEST", status_code=500)
        assert str(exc) == "test"
        assert exc.code == "TEST"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_auth_error(self):
        exc = AuthenticationError()
        assert exc.status_code == 401
        assert exc.code == "UNAUTHORIZED"

    def test_access_denied_with_resource(self):
        exc = AccessDeniedError(resource="orders")
        assert exc.status_code == 403
        assert exc.details["resource"] == "orders"

    def test_sql_validation_error_with_errors(self):
        exc = SQLValidationError(errors=["table not found", "column mismatch"])
        assert exc.status_code == 422
        assert len(exc.details["errors"]) == 2

    def test_sql_generation_error(self):
        exc = SQLGenerationError()
        assert exc.code == "SQL_GENERATION_FAILED"

    def test_cost_exceeded_error(self):
        exc = QueryCostExceededError(estimated_cost=5000.0, max_cost=1000.0)
        assert exc.details["estimated_cost"] == 5000.0
        assert exc.details["max_cost"] == 1000.0

    def test_not_found_error(self):
        exc = NotFoundError(resource="query-123")
        assert exc.status_code == 404
        assert exc.details["resource"] == "query-123"


class TestTypes:
    """Test core type definitions."""

    def test_query_state_enum(self):
        assert QueryState.RECEIVED == "received"
        assert QueryState.COMPLETED == "completed"

    def test_user_context(self):
        user = UserContext(
            user_id="u1",
            email="test@example.com",
            display_name="Test User",
            roles=["analyst"],
        )
        assert user.user_id == "u1"
        assert user.roles == ["analyst"]

    def test_permissions(self):
        perms = Permissions(
            allowed_tables={"orders", "products"},
            denied_columns={"customers": {"email", "phone"}},
        )
        assert "orders" in perms.allowed_tables
        assert "email" in perms.denied_columns["customers"]

    def test_intent_result(self):
        intent = IntentResult(
            category="aggregation",
            entities=["revenue", "products"],
            ambiguity_score=0.2,
        )
        assert intent.category == "aggregation"
        assert len(intent.entities) == 2

    def test_sql_generation_result(self):
        result = SQLGenerationResult(
            sql="SELECT * FROM orders",
            tables_used=["orders"],
            confidence=0.85,
        )
        assert result.confidence == 0.85

    def test_validation_result_valid(self):
        result = ValidationResult(is_valid=True, risk_level="LOW")
        assert result.is_valid is True
        assert result.errors == []

    def test_validation_result_invalid(self):
        result = ValidationResult(
            is_valid=False,
            errors=["Unknown table: nonexistent"],
            risk_level="HIGH",
        )
        assert result.is_valid is False
        assert len(result.errors) == 1

    def test_retrieved_context_defaults(self):
        ctx = RetrievedContext()
        assert ctx.tables == []
        assert ctx.total_context_tokens == 0

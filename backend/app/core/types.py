"""Shared type definitions used across the application.

These are domain-level data structures — not ORM models, not API schemas.
They represent the internal contracts between modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# --- Enums ---


class QueryState(str, Enum):
    """States in the query orchestrator state machine."""

    RECEIVED = "received"
    AUTHENTICATING = "authenticating"
    INTENT_DETECTION = "intent_detection"
    CONTEXT_RETRIEVAL = "context_retrieval"
    SQL_GENERATION = "sql_generation"
    VALIDATION = "validation"
    SECURITY_CHECK = "security_check"
    COST_CHECK = "cost_check"
    EXECUTION = "execution"
    SELF_CORRECTION = "self_correction"
    RESULT_PROCESSING = "result_processing"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# --- Data Structures ---


@dataclass
class UserContext:
    """Represents an authenticated user with their permissions."""

    user_id: str
    email: str
    display_name: str
    roles: list[str] = field(default_factory=list)
    permissions: Permissions | None = None


@dataclass
class Permissions:
    """Resolved user permissions."""

    allowed_tables: set[str] = field(default_factory=set)
    allowed_columns: dict[str, set[str]] = field(default_factory=dict)  # table -> columns
    denied_columns: dict[str, set[str]] = field(default_factory=dict)  # table -> columns
    row_filters: dict[str, str] = field(default_factory=dict)  # table -> WHERE clause
    max_rows: int = 1000


@dataclass
class IntentResult:
    """Result of intent detection."""

    category: str
    entities: list[str] = field(default_factory=list)
    time_range: dict[str, Any] | None = None
    filters: list[dict[str, Any]] = field(default_factory=list)
    ambiguity_score: float = 0.0


@dataclass
class TableSchema:
    """Schema definition for a single table."""

    table_name: str
    schema_name: str = "public"
    description: str = ""
    columns: list[ColumnSchema] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)


@dataclass
class ColumnSchema:
    """Schema definition for a single column."""

    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    description: str = ""
    business_definition: str = ""


@dataclass
class ForeignKey:
    """Foreign key relationship."""

    column: str
    references_table: str
    references_column: str


@dataclass
class RetrievedContext:
    """Context package assembled by the RAG retriever."""

    tables: list[TableSchema] = field(default_factory=list)
    relationships: list[dict[str, str]] = field(default_factory=list)
    glossary_terms: list[dict[str, str]] = field(default_factory=list)
    metrics: list[dict[str, str]] = field(default_factory=list)
    example_queries: list[dict[str, str]] = field(default_factory=list)
    total_context_tokens: int = 0


@dataclass
class SQLGenerationResult:
    """Result of SQL generation."""

    sql: str
    tables_used: list[str] = field(default_factory=list)
    columns_used: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    tokens_used: int = 0
    generation_time_ms: float = 0.0


@dataclass
class ValidationResult:
    """Result of SQL validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tables_used: list[str] = field(default_factory=list)
    columns_used: list[str] = field(default_factory=list)
    operations_detected: list[str] = field(default_factory=list)
    risk_level: str = "LOW"


@dataclass
class SecurityResult:
    """Result of security/permission check."""

    allowed: bool
    violations: list[dict[str, str]] = field(default_factory=list)
    row_filters_applied: list[str] = field(default_factory=list)


@dataclass
class CostResult:
    """Result of query cost estimation."""

    estimated_cost: float = 0.0
    estimated_rows: int = 0
    within_limits: bool = True
    verdict: str = "safe"  # safe | warning | reject
    warnings: list[str] = field(default_factory=list)
    query_plan_summary: str = ""


@dataclass
class ExecutionResult:
    """Result of query execution."""

    status: str  # success | error | timeout
    columns: list[dict[str, str]] = field(default_factory=list)  # [{name, type}]
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    execution_time_ms: float = 0.0
    error_message: str | None = None


@dataclass
class VisualizationConfig:
    """Recommended visualization configuration."""

    chart_type: str = "table"
    config: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class CorrectionRecord:
    """Record of a single self-correction attempt."""

    attempt_number: int
    original_sql: str
    error_message: str
    corrected_sql: str
    correction_status: str  # success | failed
    latency_ms: float = 0.0


@dataclass
class QueryMetadata:
    """Metadata collected during query processing."""

    request_id: str = ""
    total_latency_ms: float = 0.0
    llm_tokens_used: int = 0
    estimated_llm_cost_usd: float = 0.0
    retry_count: int = 0
    states_visited: list[str] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    text: str
    tokens_input: int = 0
    tokens_output: int = 0
    model: str = ""
    latency_ms: float = 0.0


@dataclass
class SearchResult:
    """Single result from a vector store search."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

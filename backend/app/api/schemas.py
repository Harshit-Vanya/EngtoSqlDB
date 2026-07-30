"""Pydantic request/response schemas for the API layer.

All API I/O contracts are defined here — separate from the internal
domain types in core.types to allow independent evolution.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    """POST /api/v1/query request body."""

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language question to convert to SQL.",
        examples=["What are the top 5 products by revenue?"],
    )
    user_id: str | None = Field(
        default=None,
        description="Optional user identifier for audit logging.",
    )


class SchemaIndexRequest(BaseModel):
    """POST /api/v1/schema/index request body."""

    force_reindex: bool = Field(
        default=False,
        description="If true, re-index even if already indexed.",
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class QueryResponse(BaseModel):
    """POST /api/v1/query response body."""

    query: str = Field(
        description="The original natural language question.",
    )
    generated_sql: str = Field(
        description="The SQL SELECT statement generated from the prompt.",
    )
    data: list[dict] = Field(
        default_factory=list,
        description="Query result rows as list of column-keyed dicts.",
    )
    row_count: int = Field(
        default=0,
        description="Number of rows returned.",
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Total wall-clock time for the full pipeline in ms.",
    )
    explanation: str = Field(
        default="",
        description="Natural language explanation of the query and results.",
    )


class SchemaIndexResponse(BaseModel):
    """POST /api/v1/schema/index response body."""

    tables: int = 0
    glossary: int = 0
    metrics: int = 0
    examples: int = 0
    relationships: int = 0
    total_indexed: int = 0


class ServiceHealth(BaseModel):
    """Health status for a single dependency."""

    status: str = "unknown"
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """GET /health response body."""

    status: str = "healthy"
    version: str = ""
    environment: str = ""
    services: dict[str, ServiceHealth] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    success: bool = False
    error: ErrorDetail


class ErrorDetail(BaseModel):
    """Error detail payload."""

    code: str
    message: str
    details: dict | None = None

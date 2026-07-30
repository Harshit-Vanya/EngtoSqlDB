"""API Routes — FastAPI router for the NL-to-SQL analytics platform.

Endpoints:
  GET  /health              Deep health check (Postgres + ChromaDB)
  POST /api/v1/schema/index  Index schema catalog into ChromaDB
  POST /api/v1/query         Core NL → SQL → Results pipeline
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.app.api.schemas import (
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SchemaIndexRequest,
    SchemaIndexResponse,
    ServiceHealth,
)
from backend.app.core.config import get_settings
from backend.app.core.exceptions import AppException
from backend.app.core.logging import get_logger
from backend.app.infrastructure.database.session import (
    get_analytics_engine,
    get_app_engine,
)
from backend.app.infrastructure.vector_store.adapter import get_vector_store
from backend.app.rag.indexer import index_schema_catalog
from backend.app.services.query_pipeline import QueryPipeline

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter()

# Singleton pipeline — stateless, safe for concurrent use
_pipeline: QueryPipeline | None = None


def _get_pipeline() -> QueryPipeline:
    """Lazy-initialise the query pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = QueryPipeline()
    return _pipeline


# ---------------------------------------------------------------------------
# GET /health — deep health check
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Deep health check with dependency status",
)
async def health_check() -> HealthResponse:
    """Check the health of all external dependencies.

    Probes:
      - Application Postgres (primary DB)
      - Analytics Postgres (query target DB)
      - ChromaDB vector store
    """
    settings = get_settings()
    services: dict[str, ServiceHealth] = {}

    # --- Application database ---
    services["postgres_app"] = await _probe_database(get_app_engine, "app")

    # --- Analytics database ---
    services["postgres_analytics"] = await _probe_database(
        get_analytics_engine, "analytics"
    )

    # --- ChromaDB ---
    services["chromadb"] = await _probe_chromadb()

    # Overall status
    all_healthy = all(s.status == "healthy" for s in services.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=settings.app_version,
        environment=settings.app_env,
        services=services,
    )


async def _probe_database(engine_factory, label: str) -> ServiceHealth:
    """Probe a Postgres engine with SELECT 1."""
    start = time.perf_counter()
    try:
        from sqlalchemy import text as sa_text

        engine = engine_factory()
        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        return ServiceHealth(status="healthy", latency_ms=round(latency, 2))
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        return ServiceHealth(
            status="unhealthy",
            latency_ms=round(latency, 2),
            error=str(exc)[:200],
        )


async def _probe_chromadb() -> ServiceHealth:
    """Probe the ChromaDB vector store."""
    start = time.perf_counter()
    try:
        store = get_vector_store()
        ok = await store.health_check()
        latency = (time.perf_counter() - start) * 1000
        return ServiceHealth(
            status="healthy" if ok else "unhealthy",
            latency_ms=round(latency, 2),
        )
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        return ServiceHealth(
            status="unhealthy",
            latency_ms=round(latency, 2),
            error=str(exc)[:200],
        )


# ---------------------------------------------------------------------------
# POST /api/v1/schema/index — index schema into ChromaDB
# ---------------------------------------------------------------------------


@router.post(
    "/api/v1/schema/index",
    response_model=SchemaIndexResponse,
    tags=["schema"],
    summary="Index database schema definitions into ChromaDB",
)
async def index_schema(
    request: SchemaIndexRequest | None = None,
) -> SchemaIndexResponse:
    """Ingest the YAML schema catalog into the ChromaDB vector store.

    This must be called at least once before /api/v1/query will work,
    so the retriever has schema context to search over.
    """
    try:
        # Check if already indexed (skip if not forced)
        if request and not request.force_reindex:
            store = get_vector_store()
            count = await store.count()
            if count > 0:
                logger.info("schema_already_indexed", document_count=count)
                return SchemaIndexResponse(total_indexed=count)

        result = await index_schema_catalog()

        logger.info("schema_indexed", **result)
        return SchemaIndexResponse(**result)

    except AppException:
        raise
    except Exception as exc:
        logger.error("schema_index_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail={"code": "SCHEMA_INDEX_FAILED", "message": str(exc)},
        ) from exc


# ---------------------------------------------------------------------------
# POST /api/v1/query — core NL-to-SQL pipeline
# ---------------------------------------------------------------------------


@router.post(
    "/api/v1/query",
    response_model=QueryResponse,
    tags=["query"],
    summary="Convert natural language to SQL and execute",
    responses={
        422: {"model": ErrorResponse, "description": "Validation or generation failed"},
        408: {"model": ErrorResponse, "description": "Query timeout"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
)
async def run_query(request: QueryRequest) -> QueryResponse:
    """Full NL → RAG → LLM → Validate → Execute → Results pipeline.

    Accepts a natural language question, retrieves relevant schema context
    via vector search, generates a safe read-only SQL SELECT, validates it,
    executes against the analytics database, and returns formatted results.
    """
    try:
        pipeline = _get_pipeline()
        response = await pipeline.run(request)
        return response

    except AppException as exc:
        logger.warning(
            "pipeline_app_error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        ) from exc

    except Exception as exc:
        logger.error("pipeline_unexpected_error", error=str(exc), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while processing the query.",
            },
        ) from exc

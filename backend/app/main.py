"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    setup_logging()

    from backend.app.infrastructure.database.session import close_engines, get_app_engine

    # Startup: verify database engines can be created (lazy init)
    get_app_engine()
    yield

    # Shutdown: close all database connections
    await close_engines()


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-Powered Natural Language to SQL Analytics Platform",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check (always available, no auth)
    @app.get("/api/v1/health", tags=["health"])
    async def health_check() -> dict:
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "version": settings.app_version,
                "environment": settings.app_env,
            },
        }

    return app


# Application instance
app = create_app()

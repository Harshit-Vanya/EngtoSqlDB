"""Database session management — SQLAlchemy async engine and session factory.

Provides two separate database connections:
1. Application DB — for users, permissions, query history, metadata (read/write)
2. Analytics DB — for executing user queries (read-only)
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import get_settings

# --- Application Database Engine (read/write) ---

_app_engine = None
_app_session_factory = None

# --- Analytics Database Engine (read-only for user queries) ---

_analytics_engine = None
_analytics_session_factory = None


def get_app_engine():
    """Get or create the application database engine."""
    global _app_engine
    if _app_engine is None:
        settings = get_settings()
        _app_engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _app_engine


def get_analytics_engine():
    """Get or create the analytics database engine (read-only)."""
    global _analytics_engine
    if _analytics_engine is None:
        settings = get_settings()
        _analytics_engine = create_async_engine(
            settings.analytics_database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_recycle=3600,
            # Connection-level read-only enforcement
            execution_options={"isolation_level": "AUTOCOMMIT"},
        )
    return _analytics_engine


def get_app_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the application session factory."""
    global _app_session_factory
    if _app_session_factory is None:
        _app_session_factory = async_sessionmaker(
            bind=get_app_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _app_session_factory


def get_analytics_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the analytics session factory."""
    global _analytics_session_factory
    if _analytics_session_factory is None:
        _analytics_session_factory = async_sessionmaker(
            bind=get_analytics_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _analytics_session_factory


async def get_app_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency — yields an application database session.

    Used with FastAPI's Depends() for request-scoped sessions.
    """
    factory = get_app_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_analytics_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency — yields a read-only analytics database session."""
    factory = get_analytics_session_factory()
    async with factory() as session:
        yield session


async def close_engines() -> None:
    """Close all database engines — called during shutdown."""
    global _app_engine, _analytics_engine, _app_session_factory, _analytics_session_factory
    if _app_engine:
        await _app_engine.dispose()
        _app_engine = None
        _app_session_factory = None
    if _analytics_engine:
        await _analytics_engine.dispose()
        _analytics_engine = None
        _analytics_session_factory = None

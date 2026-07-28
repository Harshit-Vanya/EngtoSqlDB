"""Query record and correction models — stores query history."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, generate_uuid


class QueryRecord(Base):
    """A single query submission and its lifecycle."""

    __tablename__ = "query_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    original_question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tables_used: Mapped[list | None] = mapped_column(JSON, default=list)
    columns_used: Mapped[list | None] = mapped_column(JSON, default=list)

    # Status fields
    validation_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    security_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    execution_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    # Performance metrics
    cost_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    rows_returned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # AI outputs
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    visualization_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class QueryCorrection(Base):
    """Record of a self-correction attempt."""

    __tablename__ = "query_corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    query_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("query_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_sql: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_sql: Mapped[str] = mapped_column(Text, nullable=False)
    correction_status: Mapped[str] = mapped_column(String(20), nullable=False)  # success/failed
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

"""Schema intelligence models — metadata catalog stored in the application DB."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, generate_uuid


class SchemaMetadata(Base):
    """Metadata about a database table or column — used for RAG and schema intelligence."""

    __tablename__ = "schema_metadata"
    __table_args__ = (
        UniqueConstraint(
            "database_name", "schema_name", "table_name", "column_name",
            name="uq_schema_metadata",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    database_name: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_name: Mapped[str] = mapped_column(String(100), nullable=False, default="public")
    table_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    column_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_foreign_key: Mapped[bool] = mapped_column(Boolean, default=False)
    fk_references: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    synonyms: Mapped[list | None] = mapped_column(JSON, default=list)
    tags: Mapped[list | None] = mapped_column(JSON, default=list)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BusinessGlossary(Base):
    """Business term definitions — maps business language to database concepts."""

    __tablename__ = "business_glossary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    term: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    related_tables: Mapped[list | None] = mapped_column(JSON, default=list)
    related_columns: Mapped[list | None] = mapped_column(JSON, default=list)
    synonyms: Mapped[list | None] = mapped_column(JSON, default=list)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MetricDefinition(Base):
    """Business metric definitions with SQL formulas."""

    __tablename__ = "metric_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    metric_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sql_formula: Mapped[str] = mapped_column(Text, nullable=False)
    required_tables: Mapped[list] = mapped_column(JSON, nullable=False)
    required_columns: Mapped[list] = mapped_column(JSON, nullable=False)
    aggregation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ExampleQuery(Base):
    """Example NL-to-SQL pairs — used as few-shot examples in RAG."""

    __tablename__ = "example_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    natural_language: Mapped[str] = mapped_column(Text, nullable=False)
    sql_query: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    tables_used: Mapped[list | None] = mapped_column(JSON, default=list)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

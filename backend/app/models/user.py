"""User ORM model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """Application user."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

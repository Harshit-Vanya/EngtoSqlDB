"""RBAC models — Roles, Permissions, and their relationships."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, generate_uuid


class Role(Base):
    """A named role (admin, analyst, business_user, restricted)."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserRole(Base):
    """Many-to-many relationship between users and roles."""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )


class Permission(Base):
    """A single permission entry — grants access to a resource."""

    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource_type", "resource_name", "action", name="uq_permission"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # table, column, operation
    resource_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # orders, customers.email
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # read, masked_read
    scope: Mapped[str] = mapped_column(String(50), default="full")  # full, filtered, masked
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # row-level filter
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RolePermission(Base):
    """Grants a permission to a role."""

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    permission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

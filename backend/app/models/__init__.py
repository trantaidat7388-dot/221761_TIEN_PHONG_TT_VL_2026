"""SQLAlchemy model definitions for the application domain.

This module keeps all ORM entities in one import location to preserve
backward compatibility with existing imports:
    from backend.app import models
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base


class User(Base):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user", nullable=False, index=True)
    plan_type: Mapped[str] = mapped_column(String, default="free", nullable=False, index=True)
    token_balance: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    premium_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    premium_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    auth_provider: Mapped[str] = mapped_column(String, default="local", nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    history: Mapped[List["ConversionHistory"]] = relationship("ConversionHistory", back_populates="owner", cascade="all, delete-orphan")
    token_ledger_entries: Mapped[List["TokenLedger"]] = relationship("TokenLedger", back_populates="owner", cascade="all, delete-orphan")


class ConversionHistory(Base):
    """Tracks each conversion request/result for a user."""

    __tablename__ = "conversion_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    job_id: Mapped[Optional[str]] = mapped_column(String, index=True)
    file_name: Mapped[Optional[str]] = mapped_column(String)
    template_name: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String, default="")
    pages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship("User", back_populates="history")


class TokenLedger(Base):
    """Ledger table for all token balance changes."""

    __tablename__ = "token_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    delta_token: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False, index=True)
    job_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    meta_json: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    owner: Mapped["User"] = relationship("User", back_populates="token_ledger_entries")


class AdminAuditLog(Base):
    """Audit trail for admin actions."""

    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    target_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    target_record_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Payment(Base):
    """Tracks token top-up payments via SePay."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount_vnd: Mapped[int] = mapped_column(Integer, nullable=False)
    token_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False, index=True)
    plan_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner: Mapped["User"] = relationship("User")


class LoginSession(Base):
    """Temporary login session for Cloud-Sync Polling (Hybrid WebView OAuth)."""

    __tablename__ = "login_sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class CustomPage(Base):
    """Dynamic custom HTML pages created via Admin Page Builder."""

    __tablename__ = "custom_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content_html: Mapped[str] = mapped_column(String, nullable=False, default="")
    css_variables: Mapped[Optional[str]] = mapped_column(String, nullable=True, default="{}")
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


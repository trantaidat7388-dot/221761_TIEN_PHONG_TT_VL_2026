"""SQLAlchemy model definitions for the application domain.

This module keeps all ORM entities in one import location to preserve
backward compatibility with existing imports:
    from backend.app import models
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    """Application user account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False, index=True)
    plan_type = Column(String, default="free", nullable=False, index=True)
    token_balance = Column(Integer, default=60, nullable=False)
    premium_started_at = Column(DateTime, nullable=True)
    premium_expires_at = Column(DateTime, nullable=True, index=True)
    auth_provider = Column(String, default="local", nullable=False)
    google_id = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    history = relationship("ConversionHistory", back_populates="owner", cascade="all, delete-orphan")
    token_ledger_entries = relationship("TokenLedger", back_populates="owner", cascade="all, delete-orphan")


class ConversionHistory(Base):
    """Tracks each conversion request/result for a user."""

    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(String, index=True)
    file_name = Column(String)
    template_name = Column(String)
    status = Column(String)
    file_path = Column(String, default="")
    pages_count = Column(Integer, default=0, nullable=False)
    token_cost = Column(Integer, default=0, nullable=False)
    token_refunded = Column(Boolean, default=False, nullable=False)
    error_type = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="history")


class TokenLedger(Base):
    """Ledger table for all token balance changes."""

    __tablename__ = "token_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    delta_token = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    reason = Column(String, nullable=False, index=True)
    job_id = Column(String, nullable=True, index=True)
    meta_json = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    owner = relationship("User", back_populates="token_ledger_entries")


class AdminAuditLog(Base):
    """Audit trail for admin actions."""

    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    target_user_id = Column(Integer, nullable=True, index=True)
    target_record_id = Column(String, nullable=True)
    detail = Column(String, nullable=True)
    request_id = Column(String, nullable=True, index=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Payment(Base):
    """Tracks token top-up payments via SePay."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount_vnd = Column(Integer, nullable=False)
    token_amount = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False, index=True)  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User")


class LoginSession(Base):
    """Temporary login session for Cloud-Sync Polling (Hybrid WebView OAuth)."""

    __tablename__ = "login_sessions"

    session_id = Column(String, primary_key=True, index=True)
    token = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)  # pending, completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

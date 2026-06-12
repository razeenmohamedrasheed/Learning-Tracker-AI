from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    FetchedValue,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database.db import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id       = Column(String(20), primary_key=True, server_default=FetchedValue())
    email         = Column(String(255), unique=True, nullable=False, index=True)
    name          = Column(String(100), nullable=False)
    contact       = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id       = Column(Integer, ForeignKey("roles.id"), nullable=False, default=2)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    role           = relationship("Role", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # ← ADD THESE TWO
    subjects       = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    subject_topics = relationship("SubjectTopic", back_populates="user", cascade="all, delete-orphan")
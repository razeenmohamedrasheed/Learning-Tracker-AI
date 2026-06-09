from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.database.db import Base


class Subject(Base):
    __tablename__ = "subjects"

    id         = Column(String(36), primary_key=True)   # UUID
    user_id    = Column(String(20), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    name       = Column(String(100), nullable=False)     # e.g. "Python"
    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=False)
    status     = Column(String(20), default="active")    # active/completed/paused
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user   = relationship("User", back_populates="subjects")
    topics = relationship("SubjectTopic", back_populates="subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject id={self.id} name={self.name}>"


class SubjectTopic(Base):
    __tablename__ = "subject_topics"

    id                 = Column(String(36), primary_key=True)   # UUID
    subject_id         = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    user_id            = Column(String(20), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    topic_name         = Column(String(100), nullable=False)     # e.g. "OOPs"
    target_percentage  = Column(Numeric(5, 2), nullable=False)   # e.g. 25.00 — auto calculated
    is_completed       = Column(Boolean, default=False)
    completed_at       = Column(DateTime(timezone=True), nullable=True)
    created_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    subject = relationship("Subject", back_populates="topics")
    user    = relationship("User", back_populates="subject_topics")

    def __repr__(self):
        return f"<SubjectTopic id={self.id} topic={self.topic_name} %={self.target_percentage}>"
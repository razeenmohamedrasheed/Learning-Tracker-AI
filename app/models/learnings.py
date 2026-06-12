from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import relationship
from app.database.db import Base


class Subject(Base):
    __tablename__ = "subjects"

    id         = Column(String(36), primary_key=True)
    user_id    = Column(
        String(20),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,                          # faster queries by user
    )
    name       = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=False)

    # -------------------------------------------------------
    # CHANGED: status values updated to match business logic
    # in_progress | completed | failed | partially_completed
    # Set manually by user — NOT auto-derived
    # -------------------------------------------------------
    status     = Column(String(30), nullable=False, default="in_progress")

    # -------------------------------------------------------
    # status_updated_at — tracked separately so we can detect
    # stale status (topics changed AFTER user set status)
    # -------------------------------------------------------
    status_updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user   = relationship("User", back_populates="subjects")
    topics = relationship(
        "SubjectTopic",
        back_populates="subject",
        cascade="all, delete-orphan",
        lazy="selectin",                     # async-safe eager load
    )

    def __repr__(self):
        return f"<Subject id={self.id} name={self.name} status={self.status}>"


class SubjectTopic(Base):
    __tablename__ = "subject_topics"

    id         = Column(String(36), primary_key=True)
    subject_id = Column(
        String(36),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id    = Column(
        String(20),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_name = Column(String(100), nullable=False)

    # -------------------------------------------------------
    # target_percentage — auto-calculated in service layer
    # formula: 100 / total_topics_in_subject
    # recalculated every time topics are added or deleted
    # last topic absorbs rounding remainder (e.g. 33.34 vs 33.33)
    # -------------------------------------------------------
    target_percentage = Column(
        Numeric(5, 2),
        nullable=False,
        default=0,
    )

    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at   = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    subject = relationship("Subject", back_populates="topics")
    user    = relationship("User", back_populates="subject_topics")

    def __repr__(self):
        return (
            f"<SubjectTopic id={self.id} "
            f"topic={self.topic_name} "
            f"pct={self.target_percentage} "
            f"done={self.is_completed}>"
        )
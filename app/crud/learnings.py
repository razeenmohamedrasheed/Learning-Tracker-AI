# app/crud/subject.py

import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.learnings import Subject, SubjectTopic


# -------------------------------------------------------
# SUBJECT CRUD
# -------------------------------------------------------

async def create_subject(
    db: AsyncSession,
    user_id: str,
    data: dict,
) -> Subject:
    """Create a new subject."""
    subject = Subject(
        id         = str(uuid.uuid4()),
        user_id    = user_id,
        **data,
    )
    db.add(subject)
    await db.flush()
    await db.refresh(subject)
    return subject


async def get_subject_by_id(
    db: AsyncSession,
    subject_id: str,
    user_id: str,
) -> Subject | None:
    """Get a subject by ID — only if it belongs to the user."""
    result = await db.execute(
        select(Subject).where(
            Subject.id      == subject_id,
            Subject.user_id == user_id,
        )
    )
    return result.scalars().first()


async def get_all_subjects(
    db: AsyncSession,
    user_id: str,
) -> list[Subject]:
    """Get all subjects for a user."""
    result = await db.execute(
        select(Subject)
        .where(Subject.user_id == user_id)
        .order_by(Subject.created_at.desc())
    )
    return result.scalars().all()


async def update_subject(
    db: AsyncSession,
    subject: Subject,
    data: dict,
) -> Subject:
    """Update subject fields."""
    for key, value in data.items():
        if value is not None:
            setattr(subject, key, value)
    subject.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(subject)
    return subject


async def delete_subject(
    db: AsyncSession,
    subject: Subject,
) -> None:
    """Delete a subject and all its topics (cascade)."""
    await db.delete(subject)
    await db.flush()


# -------------------------------------------------------
# TOPIC CRUD
# -------------------------------------------------------

async def create_topic(
    db: AsyncSession,
    subject_id: str,
    user_id: str,
    topic_name: str,
) -> SubjectTopic:
    """
    Create a new topic.
    target_percentage is set AFTER creation via recalculate.
    """
    topic = SubjectTopic(
        id                = str(uuid.uuid4()),
        subject_id        = subject_id,
        user_id           = user_id,
        topic_name        = topic_name,
        target_percentage = Decimal("0.00"),  # will be recalculated right after
    )
    db.add(topic)
    await db.flush()
    return topic


async def get_topics_by_subject(
    db: AsyncSession,
    subject_id: str,
) -> list[SubjectTopic]:
    """Get all topics under a subject."""
    result = await db.execute(
        select(SubjectTopic)
        .where(SubjectTopic.subject_id == subject_id)
        .order_by(SubjectTopic.created_at.asc())
    )
    return result.scalars().all()


async def get_topic_by_id(
    db: AsyncSession,
    topic_id: str,
    user_id: str,
) -> SubjectTopic | None:
    """Get a topic by ID — only if it belongs to the user."""
    result = await db.execute(
        select(SubjectTopic).where(
            SubjectTopic.id      == topic_id,
            SubjectTopic.user_id == user_id,
        )
    )
    return result.scalars().first()


async def recalculate_topic_percentages(
    db: AsyncSession,
    subject_id: str,
) -> None:
    """
    Recalculate target_percentage for ALL topics under a subject.
    Called after adding or deleting a topic.

    Formula: 100 / total_topics
    e.g. 4 topics → 25.00% each
         5 topics → 20.00% each
    """
    topics = await get_topics_by_subject(db, subject_id)
    total  = len(topics)

    if total == 0:
        return

    percentage = Decimal("100.00") / Decimal(str(total))
    percentage = percentage.quantize(Decimal("0.01"))  # round to 2 decimal places

    for topic in topics:
        topic.target_percentage = percentage

    await db.flush()


async def mark_topic_complete(
    db: AsyncSession,
    topic: SubjectTopic,
) -> SubjectTopic:
    """Mark a topic as completed."""
    topic.is_completed = True
    topic.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(topic)
    return topic


async def mark_topic_incomplete(
    db: AsyncSession,
    topic: SubjectTopic,
) -> SubjectTopic:
    """Unmark a topic as completed."""
    topic.is_completed = False
    topic.completed_at = None
    await db.flush()
    await db.refresh(topic)
    return topic


async def delete_topic(
    db: AsyncSession,
    topic: SubjectTopic,
) -> None:
    """Delete a topic then recalculate percentages for remaining topics."""
    subject_id = topic.subject_id
    await db.delete(topic)
    await db.flush()
    await recalculate_topic_percentages(db, subject_id)


# -------------------------------------------------------
# COMPUTED FIELDS
# -------------------------------------------------------

async def get_subject_completion(
    db: AsyncSession,
    subject_id: str,
) -> dict:
    """
    Compute completion stats for a subject.
    Returns total_topics, completed_topics, completion_percentage.
    """
    topics = await get_topics_by_subject(db, subject_id)

    total_topics     = len(topics)
    completed_topics = sum(1 for t in topics if t.is_completed)
    completion_pct   = sum(
        t.target_percentage for t in topics if t.is_completed
    )

    return {
        "total_topics":            total_topics,
        "completed_topics":        completed_topics,
        "completion_percentage":   completion_pct,
    }
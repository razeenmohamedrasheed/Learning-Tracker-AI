import uuid
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

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
        id      = str(uuid.uuid4()),
        user_id = user_id,
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
    """Get all subjects for a user — topics loaded via selectin."""
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
    """
    Update subject fields.
    If status is being changed → record status_updated_at timestamp.
    This timestamp is used to detect stale status later.
    """
    for key, value in data.items():
        if value is not None:
            setattr(subject, key, value)

            # -------------------------------------------------------
            # FIX: track when status was last manually set
            # used in service layer to detect stale status
            # e.g. user set "completed" → then added new topics
            # -------------------------------------------------------
            if key == "status":
                subject.status_updated_at = datetime.now(timezone.utc)

    subject.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(subject)
    return subject


async def delete_subject(
    db: AsyncSession,
    subject: Subject,
) -> None:
    """Delete subject — topics cascade via DB FK."""
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
    Create a single topic.
    target_percentage starts at 0 — recalculate() called right after.
    """
    topic = SubjectTopic(
        id                = str(uuid.uuid4()),
        subject_id        = subject_id,
        user_id           = user_id,
        topic_name        = topic_name,
        target_percentage = Decimal("0.00"),
    )
    db.add(topic)
    await db.flush()
    return topic


async def get_topics_by_subject(
    db: AsyncSession,
    subject_id: str,
) -> list[SubjectTopic]:
    """Get all topics under a subject ordered by creation time."""
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
    Called after: topic added, topic deleted.

    Formula: 100 / total_topics per topic
    Last topic absorbs rounding remainder to ensure sum = exactly 100.

    e.g. 3 topics:
        topic 1 → 33.33
        topic 2 → 33.33
        topic 3 → 33.34  ← absorbs remainder
        total   = 100.00 ✓
    """
    topics = await get_topics_by_subject(db, subject_id)
    total  = len(topics)

    if total == 0:
        return

    per_topic = (Decimal("100.00") / Decimal(total)).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )

    # sum of all but last
    assigned_sum = per_topic * (total - 1)

    # last topic gets the remainder
    remainder = Decimal("100.00") - assigned_sum

    for i, topic in enumerate(topics):
        topic.target_percentage = remainder if i == total - 1 else per_topic

    await db.flush()


async def toggle_topic_completion(
    db: AsyncSession,
    topic: SubjectTopic,
    is_completed: bool,
) -> SubjectTopic:
    """
    Mark topic complete or incomplete.
    Merged mark_topic_complete + mark_topic_incomplete into one fn.
    Matches PATCH /topics/:id payload: { is_completed: bool }
    """
    topic.is_completed = is_completed
    topic.completed_at = datetime.now(timezone.utc) if is_completed else None
    await db.flush()
    await db.refresh(topic)
    return topic


async def delete_topic(
    db: AsyncSession,
    topic: SubjectTopic,
) -> None:
    """Delete topic → recalculate percentages for remaining topics."""
    subject_id = topic.subject_id
    await db.delete(topic)
    await db.flush()
    # recalc after delete so remaining topics fill 100%
    await recalculate_topic_percentages(db, subject_id)


# -------------------------------------------------------
# COMPUTED FIELDS
# -------------------------------------------------------

def compute_subject_completion(topics: list[SubjectTopic]) -> dict:
    """
    Compute completion stats from already-loaded topics list.
    Pure function — no DB call needed.
    Called in service layer after topics are fetched.

    Returns:
        total_topics, completed_topics, completion_percentage, status_stale
    """
    total_topics     = len(topics)
    completed_topics = sum(1 for t in topics if t.is_completed)
    completion_pct   = sum(
        t.target_percentage for t in topics if t.is_completed
    )

    return {
        "total_topics":          total_topics,
        "completed_topics":      completed_topics,
        "completion_percentage": completion_pct,
    }
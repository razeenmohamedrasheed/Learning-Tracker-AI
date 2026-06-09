# app/services/subject_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.crud.learnings import (
    create_subject,
    get_subject_by_id,
    get_all_subjects,
    update_subject,
    delete_subject,
    create_topic,
    get_topics_by_subject,
    get_topic_by_id,
    recalculate_topic_percentages,
    mark_topic_complete,
    mark_topic_incomplete,
    delete_topic,
    get_subject_completion,
)
from app.schemas.learnings import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    TopicCreate,
    TopicResponse,
    TopicCompleteResponse,
)


# -------------------------------------------------------
# OOP CONCEPT: SINGLE RESPONSIBILITY
# SubjectService — only subject-level operations
# TopicService   — only topic-level operations
# -------------------------------------------------------

class SubjectService:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        payload: SubjectCreate,
    ) -> SubjectResponse:
        """Create a new subject for the user."""
        logger.info(f"Creating subject '{payload.name}' for user {user_id}")

        subject = await create_subject(
            db      = db,
            user_id = user_id,
            data    = payload.model_dump(),
        )

        return await SubjectService._build_response(db, subject)

    @staticmethod
    async def get_all(
        db: AsyncSession,
        user_id: str,
    ) -> list[SubjectResponse]:
        """Get all subjects for a user with completion stats."""
        subjects = await get_all_subjects(db, user_id)
        result   = []

        for subject in subjects:
            response = await SubjectService._build_response(db, subject)
            result.append(response)

        return result

    @staticmethod
    async def get_one(
        db: AsyncSession,
        subject_id: str,
        user_id: str,
    ) -> SubjectResponse:
        """Get a single subject with full topic list and completion stats."""
        subject = await get_subject_by_id(db, subject_id, user_id)
        if not subject:
            raise ValueError("Subject not found")

        return await SubjectService._build_response(db, subject)

    @staticmethod
    async def update(
        db: AsyncSession,
        subject_id: str,
        user_id: str,
        payload: SubjectUpdate,
    ) -> SubjectResponse:
        """Update subject fields."""
        subject = await get_subject_by_id(db, subject_id, user_id)
        if not subject:
            raise ValueError("Subject not found")

        updated = await update_subject(
            db      = db,
            subject = subject,
            data    = payload.model_dump(exclude_none=True),
        )

        return await SubjectService._build_response(db, updated)

    @staticmethod
    async def delete(
        db: AsyncSession,
        subject_id: str,
        user_id: str,
    ) -> None:
        """Delete a subject and all its topics."""
        subject = await get_subject_by_id(db, subject_id, user_id)
        if not subject:
            raise ValueError("Subject not found")

        await delete_subject(db, subject)
        logger.info(f"Deleted subject {subject_id}")

    @staticmethod
    async def _build_response(db, subject) -> SubjectResponse:
        """
        Internal helper — builds SubjectResponse with computed fields.
        Prefixed with _ means it's for internal use only (convention).
        """
        topics = await get_topics_by_subject(db, subject.id)
        stats  = await get_subject_completion(db, subject.id)

        topic_responses = [TopicResponse.model_validate(t) for t in topics]

        return SubjectResponse(
            id                     = subject.id,
            user_id                = subject.user_id,
            name                   = subject.name,
            start_date             = subject.start_date,
            end_date               = subject.end_date,
            status                 = subject.status,
            created_at             = subject.created_at,
            updated_at             = subject.updated_at,
            topics                 = topic_responses,
            **stats,
        )


class TopicService:

    @staticmethod
    async def add_topic(
        db: AsyncSession,
        subject_id: str,
        user_id: str,
        payload: TopicCreate,
    ) -> SubjectResponse:
        """
        Add a topic to a subject.
        After adding, recalculate ALL topic percentages.
        Returns updated subject with new percentages.
        """
        # verify subject belongs to user
        subject = await get_subject_by_id(db, subject_id, user_id)
        if not subject:
            raise ValueError("Subject not found")

        logger.info(f"Adding topic '{payload.topic_name}' to subject {subject_id}")

        # create topic
        await create_topic(
            db         = db,
            subject_id = subject_id,
            user_id    = user_id,
            topic_name = payload.topic_name,
        )

        # recalculate ALL topic percentages
        await recalculate_topic_percentages(db, subject_id)

        # return full updated subject
        return await SubjectService._build_response(db, subject)

    @staticmethod
    async def complete_topic(
        db: AsyncSession,
        subject_id: str,
        topic_id: str,
        user_id: str,
    ) -> TopicCompleteResponse:
        """
        Mark a topic as completed.
        Returns updated topic + new subject completion %.
        """
        topic = await get_topic_by_id(db, topic_id, user_id)
        if not topic:
            raise ValueError("Topic not found")

        if topic.is_completed:
            raise ValueError("Topic already completed")

        updated_topic = await mark_topic_complete(db, topic)

        # get updated subject completion %
        stats = await get_subject_completion(db, subject_id)

        return TopicCompleteResponse(
            **TopicResponse.model_validate(updated_topic).model_dump(),
            subject_completion_percentage = stats["completion_percentage"],
        )

    @staticmethod
    async def uncomplete_topic(
        db: AsyncSession,
        topic_id: str,
        user_id: str,
    ) -> TopicResponse:
        """Unmark a topic as completed."""
        topic = await get_topic_by_id(db, topic_id, user_id)
        if not topic:
            raise ValueError("Topic not found")

        updated = await mark_topic_incomplete(db, topic)
        return TopicResponse.model_validate(updated)

    @staticmethod
    async def remove_topic(
        db: AsyncSession,
        subject_id: str,
        topic_id: str,
        user_id: str,
    ) -> SubjectResponse:
        """
        Delete a topic.
        After deletion, recalculate remaining topic percentages.
        Returns updated subject.
        """
        topic = await get_topic_by_id(db, topic_id, user_id)
        if not topic:
            raise ValueError("Topic not found")

        subject = await get_subject_by_id(db, subject_id, user_id)

        await delete_topic(db, topic)
        logger.info(f"Deleted topic {topic_id}, recalculating percentages")

        return await SubjectService._build_response(db, subject)
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
    toggle_topic_completion,
    delete_topic,
    compute_subject_completion,
)
from app.schemas.learnings import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    AddTopicsRequest,
    TopicCreate,
    TopicResponse,
    TopicCompleteResponse,
)


class SubjectService:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        payload: SubjectCreate,
    ) -> SubjectResponse:
        """
        Create subject + optional topics in one shot.
        Steps:
          1. extract topics from payload (exclude from subject data)
          2. create subject row
          3. create topics if any
          4. recalculate percentages
          5. return full response
        """
        logger.info(f"Creating subject '{payload.name}' for user {user_id}")

        # -------------------------------------------------------
        # FIX: exclude 'topics' — Subject model has no topics field
        # topics is a relationship, not a column
        # -------------------------------------------------------
        subject_data = payload.model_dump(exclude={"topics"})

        subject = await create_subject(db=db, user_id=user_id, data=subject_data)

        # create topics if provided at creation time
        if payload.topics:
            for topic in payload.topics:
                await create_topic(
                    db         = db,
                    subject_id = subject.id,
                    user_id    = user_id,
                    topic_name = topic.topic_name,
                )
            await recalculate_topic_percentages(db, subject.id)

        return await SubjectService._build_response(db, subject)

    @staticmethod
    async def get_all(
        db: AsyncSession,
        user_id: str,
    ) -> list[SubjectResponse]:
        """Get all subjects for a user with completion stats."""
        subjects = await get_all_subjects(db, user_id)
        return [
            await SubjectService._build_response(db, s)
            for s in subjects
        ]

    @staticmethod
    async def get_one(
        db: AsyncSession,
        subject_id: str,
        user_id: str,
    ) -> SubjectResponse:
        """Get single subject with topics + completion stats."""
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
        """Update subject fields. Status change recorded via status_updated_at."""
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
        """Delete subject + cascade topics."""
        subject = await get_subject_by_id(db, subject_id, user_id)
        if not subject:
            raise ValueError("Subject not found")

        await delete_subject(db, subject)
        logger.info(f"Deleted subject {subject_id}")

    @staticmethod
    async def _build_response(db: AsyncSession, subject) -> SubjectResponse:
        """
        Internal helper — builds SubjectResponse with computed fields.

        Computed fields (not stored in DB):
          - total_topics
          - completed_topics
          - completion_percentage
          - status_stale

        status_stale = True when:
          subject.status == "completed"
          AND a topic was created AFTER status_updated_at
          → warns user their status may no longer reflect reality
        """
        # fetch topics — single DB call
        topics = await get_topics_by_subject(db, subject.id)

        # FIX: compute_subject_completion is now sync (no DB call)
        stats  = compute_subject_completion(topics)

        # -------------------------------------------------------
        # FIX: compute status_stale
        # check if any topic was added AFTER status was last set
        # only relevant when status = "completed"
        # -------------------------------------------------------
        status_stale = False
        if subject.status == "completed" and subject.status_updated_at:
            status_stale = any(
                t.created_at > subject.status_updated_at
                for t in topics
            )

        topic_responses = [TopicResponse.model_validate(t) for t in topics]

        return SubjectResponse(
            id           = subject.id,
            user_id      = subject.user_id,
            name         = subject.name,
            start_date   = subject.start_date,
            end_date     = subject.end_date,
            status       = subject.status,
            status_stale = status_stale,
            created_at   = subject.created_at,
            updated_at   = subject.updated_at,
            topics       = topic_responses,
            **stats,
        )


class TopicService:

    @staticmethod
    async def add_topics(
        db: AsyncSession,
        subject_id: str,
        user_id: str,
        payload: AddTopicsRequest,
    ) -> SubjectResponse:
        """
        Add one or more topics to existing subject.
        FIX: accepts AddTopicsRequest (list) not single TopicCreate.
        Recalculates all percentages after bulk insert.
        """
        subject = await get_subject_by_id(db, subject_id, user_id)
        if not subject:
            raise ValueError("Subject not found")

        logger.info(
            f"Adding {len(payload.topics)} topic(s) to subject {subject_id}"
        )

        for topic in payload.topics:
            await create_topic(
                db         = db,
                subject_id = subject_id,
                user_id    = user_id,
                topic_name = topic.topic_name,
            )

        # single recalc after all inserts — not inside loop
        await recalculate_topic_percentages(db, subject_id)

        return await SubjectService._build_response(db, subject)

    @staticmethod
    async def toggle_topic(
        db: AsyncSession,
        subject_id: str,
        topic_id: str,
        user_id: str,
        is_completed: bool,
    ) -> TopicCompleteResponse:
        """
        FIX: merged complete + uncomplete into one method.
        Matches PATCH /topics/:id payload: { is_completed: bool }
        Returns topic + updated subject completion %.
        """
        topic = await get_topic_by_id(db, topic_id, user_id)
        if not topic:
            raise ValueError("Topic not found")

        # guard: no-op if already in desired state
        if topic.is_completed == is_completed:
            state = "completed" if is_completed else "incomplete"
            raise ValueError(f"Topic already {state}")

        updated_topic = await toggle_topic_completion(
            db           = db,
            topic        = topic,
            is_completed = is_completed,
        )

        # get fresh completion % after toggle
        topics = await get_topics_by_subject(db, subject_id)
        stats  = compute_subject_completion(topics)

        return TopicCompleteResponse(
            **TopicResponse.model_validate(updated_topic).model_dump(),
            subject_completion_percentage = stats["completion_percentage"],
        )

    @staticmethod
    async def remove_topic(
        db: AsyncSession,
        subject_id: str,
        topic_id: str,
        user_id: str,
    ) -> SubjectResponse:
        """
        Delete topic → recalc percentages → return updated subject.
        delete_topic in crud already calls recalculate internally.
        """
        topic = await get_topic_by_id(db, topic_id, user_id)
        if not topic:
            raise ValueError("Topic not found")

        subject = await get_subject_by_id(db, subject_id, user_id)
        if not subject:
            raise ValueError("Subject not found")

        await delete_topic(db, topic)
        logger.info(f"Deleted topic {topic_id} from subject {subject_id}")

        return await SubjectService._build_response(db, subject)
# app/api/routers/v1/subject.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.db import get_db
from app.core.dependencies import get_current_user
from app.models.registration import User
from app.schemas.learnings import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    TopicCreate,
    TopicResponse,
    TopicCompleteResponse,
)
from app.api.controllers.v1.learnings import SubjectService, TopicService


router = APIRouter()


# -------------------------------------------------------
# SUBJECT ROUTES
# -------------------------------------------------------

@router.post(
    "/",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subject",
)
async def create_subject(
    payload: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await SubjectService.create(
            db      = db,
            user_id = current_user.user_id,
            payload = payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create subject error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subject")


@router.get(
    "/",
    response_model=list[SubjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all subjects",
)
async def get_all_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await SubjectService.get_all(db=db, user_id=current_user.user_id)


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get subject detail with topics",
)
async def get_subject(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await SubjectService.get_one(
            db         = db,
            subject_id = subject_id,
            user_id    = current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update subject",
)
async def update_subject(
    subject_id: str,
    payload: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await SubjectService.update(
            db         = db,
            subject_id = subject_id,
            user_id    = current_user.user_id,
            payload    = payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subject and all its topics",
)
async def delete_subject(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await SubjectService.delete(
            db         = db,
            subject_id = subject_id,
            user_id    = current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -------------------------------------------------------
# TOPIC ROUTES
# -------------------------------------------------------

@router.post(
    "/{subject_id}/topics",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a topic to a subject",
)
async def add_topic(
    subject_id: str,
    payload: TopicCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await TopicService.add_topic(
            db         = db,
            subject_id = subject_id,
            user_id    = current_user.user_id,
            payload    = payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Add topic error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add topic")


@router.patch(
    "/{subject_id}/topics/{topic_id}/complete",
    response_model=TopicCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a topic as completed",
)
async def complete_topic(
    subject_id: str,
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await TopicService.complete_topic(
            db         = db,
            subject_id = subject_id,
            topic_id   = topic_id,
            user_id    = current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{subject_id}/topics/{topic_id}/uncomplete",
    response_model=TopicResponse,
    status_code=status.HTTP_200_OK,
    summary="Unmark a topic as completed",
)
async def uncomplete_topic(
    subject_id: str,
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await TopicService.uncomplete_topic(
            db       = db,
            topic_id = topic_id,
            user_id  = current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{subject_id}/topics/{topic_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a topic and recalculate percentages",
)
async def delete_topic(
    subject_id: str,
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await TopicService.remove_topic(
            db         = db,
            subject_id = subject_id,
            topic_id   = topic_id,
            user_id    = current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
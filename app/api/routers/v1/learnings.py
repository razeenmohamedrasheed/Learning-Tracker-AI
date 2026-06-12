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
    AddTopicsRequest,
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
    summary="Create a new subject with optional topics",
    responses={
        201: {"description": "Subject created successfully"},
        400: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Create subject error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create subject")


@router.get(
    "/",
    response_model=list[SubjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all subjects for current user",
)
async def get_all_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await SubjectService.get_all(
            db      = db,
            user_id = current_user.user_id,
        )
    except Exception as e:
        logger.error(f"Get all subjects error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch subjects")


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a subject with all topics and completion stats",
    responses={
        404: {"description": "Subject not found"},
    },
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Get subject error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch subject")


@router.patch(
    "/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update subject name, dates, or status",
    responses={
        404: {"description": "Subject not found"},
    },
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Update subject error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update subject")


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subject and all its topics",
    responses={
        404: {"description": "Subject not found"},
    },
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Delete subject error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete subject")


# -------------------------------------------------------
# TOPIC ROUTES
# -------------------------------------------------------

@router.post(
    "/{subject_id}/topics",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add one or more topics to a subject",
    responses={
        404: {"description": "Subject not found"},
        500: {"description": "Internal server error"},
    },
)
async def add_topics(
    subject_id: str,
    payload: AddTopicsRequest,          # FIX: was TopicCreate (single) → now AddTopicsRequest (list)
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await TopicService.add_topics(
            db         = db,
            subject_id = subject_id,
            user_id    = current_user.user_id,
            payload    = payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Add topics error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add topics")


@router.patch(
    "/{subject_id}/topics/{topic_id}",
    response_model=TopicCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle topic completion status",
    responses={
        400: {"description": "Topic already in desired state"},
        404: {"description": "Topic not found"},
    },
)
async def toggle_topic(
    subject_id: str,
    topic_id: str,
    is_completed: bool,                 # FIX: query param — simple bool, no request body needed
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle topic completion.
    Pass ?is_completed=true to mark done.
    Pass ?is_completed=false to unmark.
    """
    try:
        return await TopicService.toggle_topic(
            db           = db,
            subject_id   = subject_id,
            topic_id     = topic_id,
            user_id      = current_user.user_id,
            is_completed = is_completed,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Toggle topic error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to toggle topic")


@router.delete(
    "/{subject_id}/topics/{topic_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a topic and recalculate percentages",
    responses={
        404: {"description": "Topic or subject not found"},
    },
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Delete topic error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete topic")
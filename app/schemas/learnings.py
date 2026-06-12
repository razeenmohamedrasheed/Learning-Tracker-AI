from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


# -------------------------------------------------------
# TOPIC SCHEMAS
# defined first — SubjectCreate + SubjectResponse ref them
# -------------------------------------------------------


class TopicCreate(BaseModel):
    """Schema for adding a new topic."""

    topic_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["OOPs"],
    )


class TopicUpdate(BaseModel):
    """Schema for toggling topic completion status."""

    is_completed: bool


class TopicResponse(BaseModel):
    """Schema for returning topic data."""

    id:                str
    subject_id:        str
    user_id:           str
    topic_name:        str
    target_percentage: Decimal   # auto-calculated — e.g. 25.00
    is_completed:      bool
    completed_at:      Optional[datetime] = None
    created_at:        datetime

    model_config = {"from_attributes": True}


class TopicCompleteResponse(TopicResponse):
    """
    Returned after marking a topic complete/incomplete.
    Includes updated subject completion percentage.
    """

    subject_completion_percentage: Decimal


# -------------------------------------------------------
# SUBJECT SCHEMAS
# -------------------------------------------------------


class SubjectBase(BaseModel):
    """Common fields shared across subject schemas."""

    name:       str  = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Python"],
    )
    start_date: date = Field(..., examples=["2026-06-01"])
    end_date:   date = Field(..., examples=["2026-08-31"])

    @model_validator(mode="after")
    def validate_dates(self) -> "SubjectBase":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SubjectCreate(SubjectBase):
    """
    Schema for creating a new subject.
    Topics are optional at creation — can be added later via
    POST /subjects/:id/topics
    """

    topics: List[TopicCreate] = Field(
        default_factory=list,
        description="Optional list of topics to add at creation time",
    )


class AddTopicsRequest(BaseModel):
    """
    Schema for adding topics to an existing subject.
    Used by: POST /subjects/:id/topics
    """

    topics: List[TopicCreate] = Field(
        ...,
        min_length=1,
        description="One or more topics to add to the subject",
    )


class SubjectUpdate(BaseModel):
    """
    Schema for updating a subject.
    All fields optional — send only what needs to change.
    Status must be set manually by user.
    """

    name:       Optional[str]  = Field(None, min_length=2, max_length=100)
    start_date: Optional[date] = None
    end_date:   Optional[date] = None
    status:     Optional[str]  = Field(
        None,
        pattern="^(in_progress|completed|failed|partially_completed)$",
        description="Manually set by user based on progress",
    )

    @model_validator(mode="after")
    def validate_dates_if_both_present(self) -> "SubjectUpdate":
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be after start_date")
        return self


class SubjectResponse(SubjectBase):
    """
    Schema for returning subject data.
    Computed fields: total_topics, completed_topics,
    completion_percentage, status_stale.
    """

    id:         str
    user_id:    str
    status:     str

    # --- computed fields (set in service layer, not stored in DB) ---
    total_topics:             int     = 0
    completed_topics:         int     = 0
    completion_percentage:    Decimal = Decimal("0.00")

    # True when topics were added/removed after status was set to
    # "completed" — warns user their status may be stale
    status_stale:             bool    = False

    created_at: datetime
    updated_at: datetime

    topics: List[TopicResponse] = []

    model_config = {"from_attributes": True}
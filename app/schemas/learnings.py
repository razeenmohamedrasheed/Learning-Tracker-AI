from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

# -------------------------------------------------------
# SUBJECT SCHEMAS
# -------------------------------------------------------

class SubjectBase(BaseModel):
    """Common fields for subject schemas."""
    name:       str  = Field(..., min_length=2, max_length=100, examples=["Python"])
    start_date: date = Field(..., examples=["2026-06-01"])
    end_date:   date = Field(..., examples=["2026-08-31"])

    # -------------------------------------------------------
    # OOP CONCEPT: METHOD inside class — validation
    # -------------------------------------------------------
    @model_validator(mode="after")
    def validate_dates(self) -> "SubjectBase":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SubjectCreate(SubjectBase):
    """Schema for creating a new subject — only needs base fields."""
    pass


class SubjectUpdate(BaseModel):
    """Schema for updating subject — all fields optional."""
    name:       Optional[str]  = Field(None, min_length=2, max_length=100)
    start_date: Optional[date] = None
    end_date:   Optional[date] = None
    status:     Optional[str]  = Field(None, pattern="^(active|completed|paused)$")


class SubjectResponse(SubjectBase):
    """Schema for returning subject data — includes computed fields."""
    id:                 str
    user_id:            str
    status:             str
    total_topics:       int       = 0       # computed — count of topics
    completed_topics:   int       = 0       # computed — count of completed topics
    completion_percentage: Decimal = Decimal("0.00")  # computed — total %
    created_at:         datetime
    updated_at:         datetime
    topics:             List["TopicResponse"] = []    # nested topics

    model_config = {"from_attributes": True}


# -------------------------------------------------------
# TOPIC SCHEMAS
# -------------------------------------------------------

class TopicBase(BaseModel):
    """Common fields for topic schemas."""
    topic_name: str = Field(..., min_length=2, max_length=100, examples=["OOPs"])


class TopicCreate(TopicBase):
    """Schema for adding a new topic to a subject."""
    pass


class TopicResponse(TopicBase):
    """Schema for returning topic data."""
    id:                str
    subject_id:        str
    user_id:           str
    target_percentage: Decimal    # auto calculated — e.g. 25.00
    is_completed:      bool
    completed_at:      Optional[datetime] = None
    created_at:        datetime

    model_config = {"from_attributes": True}


class TopicCompleteResponse(TopicResponse):
    """Returned after marking a topic complete — includes updated subject %."""
    subject_completion_percentage: Decimal  # updated subject total %
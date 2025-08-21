from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    title: str
    description: str
    completed: bool = False

    class Config:
        # Makes your model JSON-serializable with .model_dump_json()
        populate_by_name = True
        frozen = True  # makes it immutable (optional, nice for safety)


class RegularTask(Task):
    due_date: datetime = Field(..., description="Deadline for the task")


class RecurringTask(Task):
    interval: str = Field(
        ..., description="Recurrence interval, e.g. 'daily', 'weekly'"
    )

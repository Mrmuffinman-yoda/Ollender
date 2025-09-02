from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Event(BaseModel):
    title: str = Field(..., description="Title of the event")
    description: str | None = Field(None, description="Description of the event")
    start_time: Optional[datetime] = Field(
        None, description="Start time of the event in ISO 8601 format"
    )
    end_time: Optional[datetime] = Field(
        None, description="End time of the event in ISO 8601 format"
    )
    additional_info: str | None = Field(None, description="Additional information about the event")
    reasoning: Optional[str] = None

    def __str__(self):
        start = self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else None
        end = self.end_time.strftime("%Y-%m-%d %H:%M") if self.end_time else None
        return f"Event(title={self.title}, description={self.description}, start_time={start}, end_time={end})"

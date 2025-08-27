from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    """A minimalist model for creating a new Google Task."""

    title: str = Field(
        ..., description="The title of the task. This is the only required field."
    )
    notes: Optional[str] = Field(
        None, description="A detailed description of the task."
    )
    due: Optional[datetime] = Field(
        None, description="The due date for the task, in YYYY-MM-DD format."
    )


class TaskFactory(BaseModel):
    """Factory for creating Task instances."""

    @staticmethod
    def create_task(
        title: str, notes: Optional[str] = None, due: Optional[datetime] = None
    ) -> Task:
        """Create a new Task instance.

        Args:
            title (str): The title of the task.
            notes (Optional[str]): Optional notes for the task.
            due (Optional[datetime]): Optional due date for the task.

        Returns:
            Task: A new Task instance.
        """
        return Task(title=title, notes=notes, due=due)

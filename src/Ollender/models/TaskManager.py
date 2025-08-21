from datetime import datetime
from typing import Union

from loguru import logger
from multipledispatch import dispatch
from pydantic import ValidationError
import json
from models.GCalender import GoogleCalendarConnector
from .OllamaConnector import OllamaConnector
from data_models.task import Task, RegularTask, RecurringTask


class TaskManager:
    def __init__(self) -> None:
        self.gcal = GoogleCalendarConnector()
        self.ollama = OllamaConnector(
            f"""
           You are a task manager assistant. 
          You will only respond with a **valid JSON object** and nothing else. 
          Do not include explanations or extra text.

          There are two types of tasks you can create:

          1. RegularTask
          {{
            "task_title": string,
            "task_description": string,
            "completed": boolean,
            "time_to_complete": ISO8601 datetime string (e.g. "2025-08-21T10:00:00Z")
          }}

          2. RecurringTask
          {{
            "task_title": string,
            "task_description": string,
            "completed": boolean,
            "interval": string (one of: "daily", "weekly", "monthly", "yearly")
          }}

          Rules:
          - Always choose the correct type based on the request.
          - For RegularTask, always include a realistic "time_to_complete" based on the current date and time: {datetime.now().isoformat()}.
          - For RecurringTask, always include a valid "interval".
          - Ensure the JSON can be parsed without errors.
            """,
            "llama3.1:8b",
            "gpt-oss:20b",
        )
        logger.info("TaskManager initialized")

    @dispatch(RegularTask)
    def task_prompt(self, task: RegularTask) -> str:
        return f"Assign a time and date for the task: {task.title} - {task.description}"

    @dispatch(RecurringTask)
    def task_prompt(self, task: RecurringTask) -> str:
        return f"Assign scheduling for the recurring task: {task.title} - {task.description}, recurring every {task.interval}"

    def json_to_task(self, json_data: dict) -> Union[RegularTask, RecurringTask]:
        """
        Convert JSON data from LLM into a Pydantic Task model.
        """
        try:
            if "interval" in json_data:
                return RecurringTask(
                    title=json_data["task_title"],
                    description=json_data["task_description"],
                    interval=json_data["interval"],
                    completed=json_data.get("completed", False),
                )
            else:
                return RegularTask(
                    title=json_data["task_title"],
                    description=json_data["task_description"],
                    due_date=datetime.fromisoformat(json_data["time_to_complete"]),
                    completed=json_data.get("completed", False),
                )
        except ValidationError as e:
            logger.error(f"Validation error while creating task: {e}")
            raise

    def create_task(self, task: Union[RegularTask, RecurringTask]) -> None:
        logger.info(f"Creating task: {task.title} - {task.description}")

        # Ask LLM for scheduling / validation
        response = self.ollama.ask(self.task_prompt(task), use_strong_model=False)

        # Convert JSON response → Task object
        new_task = self.json_to_task(json.loads(response))

        # Add to Google Calendar if RegularTask
        if isinstance(new_task, RegularTask):
            self.gcal.add_event(new_task.title, new_task.description, new_task.due_date)

        logger.info(f"Task created: {new_task.model_dump_json(indent=2)}")

    def get_tasks(self) -> list[Task]:
        # TODO: implement task retrieval logic (db, in-memory, etc.)
        return []

    def delete_task(self, task_id: str) -> None:
        # TODO: implement delete logic (db + gcal)
        logger.info(f"Deleting task with id: {task_id}")


if __name__ == "__main__":
    logger.info("Test   TaskManager")

    task_manager = TaskManager()

    regular_task = RegularTask(
        title="Wash clothes",
        description="Weekly task for washing clothes",
        due_date=datetime.now(),
    )
    recurring_task = RecurringTask(
        title="Vacuum the floor",
        description="Self-explanatory",
        interval="weekly",
    )

    # Create tasks using the TaskManager
    task_manager.create_task(regular_task)
    task_manager.create_task(recurring_task)

    # Retrieve and log tasks
    tasks = task_manager.get_tasks()
    for task in tasks:
        logger.info(f"Retrieved task: {task.model_dump_json(indent=2)}")

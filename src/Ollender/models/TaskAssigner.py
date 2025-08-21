from OllamaConnector import OllamaConnector
from datetime import datetime
import pydantic


class Task(pydantic.BaseModel):
    task_title: str
    task_description: str
    time_to_complete: str  # ISO 8601 format


class TaskAssigner:
    def __init__(self, task_list):
        self.ordered_tasks: list[Task] = []
        self.standard_tasks: list[Task] = []

        with open("data/standard_tasks.txt", "r") as file:
            self.standard_tasks = [line.strip() for line in file if line.strip()]
        self.standard_tasks += task_list

        self.LLMAdapter: OllamaConnector = OllamaConnector(
            system_prompt=f"""
                You are a helpful assistant. Your job is to take tasks and assign them a time and date to complete them.
                Return the task title, task description, time and date to complete the task in a JSON format.
                Example:
                {{
                    "task_title": "Buy groceries",
                    "task_description": "Buy milk, eggs, and bread",
                    "time_to_complete": "2023-10-01T10:00:00Z"
                }}
                The current date and time is {datetime.now().isoformat()}.
            """
        )

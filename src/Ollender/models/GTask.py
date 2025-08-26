from __future__ import annotations
import os
from typing import Dict

from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger


class GTask:
    """
    Connector for the Google Tasks API.
    Handles authentication and task creation.
    """

    SCOPES = ["https://www.googleapis.com/auth/tasks"]

    def __init__(
        self, credentials_file: str = "credentials.json", token_file: str = "token.json"
    ):
        """
        Initializes the connector.

        Args:
            credentials_file (str): Path to the Google Cloud credentials file.
            token_file (str): Path to store the user's token.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds: Credentials | None = None
        self.service = None
        self.authenticate()

        logger.info("Google Tasks Connector initialized")

    def authenticate(self) -> None:
        """Authenticate user and initialize the Google Tasks service."""
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(
                self.token_file, self.SCOPES
            )

        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    logger.error(
                        f"Credentials file not found at: {self.credentials_file}"
                    )
                    raise FileNotFoundError(
                        f"Error: The credentials file '{self.credentials_file}' was not found."
                    )

                logger.info(
                    "No valid credentials found, starting authentication flow..."
                )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                # Set open_browser=False to match the calendar class style
                self.creds = flow.run_local_server(port=0, open_browser=False)

            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(self.creds.to_json())
                logger.success(f"Credentials saved to {self.token_file}")

        self.service = build("tasks", "v1", credentials=self.creds)
        logger.success("Google Tasks service created successfully.")

    def get_tasks(
        self,
        tasklist_id: str = "@default",
        show_completed: bool = True,
        show_hidden: bool = False,
        max_results: int = 100,
    ) -> list[Dict] | None:
        """
        Retrieve tasks from the specified task list.

        Args:
            tasklist_id (str): The ID of the task list. Defaults to the primary list.
            show_completed (bool): Whether to include completed tasks. Defaults to True.
            show_hidden (bool): Whether to include hidden tasks. Defaults to False.
            max_results (int): Maximum number of tasks to retrieve. Defaults to 100.

        Returns:
            list[Dict] | None: A list of task objects, or None if an error occurred.
        """
        try:
            results = (
                self.service.tasks()
                .list(
                    tasklist=tasklist_id,
                    showCompleted=show_completed,
                    showHidden=show_hidden,
                    maxResults=max_results,
                )
                .execute()
            )
            tasks = results.get("items", [])
            logger.success(
                f"Retrieved {len(tasks)} tasks from tasklist '{tasklist_id}'."
            )
            return tasks
        except HttpError as err:
            logger.error(f"An API error occurred while retrieving tasks: {err}")
            return None

    def create_task(
        self,
        title: str,
        notes: str | None = None,
        due: datetime | None = None,
        tasklist_id: str = "@default",
    ) -> Dict | None:
        """
        Create a new task in the specified task list.

        Args:
            title (str): The title of the task.
            notes (str | None): Optional notes for the task.
            tasklist_id (str): The ID of the task list. Defaults to the primary list.

        Returns:
            Dict | None: The created task object, or None if an error occurred.
        """
        try:
            task_body = {"title": title, "notes": notes if notes else ""}
            if due:
                # Google Tasks expects RFC3339 timestamp (ISO 8601, UTC)
                # If due is naive, treat as local and convert to UTC
                if due.tzinfo is None:
                    from datetime import timezone

                    due = due.replace(tzinfo=timezone.utc)
                task_body["due"] = due.isoformat().replace("+00:00", "Z")
            created_task = (
                self.service.tasks()
                .insert(tasklist=tasklist_id, body=task_body)
                .execute()
            )
            logger.success(
                f"Task created: '{created_task['title']}' (ID: {created_task['id']})"
            )
            return created_task
        except HttpError as err:
            logger.error(f"An API error occurred while creating a task: {err}")
            return None


# --- Example Usage ---
if __name__ == "__main__":
    try:
        # Initialize the connector
        # Make sure to point to the correct path for your credentials file
        tasks_connector = GTask(credentials_file="credentials.json")

        # Create a couple of tasks

        tasks_connector.create_task(
            title="Buy a new fragrance",
            notes="Check out the new Lattafa Pride releases.",
            due=datetime.now() + timedelta(days=7),  # Example due date as datetime
        )
        tasks_connector.create_task(title="Submit the weekly report")

        # get task list

        tasks = tasks_connector.get_tasks()
        if tasks:
            for task in tasks:
                logger.info(f"Task: {task['title']} (ID: {task['id']})")
        else:
            logger.warning("No tasks found.")

    except FileNotFoundError as e:
        logger.error(e)
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main script: {e}")

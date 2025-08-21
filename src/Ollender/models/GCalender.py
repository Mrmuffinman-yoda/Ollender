from __future__ import annotations
import datetime
import os
from typing import List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger
from multipledispatch import dispatch


class GoogleCalendarConnector:
    """
    Connector for Google Calendar API.
    Handles authentication, fetching, and creating events.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds: Credentials | None = None
        self.service = None
        self.authenticate()

        logger.info("Google Calendar Connector initialized")

    def authenticate(self) -> None:
        """Authenticate user and initialize the Google Calendar service."""
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0, open_browser=False)

            with open(self.token_file, "w") as token:
                token.write(self.creds.to_json())

        self.service = build("calendar", "v3", credentials=self.creds)

    def list_events(self, calendar_id: str = "primary", max_results: int = 10) -> List[Dict]:
        """Return upcoming events from the specified calendar."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = (
            self.service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    def create_event(
        self,
        summary: str,
        start: datetime.datetime,
        end: datetime.datetime,
        calendar_id: str = "primary",
    ) -> Dict:
        """Create a new calendar event."""
        event = {
            "summary": summary,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }
        return self.service.events().insert(calendarId=calendar_id, body=event).execute()


if __name__ == "__main__":
    connector = GoogleCalendarConnector("src/models/credentials.json")
    events = connector.list_events(max_results=5)
    for e in events:
        print(e.get("summary"), e.get("start"))

    event = connector.create_event(
        summary="Python Calendar Event",
        start=datetime.datetime.now() + datetime.timedelta(hours=1),
        end=datetime.datetime.now() + datetime.timedelta(hours=2),
    )

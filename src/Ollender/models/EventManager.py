import json
from datetime import datetime
from typing import List
from loguru import logger
from models.GCalender import GoogleCalendarConnector
from models.OllamaConnector import OllamaConnector
from data_models.Event import Event


class EventManager:
    """
    Manages event creation by intelligently scheduling them using an LLM
    to find available time slots.
    """
    def __init__(self) -> None:
        self.calendar = GoogleCalendarConnector()
        self.ollama = OllamaConnector(
            system_prompt="You are a helpful scheduling assistant. Your only output is a single, valid JSON object.",
            model="deepseek-r1:14b",
        )

    def _build_scheduling_prompt(self, event: Event, upcoming_events: List[Event]) -> str:
        """
        Builds a concise, task-focused prompt for the LLM.
        This version removes verbose formatting instructions and examples.
        """
        simplified_events_list = []
        for ev in upcoming_events:
            start_str = ev.start_time.isoformat() if hasattr(ev, 'start_time') and ev.start_time else "N/A"
            end_str = ev.end_time.isoformat() if hasattr(ev, 'end_time') and ev.end_time else "N/A"
            simplified_events_list.append(f"- Title: {ev.title}, Start: {start_str}, End: {end_str}")

        simplified_events_str = "\n".join(simplified_events_list) if simplified_events_list else "No upcoming events."

        prompt = f"""
          Your task is to schedule the following event. Find a suitable time slot based on the given constraints and the user's existing calendar.

          ### New Event
          - **Title:** {event.title}
          - **Description:** {event.description}

          ### Constraints
          - **User Instructions:** "{event.additional_info if event.additional_info else 'No specific instructions provided.'}"
          - **Conflicts:** Must not overlap with any existing events.
          - **Buffer:** Must have a 15-minute buffer before and after existing events.
          - **Current Time:** {datetime.now().isoformat()}

          ### Existing Calendar Events
          {simplified_events_str}

          ### Your Response
          Respond with a single JSON object with keys: "title", "description", "start_time", and "end_time".
        """
        return prompt

    def create_event(self, event: Event) -> None:
        """
        Creates a new event in Google Calendar by using the LLM to find and
        assign a suitable start and end time.
        """
        upcoming_events = self.calendar.list_events(max_results=30)
        prompt = self._build_scheduling_prompt(event, upcoming_events)
        logger.debug(f"Final prompt sent to LLM:\n{prompt}")

        response_str = self.ollama.ask(prompt)
        logger.info(f"LLM response: {response_str}")

        try:
            response_data = json.loads(response_str)
            event.title = f"[Ollender] {response_data['title']}"
            event.description = response_data['description']
            event.start_time = datetime.fromisoformat(response_data["start_time"])
            event.end_time = datetime.fromisoformat(response_data["end_time"])
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response due to: {e}. Response was: '{response_str}'")
            return

        self.calendar.create_event(event)
        logger.success(f"Event '{event.title}' created successfully.")
        logger.debug(f"Final event details: {event.model_dump()}")


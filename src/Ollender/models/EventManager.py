import json
from datetime import datetime
from typing import List
from loguru import logger
from models.GCalender import GoogleCalendarConnector
from models.OllamaConnector import OllamaConnector
from data_models.Event import Event
from models.MultiStepReasoner import MultiStepReasoner


class EventManager:
    """
    Manages event creation by intelligently scheduling them using an LLM
    to find available time slots.
    """

    def __init__(self, multi=False) -> None:
        self.calendar = GoogleCalendarConnector()
        self.ollama = OllamaConnector(
            system_prompt="You are a helpful scheduling assistant. Your only output is a single, valid JSON object.",
            model="hf.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF:Q3_K_M",
        )
        self.multi = multi  # Boolean to use multi-step reasoning instead

    def _build_upcoming_events_str(self, upcoming_events: List[Event]) -> str:
        events_list = []
        for ev in upcoming_events:
            start_str = (
                ev.start_time.isoformat() if hasattr(ev, "start_time") and ev.start_time else "N/A"
            )
            end_str = ev.end_time.isoformat() if hasattr(ev, "end_time") and ev.end_time else "N/A"
            events_list.append(f"- Title: {ev.title}, Start: {start_str}, End: {end_str}")

        return "\n".join(events_list) if events_list else "No upcoming events."

    def _build_scheduling_prompt(self, event: Event, upcoming_events: List[Event]) -> str:
        """
        Builds a concise, task-focused prompt for the LLM.
        This version removes verbose formatting instructions and examples.
        """

        simplified_events_str = self._build_upcoming_events_str(upcoming_events)
        prompt = f"""
          You are an expert AI scheduling assistant. Your task is to find the earliest suitable time for a new event by following a precise algorithm.

        ---ALGORITHM---
        1.  **Identify Constraints:** First, parse the "User Instructions" to determine the target day(s) and time window (e.g., "Thursday next week between 9am and 5pm").
        2.  **Create "Busy Blocks":** Process the "Existing Calendar Events". For each event on the target day, create a "busy block" of time that starts 15 minutes *before* the event's start time and ends 15 minutes *after* its end time. List these final busy blocks.
        3.  **Find the Earliest Slot:** Starting from the beginning of the allowed time window (e.g., 9am), search forward for the first available time slot that has a duration of at least 20 minutes and does not overlap with any of the "busy blocks".
        4.  **Conclude:** Once you find a valid slot, state the chosen start and end time. Your reasoning is complete.

        ---YOUR TASK---
        Analyze the details below and generate your response by precisely following the algorithm.

        ### New Event
        - **Title:** {event.title}
        - **Description:** {event.description}

        ### Constraints
        - **User Instructions:** "{event.additional_info if event.additional_info else 'No specific instructions provided.'}"
        - **Conflicts:** Must not overlap with any existing events.
        - **Buffer:** Must have a 15-minute buffer before and after existing events.
        - **Current Time:** {datetime.now().isoformat()}
        - **Current Day:** {datetime.now().strftime('%A')}

        ### Existing Calendar Events
        {simplified_events_str}

        ---YOUR RESPONSE---
        <thinking>
        *Execute the 4 steps of the algorithm here*
        </thinking>
        <json>
        {{
        "title": "Team Meeting",
        "description": "Discuss project updates and next steps.",
        "start_time": "...",
        "end_time": "...",
        "error": null
        }}
        </json>
        """
        return prompt

    def find_json(self, response_str: str) -> str | None:
        return response_str[response_str.find("{") : response_str.rfind("}") + 1]

    def create_event(self, event: Event) -> None:
        """
        Creates a new event in Google Calendar by using the LLM to find and
        assign a suitable start and end time.
        """
        event_maxresults = 25
        upcoming_events = self.calendar.list_events(max_results=event_maxresults)
        if self.multi:
            msr = MultiStepReasoner(self.ollama, event, upcoming_events)
            msr.run()
            return

        prompt = self._build_scheduling_prompt(event, upcoming_events)
        logger.debug(f"Final prompt sent to LLM:\n{prompt}")

        response_str = self.find_json(self.ollama.ask(prompt))
        logger.info(f"LLM response: {response_str}")

        try:
            response_data = json.loads(response_str)
            event.title = f"[Ollender] {response_data['title']}"
            event.description = response_data["description"]
            event.start_time = datetime.fromisoformat(response_data["start_time"])
            event.end_time = datetime.fromisoformat(response_data["end_time"])
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(
                f"Failed to parse LLM response due to: {e}. Response was: '{response_str}'"
            )
            return

        self.calendar.create_event(event)
        logger.success(f"Event '{event.title}' created successfully.")
        logger.debug(f"Final event details: {event.model_dump()}")

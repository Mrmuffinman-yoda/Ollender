from models.OllamaConnector import OllamaConnector
from data_models.Event import Event
from datetime import datetime
from typing import List
import json
from loguru import logger
from pydantic import BaseModel, ValidationError


class LLMResponse(BaseModel):
    event_data: List[Event]
    error: str | None


class MultiStepReasoner:
    def __init__(
        self,
        ollama: OllamaConnector,
        event: Event,
        upcoming_events: List[Event],
    ):
        self.ollama: OllamaConnector = ollama
        self.event: Event = event
        self.upcoming_events: List[Event] = upcoming_events  # Corrected type hint
        self.start_time: datetime | None = None

    def event_prompt(self):
        prompt = f"""
            - **Title:** {self.event.title}
            - **Description:** {self.event.description}
        """
        return prompt

    def json_shape_prompt(self):
        prompt = f"""
        {{
            "event_data": [
                {{
                    "title": "{self.event.title}",
                    "description": "{self.event.description}",
                    "start_time": "YYYY-MM-DDTHH:MM:SS",
                    "end_time": "YYYY-MM-DDTHH:MM:SS",
                    "reasoning": "This is the earliest available slot on Monday morning that respects all buffer and conflict constraints."
                }},
            "error":"Any errors encountered"
          ]
        }}
        """
        return prompt

    def general_constraints_prompt(self):
        prompt = f"""
        - **User Instructions:** "{self.event.additional_info or 'No specific instructions provided.'}"
        - **Conflicts:** Must not overlap with any events in the user's existing calendar.
        - **Buffer:** A **15-minute buffer** is required both before and after each existing event.
        - **Working Hours:** Only suggest slots between **09:00 and 18:00 on weekdays** (Monday-Friday).
        - **Time Context:** All suggestions must be in the future. The current time is **{self.start_time.isoformat()} (BST)**.

        """
        return prompt

    def _build_upcoming_events_str(self) -> str:
        simplified_events = []
        for e in self.upcoming_events:
            simplified_events.append(
                f"- {e.title} from {e.start_time.isoformat() if e.start_time else 'N/A'} to {e.end_time.isoformat() if e.end_time else 'N/A'}"
            )
        return (
            "\n".join(simplified_events) if simplified_events else "No upcoming events."
        )

    def _build_initial_prompt(self) -> str:
        """Generates the first prompt to find candidate slots."""

        simplified_events_str = self._build_upcoming_events_str()
        return f"""
        You are a highly intelligent scheduling AI. Your goal is to analyze the user's new event, their existing calendar, and a set of constraints to propose 5 suitable, conflict-free time slots.
        
        ### New Event to Schedule
        {self.event_prompt()}

        ### Scheduling Constraints
        {self.general_constraints_prompt()}

        ### Existing Calendar Events
        {simplified_events_str}

        ### Output Format
        Return your response as a valid JSON array of 5 event objects. Each object must include a "reasoning" field explaining why the slot is suitable.

        {self.json_shape_prompt()}
        """

    def _validation_prompt(self, proposed_slots: List[Event]) -> str:
        """Validate the proposed time slots against all constraints and user preferences."""

        # Convert Event objects to dictionaries for JSON serialization
        slots_dicts = []
        for slot in proposed_slots:
            # Convert datetime objects to ISO format strings for JSON serialization
            slot_dict = slot.model_dump()
            if slot.start_time:
                slot_dict["start_time"] = slot.start_time.isoformat()
            if slot.end_time:
                slot_dict["end_time"] = slot.end_time.isoformat()
            slots_dicts.append(slot_dict)

        simplified_events_str = self._build_upcoming_events_str()
        prompt = f"""
          You are an expert in scheduling and validating calendar events. Your task is to validate a list of proposed time slots for a new event against a set of constraints and user preferences.
          return only the valid options in a json array. Remove at least 2 of the options.

          ### Proposed Time Slots
          {json.dumps(slots_dicts, indent=2)}

          ### Existing Calendar Events
          {simplified_events_str}

          ### Constraints
          {self.general_constraints_prompt()}


          ### User Event
          {self.event_prompt()}

          ### Current time and day
            - **Current Time:** {datetime.now().isoformat()}
            - **Current Day:** {datetime.now().strftime('%A')}

          ---YOUR RESPONSE---
          {self.json_shape_prompt()}
          """
        return prompt

    def _selection_step(self, proposed_slots: List[Event]) -> str:
        """Select the most suitable time slot from the proposed options based on user preferences and constraints."""

        # Convert Event objects to dictionaries for JSON serialization
        slots_dicts = []
        for slot in proposed_slots:
            # Convert datetime objects to ISO format strings for JSON serialization
            slot_dict = slot.model_dump()
            if slot.start_time:
                slot_dict["start_time"] = slot.start_time.isoformat()
            if slot.end_time:
                slot_dict["end_time"] = slot.end_time.isoformat()
            slots_dicts.append(slot_dict)

        simplified_events_str = self._build_upcoming_events_str()
        prompt = f"""
        You are an expert scheduling assistant. Your task is to select the most suitable time slot for a new event from a list of proposed options based on user preferences and constraints.

        ### Proposed Time Slots
        {json.dumps(slots_dicts, indent=2)}

        ### Existing Calendar Events
        {simplified_events_str}

        ### New Event
        {self.event_prompt()}

        ### Constraints
        {self.general_constraints_prompt()}

        ---YOUR RESPONSE---
        {self.json_shape_prompt()}
        """

    def _parse_llm_response(self, response_str: str) -> LLMResponse:
        """Parses the raw LLM response to a validated LLM response."""
        json_data_str = response_str[
            response_str.find("{") : response_str.rfind("}") + 1
        ]
        json_data = json.loads(json_data_str)
        return LLMResponse.model_validate(json_data)

    def run(self):

        self.start_time = datetime.now()  # Current datetime for LLM context

        # Initial round
        initial_prompt = self._build_initial_prompt()
        logger.debug(initial_prompt)
        res = self.ollama.ask_continuous(initial_prompt)

        # Call the dedicated parser function and save the output.
        proposed_slots_data: LLMResponse = self._parse_llm_response(res)
        logger.info(f"Received {len(proposed_slots_data.event_data)} proposed slots.")

        # Validation round
        validation_prompt = self._validation_prompt(proposed_slots_data.event_data)
        logger.debug(validation_prompt)

        res = self.ollama.ask_continuous(validation_prompt)
        validated_slots_data: LLMResponse = self._parse_llm_response(res)
        logger.info(f"Received {len(validated_slots_data.event_data)} validated slots.")

        # Selection Round
        selection_prompt = self._selection_step(validated_slots_data.event_data)
        logger.debug(selection_prompt)

        res = self.ollama.ask_continuous(selection_prompt)
        selected_slot_data: LLMResponse = self._parse_llm_response(res)
        logger.success(f"Final slot, {selected_slot_data.event_data[0]}")

        self.ollama.reset_memory()

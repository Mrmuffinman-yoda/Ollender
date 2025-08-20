import os
import requests
import json
import datetime
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaConnector:
    def __init__(
        self,
        system_prompt: str = None,
        weak_model: str = "llama3.1:8b",
        strong_model: str = "gpt-oss:20b",
    ):
        base_url = os.getenv("OLLAMA_HOST", "http://192.168.1.100:11435")
        self.api_url = f"{base_url}/api/chat"
        self.strong_model = strong_model
        self.weak_model = weak_model
        self.system_prompt = system_prompt

        # Conversation memory for continuous mode
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def ask(self, user_prompt: str, use_strong_model: bool = True) -> str:
        """
        Single-shot query to Ollama (stateless).
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        data = {
            "model": self.strong_model if use_strong_model else self.weak_model,
            "messages": messages,
            "stream": False,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=data, timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama API: {e}")
            return None

    def ask_continuous(self, user_prompt: str, use_strong_model: bool = True) -> str:
        """
        Multi-turn conversation with memory.
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        self.messages.append({"role": "user", "content": user_prompt})

        data = {
            "model": self.strong_model if use_strong_model else self.weak_model,
            "messages": self.messages,
            "stream": False,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=data, timeout=30
            )
            response.raise_for_status()
            result = response.json()
            assistant_reply = result.get("message", {}).get("content", "")
            if assistant_reply:
                self.messages.append({"role": "assistant", "content": assistant_reply})
            return assistant_reply
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama API: {e}")
            return None

    def reset_memory(self):
        """
        Clear conversation history but keep system prompt if set.
        """
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def yes_or_no(
        self,
        question: str,
        use_strong_model: bool = True,
    ) -> bool:
        """
        Ask a yes/no question, if the answer contains yes return True, if it contains no return False.
        """
        question += " (Please only answer with 'yes' or 'no')"
        response = self.ask(question, use_strong_model=use_strong_model)
        logging.info(f"Received response: {response}")
        if "yes" in response.lower():
            return True
        elif "no" in response.lower():
            return False


if __name__ == "__main__":
    system_prompt = f"""
    You are a helpful assistant. Your job is to take tasks and assign them a time and date to complete them.
    Return the task title, task description, time and date to complete the task in a JSON format.
    Example:
    {{
        "task_title": "Buy groceries",
        "task_description": "Buy milk, eggs, and bread",
        "time_to_complete": "2023-10-01T10:00:00Z"
    }}
    The current date and time is {datetime.datetime.now().isoformat()}.
    """

    connector = OllamaConnector(system_prompt=system_prompt)

    response = connector.ask("Order socks online?")
    print(f"Response: {response}")

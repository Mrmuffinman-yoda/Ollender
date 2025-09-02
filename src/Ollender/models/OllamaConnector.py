import os
import datetime
from loguru import logger
import ollama
import requests


class OllamaConnector:
    """
    A connector class to interact with the Ollama API using the official ollama library.
    This class supports both single-shot (stateless) and continuous (stateful) conversations.
    """

    def __init__(
        self,
        system_prompt: str = None,
        model: str = "llama3",  # A more common default model
    ):
        """
        Initializes the OllamaConnector.

        Args:
            system_prompt (str, optional): A prompt to set the behavior of the assistant. Defaults to None.
            model (str, optional): The name of the Ollama model to use. Defaults to "llama3".
        """
        # Check for the OLLAMA_HOST environment variable
        host = os.getenv("OLLAMA_HOST")
        if host:
            logger.info("Found OLLAMA_HOST environment variable.")
            logger.info(f"Connecting to {host}")
        else:
            host = "http://127.0.0.1:11435"
            logger.info(f"OLLAMA_HOST not set. Using default host: {host}")

        # check if host is reachable
        try:
            response = requests.get(host, timeout=5)
            logger.info(response)
        except requests.exceptions.ConnectTimeout as e:
            logger.error(f"Failed to connect to Ollama host {host}: {e}")
            raise

        # Initialize the Ollama client with the specified host and timeout
        self.client = ollama.Client(host=host, timeout=90)

        self.model = model
        self.system_prompt = system_prompt

        # Conversation memory for continuous mode
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def ask(self, user_prompt: str) -> str:
        """
        Sends a single-shot, stateless query to Ollama.
        Conversation history is not maintained.

        Args:
            user_prompt (str): The user's prompt.

        Returns:
            str: The assistant's response, or an empty string if an error occurs.
        """
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        try:
            # Send the request to the Ollama API via the client
            response = self.client.chat(model=self.model, messages=messages)
            return response.get("message", {}).get("content", "")
        except ollama.ResponseError as e:
            logger.error(f"Ollama API Error: {e.error}")
            return f"Error: {e.error}"
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return ""

    def ask_continuous(self, user_prompt: str) -> str:
        """
        Sends a query to Ollama as part of a multi-turn, stateful conversation.
        Conversation history is maintained.

        Args:
            user_prompt (str): The user's prompt.

        Returns:
            str: The assistant's response, or an empty string if an error occurs.
        """
        self.messages.append({"role": "user", "content": user_prompt})

        try:
            # Send the entire conversation history to the Ollama API
            response = self.client.chat(model=self.model, messages=self.messages)
            assistant_reply = response.get("message", {}).get("content", "")

            # If a reply was received, add it to the conversation history
            if assistant_reply:
                self.messages.append({"role": "assistant", "content": assistant_reply})

            return assistant_reply
        except ollama.ResponseError as e:
            logger.error(f"Ollama API Error: {e.error}")
            return f"Error: {e.error}"
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return ""

    def reset_memory(self):
        """
        Clears the conversation history but retains the initial system prompt.
        """
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})
        logger.info("Conversation memory has been reset.")

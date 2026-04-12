from openai import OpenAI
import base64
import json
from django.conf import settings

client = OpenAI(
    api_key=settings.DEEP_SEEK_API_KEY,
    base_url="https://api.deepseek.com",
)


class BaseAiAgent:
    def __init__(self, payload=None):
        self.client = client
        self.payload = payload
        self.system_message = {"role": "system", "content": self.get_system_message()}

    def get_system_message(self):
        """Define the system message. Subclasses can override this."""
        raise NotImplementedError("Subclasses must implement this method.")

    async def chat_with_ai(self, prompt):
        """Simulate a conversation with vision."""

        # Create the conversation with the system message and the user's message
        messages = [self.system_message, {"role": "user", "content": prompt}]

        # Send the conversation to the API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            response_format={"type": "json_object"},
        )

        # Get the assistant's response
        assistant_response = response.choices[0].message.content

        return assistant_response

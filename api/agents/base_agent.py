import os
from openai import OpenAI


class BaseAiAgent:
    def __init__(self):
        # Initialize client lazily so it does not crash at import time
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


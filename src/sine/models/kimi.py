"""Kimi provided model api wrapper."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

kimi_api_key = os.environ.get("MOONSHOT_API_KEY")
kimi_base_url = "https://api.moonshot.cn/v1"

MOONSHOT_MODEL_NAMES = [
    "moonshot-v1-32k",
    "moonshot-v1-8k",
]


class MoonshotWrapper:
    """Moonshot model api client wrapper."""

    def __init__(self):
        """Init model client with api_key and base_url."""
        self.client = OpenAI(api_key=kimi_api_key, base_url=kimi_base_url)

    def chat(self, message):
        """Chat method provided to agent."""
        response = self.client.chat.completions.create(
            model=MOONSHOT_MODEL_NAMES[1],
            messages=message,
        )

        return response.choices[0].message.content.strip()

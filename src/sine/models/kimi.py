from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

kimi_api_key = os.environ.get("MOONSHOT_API_KEY")
kimi_base_url = "https://api.moonshot.cn/v1"

MOONSHOT_MODEL_NAMES = [
    "moonshot-v1-32k",
]

class MoonshotWrapper:
    def __init__(self):
        self.client = OpenAI(api_key=kimi_api_key,
                             base_url=kimi_base_url)
    
    def chat(self, message):
        response = self.client.chat.completions.create(
            model=MOONSHOT_MODEL_NAMES[0],
            messages=message,
        )
        
        return response.choices[0].message.content.strip()
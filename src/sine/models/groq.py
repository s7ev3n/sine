import os
from groq import Groq

class GroqMixtralWrapper:
    def __init__(self, api_key=None):
        self.client = Groq(api_key=api_key if api_key else os.getenv("GROQ_API_KEY"))
    
    def chat(self, message):
        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=message,
        )
        
        return response.choices[0].message.content.strip()
    
class GroqLlama70BWrapper:
    def __init__(self, api_key=None):
        self.client = Groq(api_key=api_key if api_key else os.getenv("GROQ_API_KEY"))
    
    def chat(self, message):
        response = self.client.chat.completions.create(
            model="llama2-70b-4096",
            messages=message,
        )
        
        return response.choices[0].message.content.strip()
    
class GroqGemma7BWrapper:
    def __init__(self, api_key=None):
        self.client = Groq(api_key=api_key if api_key else os.getenv("GROQ_API_KEY"))
    
    def chat(self, message):
        response = self.client.chat.completions.create(
            model="gemma-7b-it",
            messages=message,
        )
        
        return response.choices[0].message.content.strip()
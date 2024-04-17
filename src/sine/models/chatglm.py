import os
from zhipuai import ZhipuAI

# TODO: fix System clock synchronized: no issue, then use GLM model, as their
# api service requires precise time sync, and workstation is not synced time 
# with internet and fall bebind about 5 mins.
class GLM4Wrapper:
    def __init__(self, api_key=None):
        self.client = ZhipuAI(api_key=api_key if api_key else os.getenv("ZHIPU_API_KEY"))
    
    def chat(self, message):
        response = self.client.chat.completions.create(
            model="glm-4",
            messages=message,
        )
        
        return response.choices[0].message.content.strip()
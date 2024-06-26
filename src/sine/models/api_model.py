import os

from sine.common.logger import logger

AVAILABLE_API_MODELS = {
    'groq' : [
        "mixtral-8x7b-32768", "llama2-70b-4096", "llama3-70b-8192", "llama3-8b-8192"
    ],
    'zhipuai' : ["glm-4"],
    'moonshot' : ["moonshot-v1-32k", "moonshot-v1-8k"],
    'deepseek' : ["deepseek-chat", "deepseek-coder"]
}

def get_api_model(model_name):
    if 'glm' in model_name:
        from zhipuai import ZhipuAI
        assert model_name in AVAILABLE_API_MODELS['zhipuai']
        client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
    elif 'moonshot' in model_name:
        from openai import OpenAI
        assert model_name in AVAILABLE_API_MODELS['moonshot']
        client = OpenAI(api_key=os.getenv("MOONSHOT_API_KEY"),
                        base_url="https://api.moonshot.cn/v1")
    elif 'deepseek' in model_name:
        from openai import OpenAI
        assert model_name in AVAILABLE_API_MODELS['deepseek']
        client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                        base_url="https://api.deepseek.com")
    elif model_name in AVAILABLE_API_MODELS['groq']:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    else:
        raise ValueError(f"Model {model_name} not supported. Supported models: {AVAILABLE_API_MODELS.values()}")
    logger.debug(f"API model {model_name} client initialized.")
    return client

class APIModel:
    def __init__(self, model_name):
        self.client = get_api_model(model_name)
        self._model_name = model_name

    def chat(self, message):
        if isinstance(message, str):
            message = [dict(role="user", content=message)]
        if isinstance(message, dict):
            message = [message]

        response = self.client.chat.completions.create(
            model=self._model_name,
            messages=message,
        )

        return response.choices[0].message.content.strip()

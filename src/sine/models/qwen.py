import os
import dashscope

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

class QWENWrapper:
    def __init__(self):
        pass
    
    def chat(self, message):

        response = dashscope.Generation.call(
            model='qwen-turbo',
            messages=message,
            # result_format='message',  # set the result to be "message" format.
        )
        return response.output.text.strip()
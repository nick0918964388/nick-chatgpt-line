from api.prompt import Prompt
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatGPT:
    def __init__(self):
        self.prompt = Prompt()
        self.model = os.getenv("OPENAI_MODEL", default="gpt-3.5-turbo")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", default=0))
        self.frequency_penalty = float(os.getenv("OPENAI_FREQUENCY_PENALTY", default=0))
        self.presence_penalty = float(os.getenv("OPENAI_PRESENCE_PENALTY", default=0.6))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default=240))

    def get_response(self):
        messages = []
        for msg in self.prompt.msg_list:
            if msg.startswith("system:"):
                role = "system"
                content = msg[7:].strip()
            elif msg.startswith("Human:"):
                role = "user"
                content = msg[6:].strip()
            elif msg.startswith("AI:"):
                role = "assistant"
                content = msg[3:].strip()
            else:
                continue  # 跳過無效的消息格式
            messages.append({"role": role, "content": content})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content.strip()

    def add_msg(self, text):
        self.prompt.add_msg(text)

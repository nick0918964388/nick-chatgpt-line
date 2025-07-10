from api.prompt import Prompt
import os
import ollama

class ChatGPT:
    def __init__(self):
        self.prompt = Prompt()
        self.model = os.getenv("OLLAMA_MODEL", default="qwen3:30b-a3b-q8_0")
        self.client = ollama.Client(host=os.getenv("OLLAMA_HOST", default="http://localhost:11434"))

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

        response = self.client.chat(
            model=self.model,
            messages=messages
        )
        return response['message']['content'].strip()

    def add_msg(self, text):
        self.prompt.add_msg(text)

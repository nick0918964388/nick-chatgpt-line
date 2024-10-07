from api.prompt import Prompt
import os
import requests
from openai import OpenAI

API_TYPE = os.getenv("API_TYPE", "openai")  # 默認使用 OpenAI API
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://ollama.webtw.xyz:11434/api/generate")  # Ollama API 的 URL
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:9b")  # Ollama 模型名稱

if API_TYPE == "openai":
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
        messages = self._prepare_messages()
        
        if API_TYPE == "openai":
            return self._get_openai_response(messages)
        elif API_TYPE == "ollama":
            return self._get_ollama_response(messages)
        else:
            raise ValueError(f"Unsupported API_TYPE: {API_TYPE}")

    def _prepare_messages(self):
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
        return messages

    def _get_openai_response(self, messages):
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content.strip()

    def _get_ollama_response(self, messages):
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        if response.status_code == 200:
            return response.json()["response"].strip()
        else:
            raise Exception(f"Ollama API request failed with status code {response.status_code}")

    def add_msg(self, text):
        self.prompt.add_msg(text)

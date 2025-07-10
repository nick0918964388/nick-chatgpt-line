from api.prompt import Prompt
import os
import ollama

class ChatGPT:
    def __init__(self):
        self.prompt = Prompt()
        self.model = os.getenv("OLLAMA_MODEL", default="qwen3:30b-a3b-q8_0")
        self.client = ollama.Client(host=os.getenv("OLLAMA_HOST", default="http://localhost:11434"))
        # 預先載入模型到記憶體中
        self._preload_model()

    def _preload_model(self):
        """預先載入模型到記憶體中，避免每次呼叫時重新載入"""
        try:
            # 使用一個簡單的請求來載入模型
            self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                keep_alive=3600  # 保持模型在記憶體中1小時
            )
            print(f"模型 {self.model} 已成功載入到記憶體中")
        except Exception as e:
            print(f"預載入模型時發生錯誤: {e}")

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
            messages=messages,
            keep_alive=3600  # 保持模型在記憶體中1小時
        )
        return response['message']['content'].strip()

    def add_msg(self, text):
        self.prompt.add_msg(text)

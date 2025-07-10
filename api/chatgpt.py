from api.prompt import Prompt
import os
import ollama
import requests

class ChatGPT:
    def __init__(self):
        self.prompt = Prompt()
        self.model = os.getenv("OLLAMA_MODEL", default="qwen3:7b-instruct-q4_0")  # 使用較小的模型
        self.ollama_host = os.getenv("OLLAMA_HOST", default="http://localhost:11434")
        self.client = ollama.Client(host=self.ollama_host, timeout=300)  # 5分鐘timeout
        # 預先載入模型到記憶體中
        self._preload_model()

    def _preload_model(self):
        """預先載入模型到記憶體中，避免每次呼叫時重新載入"""
        try:
            # 1. 先檢查模型是否已載入
            self._check_model_loaded()
            
            # 2. 如果沒有載入，進行預載入
            print(f"開始預載入模型 {self.model}...")
            self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "ready"}],
                keep_alive=-1  # 永遠保持在記憶體中
            )
            print(f"模型 {self.model} 已成功載入到記憶體中")
            
            # 3. 設定模型永久保持載入
            self._set_model_keep_alive()
            
        except Exception as e:
            print(f"預載入模型時發生錯誤: {e}")

    def _check_model_loaded(self):
        """檢查模型是否已載入到記憶體中"""
        try:
            response = requests.get(f"{self.ollama_host}/api/ps")
            if response.status_code == 200:
                loaded_models = response.json()
                for model in loaded_models.get('models', []):
                    if model.get('name') == self.model:
                        print(f"模型 {self.model} 已在記憶體中")
                        return True
            return False
        except Exception as e:
            print(f"檢查模型狀態時發生錯誤: {e}")
            return False

    def _set_model_keep_alive(self):
        """設定模型永久保持在記憶體中"""
        try:
            # 使用ollama的keep_alive API
            requests.post(f"{self.ollama_host}/api/generate", json={
                "model": self.model,
                "keep_alive": -1  # 永遠保持
            })
            print(f"已設定模型 {self.model} 永久保持在記憶體中")
        except Exception as e:
            print(f"設定keep_alive時發生錯誤: {e}")

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
            keep_alive=-1  # 永遠保持在記憶體中
        )
        return response['message']['content'].strip()

    def add_msg(self, text):
        self.prompt.add_msg(text)

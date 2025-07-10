from api.prompt import Prompt
import os
import ollama
import requests
import logging

# 設定logging
logger = logging.getLogger(__name__)

class ChatGPT:
    def __init__(self):
        logger.info("🔧 初始化ChatGPT類別")
        self.prompt = Prompt()
        self.model = os.getenv("OLLAMA_MODEL", default="qwen3:7b-instruct-q4_0")  # 使用較小的模型
        self.ollama_host = os.getenv("OLLAMA_HOST", default="http://localhost:11434")
        logger.info(f"🤖 使用模型: {self.model}")
        logger.info(f"🌐 Ollama主機: {self.ollama_host}")
        
        self.client = ollama.Client(host=self.ollama_host, timeout=300)  # 5分鐘timeout
        logger.info("✅ Ollama客戶端創建成功")
        
        # 預先載入模型到記憶體中
        logger.info("🚀 開始預載入模型")
        self._preload_model()
        logger.info("✅ ChatGPT初始化完成")

    def _preload_model(self):
        """預先載入模型到記憶體中，避免每次呼叫時重新載入"""
        logger.info("🔍 開始預載入模型流程")
        try:
            # 1. 先檢查模型是否已載入
            logger.info("🔍 檢查模型是否已載入")
            is_loaded = self._check_model_loaded()
            
            if not is_loaded:
                # 2. 如果沒有載入，進行預載入
                logger.info(f"📥 開始預載入模型 {self.model}...")
                response = self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": "ready"}],
                    keep_alive=-1  # 永遠保持在記憶體中
                )
                logger.info(f"✅ 模型 {self.model} 已成功載入到記憶體中")
                logger.info(f"📝 預載入回應: {response.get('message', {}).get('content', '')}")
                
                # 3. 設定模型永久保持載入
                logger.info("🔧 設定模型永久保持載入")
                self._set_model_keep_alive()
            else:
                logger.info("✅ 模型已經在記憶體中，無需重新載入")
            
        except Exception as e:
            logger.error(f"❌ 預載入模型時發生錯誤: {e}")
            import traceback
            logger.error(f"❌ 詳細錯誤: {traceback.format_exc()}")

    def _check_model_loaded(self):
        """檢查模型是否已載入到記憶體中"""
        logger.info("🔍 檢查模型載入狀態")
        try:
            response = requests.get(f"{self.ollama_host}/api/ps")
            logger.info(f"📡 API請求狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                loaded_models = response.json()
                logger.info(f"📋 已載入的模型列表: {loaded_models}")
                
                for model in loaded_models.get('models', []):
                    if model.get('name') == self.model:
                        logger.info(f"✅ 模型 {self.model} 已在記憶體中")
                        return True
                
                logger.info(f"⚠️ 模型 {self.model} 未在記憶體中")
                return False
            else:
                logger.warning(f"⚠️ API請求失敗，狀態碼: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 檢查模型狀態時發生錯誤: {e}")
            return False

    def _set_model_keep_alive(self):
        """設定模型永久保持在記憶體中"""
        logger.info("🔧 設定模型永久保持在記憶體中")
        try:
            # 使用ollama的keep_alive API
            response = requests.post(f"{self.ollama_host}/api/generate", json={
                "model": self.model,
                "keep_alive": -1  # 永遠保持
            })
            logger.info(f"📡 Keep-alive API請求狀態碼: {response.status_code}")
            logger.info(f"✅ 已設定模型 {self.model} 永久保持在記憶體中")
        except Exception as e:
            logger.error(f"❌ 設定keep_alive時發生錯誤: {e}")

    def get_response(self):
        logger.info("🧠 開始獲取AI回應")
        messages = []
        
        logger.info("📝 處理對話訊息")
        for i, msg in enumerate(self.prompt.msg_list):
            logger.info(f"📝 處理訊息 {i+1}: {msg[:50]}...")
            
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
                logger.warning(f"⚠️ 跳過無效的訊息格式: {msg[:30]}...")
                continue  # 跳過無效的消息格式
            
            messages.append({"role": role, "content": content})
            logger.info(f"✅ 已加入 {role} 訊息")

        logger.info(f"📋 總共處理 {len(messages)} 條訊息")
        logger.info("🚀 開始向Ollama請求回應")
        
        try:
            # 檢查是否隱藏思考過程
            hide_thinking = os.getenv("HIDE_THINKING", "true").lower() == "true"
            logger.info(f"🔧 隱藏思考過程設定: {hide_thinking}")
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                keep_alive=-1,  # 永遠保持在記憶體中
                think=not hide_thinking  # 如果hide_thinking=True，則think=False
            )
            logger.info("✅ 成功獲取Ollama回應")
            
            ai_response = response['message']['content'].strip()
            logger.info(f"🤖 AI回應內容: {ai_response}")
            
            # 如果有思考過程且未隱藏，記錄思考內容
            if response['message'].get('thinking') and not hide_thinking:
                logger.info(f"🧠 思考過程: {response['message']['thinking'][:100]}...")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ 獲取AI回應時發生錯誤: {e}")
            import traceback
            logger.error(f"❌ 詳細錯誤: {traceback.format_exc()}")
            raise

    def add_msg(self, text):
        logger.info(f"📝 加入訊息到對話: {text}")
        self.prompt.add_msg(text)
        logger.info(f"✅ 訊息已加入，目前對話長度: {len(self.prompt.msg_list)}")

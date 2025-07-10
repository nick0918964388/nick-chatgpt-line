from api.prompt import Prompt
from api.tools import AVAILABLE_TOOLS, execute_tool, get_tools_description
import os
import ollama
import requests
import logging
import json
import re

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
        
        # 最大工具呼叫次數，避免無限循環
        max_tool_calls = 3
        tool_call_count = 0
        
        while tool_call_count < max_tool_calls:
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
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    keep_alive=-1  # 永遠保持在記憶體中
                )
                logger.info("✅ 成功獲取Ollama回應")
                
                ai_response = response['message']['content'].strip()
                logger.info(f"🤖 AI回應內容: {ai_response}")
                
                # 檢查是否包含工具呼叫
                tool_calls = self._extract_tool_calls(ai_response)
                
                if tool_calls:
                    logger.info(f"🛠️ 檢測到 {len(tool_calls)} 個工具呼叫")
                    tool_call_count += 1
                    
                    # 執行工具並加入結果
                    tool_results = []
                    for tool_call in tool_calls:
                        result = execute_tool(tool_call["name"], tool_call["parameters"])
                        tool_results.append(result)
                        
                        # 將工具結果加入對話
                        tool_result_msg = f"system:工具執行結果 [{tool_call['name']}]: {json.dumps(result, ensure_ascii=False, indent=2)}"
                        self.prompt.add_msg(tool_result_msg)
                        logger.info(f"📝 已加入工具結果: {tool_call['name']}")
                    
                    # 繼續循環以取得最終回應
                    continue
                else:
                    # 沒有工具呼叫，回傳最終回應
                    return ai_response
                    
            except Exception as e:
                logger.error(f"❌ 獲取AI回應時發生錯誤: {e}")
                import traceback
                logger.error(f"❌ 詳細錯誤: {traceback.format_exc()}")
                raise
        
        logger.warning("⚠️ 達到最大工具呼叫次數限制")
        return "處理過程中達到工具呼叫次數限制，請稍後再試。"

    def _extract_tool_calls(self, text):
        """從AI回應中提取工具呼叫"""
        logger.info("🔍 分析AI回應中的工具呼叫")
        tool_calls = []
        
        # 匹配工具呼叫模式: [TOOL:tool_name:parameters]
        pattern = r'\[TOOL:(\w+):([^\]]+)\]'
        matches = re.findall(pattern, text)
        
        for tool_name, params_str in matches:
            logger.info(f"🛠️ 發現工具呼叫: {tool_name} 參數: {params_str}")
            
            if tool_name in AVAILABLE_TOOLS:
                try:
                    # 解析參數
                    if params_str.startswith('{') and params_str.endswith('}'):
                        # JSON格式參數
                        parameters = json.loads(params_str)
                    else:
                        # 簡單字串參數，預設為itemnum
                        parameters = {"itemnum": params_str}
                    
                    tool_calls.append({
                        "name": tool_name,
                        "parameters": parameters
                    })
                    logger.info(f"✅ 工具呼叫解析成功: {tool_name}")
                except Exception as e:
                    logger.error(f"❌ 工具參數解析失敗: {e}")
            else:
                logger.warning(f"⚠️ 未知的工具: {tool_name}")
        
        return tool_calls

    def add_msg(self, text):
        logger.info(f"📝 加入訊息到對話: {text}")
        self.prompt.add_msg(text)
        logger.info(f"✅ 訊息已加入，目前對話長度: {len(self.prompt.msg_list)}")

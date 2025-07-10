from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from api.chatgpt import ChatGPT
import os
import threading
import time
import logging

# 設定logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"
app = Flask(__name__)
chatgpt = ChatGPT()
# domain root
@app.route('/')
def home():
    return 'Hello, World!'

# 狀態檢查endpoint
@app.route('/status', methods=['GET'])
def status():
    """顯示目前的設定狀態"""
    use_sync_mode = os.getenv("USE_SYNC_MODE", "true").lower() == "true"
    
    return {
        "status": "運行中",
        "mode": "同步模式" if use_sync_mode else "異步模式",
        "line_configured": bool(os.getenv("LINE_CHANNEL_ACCESS_TOKEN")),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen3:7b-instruct-q4_0"),
        "sync_mode_enabled": use_sync_mode,
        "tools_enabled": True,
        "available_tools": ["get_inventory_info", "get_item_info"],
        "tool_api_base": "http://tra.webtw.xyz:8888/maximo/oslc/script/",
        "maxauth_configured": bool(os.getenv("MAXAUTH"))
    }

# 測試endpoint
@app.route('/test', methods=['GET'])
def test_line_api():
    """測試LINE API和ollama連接"""
    logger.info("🔍 開始測試LINE API和ollama連接")
    
    results = {
        "line_token": bool(os.getenv("LINE_CHANNEL_ACCESS_TOKEN")),
        "line_secret": bool(os.getenv("LINE_CHANNEL_SECRET")),
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen3:7b-instruct-q4_0"),
        "maxauth_configured": bool(os.getenv("MAXAUTH"))
    }
    
    # 測試ollama連接
    try:
        import requests
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        test_response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        results["ollama_connection"] = f"成功 - 狀態碼: {test_response.status_code}"
        results["ollama_models"] = test_response.json()
    except Exception as e:
        results["ollama_connection"] = f"失敗: {str(e)}"
    
    # 測試ChatGPT初始化
    try:
        test_chatgpt = ChatGPT()
        results["chatgpt_init"] = "成功"
    except Exception as e:
        results["chatgpt_init"] = f"失敗: {str(e)}"
    
    logger.info(f"📋 測試結果: {results}")
    return results

# 測試LINE push message的endpoint
@app.route('/test_push/<user_id>', methods=['GET'])
def test_push_message(user_id):
    """測試向特定用戶發送push message"""
    logger.info(f"🔍 測試向用戶 {user_id} 發送push message")
    
    try:
        response = line_bot_api.push_message(
            user_id,
            TextSendMessage(text="🧪 這是一個測試訊息")
        )
        logger.info(f"✅ Push message發送成功: {response}")
        return {"status": "success", "message": "Push message發送成功", "response": str(response)}
    except Exception as e:
        logger.error(f"❌ Push message發送失敗: {e}")
        return {"status": "error", "message": str(e)}

# 測試工具API的endpoint
@app.route('/test_tool/<tool_name>/<itemnum>', methods=['GET'])
def test_tool(tool_name, itemnum):
    """測試工具API"""
    logger.info(f"🔍 測試工具 {tool_name} 查詢料號 {itemnum}")
    
    try:
        from api.tools import execute_tool
        result = execute_tool(tool_name, {"itemnum": itemnum})
        logger.info(f"✅ 工具測試成功: {tool_name}")
        return result
    except Exception as e:
        logger.error(f"❌ 工具測試失敗: {e}")
        return {"status": "error", "message": str(e)}

# 測試Maximo API連接
@app.route('/test_maximo', methods=['GET'])
def test_maximo():
    """測試Maximo API連接和認證"""
    logger.info("🔍 測試Maximo API連接")
    
    results = {
        "maxauth_configured": bool(os.getenv("MAXAUTH")),
        "api_base": "http://tra.webtw.xyz:8888/maximo/oslc/script/",
        "tests": []
    }
    
    # 測試庫存API
    try:
        import requests
        url = "http://tra.webtw.xyz:8888/maximo/oslc/script/ZZ_ITEM_GETINVB?itemnum=TEST123"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        maxauth = os.getenv("MAXAUTH")
        if maxauth:
            headers["maxauth"] = maxauth
        
        response = requests.get(url, headers=headers, timeout=10)
        
        results["tests"].append({
            "api": "ZZ_ITEM_GETINVB",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "message": "連接成功" if response.status_code == 200 else f"HTTP {response.status_code}"
        })
        
    except Exception as e:
        results["tests"].append({
            "api": "ZZ_ITEM_GETINVB",
            "success": False,
            "error": str(e)
        })
    
    # 測試料號API
    try:
        url = "http://tra.webtw.xyz:8888/maximo/oslc/script/ZZ_ITEM_GETITEM?itemnum=TEST123"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        maxauth = os.getenv("MAXAUTH")
        if maxauth:
            headers["maxauth"] = maxauth
        
        response = requests.get(url, headers=headers, timeout=10)
        
        results["tests"].append({
            "api": "ZZ_ITEM_GETITEM",
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "message": "連接成功" if response.status_code == 200 else f"HTTP {response.status_code}"
        })
        
    except Exception as e:
        results["tests"].append({
            "api": "ZZ_ITEM_GETITEM",
            "success": False,
            "error": str(e)
        })
    
    logger.info(f"📋 Maximo API測試完成: {results}")
    return results
@app.route("/webhook", methods=['POST'])
def callback():
    logger.info("🔄 收到webhook請求")
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    logger.info(f"📝 Request body: {body}")
    # handle webhook body
    try:
        logger.info("🔍 開始處理webhook body")
        line_handler.handle(body, signature)
        logger.info("✅ Webhook處理完成")
    except InvalidSignatureError:
        logger.error("❌ 無效的簽名")
        abort(400)
    except Exception as e:
        logger.error(f"❌ Webhook處理時發生錯誤: {e}")
        abort(500)
    return 'OK'
def process_message_async(user_id, message_text):
    """異步處理訊息，避免timeout（備用方案）"""
    logger.info(f"🚀 開始異步處理訊息 - 用戶ID: {user_id}")
    logger.info(f"💬 用戶訊息: {message_text}")
    
    try:
        # 處理AI回應
        logger.info("🧠 開始處理AI回應")
        chatgpt.add_msg(f"user:{message_text}?\n")
        logger.info("📝 已將用戶訊息加入對話")
        
        logger.info("🔍 正在獲取AI回應...")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        logger.info(f"🤖 AI回應: {reply_msg}")
        
        chatgpt.add_msg(f"assistant:{reply_msg}\n")
        logger.info("📝 已將AI回應加入對話")
        
        # 發送實際回應
        logger.info("📤 發送AI回應給用戶")
        final_response = line_bot_api.push_message(
            user_id,
            TextSendMessage(text=reply_msg)
        )
        logger.info(f"✅ AI回應已成功發送，回應: {final_response}")
        
    except Exception as e:
        logger.error(f"❌ 處理訊息時發生錯誤: {e}")
        import traceback
        logger.error(f"❌ 詳細錯誤: {traceback.format_exc()}")
        
        # 發送錯誤訊息
        try:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text="❌ 處理訊息時發生錯誤，請稍後再試")
            )
            logger.info("📤 錯誤訊息已發送")
        except Exception as send_error:
            logger.error(f"❌ 發送錯誤訊息時也發生錯誤: {send_error}")

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    
    logger.info("📨 收到LINE訊息事件")
    logger.info(f"📝 事件類型: {event.type}")
    logger.info(f"📝 訊息類型: {event.message.type}")
    
    if event.message.type != "text":
        logger.info("⚠️ 非文字訊息，略過處理")
        return
    
    user_id = event.source.user_id
    message_text = event.message.text
    reply_token = event.reply_token
    
    logger.info(f"👤 用戶ID: {user_id}")
    logger.info(f"💬 收到訊息: {message_text}")
    logger.info(f"🔑 Reply Token: {reply_token}")
    
    working_status = True
    if working_status:
        logger.info("✅ 系統處於工作狀態，開始處理訊息")
        
        # 檢查是否使用同步模式（預設為true）
        use_sync_mode = os.getenv("USE_SYNC_MODE", "true").lower() == "true"
        
        if use_sync_mode:
            logger.info("🔄 使用同步模式處理")
            try:
                # 快速檢查ollama是否可用
                logger.info("🔍 快速檢查ollama連接")
                import requests
                ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                
                # 設定較短的timeout避免webhook超時
                try:
                    test_response = requests.get(f"{ollama_host}/api/tags", timeout=2)
                    if test_response.status_code != 200:
                        raise Exception("Ollama服務不可用")
                    logger.info("✅ Ollama連接正常")
                except Exception as ollama_error:
                    logger.error(f"❌ Ollama連接失敗: {ollama_error}")
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="❌ AI服務暫時無法使用，請稍後再試")
                    )
                    return
                
                # 處理AI回應（同步執行）
                logger.info("🧠 開始同步處理AI回應")
                chatgpt.add_msg(f"user:{message_text}?\n")
                logger.info("📝 已將用戶訊息加入對話")
                
                # 獲取AI回應
                reply_msg = chatgpt.get_response().replace("AI:", "", 1)
                logger.info(f"🤖 獲得AI回應: {reply_msg}")
                
                chatgpt.add_msg(f"assistant:{reply_msg}\n")
                logger.info("📝 已將AI回應加入對話")
                
                # 直接用reply_message發送AI回應
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text=reply_msg)
                )
                logger.info("✅ 同步模式處理完成")
                
            except Exception as sync_error:
                logger.error(f"❌ 同步模式處理失敗: {sync_error}")
                import traceback
                logger.error(f"❌ 詳細錯誤: {traceback.format_exc()}")
                
                # 發送錯誤訊息
                try:
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="❌ 處理訊息時發生錯誤，請稍後再試")
                    )
                except Exception as reply_error:
                    logger.error(f"❌ 發送錯誤訊息失敗: {reply_error}")
                    # 如果reply_message失敗，嘗試用push_message
                    try:
                        line_bot_api.push_message(
                            user_id,
                            TextSendMessage(text="❌ 處理訊息時發生錯誤，請稍後再試")
                        )
                    except:
                        logger.error("❌ 所有訊息發送方式都失敗")
        else:
            logger.info("🔄 使用異步模式處理")
            # 先用reply_message立即回應"正在思考"
            try:
                logger.info("📤 使用reply_message發送思考中訊息")
                line_bot_api.reply_message(
                    reply_token,
                    TextSendMessage(text="🤔 正在思考中，請稍等...")
                )
                logger.info("✅ 思考中訊息已透過reply_message發送")
            except Exception as reply_error:
                logger.error(f"❌ Reply message發送失敗: {reply_error}")
            
            # 在背景執行緒中處理AI回應
            logger.info("🧵 創建背景執行緒處理AI回應")
            thread = threading.Thread(
                target=process_message_async,
                args=(user_id, message_text)
            )
            thread.daemon = True
            thread.start()
            logger.info("🚀 背景執行緒已啟動")
            
            # 等待一小段時間確保背景執行緒開始執行
            time.sleep(0.1)
            logger.info("⏰ 已等待背景執行緒啟動")
    else:
        logger.info("⚠️ 系統未處於工作狀態，略過處理")
if __name__ == "__main__":
    app.run()

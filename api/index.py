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
    """異步處理訊息，避免timeout"""
    logger.info(f"🚀 開始異步處理訊息 - 用戶ID: {user_id}")
    logger.info(f"💬 用戶訊息: {message_text}")
    
    try:
        # 先發送"正在思考"的訊息
        logger.info("📤 發送思考中訊息")
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="🤔 正在思考中，請稍等...")
        )
        logger.info("✅ 思考中訊息已發送")
        
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
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=reply_msg)
        )
        logger.info("✅ AI回應已成功發送")
        
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
        
        # 在背景執行緒中處理AI回應
        logger.info("🧵 創建背景執行緒處理AI回應")
        thread = threading.Thread(
            target=process_message_async,
            args=(user_id, message_text)
        )
        thread.daemon = True
        thread.start()
        logger.info("🚀 背景執行緒已啟動")
    else:
        logger.info("⚠️ 系統未處於工作狀態，略過處理")
if __name__ == "__main__":
    app.run()

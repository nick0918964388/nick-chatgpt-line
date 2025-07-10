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
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'
def process_message_async(user_id, message_text):
    """異步處理訊息，避免timeout"""
    try:
        # 先發送"正在思考"的訊息
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="🤔 正在思考中，請稍等...")
        )
        
        # 處理AI回應
        chatgpt.add_msg(f"user:{message_text}?\n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"assistant:{reply_msg}\n")
        
        # 發送實際回應
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=reply_msg)
        )
    except Exception as e:
        print(f"處理訊息時發生錯誤: {e}")
        # 發送錯誤訊息
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="❌ 處理訊息時發生錯誤，請稍後再試")
        )

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    
    if event.message.type != "text":
        return
    
    working_status = True
    if working_status:
        # 立即回應webhook，避免timeout
        user_id = event.source.user_id
        message_text = event.message.text
        
        # 在背景執行緒中處理AI回應
        thread = threading.Thread(
            target=process_message_async,
            args=(user_id, message_text)
        )
        thread.daemon = True
        thread.start()
if __name__ == "__main__":
    app.run()

import os

chat_language = "zh-tw"  # 將默認語言設置為繁體中文
MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default=20))

LANGUAGE_TABLE = {
    "zh-tw": "你好！我是一個 AI 助手。我會用繁體中文回答你的問題。",
}

class Prompt:
    def __init__(self):
        self.msg_list = []
        self.msg_list.append(f"System: 你是一個有幫助的 AI 助手。請始終使用繁體中文回答。")
        self.msg_list.append(f"AI: {LANGUAGE_TABLE[chat_language]}")
    
    def add_msg(self, new_msg):
        if len(self.msg_list) >= MSG_LIST_LIMIT:
            self.remove_msg()
        self.msg_list.append(new_msg)

    def remove_msg(self):
        self.msg_list.pop(1)  # 保留系統消息，刪除最早的對話消息

    def generate_prompt(self):
        return '\n'.join(self.msg_list) + "\n請用繁體中文回答。"

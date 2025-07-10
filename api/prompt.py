import os
import logging

# 設定logging
logger = logging.getLogger(__name__)

chat_language = "zh-tw"  # 將默認語言設置為繁體中文
MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default=20))

LANGUAGE_TABLE = {
    "zh-tw": "你好！我是一個 AI 助手。我會用繁體中文回答你的問題。",
}

class Prompt:
    def __init__(self):
        logger.info("🔧 初始化Prompt類別")
        self.msg_list = []
        system_msg1 = f"system:你是一個有幫助的 AI 助手。請始終使用繁體中文回答。"
        system_msg2 = f"system:{LANGUAGE_TABLE[chat_language]}"
        
        self.msg_list.append(system_msg1)
        self.msg_list.append(system_msg2)
        
        logger.info(f"📝 已加入系統訊息1: {system_msg1}")
        logger.info(f"📝 已加入系統訊息2: {system_msg2}")
        logger.info(f"📋 訊息列表限制: {MSG_LIST_LIMIT}")
        logger.info("✅ Prompt初始化完成")
    
    def add_msg(self, new_msg):
        logger.info(f"📝 準備加入新訊息: {new_msg}")
        
        if len(self.msg_list) >= MSG_LIST_LIMIT:
            logger.warning(f"⚠️ 訊息列表達到限制 ({MSG_LIST_LIMIT})，需要移除舊訊息")
            self.remove_msg()
        
        if not new_msg.startswith(("Human:", "AI:", "system:")):
            original_msg = new_msg
            new_msg = f"Human:{new_msg}"
            logger.info(f"🔄 訊息格式化: {original_msg} -> {new_msg}")
        
        self.msg_list.append(new_msg)
        logger.info(f"✅ 訊息已加入，目前列表長度: {len(self.msg_list)}")

    def remove_msg(self):
        if len(self.msg_list) > 2:
            removed_msg = self.msg_list.pop(2)  # 保留兩個系統消息，刪除最早的對話消息
            logger.info(f"🗑️ 已移除舊訊息: {removed_msg}")
            logger.info(f"📋 移除後列表長度: {len(self.msg_list)}")
        else:
            logger.warning("⚠️ 無法移除訊息，列表中只有系統訊息")

    def generate_prompt(self):
        logger.info("🔧 生成完整提示")
        prompt = '\n'.join(self.msg_list) + "\n請用繁體中文回答。"
        logger.info(f"📝 生成的提示長度: {len(prompt)} 字元")
        return prompt

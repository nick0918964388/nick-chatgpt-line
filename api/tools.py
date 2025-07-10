import requests
import json
import logging
import os

logger = logging.getLogger(__name__)

def get_inventory_info(itemnum):
    """取得庫存量與倉庫櫃位"""
    try:
        url = f"http://tra.webtw.xyz:8888/maximo/oslc/script/ZZ_ITEM_GETINVB?itemnum={itemnum}"
        logger.info(f"🔍 查詢庫存資訊: {url}")
        
        # 設定必要的headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # 從環境變數取得maxauth
        maxauth = os.getenv("MAXAUTH")
        if maxauth:
            headers["maxauth"] = maxauth
            logger.info("🔑 已加入maxauth認證")
        else:
            logger.warning("⚠️ 未設定MAXAUTH環境變數")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"✅ 庫存查詢成功: {itemnum}")
        return {
            "success": True,
            "itemnum": itemnum,
            "type": "inventory",
            "data": data
        }
    except requests.RequestException as e:
        logger.error(f"❌ 庫存查詢失敗: {e}")
        return {
            "success": False,
            "itemnum": itemnum,
            "type": "inventory",
            "error": str(e)
        }

def get_item_info(itemnum):
    """取得料號內容"""
    try:
        url = f"http://tra.webtw.xyz:8888/maximo/oslc/script/ZZ_ITEM_GETITEM?itemnum={itemnum}"
        logger.info(f"🔍 查詢料號資訊: {url}")
        
        # 設定必要的headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # 從環境變數取得maxauth
        maxauth = os.getenv("MAXAUTH")
        if maxauth:
            headers["maxauth"] = maxauth
            logger.info("🔑 已加入maxauth認證")
        else:
            logger.warning("⚠️ 未設定MAXAUTH環境變數")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"✅ 料號查詢成功: {itemnum}")
        return {
            "success": True,
            "itemnum": itemnum,
            "type": "item",
            "data": data
        }
    except requests.RequestException as e:
        logger.error(f"❌ 料號查詢失敗: {e}")
        return {
            "success": False,
            "itemnum": itemnum,
            "type": "item",
            "error": str(e)
        }

# 工具定義
AVAILABLE_TOOLS = {
    "get_inventory_info": {
        "function": get_inventory_info,
        "description": "查詢指定料號的庫存量與倉庫櫃位資訊",
        "parameters": {
            "type": "object",
            "properties": {
                "itemnum": {
                    "type": "string",
                    "description": "要查詢的料號"
                }
            },
            "required": ["itemnum"]
        }
    },
    "get_item_info": {
        "function": get_item_info,
        "description": "查詢指定料號的詳細內容與規格資訊",
        "parameters": {
            "type": "object",
            "properties": {
                "itemnum": {
                    "type": "string",
                    "description": "要查詢的料號"
                }
            },
            "required": ["itemnum"]
        }
    }
}

def execute_tool(tool_name, parameters):
    """執行指定的工具"""
    logger.info(f"🛠️ 執行工具: {tool_name}, 參數: {parameters}")
    
    if tool_name not in AVAILABLE_TOOLS:
        logger.error(f"❌ 未知的工具: {tool_name}")
        return {
            "success": False,
            "error": f"未知的工具: {tool_name}"
        }
    
    tool_func = AVAILABLE_TOOLS[tool_name]["function"]
    try:
        result = tool_func(**parameters)
        logger.info(f"✅ 工具執行成功: {tool_name}")
        return result
    except Exception as e:
        logger.error(f"❌ 工具執行失敗: {tool_name}, 錯誤: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_tools_description():
    """取得所有可用工具的描述"""
    tools_desc = []
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        tools_desc.append(f"- {tool_name}: {tool_info['description']}")
    return "\n".join(tools_desc) 
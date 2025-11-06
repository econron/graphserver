# utils/serializers.py
# ---------------------------------------------------------
# JSONシリアライゼーション関数
# ---------------------------------------------------------
import json
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage


def get_message_role(m: BaseMessage) -> str:
    """メッセージのロールを取得"""
    if isinstance(m, HumanMessage): 
        return "user"
    if isinstance(m, AIMessage): 
        return "assistant"
    if isinstance(m, ToolMessage): 
        return "tool"
    return "system"


def to_jsonable(obj: Any) -> Any:
    """オブジェクトをJSONシリアライズ可能な形式に変換"""
    if isinstance(obj, BaseMessage):
        return {
            "type": obj.__class__.__name__, 
            "role": get_message_role(obj), 
            "content": obj.content
        }
    if isinstance(obj, list): 
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict): 
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj


def json_serializer(o: Any) -> Any:
    """JSONシリアライゼーション用のカスタムエンコーダー"""
    if isinstance(o, BaseMessage):
        return to_jsonable(o)
    # BaseMessage以外のオブジェクトの処理
    if hasattr(o, "__dict__"):
        try:
            return o.__dict__
        except (AttributeError, TypeError):
            pass
    # フォールバック: 文字列化
    return str(o)


def dump_json(data: Any) -> str:
    """データをJSON文字列に変換"""
    return json.dumps(data, ensure_ascii=False, default=json_serializer)

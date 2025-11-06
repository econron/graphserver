# graph/nodes.py
# ---------------------------------------------------------
# グラフノード関数とルーター
# ---------------------------------------------------------
import asyncio
import json
import logging
from uuid import uuid4
from typing import Any, Callable, Dict, Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from config import GraphConfig
from graph.state import GraphState, StepType

logger = logging.getLogger(__name__)


class NodeName:
    """ノード名定数"""
    PLANNER = "planner"
    TOOL = "tool"
    RESPOND = "respond"


# グローバル設定（依存性注入用）
_config: Optional[GraphConfig] = None


def set_config(config: GraphConfig):
    """設定を注入する（依存性注入）"""
    global _config
    _config = config


def get_config() -> GraphConfig:
    """現在の設定を取得（デフォルト設定を返す）"""
    global _config
    if _config is None:
        from config import _default_config
        return _default_config
    return _config


def create_planner(config: Optional[GraphConfig] = None) -> Callable:
    """プランナーノード関数を作成（設定注入版）"""
    cfg = config or get_config()
    
    async def planner(state: GraphState) -> Dict[str, Any]:
        """入力を見て、'tool:' で始まればツールノードへ。それ以外は応答へ。"""
        try:
            messages = state.get("messages", [])
            if not messages:
                logger.warning("planner: messages is empty")
                return {"step": StepType.RESPONDING}
            
            last = messages[-1]
            text = (last.content or "").strip().lower() if isinstance(last, HumanMessage) else ""
            step = StepType.TOOLING if text.startswith(cfg.tool_prefix) else StepType.RESPONDING
            return {"step": step}
        except Exception as e:
            logger.error(f"planner error: {e}", exc_info=True)
            return {"step": StepType.RESPONDING}  # エラー時は応答へ
    return planner


def create_call_tool(config: Optional[GraphConfig] = None) -> Callable:
    """ツール呼び出しノード関数を作成（設定注入版）"""
    cfg = config or get_config()
    
    async def call_tool(state: GraphState) -> Dict[str, Any]:
        """ダミーツール（検索っぽい結果を返す）。messages と updates 両方に出す。"""
        try:
            messages = state.get("messages", [])
            if not messages:
                logger.warning("call_tool: messages is empty")
                return {"step": StepType.RESPONDING}
            
            last = messages[-1]
            user_text = (last.content or "").strip() if isinstance(last, HumanMessage) else ""
            query = user_text.split(":", 1)[1].strip() if ":" in user_text else user_text

            await asyncio.sleep(cfg.tool_processing_delay)

            tool_call_id = f"tool-{uuid4().hex[:8]}"
            result = {
                "id": tool_call_id,
                "name": cfg.fake_tool_name,
                "input": {"q": query},
                "output": {
                    "top": f"Top result for '{query}'",
                    "items": [f"{query} - A", f"{query} - B", f"{query} - C"],
                },
            }

            tool_msg = ToolMessage(tool_call_id=tool_call_id, content=json.dumps(result, ensure_ascii=False))
            return {"messages": [tool_msg], "tool_results": [result], "step": StepType.RESPONDING}
        except Exception as e:
            logger.error(f"call_tool error: {e}", exc_info=True)
            return {"step": StepType.RESPONDING}  # エラー時は応答へ
    return call_tool


def create_respond(config: Optional[GraphConfig] = None) -> Callable:
    """応答ノード関数を作成（設定注入版）"""
    cfg = config or get_config()
    
    async def respond(state: GraphState) -> Dict[str, Any]:
        """最終応答（簡易エコー）"""
        try:
            messages = state.get("messages", [])
            if not messages:
                logger.warning("respond: messages is empty")
                return {"messages": [AIMessage(content="エラー: メッセージが見つかりません")]}
            
            last = messages[-1]
            user_text = (last.content or "").strip() if isinstance(last, HumanMessage) else ""
            await asyncio.sleep(cfg.response_delay)
            used_tool = bool(state.get("tool_results"))
            content = ("（ツールを使いました）\n" if used_tool else "") + f"Echo: {user_text}"
            return {"messages": [AIMessage(content=content)]}
        except Exception as e:
            logger.error(f"respond error: {e}", exc_info=True)
            return {"messages": [AIMessage(content=f"エラーが発生しました: {str(e)}")]}
    return respond


# 後方互換性のため、デフォルト設定で作成された関数をエクスポート
_planner = create_planner()
_call_tool = create_call_tool()
_respond = create_respond()

# エクスポート（後方互換性のため）
planner = _planner
call_tool = _call_tool
respond = _respond


def router(state: GraphState) -> str:
    """ステップに応じて次のノードを決定するルーター"""
    step = state.get("step", StepType.IDLE)
    STEP_ROUTING = {
        StepType.TOOLING: NodeName.TOOL,
        StepType.RESPONDING: NodeName.RESPOND,
        StepType.IDLE: NodeName.PLANNER,
    }
    return STEP_ROUTING.get(step, NodeName.PLANNER)

# app.py
# ---------------------------------------------------------
# uv pip install fastapi uvicorn langchain-core langgraph pydantic
# uv run uvicorn app:app --reload
# ---------------------------------------------------------
from __future__ import annotations
import asyncio
import json
import logging
from uuid import uuid4
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, TypedDict

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver  # ← 残してもOK（thread_id 必須だが自動採番）
# interrupt 関連は使わない

# ========= Logging =========
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ========= Configuration =========
class GraphConfig:
    """グラフ設定クラス"""
    TOOL_PREFIX = "tool:"
    TOOL_PROCESSING_DELAY = 0.3
    RESPONSE_DELAY = 0.2
    FAKE_TOOL_NAME = "fake_search"

class StepType:
    """ステップタイプ定数"""
    IDLE = "idle"
    TOOLING = "tooling"
    RESPONDING = "responding"

class NodeName:
    """ノード名定数"""
    PLANNER = "planner"
    TOOL = "tool"
    RESPOND = "respond"

# ========= API Models =========
class ChatRequest(BaseModel):
    """チャットリクエストモデル"""
    input: str = Field(..., min_length=1, description="ユーザーの入力テキスト")
    thread_id: Optional[str] = Field(None, description="スレッドID（未指定の場合は自動生成）")

# ========= Graph State =========
class GraphState(TypedDict, total=False):
    messages: List[BaseMessage]
    tool_results: List[Dict[str, Any]]
    step: Literal["idle", "tooling", "responding"]

# ========= Nodes =========
async def planner(state: GraphState) -> Dict[str, Any]:
    """入力を見て、'tool:' で始まればツールノードへ。それ以外は応答へ。"""
    try:
        messages = state.get("messages", [])
        if not messages:
            logger.warning("planner: messages is empty")
            return {"step": StepType.RESPONDING}
        
        last = messages[-1]
        text = (last.content or "").strip().lower() if isinstance(last, HumanMessage) else ""
        step = StepType.TOOLING if text.startswith(GraphConfig.TOOL_PREFIX) else StepType.RESPONDING
        return {"step": step}
    except Exception as e:
        logger.error(f"planner error: {e}", exc_info=True)
        return {"step": StepType.RESPONDING}  # エラー時は応答へ

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

        await asyncio.sleep(GraphConfig.TOOL_PROCESSING_DELAY)

        tool_call_id = f"tool-{uuid4().hex[:8]}"
        result = {
            "id": tool_call_id,
            "name": GraphConfig.FAKE_TOOL_NAME,
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

async def respond(state: GraphState) -> Dict[str, Any]:
    """最終応答（簡易エコー）"""
    try:
        messages = state.get("messages", [])
        if not messages:
            logger.warning("respond: messages is empty")
            return {"messages": [AIMessage(content="エラー: メッセージが見つかりません")]}
        
        last = messages[-1]
        user_text = (last.content or "").strip() if isinstance(last, HumanMessage) else ""
        await asyncio.sleep(GraphConfig.RESPONSE_DELAY)
        used_tool = bool(state.get("tool_results"))
        content = ("（ツールを使いました）\n" if used_tool else "") + f"Echo: {user_text}"
        return {"messages": [AIMessage(content=content)]}
    except Exception as e:
        logger.error(f"respond error: {e}", exc_info=True)
        return {"messages": [AIMessage(content=f"エラーが発生しました: {str(e)}")]}

def router(state: GraphState) -> str:
    """ステップに応じて次のノードを決定するルーター"""
    step = state.get("step", StepType.IDLE)
    STEP_ROUTING = {
        StepType.TOOLING: NodeName.TOOL,
        StepType.RESPONDING: NodeName.RESPOND,
        StepType.IDLE: NodeName.PLANNER,
    }
    return STEP_ROUTING.get(step, NodeName.PLANNER)

# ========= Build Graph =========
memory = MemorySaver()  # 省きたい場合は None にして OK（下の compile から除去）
builder = StateGraph(GraphState)
builder.add_node(NodeName.PLANNER, planner)
builder.add_node(NodeName.TOOL, call_tool)
builder.add_node(NodeName.RESPOND, respond)
builder.add_conditional_edges(
    START, 
    router, 
    {
        NodeName.PLANNER: NodeName.PLANNER, 
        NodeName.TOOL: NodeName.TOOL, 
        NodeName.RESPOND: NodeName.RESPOND
    }
)
builder.add_edge(NodeName.PLANNER, NodeName.TOOL)
builder.add_edge(NodeName.TOOL, NodeName.RESPOND)
builder.add_edge(NodeName.RESPOND, END)
graph = builder.compile(checkpointer=memory)

# ========= FastAPI (SSE endpoints) =========
app = FastAPI()

def _role_of(m: BaseMessage) -> str:
    """メッセージのロールを取得"""
    if isinstance(m, HumanMessage): 
        return "user"
    if isinstance(m, AIMessage): 
        return "assistant"
    if isinstance(m, ToolMessage): 
        return "tool"
    return "system"

def _to_jsonable(obj: Any) -> Any:
    """オブジェクトをJSONシリアライズ可能な形式に変換"""
    if isinstance(obj, BaseMessage):
        return {"type": obj.__class__.__name__, "role": _role_of(obj), "content": obj.content}
    if isinstance(obj, list): 
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict): 
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj

def _json_serializer(o: Any) -> Any:
    """JSONシリアライゼーション用のカスタムエンコーダー"""
    if isinstance(o, BaseMessage):
        return _to_jsonable(o)
    # BaseMessage以外のオブジェクトの処理
    if hasattr(o, "__dict__"):
        try:
            return o.__dict__
        except (AttributeError, TypeError):
            pass
    # フォールバック: 文字列化
    return str(o)

def _dump(data: Any) -> str:
    """データをJSON文字列に変換"""
    return json.dumps(data, ensure_ascii=False, default=_json_serializer)

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    チャットエンドポイント（SSEストリーミング）
    
    Body例:
      {"input":"tool: LangGraph streaming"}      # thread_id 未指定OK（自動採番）
      {"input":"こんにちは","thread_id":"t2"}      # 指定も可
    """
    try:
        thread_id = request.thread_id or str(uuid4())
        init: GraphState = {"messages": [HumanMessage(content=request.input)], "step": StepType.IDLE}

        async def gen() -> AsyncIterator[bytes]:
            try:
                # セッション情報（thread_id）を最初に通知
                yield f"data: {_dump({'ch':'session','data':{'thread_id': thread_id}})}\n\n".encode()

                async for event in graph.astream(
                    init,
                    stream_mode=["messages", "updates"],
                    subgraphs=True,
                    config={"configurable": {"thread_id": thread_id}},  # MemorySaver を使うため
                ):
                    logger.debug(f"Graph event: {event}")
                    try:
                        if isinstance(event, dict) and "messages" in event:
                            yield f"data: {_dump({'ch':'messages','data': _to_jsonable(event['messages'])})}\n\n".encode()
                        elif isinstance(event, dict) and "updates" in event:
                            yield f"data: {_dump({'ch':'updates','data': _to_jsonable(event['updates'])})}\n\n".encode()
                        else:
                            yield f"data: {_dump({'ch':'raw','data': _to_jsonable(event)})}\n\n".encode()
                    except Exception as e:
                        logger.error(f"Error serializing event: {e}", exc_info=True)
                        error_data = _dump({'ch': 'error', 'data': {'message': f"シリアライゼーションエラー: {str(e)}"}})
                        yield f"data: {error_data}\n\n".encode()
                        
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                error_data = _dump({'ch': 'error', 'data': {'message': f"ストリーミングエラー: {str(e)}"}})
                yield f"data: {error_data}\n\n".encode()

        return StreamingResponse(gen(), media_type="text/event-stream", headers={"X-Thread-Id": thread_id})
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")

# ローカル直接起動用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

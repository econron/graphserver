# app.py
# ---------------------------------------------------------
# uv pip install fastapi uvicorn langchain-core langgraph
# uv run uvicorn app:app --reload
# ---------------------------------------------------------
from __future__ import annotations
import asyncio
import json
from uuid import uuid4
from typing import Any, AsyncIterator, Dict, List, Literal, TypedDict

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver  # ← 残してもOK（thread_id 必須だが自動採番）
# interrupt 関連は使わない

# ========= Graph State =========
class GraphState(TypedDict, total=False):
    messages: List[BaseMessage]
    tool_results: List[Dict[str, Any]]
    step: Literal["idle", "tooling", "responding"]

# ========= Nodes =========
async def planner(state: GraphState) -> GraphState:
    """入力を見て、'tool:' で始まればツールノードへ。それ以外は応答へ。"""
    last = state["messages"][-1]
    text = (last.content or "").strip().lower() if isinstance(last, HumanMessage) else ""
    return {"step": "tooling" if text.startswith("tool:") else "responding"}

async def call_tool(state: GraphState) -> GraphState:
    """ダミーツール（検索っぽい結果を返す）。messages と updates 両方に出す。"""
    last = state["messages"][-1]
    user_text = (last.content or "").strip() if isinstance(last, HumanMessage) else ""
    query = user_text.split(":", 1)[1].strip() if ":" in user_text else user_text

    await asyncio.sleep(0.3)  # 処理中っぽさ

    result = {
        "id": "fake-1",
        "name": "fake_search",
        "input": {"q": query},
        "output": {
            "top": f"Top result for '{query}'",
            "items": [f"{query} - A", f"{query} - B", f"{query} - C"],
        },
    }

    tool_msg = ToolMessage(tool_call_id="fake-1", content=json.dumps(result, ensure_ascii=False))
    return {"messages": [tool_msg], "tool_results": [result], "step": "responding"}

async def respond(state: GraphState) -> GraphState:
    """最終応答（簡易エコー）"""
    last = state["messages"][-1]
    user_text = (last.content or "").strip() if isinstance(last, HumanMessage) else ""
    await asyncio.sleep(0.2)
    used_tool = bool(state.get("tool_results"))
    content = ("（ツールを使いました）\n" if used_tool else "") + f"Echo: {user_text}"
    return {"messages": [AIMessage(content=content)]}

def router(state: GraphState) -> str:
    step = state.get("step", "idle")
    if step == "tooling":
        return "tool"
    if step == "responding":
        return "respond"
    return "planner"

# ========= Build Graph =========
memory = MemorySaver()  # 省きたい場合は None にして OK（下の compile から除去）
builder = StateGraph(GraphState)
builder.add_node("planner", planner)
builder.add_node("tool", call_tool)
builder.add_node("respond", respond)
builder.add_conditional_edges(START, router, {"planner": "planner", "tool": "tool", "respond": "respond"})
builder.add_edge("planner", "tool")
builder.add_edge("tool", "respond")
builder.add_edge("respond", END)
graph = builder.compile(checkpointer=memory)

# ========= FastAPI (SSE endpoints) =========
app = FastAPI()

def _role_of(m: BaseMessage) -> str:
    if isinstance(m, HumanMessage): return "user"
    if isinstance(m, AIMessage): return "assistant"
    if isinstance(m, ToolMessage): return "tool"
    return "system"

def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, BaseMessage):
        return {"type": obj.__class__.__name__, "role": _role_of(obj), "content": obj.content}
    if isinstance(obj, list): return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict): return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj

def _dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=_json_default)

def _json_default(o: Any):
    if isinstance(o, BaseMessage):
        return _to_jsonable(o)
    try:
        return o.__dict__
    except Exception:
        return str(o)

@app.post("/chat")
async def chat(payload: Dict[str, Any]):
    """
    Body例:
      {"input":"tool: LangGraph streaming"}      # thread_id 未指定OK（自動採番）
      {"input":"こんにちは","thread_id":"t2"}      # 指定も可
    """
    text = (payload.get("input") or "").strip()
    if not text:
        raise HTTPException(400, "input is required")

    thread_id = payload.get("thread_id") or str(uuid4())

    init: GraphState = {"messages": [HumanMessage(content=text)], "step": "idle"}

    async def gen() -> AsyncIterator[bytes]:
        # セッション情報（thread_id）を最初に通知
        yield f"data: {_dump({'ch':'session','data':{'thread_id': thread_id}})}\n\n".encode()

        async for event in graph.astream(
            init,
            stream_mode=["messages", "updates"],
            subgraphs=True,
            config={"configurable": {"thread_id": thread_id}},  # MemorySaver を使うため
        ):
            print(event)
            if isinstance(event, dict) and "messages" in event:
                yield f"data: {_dump({'ch':'messages','data': _to_jsonable(event['messages'])})}\n\n".encode()
            elif isinstance(event, dict) and "updates" in event:
                yield f"data: {_dump({'ch':'updates','data': _to_jsonable(event['updates'])})}\n\n".encode()
            else:
                yield f"data: {_dump({'ch':'raw','data': _to_jsonable(event)})}\n\n".encode()

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"X-Thread-Id": thread_id})

# ローカル直接起動用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

# tests/fixtures/mock_graph.py
# ---------------------------------------------------------
# テスト用モックグラフ
# ---------------------------------------------------------
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from graph.state import GraphState, StepType
from graph.nodes import NodeName


async def mock_planner(state: GraphState) -> Dict[str, Any]:
    """
    モックプランナーノード（即座に結果を返す）
    実際のロジックを再現しつつ、遅延なしで動作
    """
    messages = state.get("messages", [])
    if not messages:
        return {"step": StepType.RESPONDING}
    
    last = messages[-1]
    text = (last.content or "").strip().lower() if isinstance(last, HumanMessage) else ""
    step = StepType.TOOLING if text.startswith("tool:") else StepType.RESPONDING
    return {"step": step}


async def mock_call_tool(state: GraphState) -> Dict[str, Any]:
    """
    モックツール呼び出しノード（即座に結果を返す）
    実際のツール呼び出しをシミュレート
    """
    messages = state.get("messages", [])
    if not messages:
        return {"step": StepType.RESPONDING}
    
    last = messages[-1]
    user_text = (last.content or "").strip() if isinstance(last, HumanMessage) else ""
    query = user_text.split(":", 1)[1].strip() if ":" in user_text else user_text
    
    # モックツール結果
    tool_call_id = "tool-mock-12345"
    result = {
        "id": tool_call_id,
        "name": "mock_search",
        "input": {"q": query},
        "output": {
            "top": f"Mock result for '{query}'",
            "items": [f"{query} - Mock A", f"{query} - Mock B"],
        },
    }
    
    tool_msg = ToolMessage(tool_call_id=tool_call_id, content=str(result))
    return {
        "messages": [tool_msg],
        "tool_results": [result],
        "step": StepType.RESPONDING
    }


async def mock_respond(state: GraphState) -> Dict[str, Any]:
    """
    モック応答ノード（即座に結果を返す）
    実際の応答をシミュレート
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": [AIMessage(content="Mock: メッセージが見つかりません")]}
    
    last = messages[-1]
    user_text = (last.content or "").strip() if isinstance(last, HumanMessage) else ""
    used_tool = bool(state.get("tool_results"))
    content = ("（ツールを使いました）\n" if used_tool else "") + f"Mock Echo: {user_text}"
    return {"messages": [AIMessage(content=content)]}


def mock_router(state: GraphState) -> str:
    """
    モックルーター（実際のルーターと同じロジック）
    """
    step = state.get("step", StepType.IDLE)
    STEP_ROUTING = {
        StepType.TOOLING: NodeName.TOOL,
        StepType.RESPONDING: NodeName.RESPOND,
        StepType.IDLE: NodeName.PLANNER,
    }
    return STEP_ROUTING.get(step, NodeName.PLANNER)


def create_mock_graph(checkpointer=None):
    """
    テスト用のモックグラフを作成
    
    Args:
        checkpointer: チェックポインター（Noneの場合はMemorySaverを使用）
    
    Returns:
        コンパイルされたモックグラフ
    """
    if checkpointer is None:
        checkpointer = MemorySaver()
    
    builder = StateGraph(GraphState)
    builder.add_node(NodeName.PLANNER, mock_planner)
    builder.add_node(NodeName.TOOL, mock_call_tool)
    builder.add_node(NodeName.RESPOND, mock_respond)
    builder.add_conditional_edges(
        START,
        mock_router,
        {
            NodeName.PLANNER: NodeName.PLANNER,
            NodeName.TOOL: NodeName.TOOL,
            NodeName.RESPOND: NodeName.RESPOND
        }
    )
    builder.add_edge(NodeName.PLANNER, NodeName.TOOL)
    builder.add_edge(NodeName.TOOL, NodeName.RESPOND)
    builder.add_edge(NodeName.RESPOND, END)
    
    return builder.compile(checkpointer=checkpointer)


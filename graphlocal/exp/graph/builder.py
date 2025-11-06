# graph/builder.py
# ---------------------------------------------------------
# グラフ構築ロジック
# ---------------------------------------------------------
from typing import Optional

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from config import GraphConfig
from graph.state import GraphState, StepType
from graph.nodes import create_planner, create_call_tool, create_respond, router, NodeName


def create_graph(config: Optional[GraphConfig] = None, checkpointer=None):
    """
    グラフを構築して返す
    
    Args:
        config: グラフ設定（Noneの場合はデフォルト設定を使用）
        checkpointer: チェックポインター（Noneの場合はMemorySaverを使用）
    
    Returns:
        コンパイルされたグラフ
    """
    if checkpointer is None:
        checkpointer = MemorySaver()
    
    # 設定に基づいてノード関数を作成
    planner_node = create_planner(config)
    tool_node = create_call_tool(config)
    respond_node = create_respond(config)
    
    builder = StateGraph(GraphState)
    builder.add_node(NodeName.PLANNER, planner_node)
    builder.add_node(NodeName.TOOL, tool_node)
    builder.add_node(NodeName.RESPOND, respond_node)
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
    
    return builder.compile(checkpointer=checkpointer)


# デフォルトグラフインスタンス（後方互換性のため）
graph = create_graph()

# graph/state.py
# ---------------------------------------------------------
# グラフステート定義
# ---------------------------------------------------------
from typing import Any, Dict, List, Literal, TypedDict

from langchain_core.messages import BaseMessage


class StepType:
    """ステップタイプ定数"""
    IDLE = "idle"
    TOOLING = "tooling"
    RESPONDING = "responding"


class GraphState(TypedDict, total=False):
    """グラフの状態を定義するTypedDict"""
    messages: List[BaseMessage]
    tool_results: List[Dict[str, Any]]
    step: Literal["idle", "tooling", "responding"]

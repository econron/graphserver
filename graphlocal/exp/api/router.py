# api/router.py
# ---------------------------------------------------------
# FastAPIルーター定義
# ---------------------------------------------------------
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from api.models import ChatRequest
from api.controllers.chat_controller import ChatController

# グラフインスタンスをグローバルに保持（app.pyで設定される）
_graph_instance: Any = None


def set_graph_instance(graph: Any):
    """グラフインスタンスを設定する（app.pyから呼び出される）"""
    global _graph_instance
    _graph_instance = graph


def get_chat_controller() -> ChatController:
    """チャットコントローラーを取得する依存性関数"""
    global _graph_instance
    return ChatController(graph_instance=_graph_instance)


# ========= Router =========
router = APIRouter(
    tags=["graph"],
)

# ========= Register Endpoints =========
@router.post("/chat", response_model=None)
async def chat(
    request: ChatRequest,
    controller: Annotated[ChatController, Depends(get_chat_controller)]
):
    """
    チャットエンドポイント（SSEストリーミング）
    
    Body例:
      {"input":"tool: LangGraph streaming"}      # thread_id 未指定OK（自動採番）
      {"input":"こんにちは","thread_id":"t2"}      # 指定も可
    """
    return await controller.chat(request)

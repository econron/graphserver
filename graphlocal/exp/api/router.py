# api/router.py
# ---------------------------------------------------------
# FastAPIルーター定義
# ---------------------------------------------------------
from typing import Annotated

from fastapi import APIRouter, Depends

from api.models import ChatRequest
from api.controllers.chat_controller import ChatController
from api.services.chat_service import ChatService
from api.repositories.graph_repository import GraphRepository

# リポジトリとサービスをグローバルに保持（app.pyで設定される）
_graph_repository: GraphRepository | None = None
_chat_service: ChatService | None = None


def set_graph_repository(repository: GraphRepository):
    """グラフリポジトリを設定する（app.pyから呼び出される）"""
    global _graph_repository
    _graph_repository = repository


def get_chat_service() -> ChatService:
    """チャットサービスを取得する依存性関数"""
    global _graph_repository, _chat_service
    if _chat_service is None:
        if _graph_repository is None:
            raise RuntimeError("GraphRepository is not initialized. Call set_graph_repository() first.")
        _chat_service = ChatService(_graph_repository)
    return _chat_service


def get_chat_controller() -> ChatController:
    """チャットコントローラーを取得する依存性関数"""
    chat_service = get_chat_service()
    return ChatController(chat_service)


# ========= Router =========
router = APIRouter(
    tags=["graph"],
)

# ========= Register Endpoints =========
@router.post("/chat", response_model=None)
async def chat(
    request: ChatRequest,
    controller: Annotated[ChatController, Depends(get_chat_controller)],
    graph_name: str = "default"
):
    """
    チャットエンドポイント（SSEストリーミング）
    
    Args:
        request: チャットリクエスト
        controller: チャットコントローラー
        graph_name: 使用するグラフ名（デフォルト: "default"）
    
    Body例:
      {"input":"tool: LangGraph streaming"}      # thread_id 未指定OK（自動採番）
      {"input":"こんにちは","thread_id":"t2"}      # 指定も可
    """
    return await controller.chat(request, graph_name=graph_name)

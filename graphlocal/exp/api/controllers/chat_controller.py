# api/controllers/chat_controller.py
# ---------------------------------------------------------
# チャットコントローラー（HTTP処理のみ）
# ---------------------------------------------------------
import logging
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from api.models import ChatRequest
from api.services.chat_service import ChatService

logger = logging.getLogger(__name__)


class ChatController:
    """チャット関連のコントローラー（HTTP処理のみ）"""
    
    def __init__(self, chat_service: ChatService):
        """
        初期化
        
        Args:
            chat_service: チャットサービス
        """
        self.chat_service = chat_service
    
    async def chat(
        self,
        request: ChatRequest,
        graph_name: str = "default"
    ) -> StreamingResponse:
        """
        チャットエンドポイント（SSEストリーミング）
        
        Args:
            request: チャットリクエスト
            graph_name: 使用するグラフ名（デフォルト: "default"）
        
        Returns:
            SSEストリーミングレスポンス
        """
        try:
            # スレッドIDを取得（リクエストから、または生成）
            thread_id = request.thread_id or str(uuid4())
            
            # サービスを呼び出してストリーミングを生成
            async def gen():
                async for chunk in self.chat_service.process_chat_stream(request, graph_name):
                    yield chunk
            
            return StreamingResponse(
                gen(),
                media_type="text/event-stream",
                headers={"X-Thread-Id": thread_id}
            )
        except Exception as e:
            logger.error(f"Chat controller error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")

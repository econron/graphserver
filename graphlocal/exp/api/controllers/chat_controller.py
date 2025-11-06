# api/controllers/chat_controller.py
# ---------------------------------------------------------
# チャットコントローラー
# ---------------------------------------------------------
import logging
from typing import AsyncIterator, Optional
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from langchain_core.messages import HumanMessage

from graph.builder import create_graph
from graph.state import StepType, GraphState
from api.models import ChatRequest
from utils.serializers import to_jsonable, dump_json

logger = logging.getLogger(__name__)


class ChatController:
    """チャット関連のコントローラー"""
    
    def __init__(self, graph_instance=None):
        """
        初期化
        
        Args:
            graph_instance: グラフインスタンス（Noneの場合はデフォルトを使用）
        """
        self.graph_instance = graph_instance or self._get_default_graph()
    
    def _get_default_graph(self):
        """デフォルトのグラフインスタンスを取得"""
        from graph.builder import graph as default_graph
        return default_graph
    
    async def chat(self, request: ChatRequest) -> StreamingResponse:
        """
        チャットエンドポイント（SSEストリーミング）
        
        Args:
            request: チャットリクエスト
        
        Returns:
            SSEストリーミングレスポンス
        """
        try:
            thread_id = request.thread_id or str(uuid4())
            init: GraphState = {
                "messages": [HumanMessage(content=request.input)], 
                "step": StepType.IDLE
            }

            async def gen() -> AsyncIterator[bytes]:
                try:
                    # セッション情報（thread_id）を最初に通知
                    yield f"data: {dump_json({'ch':'session','data':{'thread_id': thread_id}})}\n\n".encode()

                    async for event in self.graph_instance.astream(
                        init,
                        stream_mode=["messages", "updates"],
                        subgraphs=True,
                        config={"configurable": {"thread_id": thread_id}},  # MemorySaver を使うため
                    ):
                        logger.debug(f"Graph event: {event}")
                        try:
                            if isinstance(event, dict) and "messages" in event:
                                yield f"data: {dump_json({'ch':'messages','data': to_jsonable(event['messages'])})}\n\n".encode()
                            elif isinstance(event, dict) and "updates" in event:
                                yield f"data: {dump_json({'ch':'updates','data': to_jsonable(event['updates'])})}\n\n".encode()
                            else:
                                yield f"data: {dump_json({'ch':'raw','data': to_jsonable(event)})}\n\n".encode()
                        except Exception as e:
                            logger.error(f"Error serializing event: {e}", exc_info=True)
                            error_data = dump_json({'ch': 'error', 'data': {'message': f"シリアライゼーションエラー: {str(e)}"}})
                            yield f"data: {error_data}\n\n".encode()
                            
                except Exception as e:
                    logger.error(f"Streaming error: {e}", exc_info=True)
                    error_data = dump_json({'ch': 'error', 'data': {'message': f"ストリーミングエラー: {str(e)}"}})
                    yield f"data: {error_data}\n\n".encode()

            return StreamingResponse(
                gen(), 
                media_type="text/event-stream", 
                headers={"X-Thread-Id": thread_id}
            )
        except Exception as e:
            logger.error(f"Chat controller error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")

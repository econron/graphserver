# api/services/chat_service.py
# ---------------------------------------------------------
# チャットサービス（ビジネスロジック）
# ---------------------------------------------------------
import logging
from typing import AsyncIterator
from uuid import uuid4

from langchain_core.messages import HumanMessage

from graph.state import StepType, GraphState
from api.models import ChatRequest
from api.repositories.graph_repository import GraphRepository
from utils.serializers import to_jsonable, dump_json

logger = logging.getLogger(__name__)


class ChatService:
    """チャット関連のビジネスロジックを担当するサービス"""
    
    def __init__(self, graph_repository: GraphRepository):
        """
        初期化
        
        Args:
            graph_repository: グラフリポジトリ
        """
        self.graph_repo = graph_repository
    
    def _create_initial_state(self, input_text: str) -> GraphState:
        """
        初期状態を作成
        
        Args:
            input_text: ユーザー入力テキスト
        
        Returns:
            初期状態
        """
        return {
            "messages": [HumanMessage(content=input_text)],
            "step": StepType.IDLE
        }
    
    def _transform_event(self, event: dict) -> dict:
        """
        グラフイベントをクライアント向け形式に変換
        
        Args:
            event: グラフイベント
        
        Returns:
            変換されたイベントデータ
        """
        if isinstance(event, dict) and "messages" in event:
            return {"ch": "messages", "data": to_jsonable(event["messages"])}
        elif isinstance(event, dict) and "updates" in event:
            return {"ch": "updates", "data": to_jsonable(event["updates"])}
        else:
            return {"ch": "raw", "data": to_jsonable(event)}
    
    async def process_chat_stream(
        self,
        request: ChatRequest,
        graph_name: str = "default"
    ) -> AsyncIterator[bytes]:
        """
        チャット処理をストリーミング形式で実行
        
        Args:
            request: チャットリクエスト
            graph_name: 使用するグラフ名（デフォルト: "default"）
        
        Yields:
            SSE形式のバイトデータ
        """
        thread_id = request.thread_id or str(uuid4())
        initial_state = self._create_initial_state(request.input)
        
        # セッション情報を最初に通知
        session_data = dump_json({"ch": "session", "data": {"thread_id": thread_id}})
        yield f"data: {session_data}\n\n".encode()
        
        try:
            async for event in self.graph_repo.stream_execution(
                graph_name=graph_name,
                initial_state=initial_state,
                config={"thread_id": thread_id}
            ):
                logger.debug(f"Graph event: {event}")
                try:
                    transformed = self._transform_event(event)
                    event_data = dump_json(transformed)
                    yield f"data: {event_data}\n\n".encode()
                except Exception as e:
                    logger.error(f"Error serializing event: {e}", exc_info=True)
                    error_data = dump_json({
                        "ch": "error",
                        "data": {"message": f"シリアライゼーションエラー: {str(e)}"}
                    })
                    yield f"data: {error_data}\n\n".encode()
        except ValueError as e:
            # グラフが見つからない場合
            logger.error(f"Graph execution error: {e}", exc_info=True)
            error_data = dump_json({
                "ch": "error",
                "data": {"message": str(e)}
            })
            yield f"data: {error_data}\n\n".encode()
        except Exception as e:
            # その他のエラー
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_data = dump_json({
                "ch": "error",
                "data": {"message": f"ストリーミングエラー: {str(e)}"}
            })
            yield f"data: {error_data}\n\n".encode()

# api/repositories/graph_repository.py
# ---------------------------------------------------------
# グラフリポジトリ（グラフインスタンス管理と実行）
# ---------------------------------------------------------
import logging
from typing import Any, AsyncIterator, Dict, Optional

from graph.state import GraphState

logger = logging.getLogger(__name__)


class GraphRepository:
    """グラフインスタンスの管理と実行を担当するリポジトリ"""
    
    def __init__(self):
        """初期化"""
        self._graphs: Dict[str, Any] = {}
    
    def register(self, name: str, graph_instance: Any) -> None:
        """
        グラフインスタンスを登録
        
        Args:
            name: グラフ名（例: "default", "v2_graph"）
            graph_instance: グラフインスタンス
        """
        if name in self._graphs:
            logger.warning(f"Graph '{name}' is already registered. Overwriting.")
        self._graphs[name] = graph_instance
        logger.info(f"Graph '{name}' registered successfully")
    
    def get(self, name: str = "default") -> Optional[Any]:
        """
        グラフインスタンスを取得
        
        Args:
            name: グラフ名（デフォルト: "default"）
        
        Returns:
            グラフインスタンス（存在しない場合はNone）
        """
        graph = self._graphs.get(name)
        if graph is None:
            logger.warning(f"Graph '{name}' not found. Available graphs: {list(self._graphs.keys())}")
        return graph
    
    def list_graphs(self) -> list[str]:
        """
        登録されているグラフ名のリストを取得
        
        Returns:
            グラフ名のリスト
        """
        return list(self._graphs.keys())
    
    async def stream_execution(
        self,
        graph_name: str,
        initial_state: GraphState,
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Any]:
        """
        グラフを実行してストリーミング形式でイベントを返す
        
        Args:
            graph_name: グラフ名
            initial_state: 初期状態
            config: 実行設定（thread_id等）
        
        Yields:
            グラフ実行イベント
        
        Raises:
            ValueError: グラフが見つからない場合
        """
        graph = self.get(graph_name)
        if graph is None:
            raise ValueError(f"Graph '{graph_name}' not found. Available graphs: {self.list_graphs()}")
        
        if config is None:
            config = {}
        
        async for event in graph.astream(
            initial_state,
            stream_mode=["messages", "updates"],
            subgraphs=True,
            config={"configurable": config} if config else None,
        ):
            yield event

# tests/integration/test_repository.py
# ---------------------------------------------------------
# 統合テスト（リポジトリ）
# ---------------------------------------------------------
import pytest

from api.repositories.graph_repository import GraphRepository
from tests.fixtures.mock_graph import create_mock_graph


def test_repository_register_and_get():
    """
    リポジトリへのグラフ登録と取得のテスト
    """
    repo = GraphRepository()
    mock_graph = create_mock_graph()
    
    repo.register("test_graph", mock_graph)
    
    retrieved_graph = repo.get("test_graph")
    assert retrieved_graph is not None
    assert retrieved_graph == mock_graph


def test_repository_list_graphs():
    """
    登録されているグラフのリスト取得のテスト
    """
    repo = GraphRepository()
    mock_graph1 = create_mock_graph()
    mock_graph2 = create_mock_graph()
    
    repo.register("graph1", mock_graph1)
    repo.register("graph2", mock_graph2)
    
    graphs = repo.list_graphs()
    assert "graph1" in graphs
    assert "graph2" in graphs
    assert len(graphs) == 2


def test_repository_get_nonexistent():
    """
    存在しないグラフを取得しようとした場合のテスト
    """
    repo = GraphRepository()
    
    graph = repo.get("nonexistent")
    assert graph is None


def test_repository_overwrite():
    """
    既存のグラフを上書きするテスト
    """
    repo = GraphRepository()
    mock_graph1 = create_mock_graph()
    mock_graph2 = create_mock_graph()
    
    repo.register("test_graph", mock_graph1)
    repo.register("test_graph", mock_graph2)  # 上書き
    
    retrieved_graph = repo.get("test_graph")
    assert retrieved_graph == mock_graph2


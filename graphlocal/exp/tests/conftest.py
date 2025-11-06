# tests/conftest.py
# ---------------------------------------------------------
# pytest設定と共通フィクスチャ
# ---------------------------------------------------------
import pytest
from fastapi.testclient import TestClient

from api.repositories.graph_repository import GraphRepository
from api import set_graph_repository
from tests.fixtures.mock_graph import create_mock_graph


@pytest.fixture
def mock_graph_repository():
    """
    モックグラフを使用したリポジトリを作成
    """
    repo = GraphRepository()
    mock_graph = create_mock_graph()
    repo.register("default", mock_graph)
    return repo


@pytest.fixture
def test_app(mock_graph_repository):
    """
    テスト用のFastAPIアプリケーションを作成
    """
    from fastapi import FastAPI
    from api import router
    
    app = FastAPI()
    set_graph_repository(mock_graph_repository)
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """
    テスト用のHTTPクライアント
    """
    return TestClient(test_app)


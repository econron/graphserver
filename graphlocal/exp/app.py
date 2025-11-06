# app.py
# ---------------------------------------------------------
# uv pip install fastapi uvicorn langchain-core langgraph pydantic pydantic-settings python-dotenv
# uv run uvicorn app:app --reload
# ---------------------------------------------------------
import logging
from functools import lru_cache

from fastapi import FastAPI

from config import GraphConfig
from graph.builder import create_graph
from api import router, set_graph_repository
from api.repositories.graph_repository import GraphRepository

# ========= Logging =========
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ========= Configuration Injection =========
@lru_cache
def get_config() -> GraphConfig:
    """
    設定を取得する（lru_cacheで一度だけ読み込む）
    
    Returns:
        GraphConfig: グラフ設定オブジェクト
    """
    return GraphConfig()


# 設定を取得してグラフを作成
config = get_config()
default_graph = create_graph(config=config)

# ========= Graph Repository Setup =========
graph_repository = GraphRepository()
graph_repository.register("default", default_graph)

# 将来的に他のグラフを追加する例:
# v2_graph = create_graph_v2(config)
# graph_repository.register("v2_graph", v2_graph)
# test_graph = create_test_graph()
# graph_repository.register("test_graph", test_graph)

# ========= FastAPI Application =========
app = FastAPI()

# グラフリポジトリをルーターに設定
set_graph_repository(graph_repository)

# ========= Register Router =========
app.include_router(router)

# ローカル直接起動用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
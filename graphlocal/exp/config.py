# config.py
# ---------------------------------------------------------
# アプリケーション設定定義（Pydantic Settings使用）
# ---------------------------------------------------------
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class GraphConfig(BaseSettings):
    """グラフ設定クラス（Pydantic Settingsを使用）"""
    tool_prefix: str = "tool:"
    tool_processing_delay: float = 0.3
    response_delay: float = 0.2
    fake_tool_name: str = "fake_search"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class OpenAIConfig(BaseSettings):
    """OpenAI設定クラス"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="OPENAI_",  # OPENAI_API_KEY, OPENAI_BASE_URL など
    )


class GrafanaConfig(BaseSettings):
    """Grafana設定クラス"""
    url: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    org_id: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="GRAFANA_",  # GRAFANA_URL, GRAFANA_API_KEY など
    )


class AppSettings:
    """アプリケーション全体の設定クラス（通常のクラスとして実装）"""
    
    def __init__(self):
        """初期化時に各設定クラスをインスタンス化"""
        # ネストされた設定をインスタンス化
        self.graph = GraphConfig()
        self.openai = OpenAIConfig()
        self.grafana = GrafanaConfig()
        
        # アプリケーション設定（環境変数から読み込み）
        self.debug: bool = self._get_env_bool("DEBUG", False)
        self.log_level: str = self._get_env_str("LOG_LEVEL", "INFO")
        self.environment: str = self._get_env_str("ENVIRONMENT", "development")
    
    @staticmethod
    def _get_env_str(key: str, default: str) -> str:
        """環境変数から文字列を取得"""
        import os
        return os.getenv(key, default)
    
    @staticmethod
    def _get_env_bool(key: str, default: bool) -> bool:
        """環境変数からブール値を取得"""
        import os
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")


# デフォルト設定インスタンス（後方互換性のため）
# 注意: グローバルインスタンスは遅延評価で作成（モジュール読み込み時のエラーを回避）
_default_graph_config: GraphConfig | None = None
_default_settings: AppSettings | None = None

def get_default_graph_config() -> GraphConfig:
    """デフォルトグラフ設定を取得（遅延評価）"""
    global _default_graph_config
    if _default_graph_config is None:
        _default_graph_config = GraphConfig()
    return _default_graph_config

def get_default_settings() -> AppSettings:
    """デフォルトアプリケーション設定を取得（遅延評価）"""
    global _default_settings
    if _default_settings is None:
        _default_settings = AppSettings()
    return _default_settings

# config.py
# ---------------------------------------------------------
# グラフ設定定義（Pydantic Settings使用）
# ---------------------------------------------------------
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


# デフォルト設定インスタンス（後方互換性のため）
_default_config = GraphConfig()

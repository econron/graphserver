# api/models.py
# ---------------------------------------------------------
# Pydanticモデル定義
# ---------------------------------------------------------
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """チャットリクエストモデル"""
    input: str = Field(..., min_length=1, description="ユーザーの入力テキスト")
    thread_id: Optional[str] = Field(None, description="スレッドID（未指定の場合は自動生成）")

# tests/e2e/test_chat_api.py
# ---------------------------------------------------------
# エンドツーエンドテスト（チャットAPI）
# ---------------------------------------------------------
import pytest


def test_chat_endpoint_basic(client):
    """
    基本的なチャットエンドポイントのテスト
    """
    response = client.post(
        "/chat",
        json={"input": "こんにちは"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # SSEイベントを読み取る
    events = []
    for line in response.iter_lines():
        line_str = line if isinstance(line, str) else line.decode("utf-8")
        if line_str.startswith("data: "):
            events.append(line_str[6:])  # "data: "を除去
    
    assert len(events) > 0
    
    # セッションイベントが最初に来ることを確認
    import json
    first_event = json.loads(events[0])
    assert first_event["ch"] == "session"
    assert "thread_id" in first_event["data"]


def test_chat_endpoint_with_thread_id(client):
    """
    スレッドIDを指定したチャットエンドポイントのテスト
    """
    thread_id = "test-thread-123"
    response = client.post(
        "/chat",
        json={"input": "test message", "thread_id": thread_id}
    )
    
    assert response.status_code == 200
    
    # レスポンスヘッダーにスレッドIDが含まれることを確認
    assert "X-Thread-Id" in response.headers
    assert response.headers["X-Thread-Id"] == thread_id


def test_chat_endpoint_tool_prefix(client):
    """
    tool:プレフィックス付きのメッセージのテスト
    """
    response = client.post(
        "/chat",
        json={"input": "tool: search test"}
    )
    
    assert response.status_code == 200
    
    # SSEイベントを読み取る
    events = []
    for line in response.iter_lines():
        line_str = line if isinstance(line, str) else line.decode("utf-8")
        if line_str.startswith("data: "):
            events.append(line_str[6:])
    
    assert len(events) > 0
    
    # メッセージイベントまたはupdatesイベントが含まれることを確認
    import json
    message_events = []
    for e in events:
        try:
            event_data = json.loads(e)
            if event_data.get("ch") in ["messages", "updates", "raw"]:
                message_events.append(event_data)
        except json.JSONDecodeError:
            continue
    
    # 少なくとも何らかのイベントが存在することを確認
    assert len(message_events) > 0


def test_chat_endpoint_invalid_request(client):
    """
    無効なリクエストのテスト
    """
    # 空のinput
    response = client.post(
        "/chat",
        json={"input": ""}
    )
    assert response.status_code == 422  # Validation error
    
    # inputが欠けている
    response = client.post(
        "/chat",
        json={}
    )
    assert response.status_code == 422  # Validation error


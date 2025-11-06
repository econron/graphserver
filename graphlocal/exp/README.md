## 起動

sh run.sh

## 実行

sh test.sh

## 環境変数設定

`.env`ファイルを作成して、以下の環境変数を設定できます：

### グラフ設定

```env
TOOL_PREFIX=tool:
TOOL_PROCESSING_DELAY=0.3
RESPONSE_DELAY=0.2
FAKE_TOOL_NAME=fake_search
```

### OpenAI設定

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MAX_TOKENS=2000
```

### Grafana設定

```env
# GRAFANA_URL=http://localhost:3000
# GRAFANA_API_KEY=your_grafana_api_key_here
# GRAFANA_USERNAME=admin
# GRAFANA_PASSWORD=admin
# GRAFANA_ORG_ID=1
```

### アプリケーション設定

```env
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 設定の使用例

```python
from config import AppSettings

settings = AppSettings()
# OpenAI APIキーを使用
if settings.openai.api_key:
    # OpenAIクライアントを初期化
    pass

# Grafana URLを使用
if settings.grafana.url:
    # Grafanaクライアントを初期化
    pass
```
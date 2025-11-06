# テストガイド

## セットアップ

テスト用の依存関係をインストールします：

```bash
uv pip install -e ".[dev]"
```

または、個別にインストール：

```bash
uv pip install pytest pytest-asyncio httpx
```

## テストの実行

### すべてのテストを実行

```bash
uv run pytest
```

### 特定のテストカテゴリを実行

```bash
# E2Eテストのみ
uv run pytest tests/e2e/

# 統合テストのみ
uv run pytest tests/integration/

# ユニットテストのみ
uv run pytest tests/unit/
```

### 詳細な出力で実行

```bash
uv run pytest -v
```

### カバレッジレポート付きで実行

```bash
uv run pytest --cov=. --cov-report=html
```

## テスト構造

```
tests/
├── conftest.py              # 共通フィクスチャ
├── fixtures/
│   └── mock_graph.py       # モックグラフ
├── e2e/
│   └── test_chat_api.py    # E2Eテスト（APIエンドポイント）
├── integration/
│   ├── test_graph_execution.py  # グラフ実行の統合テスト
│   └── test_repository.py       # リポジトリの統合テスト
└── unit/
    └── (将来追加)
```

## テストの説明

### E2Eテスト (`tests/e2e/`)

実際のAPIエンドポイントをテストします。モックグラフを使用して高速に実行されます。

- 基本的なチャットエンドポイントの動作確認
- スレッドIDの指定
- ツール呼び出しの動作確認
- 無効なリクエストのハンドリング

### 統合テスト (`tests/integration/`)

グラフの実行やリポジトリの動作をテストします。

- グラフ実行の基本動作
- ツール呼び出しを含むグラフ実行
- リポジトリの登録・取得・リスト取得

### モックグラフ (`tests/fixtures/mock_graph.py`)

実際のグラフと同じ構造を持ちますが、即座に結果を返す軽量な実装です。テストの高速化と、実際のLLM呼び出しなしでのテストを可能にします。


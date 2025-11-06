# syntax=docker/dockerfile:1

# 1. ビルダー・ステージ: 依存関係をインストールする
# プロジェクトがPython 3.13を要求しているため (cite: 4, 14)
FROM python:3.13-slim as builder

# uvをインストール
RUN pip install uv

WORKDIR /app

# 依存関係ファイルのみをコピー
COPY pyproject.toml uv.lock ./

# uv venvで仮想環境を作成し、uv pip syncでロックファイルから依存関係をインストール
# これにより、ビルドが高速化され、再現性が担保されます
RUN uv venv /opt/venv && \
    /opt/venv/bin/uv pip sync uv.lock

# 2. ファイナル・ステージ: 実行環境
FROM python:3.13-slim as final

WORKDIR /app

# ビルダーから仮想環境をコピー
COPY --from=builder /opt/venv /opt/venv

# アプリケーションコードをコピー
COPY . .

# 仮想環境をPATHに追加
ENV PATH="/opt/venv/bin:$PATH"

# コンテナ起動コマンド
# run.sh (cite: 23) とは異なり、本番環境では --reload を外し、
# コンテナ外からアクセスできるよう --host 0.0.0.0 を指定します。
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
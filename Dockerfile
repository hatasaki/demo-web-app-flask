# 1) 公式の軽量 Python イメージを使う (Debian 系 slim)
FROM python:3.12-slim AS base

# 2) コンテナ内の作業ディレクトリを作成/移動
WORKDIR /app

# 3) 依存ライブラリを先にコピーしてインストール
#    (アプリコードより先に行うことでキャッシュが効きやすくなる)
COPY requirements.txt ./

# 4) 余計なキャッシュを残さないようにしつつインストール
RUN pip install --no-cache-dir -r requirements.txt

# 5) アプリ本体をコピー
COPY . .

# 6) Flask が利用するポートを明示 (説明用。EXPOSE はドキュメント目的)
EXPOSE 5000

# 8) デフォルト起動コマンド
CMD ["python", "app.py"]
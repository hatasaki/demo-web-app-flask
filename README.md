# シンプル Flask メモアプリ (研修用)

最小構成で CRUD (Create/Read/Update/Delete) を行えるテキストメモアプリです。学習目的でコードを読みやすく、変更しやすくしています。

## 特徴
- Flask (最新版 3.x 系想定)
- SQLite の組み込み DB (`memo.db` 1ファイル)
- メモ本文のみ (タイトル等は無しで最小化)
- 背景色を 1 箇所の CSS 変数で簡単変更
- テンプレート継承 (`base.html`) によりレイアウト簡素化
 - 入力フォームはページ上部カード + 区切り線で一覧と分離
 - メモ一覧左に作成(C)/更新(U)日時表示

## 動作要件
- Python 3.10+ (3.11 以上推奨)

## セットアップ & 起動
```bash
# 仮想環境 (任意)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# 依存インストール
pip install -r requirements.txt

# (初回は自動作成されるため省略可) 明示的にテーブルを作成する場合
flask --app app.py init-db

# 起動
python app.py
# もしくは (開発サーバ)
flask --app app.py run --debug
```
ブラウザで: http://127.0.0.1:5000/

## Docker での実行方法
ローカル環境へ Python を直接入れたくない場合や本番相当の gunicorn で試す場合は Docker を利用できます。

### 1. ビルド
```bash
docker build -t flask-memo:latest .
```

### 2. 起動 (最小例)
```bash
docker run --rm -p 5000:5000 flask-memo:latest
```
http://localhost:5000 にアクセス。

### 3. メモDBを永続化したい場合
コンテナ破棄時に `memo.db` が消えないよう、ホストへマウントします。
```bash
docker run --rm -p 5000:5000 \
  -v $(pwd)/memo.db:/app/memo.db \
  flask-memo:latest
```

### 4. 環境変数 (アプリタイトルや SECRET_KEY を切り替え)
```bash
docker run --rm -p 5000:5000 \
  -e MEMO_NAME="研修メモ" \
  -e FLASK_SECRET_KEY=$(python -c "import secrets;print(secrets.token_hex(32))") \
  flask-memo:latest
```

### 5. 本番風 (任意パラメータ調整)
`Dockerfile` では `gunicorn wsgi:application --workers 3 --bind 0.0.0.0:5000 --preload` で起動しています。
CPU コア数に応じてワーカー数を増減可能です。(目安: `2 * CPU + 1`)
例: 4コアなら `--workers 9`。

### 6. イメージの軽量化検討 (発展)
- `build-essential` を削除し最小構成にする
- `python:3.12-alpine` を利用 (ただしビルドに追加パッケージが必要な場合あり)
- マルチステージでビルド用依存を除去

### 7. コンテナ内で初期化コマンドを明示実行したい場合
基本は初回起動時に自動作成されるため不要ですが、明示的にテーブル作成を行うなら:
```bash
docker run --rm -it --entrypoint bash flask-memo:latest -c "flask --app app.py init-db"
```

### 8. docker compose 利用 (任意)
将来的に他サービス (例: 外部DB) を追加する場合は `docker-compose.yml` でポート/ボリューム/環境変数を定義すると管理しやすくなります。


## 背景色の変更方法
`static/style.css` 冒頭にある `:root { --background-color: #ffffff; }` を編集します。
例:
```css
:root {
  --background-color: #f0f8ff; /* 薄い水色 */
}
```
保存後、ブラウザをリロードすると反映されます。

## 主なファイル構成
```
app.py                # Flask アプリ本体 (ルート & DB 初期化)
requirements.txt      # 依存ライブラリ (Flask)
static/style.css      # スタイル (背景色カスタム変数など)
templates/base.html   # ベースレイアウト
templates/index.html  # メモ一覧 + 追加フォーム
templates/edit.html   # メモ編集フォーム
memo.db               # 起動後に生成される SQLite DB (Git管理外推奨)
```

### 画面構成 (現在のUI)
1. タイトル「メモ」
2. 新規メモ入力カード (`.new-note`)
3. 区切り線 `<hr class="divider" />`
4. メモ一覧 (`.note-list`) — 各行: 日時メタ列 / 本文 / 操作ボタン

### 日時表示仕様
- 左列 `C:` は作成日時 (Created)
- 左列 `U:` は更新日時 (Updated)
- 形式: `YYYY-MM-DD HH:MM` (先頭16文字を表示)
- まだ更新されていない場合 (`created_at == updated_at`) は更新日時表示が淡色 (opacity 約0.35)

### 主要CSSクラス概要
| クラス | 目的 |
|--------|------|
| `.new-note` | 新規メモ入力カード枠 |
| `.divider` | 入力部と一覧の視覚的区切り線 |
| `.note-list` | メモ一覧ULコンテナ |
| `.note-meta` | 各メモ左側の日時カラム |
| `.flash` / `.flash-error` | フラッシュメッセージ表示 |
| `.note-text` | メモ本文領域 |
| `.actions` | 編集/削除ボタン群 |

### SECRET_KEY について
`app.config['SECRET_KEY']` は flash メッセージなどセッション署名に使用する開発用プレースホルダです。本番運用時は環境変数で差し替えてください。

例 (環境変数設定):
```bash
export FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```
`app.py` 側の書き換え例:
```python
import os, secrets
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
```

## コード解説 (概要)
- `get_db()` / `teardown_appcontext`: リクエスト毎に SQLite コネクションを確立・終了
- `init_db()`: テーブル (`notes`) を作成
- `/` (GET): メモ一覧表示 + 追加フォーム (POST `/add`)
- `/add` (POST): 新規メモ追加
- `/edit/<id>` (GET/POST): メモ編集
- `/delete/<id>` (POST): メモ削除 (確認ダイアログあり)
- Flash メッセージ: 成功/エラー通知に使用
  - 一度表示された flash は次リクエストで消える (セッションCookie 利用)

## 研修用課題アイデア
- バリデーション強化 (文字数制限など)
- 検索機能の追加
- タグやタイトル列の追加
- 完了フラグや並び替え
- ページネーション

## Azure App Service への Cloud Shell からの最速デプロイ手順
Azure ポータル上の Cloud Shell (Bash) を開き、このリポジトリをデプロイします。

### 前提
- Azure サブスクリプションが有効
- Cloud Shell (Bash) が利用可能 (初回はストレージ作成を求められたら作成)
- 本リポジトリは GitHub で公開/参照可能 (クローン URL を `GIT_URL` として使用)

1.Clud shellの起動
Cloud Shellでbashのターミナルを起動します
初回起動時に設定画面が表示される場合、「ストレージアカウントは不要」オプションで問題ありません。サブスクリプションはご利用のものを選択してください

2.リポジトリのクローン
本リポジトリをクローンします
```bash
git clone github.com/hatasaki/demo-web-app-flask
```

2.環境変数の準備
任意の一意な Web アプリ名を環境変数 `APP_NAME` に設定します。<br>
`APP_NAME` はグローバル一意 (英小文字/数字/ハイフン) である必要があります。

```bash
RG_NAME="<あなたのリソースグループ名>";
APP_NAME="flask-memo-$RANDOM";
```

3.Azure App Serviceへのアプリのデプロイ
```bash
az webapp up \
  --name $APP_NAME \
  --resource-group $RG_NAME \
  --runtime "PYTHON:3.11" \
  --sku S1 \
  --logs \
  --os-type linux \
  --src .
```

`az webapp up` は以下を自動的に行います:
- (存在しなければ) App Service プラン作成
- (存在しなければ) Web アプリ作成
- Oryx によるビルド & デプロイ
- デプロイ後 URL を出力 (例: `https://<APP_NAME>.azurewebsites.net`)

4.アプリへの接続
コマンド完了後に表示されるアプリの URL にブラウザから接続して動作を確認



## ライセンス
研修用途サンプル。必要に応じて社内規約に合わせてください。

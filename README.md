# Azure App PaaS ワークショップ

Azure App Service および Container Apps へのアプリデプロイを実施するためのアプリです。
このアプリは最小構成で CRUD (Create/Read/Update/Delete) を行える Web テキストメモアプリです。学習目的でコードを読みやすく、変更しやすくしています。

## ワークショップ１: Azure App Service へ Cloud Shell (Bash) からデプロイ
Azure ポータルの Cloud Shell (Bash) 上で、このリポジトリをそのまま Azure App Service にデプロイする手順です。

### 前提条件
- Azure サブスクリプションが有効である
- Cloud Shell (Bash) が利用可能 (初回はストレージ作成プロンプトに従う)
- インターネット経由で本リポジトリをクローンできる

### 手順概要
1. Cloud Shell 起動
2. リポジトリ取得
3. 環境変数 (リソース名) 設定
4. `az webapp up` でビルド & デプロイ
5. 動作確認 (URL へアクセス)

---
### 1. Cloud Shell を開く
Azure ポータル右上の `</>` (Cloud Shell) アイコンから Bash を選択。初回起動時に設定画面が表示される場合、「ストレージアカウントは不要」オプションで問題ありません。サブスクリプションはご利用のものを選択してください。

### 2. リポジトリをクローン
```bash
git clone https://github.com/hatasaki/demo-web-app-flask.git
cd demo-web-app-flask
```

### 3. 環境変数を設定
デプロイ先のリソースグループ名 (既存 or これから作成) と、グローバル一意なアプリ名を指定します。
`APP_NAME` は英小文字/数字/ハイフンのみ、先頭は英字推奨。被っているとエラーになります。
```bash
RG_NAME="<既存または作成したいリソースグループ名>"
APP_NAME="flask-memo-$RANDOM"  # 例: ランダム値で衝突回避
LOCATION="japaneast"          # リソースグループ新規作成時のみ使用
```
リソースグループを新規作成する場合:
```bash
az group create --name $RG_NAME --location $LOCATION
```

### 4. デプロイ実行
`az webapp up` で必要なリソース (App Service プラン / Web アプリ) をまとめて作成 & デプロイします。

```bash
az webapp up \
  --name $APP_NAME \
  --resource-group $RG_NAME \
  --location $LOCATION \
  --runtime "PYTHON:3.11" \
  --sku S1 \
  --os-type linux
```

処理には 1〜3 分ほどかかることがあります。完了すると `https://<APP_NAME>.azurewebsites.net` の URL が表示されます。

`az webapp up` が内部で行う代表的処理:
- (未存在なら) App Service プラン作成
- (未存在なら) Web アプリ作成
- Oryx によるビルド & パッケージング
- ZIP デプロイ

### 5. 動作確認
表示された URL をブラウザで開き、トップページが表示され CRUD が行えるか確認します。

### よくあるエラー / チェックポイント
- `Name is already in use` : `APP_NAME` を別名に変えて再実行
- `ResourceGroupNotFound` : 事前にリソースグループを作成したか確認 (手順 3 参照)
- 500 エラー: 初回数十秒はウォームアップ中の場合あり。`az webapp log tail --name $APP_NAME --resource-group $RG_NAME` でログ確認

### 追加操作 (任意)
ログをリアルタイムで見る:
```bash
az webapp log tail --name $APP_NAME --resource-group $RG_NAME
```

Azure Portal で `MEMO_NAME` アプリ設定を追加し、表示変化を確認:
1. Azure Portal > 対象 Web アプリ > 設定 > 構成 > アプリケーション設定 で `MEMO_NAME` を追加 (例: `TeamA`)
2. 保存後 数十秒～1 分で反映。ブラウザをリロードしヘッダのタイトルが `TeamAメモ` になることを確認

スタイルを変更して別スロットで動作差分を確認 (背景色差分):
```bash
# Cloud Shell でスタイルを編集
code static/style.css   # エディタで --background-color を別の色 (例: #f0f8ff) に変更し保存

# 追加デプロイ スロット作成 (例: staging)
az webapp deployment slot create \
  --name $APP_NAME \
  --resource-group $RG_NAME \
  --slot staging

# スロットへデプロイ
# az webapp up はスロット指定 ( --slot ) や --src オプションをサポートしないため、
# スロットには ZIP デプロイ (az webapp deploy) を利用します。
zip -r app.zip .
az webapp deploy \
  --name $APP_NAME \
  --resource-group $RG_NAME \
  --slot staging \
  --src-path app.zip \
  --type zip

# スロット URL 例: https://<APP_NAME>-staging.azurewebsites.net
# 既定 (本番) と staging で背景色が異なることをブラウザで確認
```

#### 補足: コマンド修正の背景
以前 README に記載していた `--src .` は `az webapp up` の有効な引数ではなく、Azure CLI 実行時に `unrecognized arguments: --src .` エラーとなるため削除しました。`az webapp up` は "現在の作業ディレクトリ" を自動で ZIP デプロイ対象として扱うためソース指定は不要です。またデプロイ スロットへの直接デプロイは `az webapp up` では行えないため、スロットには `az webapp deploy --slot <slotName> --src-path <artifact>` を利用する手順に変更しました。

参照 (Microsoft Docs):
- az webapp up: https://learn.microsoft.com/cli/azure/webapp#az-webapp-up
- az webapp deploy: https://learn.microsoft.com/cli/azure/webapp#az-webapp-deploy

## ワークショップ2: Azure Container Apps へデプロイ
Azure ポータルで Azure Container Apps にアプリコンテナーデプロイする手順です。

### 前提条件
- 有効な Azure サブスクリプション
- ブラウザで Azure ポータルへサインイン済み
- GHCR のイメージ `ghcr.io/hatasaki/demo-web-app-flask:latest` が Pull 可能 (公開)
  - (参考) イメージは Flask アプリを `5000` 番ポートで待ち受ける設定

### アーキテクチャ簡単説明
Azure Container Apps (ACA) はコンテナオーケストレーション (Kubernetes ベース) をマネージドで抽象化。Consumption プランでは要求が無いとき 0 レプリカ (休止) としてコストを抑え、アクセス時に自動的に起動 (コールドスタート数秒) します。

### 手順サマリ
1. リソース グループ (必要なら新規) を作成
2. Container Apps Environment を作成
3. Container App を作成 (イメージ指定 / Ingress 有効化 / スケール最小設定)
4. 起動と URL 動作確認
5. (任意) 環境変数 `MEMO_NAME` を追加して表示変更
6. (任意) 後片付け (リソース削除)

---
### 1. Container Apps Environment を作成
1. ポータル上部検索で「Container Apps」を検索しサービスを開く
2. 「+ 作成」 > 「Container Apps」
3. タブ「基本情報」で以下を入力:
   - サブスクリプション / リソース グループ: (ご自身のもの)
   - コンテナーアプリ名 `memo-app` (重複しない任意名)
   - デプロイ元 コンテナーイメージ
   - Container Apps Environment
      - リージョン: (RG と同じ)
      - 下部の「新しい環境の作成」を選択すると画面が切り替わるので、環境名に`env-flask-memo`などを入力、その他のタブや設定はデフォルトのまま画面下部の「作成」をクリック
5. 「次へ: コンテナー」へ進む

### 2. コンテナータブ:
- イメージのソース: 「Docker Hub またはその他のレジストリ」
- イメージの種類：パブリック
- レジストリログインサーバー: `ghcr.io`
- イメージとタグ: `hatasaki/demo-web-app-flask:latest`
- 環境変数 (任意): `MEMO_NAME` を追加できます。
- その他の設定はデフォルトのまま「次へ: イングレス」へ進む

### 3. イングレスタブ:
- イングレス: 有効にチェック
- イングレス トラフィック: どこからでもトラフィックを受け入れます を選択
- イングレスタイプ: HTTP
- ターゲットポート: 5000
- その他の設定はデフォルトのまま「確認と作成」に移動し、「作成」を実行

### 4. 動作確認
1. デプロイ完了通知からリソースへ移動
2. 左メニュー「アプリケーション URL」(または概要の URL) をクリック
3. 初回アクセス時はコールドスタートで数秒かかる場合あり
4. トップページが表示されるのでメモ追加/編集/削除を試す


### よくあるハマりどころ / トラブルシュート
- 404 / 502: ポート番号が 5000 以外に設定されていないか (Flask コードは 5000)
- 502 (Cold Start 後): 数秒待って再読み込み
- アプリがまっさら: レプリカ再生成で内部 `memo.db` が初期化。永続化したい場合は Azure File / Managed Redis 等を別途検討 (本研修では対象外)
- イメージ Pull 失敗: `ghcr.io` へネットワーク到達できるか、Private なら資格情報 (PAT) 設定漏れを確認


### 補足: なぜポート 5000?
コンテナの `app.py` 末尾で `app.run(host='0.0.0.0', port=5000)` 明示。ACA Ingress は内部で `5000` を対象にリクエストを転送するため Portal 側でも揃える必要があります。

### 補足: 状態（ローカルストレージ） の扱い
SQLite ファイル `memo.db` はコンテナーのローカルストレージの書き込みレイヤに置かれるため、
- スケール 0→1 復帰
- 新リビジョン作成
- 再デプロイ
などで消える／初期化され得ます。実運用なら外部永続ストレージやマネージド DB へ移行が必要となる点を学習ポイントとして意識してください。

--
# アプリ情報

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

## 背景色の変更方法
`static/style.css` 冒頭にある `:root { --background-color: #ffffff; }` を編集します。
例:
```css
:root {
  --background-color: #f0f8ff; /* 薄い水色 */
}
```
保存後、ブラウザをリロードすると反映されます。

## ライセンス
研修用途サンプル。必要に応じて社内規約に合わせてください。


+# コードレビュー所見
+
+## 1. 環境変数がないと Settings の初期化に失敗する
+- **ファイル:** `backend/app/config.py`
+- **重大度:** 高
+- **問題:** `Settings` は `database_url` と `postgres_password` に既定値を設けずに定義していますが、クラスがすぐにインスタンス化されています（`settings = Settings()`）。プロセスが環境変数なしで起動すると、Pydantic はこれらのフィールドを必須と見なして `ValidationError` を送出し、アプリの起動を阻害します。カスタムバリデータが既定の URL を構築する前にこの問題が発生します。
+- **提案:** 安全な既定値を用意する（例: `database_url: Optional[str] = None`、`postgres_password: str = ""`）か、設定値が揃うまでインスタンス化を遅らせてください。
+
+## 2. auth ルーターでの import 漏れ
+- **ファイル:** `backend/app/routers/auth.py`
+- **重大度:** 中
+- **問題:** `/users/{user_id}` ハンドラーは `created_at` を設定するために `datetime.now()` を使用していますが、`datetime` が import されていません。そのためエンドポイントを呼び出すたびに `NameError` が発生します。
+- **提案:** `from datetime import datetime` を追加する（または共通のタイムスタンプソースを再利用する）ようにしてください。
+
+## 3. イベントループが存在する前にバックグラウンドタスクをスケジュールしている
+- **ファイル:** `backend/app/websocket_manager.py`
+- **重大度:** 高
+- **問題:** `SocketManager.__init__` が `asyncio.create_task(self._init_redis())` を呼び出しており、グローバルインスタンスが import 時に生成されています。FastAPI の起動時（または任意の同期 import 時）にはまだ実行中のイベントループがないため、`RuntimeError: no running event loop` が発生し、アプリケーションの起動が失敗します。
+- **提案:** Redis の初期化を非同期のスタートアップフック（例: FastAPI の `startup` イベント）に遅延させるか、ループが実行された後にマネージャーを注入してください。

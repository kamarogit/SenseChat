# SenseChat MVP

**家族内使用・技術検証版**

テキストの「意味」で会話が成立するかを検証するプロトタイプアプリケーション。要約＋Embeddingを送信し、受信側で意味検索＋LLM再構成を行う新しいコミュニケーション手法を実装しています。

## 🎯 プロジェクト概要

### コア体験
1. **送信者**: テキスト入力 → 要約 → Embedding化
2. **サーバー**: ベクトル＋スロットを送信
3. **受信者**: 意味検索 → LLM再構成 → スタイル反映
4. **返信**: 同フローで往復通信

### 技術検証の目的
- 意味ベース通信の実現可能性
- 日本語⇄英語の自然な変換
- ビジネス⇄カジュアルの文体適応
- ベクトル検索による学習機能

## 🚀 クイックスタート

### 前提条件
- Docker & Docker Compose
- インターネット接続（LLM API用）
- 2GB以上のメモリ

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-username/sensechat-mvp.git
cd sensechat-mvp
```

### 2. 環境設定

#### Windows (コマンドプロンプト)
```cmd
REM 環境変数ファイルの作成
copy env.example .env

REM 必要なAPIキーを設定
notepad .env
```

#### Windows (PowerShell)
```powershell
# 環境変数ファイルの作成
Copy-Item env.example .env

# 必要なAPIキーを設定
notepad .env
```

### 3. 起動

#### 自動セットアップ（推奨）
```cmd
REM Windows コマンドプロンプト
setup.bat
```

```powershell
# Windows PowerShell
.\setup.ps1
```

#### 手動起動
```cmd
REM 全サービスを起動
docker-compose up -d

REM ログ確認
docker-compose logs -f
```

### 4. アクセス
- **フロントエンド**: http://localhost:3000
- **API**: http://localhost:8000
- **API文書**: http://localhost:8000/docs

## ⚙️ 設定

### 環境変数（.env）
```bash
# LLM API設定
GOOGLE_PALM_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here  # オプション

# アプリケーション設定
APP_NAME=SenseChat MVP
DEBUG=true
LOG_LEVEL=INFO

# データベース設定（SQLite）
DATABASE_URL=sqlite:///./sensechat.db

# ユーザー設定
USERS_CONFIG=config/users.json
```

### ユーザー設定（config/users.json）
```json
{
  "users": [
    {
      "id": "user_1",
      "name": "田中太郎",
      "language": "ja",
      "style_preset": "biz_formal"
    },
    {
      "id": "user_2",
      "name": "田中花子", 
      "language": "ja",
      "style_preset": "emoji_casual"
    }
  ]
}
```

## 🏗️ アーキテクチャ

### 技術スタック
- **フロントエンド**: Next.js 14 + TypeScript + Tailwind CSS
- **バックエンド**: FastAPI + Python 3.11
- **データベース**: SQLite + FAISS
- **AI/ML**: 
  - ローカル: sentence-transformers (Embedding)
  - クラウド: Google PaLM API (LLM再構成)

### システム構成
```
┌─────────────────┐
│   Next.js       │ (Frontend)
├─────────────────┤
│   FastAPI       │ (Backend)
├─────────────────┤
│   SQLite        │ (Database)
├─────────────────┤
│   FAISS         │ (Vector DB)
├─────────────────┤
│   Google PaLM   │ (LLM API)
└─────────────────┘
```

## 📊 成功指標

- **意図一致率**: ≥ 80%
- **スロット再現率**: ≥ 95%
- **受信者編集率**: ≤ 20%
- **往復堅牢性**: ≥ 70%
- **主観UXスコア**: ≥ 4.0/5

## 💰 コスト見積もり

### 家族内使用想定
- **使用量**: 100メッセージ/日
- **Google PaLM API**: 月額約$0.6
- **OpenAI GPT-3.5-turbo**: 月額約$1.2

## 🔧 開発

### ローカル開発環境

#### Windows (コマンドプロンプト)
```cmd
REM バックエンド開発
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

REM フロントエンド開発
cd frontend
npm install
npm run dev
```

#### Windows (PowerShell)
```powershell
# バックエンド開発
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload

# フロントエンド開発
cd frontend
npm install
npm run dev
```

### テスト実行

#### Windows (コマンドプロンプト)
```cmd
REM バックエンドテスト
cd backend
pytest

REM フロントエンドテスト
cd frontend
npm test
```

#### Windows (PowerShell)
```powershell
# バックエンドテスト
cd backend
pytest

# フロントエンドテスト
cd frontend
npm test
```

### データベース管理

#### Windows (コマンドプロンプト)
```cmd
REM マイグレーション実行
cd backend
alembic upgrade head

REM データベースリセット
del sensechat.db
alembic upgrade head
```

#### Windows (PowerShell)
```powershell
# マイグレーション実行
cd backend
alembic upgrade head

# データベースリセット
Remove-Item sensechat.db
alembic upgrade head
```

## 📝 API仕様

### 主要エンドポイント

#### メッセージ作成
```bash
POST /api/v1/embed
Content-Type: application/json
X-User-ID: user_1

{
  "text": "明日の会議の件で、資料の準備をお願いします",
  "lang_hint": "ja"
}
```

#### メッセージ再構成
```bash
POST /api/v1/render
Content-Type: application/json
X-User-ID: user_2

{
  "message_id": "msg_123456789",
  "recipient_id": "user_2"
}
```

詳細なAPI仕様は [http://localhost:8000/docs](http://localhost:8000/docs) で確認できます。

## 🐛 トラブルシューティング

### よくある問題

#### 1. メモリ不足エラー
```bash
# Dockerのメモリ制限を確認
docker stats

# メモリ制限を増やす
docker-compose up -d --scale backend=1
```

#### 2. API接続エラー
```bash
# APIキーの確認
echo $GOOGLE_PALM_API_KEY

# ネットワーク接続の確認
curl -I https://generativelanguage.googleapis.com
```

#### 3. データベースエラー
```bash
# データベースファイルの権限確認
ls -la sensechat.db

# データベースの再作成
rm sensechat.db
docker-compose restart backend
```

## 📈 ロードマップ

### Phase 1: 技術検証（1-2週間）
- [x] 基本API実装
- [x] FAISS統合
- [x] 簡易UI実装
- [ ] LLM API連携
- [ ] 家族内テスト

### Phase 2: 改善・最適化（1週間）
- [ ] パフォーマンス改善
- [ ] バグ修正
- [ ] ドキュメント整備
- [ ] GitHub準備

### Phase 3: 本格版開発（将来）
- [ ] 検証成功時: 本格版をGitHubで公開
- [ ] 機能拡張: 仲介UI・文体拡張・音声対応

## 🤝 貢献

このプロジェクトは技術検証目的のため、現在はプライベートリポジトリです。

検証成功後、本格版をオープンソースとして公開予定です。

## 📄 ライセンス

MIT License

## 📞 サポート

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: your-email@example.com

---

**注意**: このプロジェクトは技術検証目的です。本格運用には追加のセキュリティ対策とスケーラビリティの検討が必要です。
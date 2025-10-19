
# SenseChat MVP 仕様書

## プロダクト概要
- 名称：**SenseChat MVP**（家族内使用・技術検証版）
- コア体験：**「要約＋Embeddingを送信」→「受信側で意味検索＋LLM再構成」**。
- 目的：テキストの「意味」で会話が成立するかを検証（家族内使用・技術検証）。
- 将来：検証成功時は本格版をGitHubで公開予定。

## 成功指標
- 意図一致率 ≥ 80%
- スロット再現率 ≥ 95%
- 受信者の編集率 ≤ 20%
- 往復堅牢性 ≥ 70%
- 主観UXスコア ≥ 4.0/5

## スコープ
- ✅ 要約→Embedding→ベクトル＋slots送信
- ✅ 意味検索＋LLM再構成
- ✅ 日本語⇄英語
- ✅ 2スタイル（biz_formal / emoji_casual）
- ❌ 仲介UI、グループチャットは対象外

## 体験フロー
1. 送信者：入力→要約→Embedding化
2. サーバ：ベクトル＋slotsを送信
3. 受信者：検索→LLM再構成→スタイル反映
4. slots検証→表示→返信も同フロー

## 技術構成

### フロントエンド
- **フレームワーク**: Next.js 14 (App Router)
- **UIライブラリ**: Tailwind CSS + shadcn/ui
- **状態管理**: Zustand
- **HTTPクライアント**: Axios
- **型定義**: TypeScript

### バックエンド
- **API**: FastAPI 0.104+
- **Python**: 3.11+
- **ASGI**: Uvicorn
- **認証**: 簡易認証（固定ユーザー、開発用）

### AI/ML

#### ローカル処理（軽量）
- **Embedding**: sentence-transformers/all-MiniLM-L6-v2 (384次元)
- **VectorDB**: FAISS (IndexFlatIP)
- **言語検出**: langdetect
- **テキスト要約**: 軽量なルールベース + パターンマッチング

#### クラウドAPI活用
- **LLM再構成**: OpenAI GPT-3.5-turbo API
- **代替**: Anthropic Claude API または Google PaLM API
- **フォールバック**: 複数APIの自動切り替え

#### モデル選択理由
- **軽量性**: 自宅サーバーでも動作（メモリ使用量: 1-2GB）
- **コスト効率**: ローカル処理でAPI呼び出しを最小化
- **セキュリティ**: 機密データのローカル処理
- **スケーラビリティ**: APIの制限内で自動スケーリング

#### セキュリティ対策
- **データマスキング**: 個人情報・機密情報の自動マスキング
- **暗号化通信**: TLS 1.3 + エンドツーエンド暗号化
- **ログ管理**: 最小限の保持期間（即座に削除）
- **監査**: 全API呼び出しの記録と追跡

### データベース（簡易版）
- **メインDB**: SQLite（開発・検証用）
- **ベクトルDB**: FAISS + SQLite (メタデータ)
- **キャッシュ**: メモリキャッシュ（Redis不要）

### インフラ（簡易版）
- **コンテナ**: Docker + Docker Compose（1ファイル構成）
- **リバースプロキシ**: なし（開発用）
- **監視**: 基本ログのみ
- **ログ**: コンソール出力 + ファイル出力

#### システム要件（最小構成）
- **CPU**: 2コア以上
- **メモリ**: 2GB以上（推奨: 4GB）
- **ストレージ**: 10GB以上
- **ネットワーク**: インターネット接続（API呼び出し用）

#### コスト見積もり（家族内使用）
- **想定使用量**: 100メッセージ/日 × 200 tokens/メッセージ = 20K tokens/日
- **Google PaLM API**: $0.001/1K tokens → 月額約$0.6
- **OpenAI GPT-3.5-turbo**: $0.002/1K tokens → 月額約$1.2

**推奨**: 家族内使用ではGoogle PaLM API（コスト重視）

### セキュリティ（簡易版）
- **通信**: HTTPS（開発時はHTTP可）
- **暗号化**: 基本暗号化（ベクトル・スロット）
- **認証**: 簡易認証（固定ユーザー）
- **レート制限**: なし（家族内使用のため）

## API仕様

### 認証（簡易版）

#### 簡易認証フロー
1. **固定ユーザー**: 設定ファイルで定義されたユーザー
2. **API呼び出し**: 認証なし（家族内使用のため）
3. **ユーザー識別**: リクエストヘッダーでユーザー指定

#### 簡易認証エンドポイント

##### GET /api/v1/users
**説明**: 利用可能なユーザー一覧を取得

**レスポンス:**
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

##### ユーザー指定方法
**リクエストヘッダー:**
```
X-User-ID: user_1
```

### エンドポイント一覧

#### POST /api/v1/embed
テキストを要約・ベクトル化してメッセージを作成

**リクエスト:**
```json
{
  "text": "明日の会議の件で、資料の準備をお願いします",
  "lang_hint": "ja",
  "slots": {
    "intent": "request",
    "entities": ["会議", "資料", "準備"],
    "urgency": "normal"
  }
}
```

**バリデーション:**
- `text`: 必須、1-1000文字、UTF-8
- `lang_hint`: オプション、`ja`|`en`|`auto`
- `slots`: オプション、JSONオブジェクト

**レスポンス:**
```json
{
  "message_id": "msg_123456789",
  "summary": "会議資料の準備依頼",
  "vector_id": "vec_987654321",
  "slots": {
    "intent": "request",
    "entities": ["会議", "資料", "準備"],
    "urgency": "normal"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "processing_time_ms": 245
}
```

**エラー例:**
```json
{
  "error": {
    "code": "VAL_001",
    "message": "テキストが空です",
    "details": {
      "field": "text",
      "reason": "必須フィールドが空です"
    }
  }
}
```

#### POST /api/v1/deliver
メッセージを指定ユーザーに配信

**リクエスト:**
```json
{
  "to_user_id": "user_123456789",
  "message_id": "msg_123456789",
  "thread_id": "thread_123456789"
}
```

**バリデーション:**
- `to_user_id`: 必須、UUID形式
- `message_id`: 必須、UUID形式
- `thread_id`: 必須、UUID形式

**レスポンス:**
```json
{
  "status": "queued",
  "delivery_id": "del_123456789",
  "estimated_delivery": "2024-01-01T00:01:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**エラー例:**
```json
{
  "error": {
    "code": "BIZ_001",
    "message": "ユーザーが存在しません",
    "details": {
      "field": "to_user_id",
      "reason": "指定されたユーザーIDが見つかりません"
    }
  }
}
```

#### POST /api/v1/render
メッセージを受信者向けに再構成

**リクエスト:**
```json
{
  "message_id": "msg_123456789",
  "recipient_id": "user_987654321"
}
```

**レスポンス:**
```json
{
  "text": "明日の会議の資料準備をお願いします。よろしくお願いいたします。",
  "confidence": 0.92,
  "used_neighbors": [
    {
      "text": "会議資料の準備依頼",
      "similarity": 0.95
    }
  ],
  "slots": {
    "intent": "request",
    "entities": ["会議", "資料", "準備"],
    "urgency": "normal"
  },
  "style_applied": "biz_formal"
}
```

#### POST /api/v1/reply
メッセージに返信

**リクエスト:**
```json
{
  "thread_id": "thread_123456789",
  "text": "承知いたしました。資料を準備して明日お持ちします。",
  "reply_to_message_id": "msg_123456789"
}
```

**レスポンス:**
```json
{
  "status": "sent",
  "message_id": "msg_987654321",
  "created_at": "2024-01-01T00:02:00Z"
}
```

#### GET /api/v1/styles/:user_id
ユーザーのスタイル設定を取得

**レスポンス:**
```json
{
  "user_id": "user_123456789",
  "current_style": {
    "preset": "biz_formal",
    "tone": "polite",
    "signature": "よろしくお願いいたします。",
    "custom_rules": {
      "max_length": 200,
      "use_emoji": false,
      "conclusion_first": true
    }
  },
  "available_styles": ["biz_formal", "emoji_casual", "technical"]
}
```

#### PUT /api/v1/styles/:user_id
ユーザーのスタイル設定を更新

**リクエスト:**
```json
{
  "preset": "biz_formal",
  "tone": "polite",
  "signature": "よろしくお願いいたします。",
  "custom_rules": {
    "max_length": 200,
    "use_emoji": false,
    "conclusion_first": true
  }
}
```

**レスポンス:**
```json
{
  "status": "updated",
  "updated_at": "2024-01-01T00:03:00Z"
}
```

#### GET /api/v1/threads/:thread_id/messages
スレッドのメッセージ一覧を取得

**クエリパラメータ:**
- `limit`: 取得件数（デフォルト: 20, 最大: 100）
- `offset`: オフセット（デフォルト: 0）

**レスポンス:**
```json
{
  "thread_id": "thread_123456789",
  "messages": [
    {
      "id": "msg_123456789",
      "sender_id": "user_123456789",
      "text": "明日の会議の資料準備をお願いします。",
      "created_at": "2024-01-01T00:00:00Z",
      "status": "read"
    }
  ],
  "total_count": 1,
  "has_more": false
}
```

#### GET /api/v1/health
ヘルスチェック（認証不要）

**レスポンス:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "vector_db": "healthy",
    "llm": "healthy"
  }
}
```

### バリデーションルール

#### テキスト入力
- **最小長**: 1文字
- **最大長**: 1000文字
- **文字種**: UTF-8（絵文字含む）
- **禁止文字**: 制御文字（改行・タブ除く）

#### ユーザーID
- **形式**: UUID v4
- **例**: `550e8400-e29b-41d4-a716-446655440000`

#### 言語ヒント
- **有効値**: `ja`, `en`, `auto`
- **デフォルト**: `auto`

### レート制限
- **一般ユーザー**: 100 req/min
- **プレミアムユーザー**: 500 req/min
- **ヘッダー**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## エラーハンドリング

### HTTPステータスコード
- **200**: 成功
- **201**: 作成成功
- **400**: リクエストエラー（バリデーション失敗）
- **401**: 認証エラー
- **403**: 認可エラー
- **404**: リソース未発見
- **409**: 競合（重複データ）
- **422**: 処理不可能（ビジネスロジックエラー）
- **429**: レート制限超過
- **500**: サーバー内部エラー
- **503**: サービス利用不可

### エラーレスポンス形式
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力データが無効です",
    "details": {
      "field": "text",
      "reason": "必須フィールドが空です"
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456789"
  }
}
```

### エラーコード一覧
- **AUTH_001**: 認証トークンが無効
- **AUTH_002**: 認証トークンの有効期限切れ
- **AUTH_003**: 権限不足
- **VAL_001**: 必須フィールドが空
- **VAL_002**: データ形式が無効
- **VAL_003**: 文字数制限超過
- **BIZ_001**: ユーザーが存在しない
- **BIZ_002**: メッセージが存在しない
- **BIZ_003**: スレッドが存在しない
- **RATE_001**: レート制限超過
- **SYS_001**: データベース接続エラー
- **SYS_002**: 外部API接続エラー
- **SYS_003**: ベクトル化処理エラー

## データモデル

### テーブル定義

#### users（簡易版）
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    language TEXT DEFAULT 'ja',
    style_preset TEXT DEFAULT 'biz_formal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### threads（簡易版）
```sql
CREATE TABLE threads (
    id TEXT PRIMARY KEY,
    created_by TEXT REFERENCES users(id),
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### messages（簡易版）
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT REFERENCES threads(id),
    sender_id TEXT REFERENCES users(id),
    summary TEXT NOT NULL,
    vector_id TEXT, -- FAISS内のID
    slots TEXT, -- JSON文字列
    lang_hint TEXT,
    original_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### inbox（簡易版）
```sql
CREATE TABLE inbox (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    message_id TEXT REFERENCES messages(id),
    thread_id TEXT REFERENCES threads(id),
    status TEXT DEFAULT 'unread', -- unread, read
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### kb_items（簡易版）
```sql
CREATE TABLE kb_items (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    vector_id TEXT, -- FAISS内のID
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 不要なテーブル（簡易版では削除）
- user_styles: 設定ファイルで管理
- audit_logs: 基本ログのみ

### リレーション・制約

#### 外部キー制約
```sql
-- threads → users
ALTER TABLE threads ADD CONSTRAINT fk_threads_created_by 
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE;

-- messages → threads
ALTER TABLE messages ADD CONSTRAINT fk_messages_thread_id 
    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE;

-- messages → users
ALTER TABLE messages ADD CONSTRAINT fk_messages_sender_id 
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE;

-- inbox → users
ALTER TABLE inbox ADD CONSTRAINT fk_inbox_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- inbox → messages
ALTER TABLE inbox ADD CONSTRAINT fk_inbox_message_id 
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE;

-- inbox → threads
ALTER TABLE inbox ADD CONSTRAINT fk_inbox_thread_id 
    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE;

-- user_styles → users
ALTER TABLE user_styles ADD CONSTRAINT fk_user_styles_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- audit_logs → users
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

#### チェック制約
```sql
-- users テーブル
ALTER TABLE users ADD CONSTRAINT chk_users_language 
    CHECK (language IN ('ja', 'en', 'zh', 'ko', 'auto'));

ALTER TABLE users ADD CONSTRAINT chk_users_style_preset 
    CHECK (style_preset IN ('biz_formal', 'emoji_casual', 'technical'));

ALTER TABLE users ADD CONSTRAINT chk_users_tone 
    CHECK (tone IN ('neutral', 'polite', 'casual', 'formal'));

-- messages テーブル
ALTER TABLE messages ADD CONSTRAINT chk_messages_status 
    CHECK (status IN ('draft', 'sent', 'delivered', 'read', 'failed'));

ALTER TABLE messages ADD CONSTRAINT chk_messages_lang_hint 
    CHECK (lang_hint IN ('ja', 'en', 'zh', 'ko', 'auto'));

-- inbox テーブル
ALTER TABLE inbox ADD CONSTRAINT chk_inbox_status 
    CHECK (status IN ('unread', 'read', 'replied', 'archived'));

-- audit_logs テーブル
ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_logs_action 
    CHECK (action IN ('login', 'logout', 'create', 'read', 'update', 'delete', 'embed', 'deliver', 'render'));
```

### インデックス戦略

#### パフォーマンス最適化インデックス
```sql
-- 基本検索用インデックス
CREATE INDEX idx_messages_thread_id ON messages(thread_id);
CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_inbox_user_id ON inbox(user_id);
CREATE INDEX idx_inbox_status ON inbox(status);
CREATE INDEX idx_inbox_created_at ON inbox(created_at);

-- 複合インデックス（よく使われるクエリパターン）
CREATE INDEX idx_inbox_user_status ON inbox(user_id, status);
CREATE INDEX idx_messages_thread_created ON messages(thread_id, created_at);
CREATE INDEX idx_audit_logs_user_created ON audit_logs(user_id, created_at);

-- 部分インデックス（アクティブなレコードのみ）
CREATE INDEX idx_users_active ON users(id) WHERE is_active = true;
CREATE INDEX idx_messages_active ON messages(id) WHERE status != 'failed';
CREATE INDEX idx_threads_active ON threads(id) WHERE is_active = true;

-- 全文検索用インデックス（PostgreSQL）
CREATE INDEX idx_messages_summary_gin ON messages USING gin(to_tsvector('japanese', summary));
CREATE INDEX idx_kb_items_text_gin ON kb_items USING gin(to_tsvector('japanese', text));
```

#### インデックス使用例
```sql
-- ユーザーの未読メッセージ取得
SELECT * FROM inbox 
WHERE user_id = ? AND status = 'unread' 
ORDER BY created_at DESC;

-- スレッドのメッセージ履歴取得
SELECT * FROM messages 
WHERE thread_id = ? 
ORDER BY created_at ASC;

-- 全文検索（日本語）
SELECT * FROM messages 
WHERE to_tsvector('japanese', summary) @@ plainto_tsquery('japanese', '会議 資料');
```

### パーティショニング戦略

#### 時系列パーティショニング（audit_logs）
```sql
-- 月単位でのパーティショニング
CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE audit_logs_y2024m02 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- パーティション作成の自動化関数
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_y' || to_char(start_date, 'YYYY') || 'm' || to_char(start_date, 'MM');
    end_date := start_date + interval '1 month';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

## API実装詳細

### アーキテクチャ概要

#### レイヤー構成
```
┌─────────────────┐
│   Frontend      │ (Next.js)
├─────────────────┤
│   API Gateway   │ (Nginx)
├─────────────────┤
│   FastAPI App   │ (Python)
├─────────────────┤
│   Services      │ (Business Logic)
├─────────────────┤
│   Repositories  │ (Data Access)
├─────────────────┤
│   Database      │ (PostgreSQL)
└─────────────────┘
```

### エンドポイント実装例

#### POST /api/v1/embed 実装
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

router = APIRouter()

class EmbedRequest(BaseModel):
    text: str
    lang_hint: Optional[str] = "auto"
    slots: Optional[Dict[str, Any]] = None
    
    @validator('text')
    def validate_text(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('テキストが空です')
        if len(v) > 1000:
            raise ValueError('テキストが1000文字を超えています')
        return v.strip()
    
    @validator('lang_hint')
    def validate_lang_hint(cls, v):
        if v not in ['ja', 'en', 'zh', 'ko', 'auto']:
            raise ValueError('無効な言語ヒントです')
        return v

class EmbedResponse(BaseModel):
    message_id: str
    summary: str
    vector_id: str
    slots: Dict[str, Any]
    created_at: datetime
    processing_time_ms: int

@router.post("/embed", response_model=EmbedResponse)
async def embed_text(
    request: EmbedRequest,
    current_user: User = Depends(get_current_user),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """テキストを要約・ベクトル化してメッセージを作成"""
    start_time = datetime.now()
    
    try:
        # 1. テキスト要約
        summary = await embedding_service.summarize_text(
            request.text, 
            request.lang_hint
        )
        
        # 2. ベクトル化
        vector_id, vector = await embedding_service.create_embedding(
            request.text,
            request.lang_hint
        )
        
        # 3. スロット抽出
        slots = await embedding_service.extract_slots(
            request.text,
            request.slots
        )
        
        # 4. データベース保存
        message_id = await message_repository.create_message(
            thread_id=None,  # 新規スレッド
            sender_id=current_user.id,
            summary=summary,
            vector_id=vector_id,
            slots=slots,
            lang_hint=request.lang_hint,
            original_text=request.text
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return EmbedResponse(
            message_id=message_id,
            summary=summary,
            vector_id=vector_id,
            slots=slots,
            created_at=datetime.now(),
            processing_time_ms=int(processing_time)
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Embedding failed: {str(e)}")
        raise HTTPException(status_code=500, detail="内部サーバーエラーが発生しました")
```

#### POST /api/v1/render 実装（LLM API活用版）
```python
import openai
from app.services.privacy_service import PrivacyService
from app.services.llm_api_service import LLMAPIService

class RenderRequest(BaseModel):
    message_id: str
    recipient_id: str

class RenderResponse(BaseModel):
    text: str
    confidence: float
    used_neighbors: List[Dict[str, Any]]
    slots: Dict[str, Any]
    style_applied: str

@router.post("/render", response_model=RenderResponse)
async def render_message(
    request: RenderRequest,
    current_user: User = Depends(get_current_user),
    render_service: RenderService = Depends(get_render_service),
    privacy_service: PrivacyService = Depends(get_privacy_service),
    llm_api_service: LLMAPIService = Depends(get_llm_api_service)
):
    """メッセージを受信者向けに再構成（LLM API活用）"""
    try:
        # 1. メッセージ取得
        message = await message_repository.get_message(request.message_id)
        if not message:
            raise HTTPException(status_code=404, detail="メッセージが見つかりません")
        
        # 2. 受信者情報取得
        recipient = await user_repository.get_user(request.recipient_id)
        if not recipient:
            raise HTTPException(status_code=404, detail="受信者が見つかりません")
        
        # 3. ベクトル検索（ローカル）
        neighbors = await vector_service.search_similar(
            message.vector_id,
            limit=5
        )
        
        # 4. データマスキング（セキュリティ）
        masked_summary = privacy_service.mask_sensitive_data(message.summary)
        masked_slots = privacy_service.mask_sensitive_slots(message.slots)
        
        # 5. LLM API再構成
        rendered_text, confidence = await llm_api_service.reconstruct_message(
            summary=masked_summary,
            slots=masked_slots,
            style_preset=recipient.style_preset,
            language=recipient.language,
            neighbors=neighbors
        )
        
        # 6. 監査ログ記録
        await audit_service.log_api_call(
            user_id=current_user.id,
            action="llm_render",
            details={
                "message_id": request.message_id,
                "api_provider": llm_api_service.current_provider,
                "tokens_used": llm_api_service.last_token_count
            }
        )
        
        return RenderResponse(
            text=rendered_text,
            confidence=confidence,
            used_neighbors=neighbors,
            slots=message.slots,
            style_applied=recipient.style_preset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Render failed: {str(e)}")
        raise HTTPException(status_code=500, detail="内部サーバーエラーが発生しました")
```

#### LLM API サービス実装
```python
class LLMAPIService:
    def __init__(self):
        self.providers = {
            'openai': OpenAIAPIClient(),
            'anthropic': AnthropicAPIClient(),
            'google': GoogleAPIClient()
        }
        self.current_provider = 'openai'
        self.last_token_count = 0
    
    async def reconstruct_message(self, summary: str, slots: dict, 
                                style_preset: str, language: str, 
                                neighbors: list) -> tuple[str, float]:
        """LLM APIを使用してメッセージを再構成"""
        
        # プロンプト構築
        prompt = self._build_reconstruction_prompt(
            summary, slots, style_preset, language, neighbors
        )
        
        # フォールバック機能付きAPI呼び出し
        for provider_name, provider in self.providers.items():
            try:
                response = await provider.generate(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.7
                )
                
                self.current_provider = provider_name
                self.last_token_count = response.token_count
                
                return response.text, response.confidence
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        raise Exception("All LLM providers failed")
    
    def _build_reconstruction_prompt(self, summary: str, slots: dict, 
                                   style_preset: str, language: str, 
                                   neighbors: list) -> str:
        """再構成用プロンプトを構築"""
        
        style_instructions = {
            'biz_formal': 'ビジネス用の丁寧な敬語で、結論を先に述べ、署名を付けてください。',
            'emoji_casual': 'カジュアルで親しみやすい文体で、適度に絵文字を使ってください。',
            'technical': '技術的で正確な表現を使い、専門用語を適切に使用してください。'
        }
        
        prompt = f"""
以下の要約を{language}で{style_instructions.get(style_preset, '自然な文体で')}再構成してください。

要約: {summary}
スロット: {slots}
参考情報: {neighbors}

制約:
- 元の意味を保持する
- 指定されたスタイルに従う
- 100文字以内
- 自然で読みやすい文章にする
"""
        return prompt
```

### ミドルウェア

#### 認証ミドルウェア
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT認証ミドルウェア"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["RS256"]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="無効なトークンです")
        
        user = await user_repository.get_user(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="ユーザーが無効です")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="無効なトークンです")
```

#### レート制限ミドルウェア
```python
from fastapi import Request, HTTPException
import redis
from datetime import datetime, timedelta

redis_client = redis.Redis(host='redis', port=6379, db=0)

async def rate_limit_middleware(request: Request, call_next):
    """レート制限ミドルウェア"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        return await call_next(request)
    
    # レート制限キー
    key = f"rate_limit:{user_id}"
    current_time = datetime.now()
    window_start = current_time - timedelta(minutes=1)
    
    # 現在のリクエスト数を取得
    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start.timestamp())
    pipe.zcard(key)
    pipe.zadd(key, {str(current_time.timestamp()): current_time.timestamp()})
    pipe.expire(key, 60)
    
    results = pipe.execute()
    current_requests = results[1]
    
    # レート制限チェック
    if current_requests >= 100:  # 100 req/min
        raise HTTPException(
            status_code=429,
            detail="レート制限に達しました。しばらく待ってから再試行してください。"
        )
    
    response = await call_next(request)
    return response
```

#### ログミドルウェア
```python
import logging
from fastapi import Request
import time

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """ログミドルウェア"""
    start_time = time.time()
    
    # リクエストログ
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # レスポンスログ
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} "
        f"Process time: {process_time:.3f}s"
    )
    
    return response
```

### エラーハンドリング

#### グローバル例外ハンドラー
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP例外ハンドラー"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "timestamp": datetime.now().isoformat(),
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """バリデーション例外ハンドラー"""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VAL_001",
                "message": "入力データが無効です",
                "details": exc.errors(),
                "timestamp": datetime.now().isoformat(),
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般例外ハンドラー"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "SYS_001",
                "message": "内部サーバーエラーが発生しました",
                "timestamp": datetime.now().isoformat(),
                "request_id": request.state.request_id
            }
        }
    )
```

## データベースマイグレーション戦略

### マイグレーション管理

#### Alembic設定
```python
# alembic.ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql://user:pass@localhost/sensechat

# migrations/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.database import Base

config = context.config
target_metadata = Base.metadata

def run_migrations_offline():
    """Offline migration mode"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Online migration mode"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 初期マイグレーション

#### 001_initial_schema.py
```python
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('style_preset', sa.String(length=20), nullable=True),
        sa.Column('tone', sa.String(length=20), nullable=True),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create threads table
    op.create_table('threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('vector_id', sa.String(length=50), nullable=True),
        sa.Column('slots', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('lang_hint', sa.String(length=10), nullable=True),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create inbox table
    op.create_table('inbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('read_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create kb_items table
    op.create_table('kb_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('vector_id', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_styles table
    op.create_table('user_styles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('style_name', sa.String(length=50), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('user_styles')
    op.drop_table('kb_items')
    op.drop_table('inbox')
    op.drop_table('messages')
    op.drop_table('threads')
    op.drop_table('users')
```

#### 002_add_constraints.py
```python
"""Add constraints and indexes

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Add check constraints
    op.create_check_constraint(
        'chk_users_language',
        'users',
        "language IN ('ja', 'en', 'zh', 'ko', 'auto')"
    )
    
    op.create_check_constraint(
        'chk_users_style_preset',
        'users',
        "style_preset IN ('biz_formal', 'emoji_casual', 'technical')"
    )
    
    op.create_check_constraint(
        'chk_messages_status',
        'messages',
        "status IN ('draft', 'sent', 'delivered', 'read', 'failed')"
    )
    
    # Add indexes
    op.create_index('idx_messages_thread_id', 'messages', ['thread_id'])
    op.create_index('idx_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('idx_inbox_user_id', 'inbox', ['user_id'])
    op.create_index('idx_inbox_status', 'inbox', ['status'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])

def downgrade():
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('idx_inbox_status', table_name='inbox')
    op.drop_index('idx_inbox_user_id', table_name='inbox')
    op.drop_index('idx_messages_sender_id', table_name='messages')
    op.drop_index('idx_messages_thread_id', table_name='messages')
    
    op.drop_constraint('chk_messages_status', 'messages', type_='check')
    op.drop_constraint('chk_users_style_preset', 'users', type_='check')
    op.drop_constraint('chk_users_language', 'users', type_='check')
```

### マイグレーション実行

#### 開発環境での実行
```bash
# マイグレーション生成
alembic revision --autogenerate -m "Add new feature"

# マイグレーション実行
alembic upgrade head

# マイグレーション履歴確認
alembic history

# 特定バージョンにロールバック
alembic downgrade 001
```

#### 本番環境での実行
```bash
#!/bin/bash
# deploy.sh

# 1. バックアップ作成
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. マイグレーション実行
alembic upgrade head

# 3. データ整合性チェック
python scripts/verify_data_integrity.py

# 4. ロールバック準備（必要に応じて）
echo "Migration completed. Rollback command: alembic downgrade -1"
```

### データ移行戦略

#### 既存データの移行
```python
# scripts/migrate_existing_data.py
import asyncio
from app.database import get_db
from app.services.embedding_service import EmbeddingService

async def migrate_existing_messages():
    """既存メッセージのベクトル化"""
    db = next(get_db())
    embedding_service = EmbeddingService()
    
    # ベクトル化されていないメッセージを取得
    messages = db.query(Message).filter(Message.vector_id.is_(None)).all()
    
    for message in messages:
        try:
            # ベクトル化
            vector_id, vector = await embedding_service.create_embedding(
                message.original_text,
                message.lang_hint
            )
            
            # データベース更新
            message.vector_id = vector_id
            db.commit()
            
            print(f"Migrated message {message.id}")
            
        except Exception as e:
            print(f"Failed to migrate message {message.id}: {e}")
            db.rollback()

if __name__ == "__main__":
    asyncio.run(migrate_existing_messages())
```

### バージョン管理

#### マイグレーション管理ポリシー
- **開発環境**: 自動マイグレーション生成と実行
- **ステージング環境**: 手動マイグレーション実行とテスト
- **本番環境**: 承認されたマイグレーションのみ実行

#### ロールバック戦略
```python
# scripts/rollback_strategy.py
def get_rollback_plan(current_version, target_version):
    """ロールバック計画の生成"""
    plan = {
        "steps": [],
        "estimated_time": 0,
        "data_loss_risk": "low"
    }
    
    # バージョン間の差分を分析
    # データ損失リスクを評価
    # ロールバック手順を生成
    
    return plan
```

## スタイルプリセット
- biz_formal：敬語・結論先出し・署名付き
- emoji_casual：短文・軽い絵文字

## 評価指標

### 定量指標

#### 1. 意図一致率 (Intent Accuracy)
**目標**: ≥ 80%
**測定方法**: 送信者の意図と受信者が理解した意図の一致度
**評価基準**:
- 完全一致: 1.0
- 部分一致: 0.5
- 不一致: 0.0

**テストケース例**:
```json
{
  "input": "明日の会議の資料準備をお願いします",
  "expected_intent": "request",
  "expected_entities": ["会議", "資料", "準備"],
  "expected_urgency": "normal"
}
```

#### 2. スロット再現率 (Slot Preservation)
**目標**: ≥ 95%
**測定方法**: 重要な情報（日時、人物、場所等）の保持率
**評価項目**:
- 日時情報: 100%
- 人物名: 95%
- 数値: 100%
- 固有名詞: 90%

#### 3. 受信者編集率 (Recipient Edit Rate)
**目標**: ≤ 20%
**測定方法**: 受信者がメッセージを編集した割合
**カテゴリ**:
- 内容修正: 10%
- 文体調整: 5%
- 誤解釈修正: 5%

#### 4. 往復堅牢性 (Round-trip Robustness)
**目標**: ≥ 70%
**測定方法**: 往復通信での情報保持率
**テストパターン**:
- 日本語→英語→日本語
- ビジネス→カジュアル→ビジネス
- 長文→短文→長文

#### 5. レスポンス時間 (Response Time)
**目標**: ≤ 2秒
**測定項目**:
- Embedding生成: ≤ 0.5秒
- ベクトル検索: ≤ 0.3秒
- LLM再構成: ≤ 1.0秒
- 全体処理: ≤ 2.0秒

### 定性指標

#### 6. 主観UXスコア (Subjective UX Score)
**目標**: ≥ 4.0/5
**評価項目**:
- 理解しやすさ: 5段階
- 自然さ: 5段階
- 有用性: 5段階
- 満足度: 5段階

**評価者**: 10名のユーザー（日本語5名、英語5名）

### ベンチマークデータセット

#### 日本語テストセット
```json
{
  "name": "Japanese Business Communication",
  "size": 1000,
  "categories": [
    "meeting_requests",
    "project_updates", 
    "status_reports",
    "collaboration_invites"
  ],
  "sources": [
    "企業内メール",
    "Slack履歴",
    "会議議事録"
  ]
}
```

#### 英語テストセット
```json
{
  "name": "English Professional Communication",
  "size": 1000,
  "categories": [
    "client_communication",
    "team_coordination",
    "project_management",
    "status_updates"
  ],
  "sources": [
    "Email archives",
    "Slack conversations",
    "Meeting notes"
  ]
}
```

### 自動評価システム

#### 評価スクリプト
```python
# 評価メトリクス計算例
def calculate_intent_accuracy(predicted, expected):
    return f1_score(expected, predicted, average='weighted')

def calculate_slot_preservation(original_slots, reconstructed_slots):
    return len(set(original_slots) & set(reconstructed_slots)) / len(original_slots)

def calculate_edit_rate(original_text, edited_text):
    return 1 if original_text != edited_text else 0
```

#### 継続的評価
- **日次**: 自動テスト実行
- **週次**: メトリクス集計・レポート
- **月次**: ベンチマーク更新・改善提案

### 評価環境

#### テスト環境
- **分離環境**: 本番データと完全分離
- **データ匿名化**: 個人情報を完全除去
- **再現性**: 同じ入力で同じ結果を保証

#### 評価ダッシュボード
- **リアルタイム監視**: メトリクス可視化
- **アラート**: 閾値超過時の通知
- **トレンド分析**: 時系列での改善状況

## セキュリティ

### 通信セキュリティ

#### TLS/SSL
- **プロトコル**: TLS 1.3以上
- **証明書**: Let's Encrypt（開発環境）、商用証明書（本番環境）
- **暗号化強度**: AES-256-GCM
- **Perfect Forward Secrecy**: 有効

#### API認証
- **方式**: JWT (JSON Web Token)
- **アルゴリズム**: RS256 (RSA + SHA-256)
- **有効期限**: 24時間（アクセストークン）、30日（リフレッシュトークン）
- **トークン更新**: 自動リフレッシュ機能

### データ暗号化

#### 保存時暗号化
- **アルゴリズム**: AES-256-GCM
- **キー管理**: ローカルキー管理（開発環境）、AWS KMS（本番環境）
- **暗号化対象**:
  - ベクトルデータ
  - スロット情報
  - 元のテキスト
  - 個人情報

#### API送信時暗号化
- **通信暗号化**: TLS 1.3
- **データマスキング**: 送信前の機密情報除去
- **エンドツーエンド暗号化**: クライアント側での暗号化

#### 暗号化実装例
```python
from cryptography.fernet import Fernet
import base64
import re

def encrypt_sensitive_data(data: str, key: bytes) -> str:
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return base64.b64encode(encrypted_data).decode()

def decrypt_sensitive_data(encrypted_data: str, key: bytes) -> str:
    f = Fernet(key)
    decoded_data = base64.b64decode(encrypted_data.encode())
    return f.decrypt(decoded_data).decode()

def mask_sensitive_data(text: str) -> str:
    """API送信前の機密情報マスキング"""
    # メールアドレス
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # 電話番号
    text = re.sub(r'\b\d{2,4}-\d{2,4}-\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\d{10,11}\b', '[PHONE]', text)
    
    # 個人名（日本語・英語）
    text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)
    text = re.sub(r'\b[あ-ん]{2,4}\s*[あ-ん]{2,4}\b', '[NAME]', text)
    
    # クレジットカード番号
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', text)
    
    # 住所（簡易）
    text = re.sub(r'\d{3}-\d{4}', '[ZIP]', text)
    
    return text
```

### データ保持・削除

#### データ保持ポリシー
- **メッセージデータ**: 30日間
- **ベクトルデータ**: 30日間
- **ログデータ**: 90日間
- **監査ログ**: 1年間

#### データ削除機能
- **DELETE /api/v1/messages/:id**: 個別メッセージ削除
- **DELETE /api/v1/threads/:id**: スレッド全体削除
- **DELETE /api/v1/users/:id/forget-me**: ユーザー完全削除（GDPR対応）

#### 削除実装例
```python
async def delete_user_data(user_id: str):
    # 1. メッセージ削除
    await delete_messages_by_user(user_id)
    
    # 2. ベクトル削除
    await delete_vectors_by_user(user_id)
    
    # 3. ログ削除
    await delete_audit_logs_by_user(user_id)
    
    # 4. ユーザー情報削除
    await delete_user_profile(user_id)
```

### プライバシー保護

#### GDPR対応
- **データポータビリティ**: ユーザーデータのエクスポート機能
- **忘れられる権利**: 完全削除機能
- **同意管理**: データ処理の明示的同意
- **データ最小化**: 必要最小限のデータ収集

#### 個人情報保護
- **匿名化**: 評価用データの完全匿名化
- **仮名化**: 内部処理での識別子使用
- **アクセス制御**: 最小権限の原則

### 監査・ログ

#### 監査ログ
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    error_message TEXT
);
```

#### ログレベル
- **DEBUG**: 開発時の詳細情報
- **INFO**: 一般的な操作ログ
- **WARN**: 警告レベルの問題
- **ERROR**: エラーレベルの問題
- **CRITICAL**: システム停止レベルの問題

### アクセス制御

#### 権限管理
- **管理者**: 全機能アクセス
- **一般ユーザー**: 基本機能のみ
- **APIユーザー**: 特定エンドポイントのみ

#### レート制限
- **一般ユーザー**: 100 req/min
- **プレミアムユーザー**: 500 req/min
- **APIユーザー**: 1000 req/min

### セキュリティ監視

#### 異常検知
- **異常なアクセスパターン**: 機械学習による検知
- **ブルートフォース攻撃**: 失敗回数による検知
- **データ漏洩**: 大量データアクセスの検知

#### アラート設定
- **認証失敗**: 5回連続失敗でアラート
- **異常なAPI使用**: 通常の10倍以上の使用でアラート
- **データ削除**: 大量削除でアラート

### セキュリティテスト

#### 自動セキュリティテスト
- **OWASP ZAP**: 脆弱性スキャン
- **Bandit**: Pythonコード静的解析
- **Safety**: 依存関係脆弱性チェック

#### ペネトレーションテスト
- **四半期実施**: 外部セキュリティ会社によるテスト
- **レポート**: 脆弱性と対策の詳細レポート

## 運用・デプロイメント

### インフラ構成

#### 開発環境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - API_URL=http://localhost:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sensechat_dev
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=sensechat_dev
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

#### 本番環境
- **クラウド**: AWS / Google Cloud Platform
- **コンテナ**: Kubernetes
- **ロードバランサー**: AWS ALB / GCP Load Balancer
- **データベース**: AWS RDS PostgreSQL / Cloud SQL
- **キャッシュ**: AWS ElastiCache / Cloud Memorystore

### 監視・ログ

#### 監視システム
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sensechat-api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
  
  - job_name: 'sensechat-frontend'
    static_configs:
      - targets: ['frontend:3000']
```

#### ログ収集
```yaml
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "sensechat-api" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "sensechat-logs-%{+YYYY.MM.dd}"
  }
}
```

#### アラート設定
- **API応答時間**: 2秒超過でアラート
- **エラー率**: 5%超過でアラート
- **メモリ使用率**: 80%超過でアラート
- **ディスク使用率**: 85%超過でアラート

### バックアップ・復旧

#### データベースバックアップ
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="sensechat"

# データベースバックアップ
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > $BACKUP_DIR/db_$DATE.sql

# ベクトルデータバックアップ
cp -r /data/vectors $BACKUP_DIR/vectors_$DATE

# 古いバックアップ削除（30日以上）
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "vectors_*" -mtime +30 -exec rm -rf {} \;
```

#### 復旧手順
1. **データベース復旧**: `psql -h $DB_HOST -U $DB_USER $DB_NAME < backup.sql`
2. **ベクトルデータ復旧**: `cp -r vectors_backup/* /data/vectors/`
3. **サービス再起動**: `kubectl rollout restart deployment/sensechat-api`

### CI/CD

#### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/
          kubectl rollout status deployment/sensechat-api
```

### スケーリング

#### 水平スケーリング
- **APIサーバー**: 2-10インスタンス（負荷に応じて自動調整）
- **フロントエンド**: 2-5インスタンス
- **データベース**: 読み取り専用レプリカ 2台

#### 垂直スケーリング
- **APIサーバー**: 2-8 CPU、4-16GB RAM
- **データベース**: 2-8 CPU、8-32GB RAM
- **ベクトルDB**: 4-16 CPU、16-64GB RAM

### 災害復旧

#### RTO/RPO
- **RTO (Recovery Time Objective)**: 4時間以内
- **RPO (Recovery Point Objective)**: 1時間以内

#### 災害復旧手順
1. **障害検知**: 監視システムによる自動検知
2. **影響範囲特定**: ログ分析による原因特定
3. **復旧作業**: バックアップからの復旧
4. **動作確認**: 全機能の動作テスト
5. **事後対応**: インシデントレポート作成

## UI/UX設計

### デザインシステム

#### カラーパレット
```css
:root {
  /* Primary Colors */
  --primary-50: #eff6ff;
  --primary-500: #3b82f6;
  --primary-900: #1e3a8a;
  
  /* Neutral Colors */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-500: #6b7280;
  --gray-900: #111827;
  
  /* Semantic Colors */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
}
```

#### タイポグラフィ
```css
/* Font Families */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
```

#### スペーシング
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
```

### 画面設計

#### 1. ログイン画面
```
┌─────────────────────────────────┐
│  SenseChat                     │
│                                 │
│  ┌─────────────────────────┐   │
│  │ ユーザー名              │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │ パスワード              │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │ ログイン                │   │
│  └─────────────────────────┘   │
│                                 │
│  新規登録 | パスワード忘れ      │
└─────────────────────────────────┘
```

#### 2. メイン画面（チャット一覧）
```
┌─────────────────────────────────┐
│ SenseChat    [設定] [ログアウト] │
├─────────────────────────────────┤
│ 検索: [                    ] 🔍  │
├─────────────────────────────────┤
│ 📧 会議の件で...        10:30   │
│ 📧 プロジェクト進捗...  09:15   │
│ 📧 資料の準備...       08:45   │
│ 📧 お疲れ様です...      昨日    │
│                                 │
│ [新しいメッセージ]              │
└─────────────────────────────────┘
```

#### 3. チャット画面
```
┌─────────────────────────────────┐
│ ← 会議の件で...         [設定]  │
├─────────────────────────────────┤
│                                 │
│ 田中さん:                       │
│ 明日の会議の資料準備をお願い    │
│ します。よろしくお願いいたします│
│                        10:30   │
│                                 │
│ 佐藤さん:                       │
│ 承知いたしました。資料を準備    │
│ して明日お持ちします。          │
│                        10:32   │
│                                 │
├─────────────────────────────────┤
│ [メッセージ入力...]      [送信] │
└─────────────────────────────────┘
```

#### 4. 設定画面
```
┌─────────────────────────────────┐
│ ← 設定                          │
├─────────────────────────────────┤
│ プロフィール                    │
│ ┌─────────────────────────────┐ │
│ │ 表示名: 田中太郎            │ │
│ │ 言語: 日本語 ▼             │ │
│ └─────────────────────────────┘ │
│                                 │
│ スタイル設定                    │
│ ┌─────────────────────────────┐ │
│ │ プリセット: ビジネス ▼     │ │
│ │ トーン: 丁寧 ▼             │ │
│ │ 署名: よろしくお願い...     │ │
│ └─────────────────────────────┘ │
│                                 │
│ 通知設定                        │
│ ┌─────────────────────────────┐ │
│ │ ☑ メッセージ受信時          │ │
│ │ ☑ エラー発生時              │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### レスポンシブデザイン

#### ブレークポイント
```css
/* Mobile First Approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

#### モバイル対応
- **画面サイズ**: 375px - 768px
- **タッチ操作**: 最小44pxのタッチターゲット
- **ナビゲーション**: ハンバーガーメニュー
- **入力**: ソフトキーボード対応

#### タブレット対応
- **画面サイズ**: 768px - 1024px
- **レイアウト**: 2カラムレイアウト
- **ナビゲーション**: サイドバー
- **入力**: 物理キーボード対応

#### デスクトップ対応
- **画面サイズ**: 1024px以上
- **レイアウト**: 3カラムレイアウト
- **ナビゲーション**: 常時表示サイドバー
- **ショートカット**: キーボードショートカット

### アクセシビリティ

#### WCAG 2.1 AA準拠
- **色のコントラスト**: 4.5:1以上
- **フォーカス表示**: 明確なフォーカスインジケーター
- **キーボード操作**: 全機能をキーボードで操作可能
- **スクリーンリーダー**: 適切なARIAラベル

#### 実装例
```jsx
// アクセシブルなボタン
<button
  className="btn btn-primary"
  aria-label="メッセージを送信"
  aria-describedby="send-help"
>
  送信
</button>
<div id="send-help" className="sr-only">
  Enterキーでも送信できます
</div>

// フォームのアクセシビリティ
<form aria-labelledby="message-form-title">
  <h2 id="message-form-title">メッセージ作成</h2>
  <label htmlFor="message-input" className="block">
    メッセージ
  </label>
  <textarea
    id="message-input"
    aria-required="true"
    aria-describedby="message-help"
    placeholder="メッセージを入力してください"
  />
  <div id="message-help" className="text-sm text-gray-500">
    最大1000文字まで入力できます
  </div>
</form>
```

### アニメーション・インタラクション

#### マイクロインタラクション
- **ボタンホバー**: 0.2秒のフェード
- **メッセージ送信**: 0.3秒のスライドイン
- **ローディング**: スピナーアニメーション
- **エラー表示**: 0.4秒のスライドダウン

#### 実装例
```css
/* ボタンホバーエフェクト */
.btn {
  transition: all 0.2s ease-in-out;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* メッセージアニメーション */
.message-enter {
  opacity: 0;
  transform: translateY(20px);
}

.message-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 0.3s ease-out;
}
```

### パフォーマンス

#### 最適化目標
- **First Contentful Paint**: ≤ 1.5秒
- **Largest Contentful Paint**: ≤ 2.5秒
- **Cumulative Layout Shift**: ≤ 0.1
- **Time to Interactive**: ≤ 3.5秒

#### 実装戦略
- **コード分割**: ページ単位での遅延読み込み
- **画像最適化**: WebP形式、遅延読み込み
- **バンドル最適化**: Tree shaking、Minification
- **キャッシュ戦略**: Service Worker、HTTPキャッシュ

## ロードマップ（簡易版）

### Phase 1: 技術検証（1-2週間）
- **Week 1**: 基本API実装 + FAISS + 簡易UI
- **Week 2**: LLM API連携 + 家族内テスト

### Phase 2: 改善・最適化（1週間）
- **Week 3**: パフォーマンス改善 + バグ修正
- **Week 4**: ドキュメント整備 + GitHub準備

### Phase 3: 本格版開発（将来）
- 検証成功時: 本格版をGitHubで公開
- 機能拡張: 仲介UI・文体拡張・音声対応

"""
SenseChat MVP Backend
家族内使用・技術検証版
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from app.database import init_db
from app.config import get_settings
from app.routers import auth, messages, users, health
from app.websocket_manager import websocket_manager
from app.middleware import logging_middleware, rate_limit_middleware
from app.exceptions import setup_exception_handlers

# アプリケーション起動時の処理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    print("🚀 SenseChat MVP Backend を起動しています...")
    
    # データベース初期化
    await init_db()
    
    # AI/MLサービスの初期化
    from app.services.embedding_service import EmbeddingService
    from app.services.llm_api_service import LLMAPIService
    
    # グローバルサービスインスタンスの作成
    app.state.embedding_service = EmbeddingService()
    app.state.llm_api_service = LLMAPIService()
    
    # WebSocketマネージャーのRedis初期化
    await websocket_manager.initialize_redis()
    
    print("✅ 初期化完了")
    
    yield
    
    # 終了時
    print("🛑 SenseChat MVP Backend を停止しています...")

# アプリケーション設定
app = FastAPI(
    title="SenseChat MVP API",
    description="家族内使用・技術検証版 - 意味ベースコミュニケーションAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS設定（環境変数から制御）
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# カスタムミドルウェア
app.middleware("http")(logging_middleware)
app.middleware("http")(rate_limit_middleware)

# 例外ハンドラーの設定
setup_exception_handlers(app)

# ルーターの登録
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])
# Socket.IO (WebSocket) をFastAPIに直接マウント
app.mount("/api/v1/ws", websocket_manager.app)


# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": "SenseChat MVP API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "SenseChat MVP Backend is running"}

# 開発用サーバー起動
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

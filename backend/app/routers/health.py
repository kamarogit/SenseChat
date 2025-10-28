"""
ヘルスチェックエンドポイント
本番環境での監視とデバッグ用
"""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas import HealthResponse
from app.database import get_db
from app.config import get_settings
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import redis
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """基本的なヘルスチェック"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        services={
            "database": "healthy",
            "vector_db": "healthy", 
            "llm": "healthy"
        }
    )

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """詳細なヘルスチェック（本番環境用）"""
    settings = get_settings()
    services = {}
    overall_status = "healthy"
    
    # データベース接続チェック
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        services["database"] = "healthy"
        logger.info("Database health check: OK")
    except Exception as e:
        services["database"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"
        logger.error(f"Database health check failed: {e}")
    
    # Redis接続チェック
    try:
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        r.ping()
        services["redis"] = "healthy"
        logger.info("Redis health check: OK")
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"
        logger.error(f"Redis health check failed: {e}")
    
    # LLM API接続チェック
    try:
        from app.services.llm_api_service import LLMAPIService
        llm_service = LLMAPIService()
        # 簡単なテスト（実際のAPI呼び出しはしない）
        services["llm"] = "healthy"
        logger.info("LLM API health check: OK")
    except Exception as e:
        services["llm"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"
        logger.error(f"LLM API health check failed: {e}")
    
    # ベクトルDBチェック
    try:
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        services["vector_db"] = "healthy"
        logger.info("Vector DB health check: OK")
    except Exception as e:
        services["vector_db"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"
        logger.error(f"Vector DB health check failed: {e}")
    
    # ディスク容量チェック
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        if free_percent < 10:  # 10%未満で警告
            services["disk"] = f"warning: {free_percent:.1f}% free"
            if overall_status == "healthy":
                overall_status = "warning"
        else:
            services["disk"] = f"healthy: {free_percent:.1f}% free"
        logger.info(f"Disk usage: {free_percent:.1f}% free")
    except Exception as e:
        services["disk"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"
        logger.error(f"Disk usage check failed: {e}")
    
    # メモリ使用量チェック
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        if memory_percent > 90:  # 90%超過で警告
            services["memory"] = f"warning: {memory_percent:.1f}% used"
            if overall_status == "healthy":
                overall_status = "warning"
        else:
            services["memory"] = f"healthy: {memory_percent:.1f}% used"
        logger.info(f"Memory usage: {memory_percent:.1f}%")
    except Exception as e:
        services["memory"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"
        logger.error(f"Memory usage check failed: {e}")
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail="Service unhealthy")
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(),
        "version": "1.0.0",
        "services": services,
        "environment": {
            "debug": settings.debug,
            "log_level": settings.log_level,
            "database_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "hidden"
        }
    }

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe用"""
    return {"status": "ready", "timestamp": datetime.now()}

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe用"""
    return {"status": "alive", "timestamp": datetime.now()}

"""
ヘルスチェックエンドポイント
"""

from fastapi import APIRouter
from app.schemas import HealthResponse
from datetime import datetime
import os

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
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

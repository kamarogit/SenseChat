"""
カスタムミドルウェア
ログ、レート制限、エラーハンドリング
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import logging
from datetime import datetime
from typing import Dict, Any

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """ログミドルウェア"""
    start_time = time.time()
    
    # リクエストログ
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # レスポンスログ
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"Process time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        # エラーログ
        process_time = time.time() - start_time
        logger.error(f"Error: {str(e)} Process time: {process_time:.3f}s")
        raise

async def rate_limit_middleware(request: Request, call_next):
    """レート制限ミドルウェア（簡易版）"""
    # 家族内使用のため、レート制限は無効化
    # 必要に応じて実装
    return await call_next(request)

def setup_exception_handlers(app):
    """例外ハンドラーの設定"""
    
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
                    "request_id": getattr(request.state, 'request_id', None)
                }
            }
        )
    
    @app.exception_handler(ValueError)
    async def validation_exception_handler(request: Request, exc: ValueError):
        """バリデーション例外ハンドラー"""
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VAL_001",
                    "message": "入力データが無効です",
                    "details": str(exc),
                    "timestamp": datetime.now().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
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
                    "request_id": getattr(request.state, 'request_id', None)
                }
            }
        )

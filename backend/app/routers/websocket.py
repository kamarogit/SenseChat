"""
WebSocketエンドポイント
リアルタイム通信のAPI
"""

from fastapi import APIRouter
from app.websocket_manager import websocket_manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket接続エンドポイント"""
    await websocket_manager.app(websocket.scope, websocket.receive, websocket.send)
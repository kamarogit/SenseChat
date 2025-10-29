"""
WebSocket接続管理
リアルタイム通信とユーザー状態管理
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime
import redis.asyncio as redis
import socketio
import logging
import os

logger = logging.getLogger(__name__)

class SocketManager:
    """Socket.IO接続とメッセージングの管理"""
    
    def __init__(self):
        # Socket.IOサーバー
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=[
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ]
        )
        self.app = socketio.ASGIApp(self.sio)
        
        # 接続されたユーザー
        self.connected_users: Dict[str, str] = {}  # user_id -> sid
        
        # Redis接続（Pub/Sub用）
        self.r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        self.pubsub = self.r.pubsub()
        
        # Socket.IOイベントハンドラーを設定
        self.setup_event_handlers()
        
        # Redis初期化フラグ
        self._redis_initialized = False
    
    def setup_event_handlers(self):
        """Socket.IOイベントハンドラーを設定"""
        
        @self.sio.on('connect')
        async def handle_connect(sid, environ):
            print(f"WebSocket connected: {sid}")
            await self.sio.emit('connection_established', {'sid': sid}, room=sid)
        
        @self.sio.on('disconnect')
        async def handle_disconnect(sid):
            user_id = None
            for uid, current_sid in self.connected_users.items():
                if current_sid == sid:
                    user_id = uid
                    break
            if user_id:
                del self.connected_users[user_id]
                print(f"WebSocket disconnected: {sid}, User: {user_id}")
                await self.broadcast_user_status(user_id, 'offline')
            else:
                print(f"WebSocket disconnected: {sid}")
        
        @self.sio.on('user_register')
        async def handle_user_register(sid, data):
            user_id = data.get('user_id')
            if user_id:
                self.connected_users[user_id] = sid
                print(f"User {user_id} registered with SID {sid}")
                await self.broadcast_user_status(user_id, 'online')
                await self.send_online_users(sid)
            else:
                print(f"User registration failed for SID {sid}: no user_id provided")
        
        @self.sio.on('typing_status')
        async def handle_typing_status(sid, data):
            user_id = None
            for uid, current_sid in self.connected_users.items():
                if current_sid == sid:
                    user_id = uid
                    break
            if user_id:
                recipient_id = data.get('recipient_id')
                is_typing = data.get('is_typing')
                if recipient_id and recipient_id in self.connected_users:
                    await self.sio.emit('user_typing', {
                        'user_id': user_id, 
                        'is_typing': is_typing
                    }, room=self.connected_users[recipient_id])
                else:
                    # Optionally broadcast to all connected users in a chat room
                    pass
        
        @self.sio.on('ping')
        async def handle_ping(sid, data):
            await self.sio.emit('pong', {'timestamp': data.get('timestamp')}, room=sid)
        
        @self.sio.on('get_online_users')
        async def handle_get_online_users(sid, data):
            await self.send_online_users(sid)
    
    async def broadcast_new_message(self, message_data: Dict[str, Any], sender_id: str, recipient_id: str):
        """新しいメッセージをブロードキャスト"""
        # Send to recipient
        if recipient_id in self.connected_users:
            await self.sio.emit('new_message', message_data, room=self.connected_users[recipient_id])
            print(f"Message {message_data.get('message_id')} sent to recipient {recipient_id} via WebSocket.")
        else:
            print(f"Recipient {recipient_id} not online, message not sent via WebSocket.")
        
        # Optionally send a delivery confirmation to sender
        if sender_id in self.connected_users:
            await self.sio.emit('message_delivered', {
                'message_id': message_data.get('message_id')
            }, room=self.connected_users[sender_id])
    
    async def broadcast_user_status(self, user_id: str, status: str):
        """ユーザーのオンライン状態をブロードキャスト"""
        await self.sio.emit('user_status', {
            'user_id': user_id, 
            'status': status
        }, skip_sid=self.connected_users.get(user_id))
        print(f"User {user_id} is now {status}")
    
    async def send_online_users(self, sid: str):
        """オンラインユーザー一覧を送信"""
        online_user_ids = list(self.connected_users.keys())
        await self.sio.emit('online_users', {'users': online_user_ids}, room=sid)
    
    def get_user_id_from_sid(self, sid: str) -> str | None:
        """SIDからユーザーIDを取得"""
        for user_id, connected_sid in self.connected_users.items():
            if connected_sid == sid:
                return user_id
        return None
    
    async def initialize_redis(self):
        """Redis接続を初期化（FastAPIスタートアップで呼び出し）"""
        if self._redis_initialized:
            return
        
        try:
            await self.pubsub.subscribe('chat_messages')
            # Redisメッセージを処理するタスクを開始
            asyncio.create_task(self._handle_redis_messages())
            self._redis_initialized = True
            logger.info("Redis接続を初期化しました")
        except Exception as e:
            logger.error(f"Redis接続エラー: {e}")
    
    async def _init_redis(self):
        """Redis接続を初期化（内部用）"""
        await self.initialize_redis()
    
    async def _handle_redis_messages(self):
        """Redisからのメッセージを処理"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await self._process_redis_message(data)
        except Exception as e:
            logger.error(f"Redisメッセージ処理エラー: {e}")
    
    async def _process_redis_message(self, data: dict):
        """Redisメッセージを処理"""
        message_type = data.get("type")
        
        if message_type == "new_message":
            await self.broadcast_new_message(
                data["message_data"],
                data["sender_id"],
                data["recipient_id"]
            )
        elif message_type == "user_status":
            await self.broadcast_user_status(
                data["user_id"],
                data["status"]
            )

# グローバルインスタンス
websocket_manager = SocketManager()
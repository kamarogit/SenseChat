"""
Pydanticスキーマ定義
APIリクエスト/レスポンス用
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# ユーザー関連スキーマ
class UserBase(BaseModel):
    name: str
    language: str = "ja"
    style_preset: str = "biz_formal"

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# メッセージ関連スキーマ
class MessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    lang_hint: Optional[str] = "auto"
    slots: Optional[Dict[str, Any]] = None
    
    @validator('lang_hint')
    def validate_lang_hint(cls, v):
        if v not in ['ja', 'en', 'zh', 'ko', 'auto']:
            raise ValueError('無効な言語ヒントです')
        return v

class MessageResponse(BaseModel):
    message_id: str
    summary: str
    vector_id: str
    slots: Dict[str, Any]
    created_at: datetime
    processing_time_ms: int

# スレッド関連スキーマ
class ThreadCreate(BaseModel):
    title: Optional[str] = None

class ThreadResponse(BaseModel):
    id: str
    title: Optional[str]
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 受信箱関連スキーマ
class InboxResponse(BaseModel):
    id: str
    user_id: str
    message_id: str
    thread_id: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# レンダリング関連スキーマ
class RenderRequest(BaseModel):
    message_id: str
    recipient_id: str

class RenderResponse(BaseModel):
    text: str
    confidence: float
    used_neighbors: List[Dict[str, Any]]
    slots: Dict[str, Any]
    style_applied: str

# 配信関連スキーマ
class DeliverRequest(BaseModel):
    to_user_id: str
    message_id: str
    thread_id: str

class DeliverResponse(BaseModel):
    status: str
    delivery_id: str
    estimated_delivery: datetime
    created_at: datetime

# エラーレスポンススキーマ
class ErrorResponse(BaseModel):
    error: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "VAL_001",
                    "message": "入力データが無効です",
                    "details": {
                        "field": "text",
                        "reason": "必須フィールドが空です"
                    },
                    "timestamp": "2024-01-01T00:00:00Z",
                    "request_id": "req_123456789"
                }
            }
        }

# ヘルスチェックスキーマ
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

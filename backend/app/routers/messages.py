"""
メッセージ関連エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from app.schemas import (
    MessageCreate, MessageResponse, RenderRequest, RenderResponse,
    DeliverRequest, DeliverResponse
)
from app.database import get_db
from app.models import Message, Thread, Inbox, User
from app.services.embedding_service import EmbeddingService
from app.services.llm_api_service import LLMAPIService
from app.websocket_manager import websocket_manager
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import uuid
import json

router = APIRouter()

# 簡易認証（ヘッダーからユーザーIDを取得）
def get_current_user(x_user_id: Optional[str] = Header(None)):
    """簡易認証（家族内使用のため）"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-ID ヘッダーが必要です")
    return x_user_id

@router.post("/embed", response_model=MessageResponse)
async def embed_message(
    request: MessageCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """テキストを要約・ベクトル化してメッセージを作成"""
    start_time = datetime.now()
    
    try:
        # EmbeddingServiceの取得（実際の実装では依存性注入）
        embedding_service = EmbeddingService()
        
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
        
        # 4. データベース保存（要約とベクトルのみ）
        from datetime import timedelta
        message = Message(
            thread_id=None,  # 新規スレッド
            sender_id=current_user,
            summary=summary,
            vector_id=vector_id,
            slots=json.dumps(slots),
            lang_hint=request.lang_hint,
            expires_at=datetime.now() + timedelta(hours=24)  # 24時間後自動削除
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MessageResponse(
            message_id=message.id,
            summary=summary,
            vector_id=vector_id,
            slots=slots,
            created_at=message.created_at,
            processing_time_ms=int(processing_time)
            # original_text は返さない（クライアント側に保存）
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"メッセージ作成に失敗しました: {str(e)}")

@router.post("/render", response_model=RenderResponse)
async def render_message(
    request: RenderRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """メッセージを受信者向けに再構成"""
    try:
        # 1. メッセージ取得
        message = db.query(Message).filter(Message.id == request.message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="メッセージが見つかりません")
        
        # 2. 受信者情報取得
        recipient = db.query(User).filter(User.id == request.recipient_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="受信者が見つかりません")
        
        # 3. ベクトル検索（実際の実装ではVectorServiceを使用）
        neighbors = []  # 実装予定
        
        # 4. LLM API再構成
        llm_service = LLMAPIService()
        rendered_text, confidence = await llm_service.reconstruct_message(
            summary=message.summary,
            slots=json.loads(message.slots or "{}"),
            style_preset=recipient.style_preset,
            language=recipient.language,
            neighbors=neighbors
        )
        
        # 5. 再構成されたテキストをクライアント側に返す
        response = RenderResponse(
            text=rendered_text,
            confidence=confidence,
            used_neighbors=neighbors,
            slots=json.loads(message.slots or "{}"),
            style_applied=recipient.style_preset
        )
        
        # 6. WebSocketでリアルタイム通知を送信
        try:
            await websocket_manager.broadcast_new_message(
                message_data={
                    "message_id": message.id,
                    "text": rendered_text,
                    "summary": message.summary,
                    "sender_id": message.sender_id,
                    "recipient_id": request.recipient_id,
                    "confidence": confidence,
                    "created_at": message.created_at.isoformat()
                },
                sender_id=message.sender_id,
                recipient_id=request.recipient_id
            )
        except Exception as e:
            # WebSocket通知の失敗はログに記録するが、APIレスポンスは継続
            print(f"WebSocket通知エラー: {e}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"メッセージ再構成に失敗しました: {str(e)}")

@router.post("/deliver", response_model=DeliverResponse)
async def deliver_message(
    request: DeliverRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """メッセージを指定ユーザーに配信"""
    try:
        # 0. メッセージの存在確認（送信者情報取得のため）
        message = db.query(Message).filter(Message.id == request.message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="メッセージが見つかりません")

        # 1. スレッドが指定されているが未存在の場合は作成（MVP: 単一デフォルトスレッドを許容）
        thread_id = request.thread_id
        if thread_id:
            existing_thread = db.query(Thread).filter(Thread.id == thread_id).first()
            if not existing_thread:
                new_thread = Thread(
                    id=thread_id,
                    created_by=message.sender_id,
                    title="default"
                )
                db.add(new_thread)
                db.flush()  # INSERTを確定してFK整合性を満たす

        # 2. 配信レコード作成
        delivery = Inbox(
            user_id=request.to_user_id,
            message_id=request.message_id,
            thread_id=thread_id,
            status="unread"
        )
        
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        
        return DeliverResponse(
            status="queued",
            delivery_id=delivery.id,
            estimated_delivery=datetime.now(),
            created_at=delivery.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"メッセージ配信に失敗しました: {str(e)}")

@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    current_user: str = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """スレッドのメッセージ一覧を取得（SenseChat MVP対応）"""
    try:
        # メッセージとその再構成を取得
        messages = db.query(Message).filter(
            Message.thread_id == thread_id
        ).offset(offset).limit(limit).all()
        
        result_messages = []
        for msg in messages:
            # クライアント側保存対応: 要約のみを返す
            # 実際のテキスト（元のテキスト or 再構成されたテキスト）はクライアント側で管理
            result_messages.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "text": msg.summary,  # 要約のみ
                "created_at": msg.created_at,
                "status": "read"  # 簡易版
            })
        
        return {
            "thread_id": thread_id,
            "messages": result_messages,
            "total_count": len(result_messages),
            "has_more": len(result_messages) == limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"メッセージ取得に失敗しました: {str(e)}")

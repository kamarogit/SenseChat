"""
データベースモデル定義
SQLite用（簡易版）
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class User(Base):
    """ユーザーモデル（簡易版）"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    language = Column(String, default="ja")
    style_preset = Column(String, default="biz_formal")
    created_at = Column(DateTime, default=func.now())
    
    # リレーション
    threads = relationship("Thread", back_populates="creator")
    messages = relationship("Message", back_populates="sender")

class Thread(Base):
    """スレッドモデル（簡易版）"""
    __tablename__ = "threads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by = Column(String, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime, default=func.now())
    
    # リレーション
    creator = relationship("User", back_populates="threads")
    messages = relationship("Message", back_populates="thread")

class Message(Base):
    """メッセージモデル（軽量化版 - クライアント側保存対応）"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String, ForeignKey("threads.id"))
    sender_id = Column(String, ForeignKey("users.id"))
    summary = Column(Text, nullable=False)  # 要約のみ（元のテキストはクライアント側に保存）
    vector_id = Column(String)  # FAISS内のID
    slots = Column(Text)  # JSON文字列
    lang_hint = Column(String)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)  # 自動削除用（24時間後）
    
    # リレーション
    thread = relationship("Thread", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    contents = relationship("MessageContent", back_populates="message", cascade="all, delete-orphan")

class MessageContent(Base):
    """メッセージコンテンツモデル（サーバー側永続化対応）"""
    __tablename__ = "message_contents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 送信者または受信者
    content_type = Column(String, nullable=False)  # 'original' or 'rendered'
    text = Column(Text, nullable=False)  # 元のテキストまたは再構成されたテキスト
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # リレーション
    message = relationship("Message", back_populates="contents")
    user = relationship("User")

class Inbox(Base):
    """受信箱モデル（簡易版）"""
    __tablename__ = "inbox"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    message_id = Column(String, ForeignKey("messages.id"))
    thread_id = Column(String, ForeignKey("threads.id"))
    status = Column(String, default="unread")  # unread, read
    created_at = Column(DateTime, default=func.now())

class KBItem(Base):
    """ナレッジベースアイテム（簡易版）"""
    __tablename__ = "kb_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(Text, nullable=False)
    vector_id = Column(String)  # FAISS内のID
    category = Column(String)
    created_at = Column(DateTime, default=func.now())

"""
ユーザー管理エンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas import UserResponse
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session
from typing import List

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_all_users(db: Session = Depends(get_db)):
    """全ユーザー一覧を取得"""
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """特定ユーザーの情報を取得"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    return user

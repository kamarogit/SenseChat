"""
認証エンドポイント（簡易版）
家族内使用のため簡素化
"""

from fastapi import APIRouter, HTTPException
from app.schemas import UserResponse
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os

router = APIRouter()

@router.get("/users", response_model=dict)
async def get_users():
    """利用可能なユーザー一覧を取得（簡易版）"""
    try:
        # 設定ファイルからユーザー情報を読み込み
        users_config_path = os.getenv("USERS_CONFIG", "config/users.json")
        
        if not os.path.exists(users_config_path):
            raise HTTPException(status_code=404, detail="ユーザー設定ファイルが見つかりません")
        
        with open(users_config_path, "r", encoding="utf-8") as f:
            users_data = json.load(f)
        
        return {"users": users_data.get("users", [])}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー情報の取得に失敗しました: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """特定ユーザーの情報を取得"""
    try:
        users_config_path = os.getenv("USERS_CONFIG", "config/users.json")
        
        with open(users_config_path, "r", encoding="utf-8") as f:
            users_data = json.load(f)
        
        users = users_data.get("users", [])
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
        return UserResponse(
            id=user["id"],
            name=user["name"],
            language=user["language"],
            style_preset=user["style_preset"],
            created_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ユーザー情報の取得に失敗しました: {str(e)}")

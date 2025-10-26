#!/usr/bin/env python3
"""
データベースマイグレーションスクリプト
SenseChat MVP用の新しいテーブルを追加
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import MessageRendering

def migrate_database():
    """新しいテーブルを作成"""
    print("🔄 データベースマイグレーションを開始...")
    
    try:
        # MessageRenderingテーブルを作成
        MessageRendering.__table__.create(engine, checkfirst=True)
        print("✅ MessageRenderingテーブルを作成しました")
        
        print("🎉 マイグレーションが完了しました！")
        
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()


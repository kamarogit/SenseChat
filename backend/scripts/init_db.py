"""
データベース初期化スクリプト
"""

import asyncio
import sys
import os

# パスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, engine, Base
from app.models import User, Thread, Message, Inbox, KBItem
import json

async def main():
    """データベース初期化"""
    print("🗄️  データベースを初期化しています...")
    
    try:
        # テーブル作成
        Base.metadata.create_all(bind=engine)
        print("✅ テーブル作成完了")
        
        # 初期データの挿入
        await insert_initial_data()
        print("✅ 初期データ挿入完了")
        
        print("🎉 データベース初期化が完了しました！")
        
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        sys.exit(1)

async def insert_initial_data():
    """初期データの挿入"""
    from sqlalchemy.orm import sessionmaker
    from app.database import engine
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # ユーザーデータの読み込み
        users_config_path = os.getenv("USERS_CONFIG", "config/users.json")
        
        if os.path.exists(users_config_path):
            with open(users_config_path, "r", encoding="utf-8") as f:
                users_data = json.load(f)
            
            # ユーザー作成
            for user_data in users_data.get("users", []):
                existing_user = db.query(User).filter(User.id == user_data["id"]).first()
                if not existing_user:
                    user = User(
                        id=user_data["id"],
                        name=user_data["name"],
                        language=user_data["language"],
                        style_preset=user_data["style_preset"]
                    )
                    db.add(user)
                    print(f"✅ ユーザー作成: {user_data['name']}")
            
            db.commit()
        else:
            print("⚠️  ユーザー設定ファイルが見つかりません")
            
    except Exception as e:
        db.rollback()
        print(f"❌ 初期データ挿入エラー: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

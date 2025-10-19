"""
データベース設定とセッション管理
SQLite使用（簡易版）
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# データベースURL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sensechat.db")

# データディレクトリの作成
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)

# SQLite用の設定
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite用
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    engine = create_engine(DATABASE_URL)

# セッションファクトリー
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラス
Base = declarative_base()

# データベース依存性
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# データベース初期化
async def init_db():
    """データベースの初期化"""
    try:
        # テーブル作成
        Base.metadata.create_all(bind=engine)
        print("✅ データベース初期化完了")
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        raise

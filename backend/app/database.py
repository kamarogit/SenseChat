"""
データベース設定とセッション管理
SQLite（開発）とPostgreSQL（本番）の両方に対応
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# データベースURL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sensechat.db")

# データディレクトリの作成（SQLite用）
if DATABASE_URL.startswith("sqlite"):
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)

# データベースエンジンの作成
if DATABASE_URL.startswith("sqlite"):
    # SQLite用の設定
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite用
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL用の設定
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        pool_pre_ping=True,  # 接続の健全性チェック
        pool_recycle=300,    # 5分で接続をリサイクル
    )
else:
    # その他のデータベース
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

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
        print(f"✅ データベース初期化完了: {DATABASE_URL.split('://')[0]}")
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        raise

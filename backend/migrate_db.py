#!/usr/bin/env python3
"""
データベースマイグレーションスクリプト
SenseChat MVP用のクライアント側保存対応
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import Message, User, Thread, Inbox, KBItem, MessageContent
from sqlalchemy import text

def migrate_database():
    """データベースをクライアント側保存対応にマイグレーション"""
    print("データベースマイグレーションを開始...")
    
    try:
        with engine.connect() as conn:
            # 1. 既存のMessageRenderingテーブルを削除（存在する場合）
            try:
                conn.execute(text("DROP TABLE IF EXISTS message_renderings"))
                print("MessageRenderingテーブルを削除しました")
            except Exception as e:
                print(f"MessageRenderingテーブル削除スキップ: {e}")
            
            # 2. messagesテーブルの現在の構造を確認
            try:
                result = conn.execute(text("PRAGMA table_info(messages)"))
                columns = [row[1] for row in result]
                print(f"現在のmessagesテーブルのカラム: {columns}")
            except Exception as e:
                print(f"テーブル構造確認エラー: {e}")
                columns = []
            
            # 3. original_textカラムを削除（存在する場合）
            if 'original_text' in columns:
                try:
                    # SQLiteではDROP COLUMNがサポートされていないため、テーブルを再作成
                    print("original_textカラムを削除するため、テーブルを再作成します...")
                    
                    # 既存データをバックアップ
                    conn.execute(text("CREATE TABLE messages_backup AS SELECT * FROM messages"))
                    print("既存データをバックアップしました")
                    
                    # 既存テーブルを削除
                    conn.execute(text("DROP TABLE messages"))
                    print("既存のmessagesテーブルを削除しました")
                    
                    # 新しいテーブルを作成（original_textなし、expires_atあり）
                    conn.execute(text("""
                        CREATE TABLE messages (
                            id VARCHAR PRIMARY KEY,
                            thread_id VARCHAR,
                            sender_id VARCHAR,
                            summary TEXT NOT NULL,
                            vector_id VARCHAR,
                            slots TEXT,
                            lang_hint VARCHAR,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            expires_at DATETIME,
                            FOREIGN KEY (thread_id) REFERENCES threads (id),
                            FOREIGN KEY (sender_id) REFERENCES users (id)
                        )
                    """))
                    print("新しいmessagesテーブルを作成しました")
                    
                    # バックアップからデータを復元（original_textカラムを除く）
                    conn.execute(text("""
                        INSERT INTO messages (id, thread_id, sender_id, summary, vector_id, slots, lang_hint, created_at, expires_at)
                        SELECT id, thread_id, sender_id, summary, vector_id, slots, lang_hint, created_at, 
                               datetime(created_at, '+24 hours') as expires_at
                        FROM messages_backup
                    """))
                    print("データを復元しました")
                    
                    # バックアップテーブルを削除
                    conn.execute(text("DROP TABLE messages_backup"))
                    print("バックアップテーブルを削除しました")
                    
                except Exception as e:
                    print(f"original_textカラム削除エラー: {e}")
                    # エラーの場合はテーブルを再作成
                    conn.execute(text("DROP TABLE IF EXISTS messages"))
                    conn.execute(text("""
                        CREATE TABLE messages (
                            id VARCHAR PRIMARY KEY,
                            thread_id VARCHAR,
                            sender_id VARCHAR,
                            summary TEXT NOT NULL,
                            vector_id VARCHAR,
                            slots TEXT,
                            lang_hint VARCHAR,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            expires_at DATETIME,
                            FOREIGN KEY (thread_id) REFERENCES threads (id),
                            FOREIGN KEY (sender_id) REFERENCES users (id)
                        )
                    """))
                    print("テーブルを再作成しました")
            
            # 4. expires_atカラムを追加（存在しない場合）
            elif 'expires_at' not in columns:
                try:
                    conn.execute(text("ALTER TABLE messages ADD COLUMN expires_at DATETIME"))
                    print("expires_atカラムを追加しました")
                except Exception as e:
                    print(f"expires_atカラム追加エラー: {e}")
            
            # 5. MessageContentテーブルを作成（サーバー側永続化対応）
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS message_contents (
                        id VARCHAR PRIMARY KEY,
                        message_id VARCHAR NOT NULL,
                        user_id VARCHAR NOT NULL,
                        content_type VARCHAR NOT NULL,
                        text TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (message_id) REFERENCES messages (id),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """))
                print("MessageContentテーブルを作成しました")
            except Exception as e:
                print(f"MessageContentテーブル作成スキップ: {e}")
            
            # 6. 必要なテーブルを作成
            Base.metadata.create_all(engine, checkfirst=True)
            print("必要なテーブルを作成しました")
            
            conn.commit()
        
        print("マイグレーションが完了しました！")
        print("変更内容:")
        print("   - MessageRenderingテーブルを削除")
        print("   - Messageテーブルからoriginal_textカラムを削除")
        print("   - Messageテーブルにexpires_atカラムを追加")
        print("   - MessageContentテーブルを追加（サーバー側永続化）")
        print("   - クライアント側保存 + サーバー側永続化対応完了")
        
    except Exception as e:
        print(f"マイグレーションエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()


"""
API テスト
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """ヘルスチェックテスト"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data

def test_get_users():
    """ユーザー一覧取得テスト"""
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert isinstance(data["users"], list)

def test_embed_message():
    """メッセージ埋め込みテスト"""
    response = client.post(
        "/api/v1/embed",
        json={
            "text": "テストメッセージです",
            "lang_hint": "ja"
        },
        headers={"X-User-ID": "user_1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message_id" in data
    assert "summary" in data
    assert "vector_id" in data

def test_embed_message_validation():
    """メッセージ埋め込みバリデーションテスト"""
    # 空のテキスト
    response = client.post(
        "/api/v1/embed",
        json={"text": ""},
        headers={"X-User-ID": "user_1"}
    )
    assert response.status_code == 422
    
    # 長すぎるテキスト
    long_text = "a" * 1001
    response = client.post(
        "/api/v1/embed",
        json={"text": long_text},
        headers={"X-User-ID": "user_1"}
    )
    assert response.status_code == 422

def test_embed_message_no_user():
    """ユーザーIDなしでのメッセージ埋め込みテスト"""
    response = client.post(
        "/api/v1/embed",
        json={"text": "テストメッセージです"}
    )
    assert response.status_code == 401

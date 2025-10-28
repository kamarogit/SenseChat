"""
設定管理
本番環境と開発環境の設定を統一的に管理
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # 基本設定
    app_name: str = "SenseChat MVP"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # データベース設定
    database_url: str
    postgres_db: str = "sensechat"
    postgres_user: str = "sensechat"
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # Redis設定
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # LLM API設定
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    default_llm_provider: str = "openai_gpt4"
    
    # セキュリティ設定
    secret_key: str = "your-secret-key-change-in-production"
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    
    # CORS設定
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # ファイルパス設定
    users_config_path: str = "/app/config/users.json"
    data_dir: str = "/app/data"
    logs_dir: str = "/app/logs"
    
    # 監視設定
    prometheus_enabled: bool = False
    grafana_enabled: bool = False
    
    # バックアップ設定
    backup_schedule: str = "0 2 * * *"  # 毎日午前2時
    s3_backup_bucket: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-west-2"
    
    @validator('database_url', pre=True)
    def build_database_url(cls, v, values):
        """データベースURLを構築"""
        if v:
            return v
        
        # 環境変数から構築
        db = values.get('postgres_db', 'sensechat')
        user = values.get('postgres_user', 'sensechat')
        password = values.get('postgres_password', '')
        host = values.get('postgres_host', 'localhost')
        port = values.get('postgres_port', 5432)
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    @validator('allowed_hosts', pre=True)
    def parse_allowed_hosts(cls, v):
        """許可ホストをパース"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """CORSオリジンをパース"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# グローバル設定インスタンス
settings = Settings()


def get_settings() -> Settings:
    """設定インスタンスを取得"""
    return settings

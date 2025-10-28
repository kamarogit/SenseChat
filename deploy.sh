#!/bin/bash

# SenseChat MVP 本番デプロイスクリプト
# 使用方法: ./deploy.sh [環境名]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="sensechat-mvp"

echo "🚀 SenseChat MVP デプロイ開始: $ENVIRONMENT"

# 環境変数ファイルの確認
if [ ! -f ".env.prod" ]; then
    echo "❌ .env.prod ファイルが見つかりません"
    echo "env.prod.example をコピーして設定してください"
    exit 1
fi

# Docker Compose の停止
echo "🛑 既存のコンテナを停止中..."
docker-compose -f docker-compose.prod.yml down

# イメージのビルド
echo "🔨 本番用イメージをビルド中..."
docker-compose -f docker-compose.prod.yml build --no-cache

# データベースのマイグレーション
echo "📊 データベースマイグレーション実行中..."
docker-compose -f docker-compose.prod.yml run --rm backend python -c "
from app.database import init_db
import asyncio
asyncio.run(init_db())
print('Database migration completed')
"

# サービスの起動
echo "🚀 サービスを起動中..."
docker-compose -f docker-compose.prod.yml up -d

# ヘルスチェック
echo "🏥 ヘルスチェック実行中..."
sleep 30

# 基本的なヘルスチェック
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ 基本ヘルスチェック: OK"
else
    echo "❌ 基本ヘルスチェック: FAILED"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# 詳細ヘルスチェック
if curl -f http://localhost/health/detailed > /dev/null 2>&1; then
    echo "✅ 詳細ヘルスチェック: OK"
else
    echo "⚠️ 詳細ヘルスチェック: WARNING"
fi

# ログの表示
echo "📋 サービス状態:"
docker-compose -f docker-compose.prod.yml ps

echo "🎉 デプロイ完了!"
echo "🌐 アプリケーション: http://localhost"
echo "📊 ヘルスチェック: http://localhost/health"
echo "🔍 詳細ヘルスチェック: http://localhost/health/detailed"

# ログの監視（オプション）
if [ "$2" = "--logs" ]; then
    echo "📝 ログを監視中... (Ctrl+C で停止)"
    docker-compose -f docker-compose.prod.yml logs -f
fi

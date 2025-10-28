#!/bin/bash

# SenseChat MVP バックアップスクリプト
# 使用方法: ./backup.sh [バックアップ名]

set -e

BACKUP_NAME=${1:-$(date +%Y%m%d_%H%M%S)}
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)

echo "💾 SenseChat MVP バックアップ開始: $BACKUP_NAME"

# バックアップディレクトリの作成
mkdir -p "$BACKUP_DIR"

# PostgreSQL データベースのバックアップ
echo "📊 PostgreSQL データベースをバックアップ中..."
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U sensechat sensechat > "$BACKUP_DIR/database_${BACKUP_NAME}.sql"

# Redis データのバックアップ
echo "🔴 Redis データをバックアップ中..."
docker-compose -f docker-compose.prod.yml exec -T redis redis-cli --rdb - > "$BACKUP_DIR/redis_${BACKUP_NAME}.rdb"

# 設定ファイルのバックアップ
echo "⚙️ 設定ファイルをバックアップ中..."
cp .env.prod "$BACKUP_DIR/env_${BACKUP_NAME}.backup" 2>/dev/null || echo "⚠️ .env.prod が見つかりません"
cp docker-compose.prod.yml "$BACKUP_DIR/docker-compose_${BACKUP_NAME}.backup"
cp nginx.conf "$BACKUP_DIR/nginx_${BACKUP_NAME}.backup"

# ログファイルのバックアップ
echo "📝 ログファイルをバックアップ中..."
mkdir -p "$BACKUP_DIR/logs_${BACKUP_NAME}"
docker-compose -f docker-compose.prod.yml logs --no-color > "$BACKUP_DIR/logs_${BACKUP_NAME}/application.log"

# バックアップ情報ファイルの作成
cat > "$BACKUP_DIR/backup_info_${BACKUP_NAME}.txt" << EOF
SenseChat MVP バックアップ情報
===============================

バックアップ名: $BACKUP_NAME
作成日時: $TIMESTAMP
バックアップディレクトリ: $BACKUP_DIR

含まれるファイル:
- database_${BACKUP_NAME}.sql (PostgreSQL データベース)
- redis_${BACKUP_NAME}.rdb (Redis データ)
- env_${BACKUP_NAME}.backup (環境変数)
- docker-compose_${BACKUP_NAME}.backup (Docker Compose設定)
- nginx_${BACKUP_NAME}.backup (Nginx設定)
- logs_${BACKUP_NAME}/application.log (アプリケーションログ)

復元方法:
1. データベース復元:
   docker-compose -f docker-compose.prod.yml exec -T postgres psql -U sensechat sensechat < database_${BACKUP_NAME}.sql

2. Redis復元:
   docker-compose -f docker-compose.prod.yml exec -T redis redis-cli --pipe < redis_${BACKUP_NAME}.rdb

3. 設定復元:
   cp env_${BACKUP_NAME}.backup .env.prod
   cp docker-compose_${BACKUP_NAME}.backup docker-compose.prod.yml
   cp nginx_${BACKUP_NAME}.backup nginx.conf
EOF

# バックアップの圧縮
echo "🗜️ バックアップを圧縮中..."
cd "$BACKUP_DIR"
tar -czf "sensechat_backup_${BACKUP_NAME}.tar.gz" \
    "database_${BACKUP_NAME}.sql" \
    "redis_${BACKUP_NAME}.rdb" \
    "env_${BACKUP_NAME}.backup" \
    "docker-compose_${BACKUP_NAME}.backup" \
    "nginx_${BACKUP_NAME}.backup" \
    "logs_${BACKUP_NAME}" \
    "backup_info_${BACKUP_NAME}.txt"

# 古いバックアップの削除（30日以上古いもの）
echo "🧹 古いバックアップを削除中..."
find . -name "sensechat_backup_*.tar.gz" -mtime +30 -delete

# AWS S3へのアップロード（環境変数が設定されている場合）
if [ ! -z "$S3_BACKUP_BUCKET" ] && [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "☁️ AWS S3にアップロード中..."
    aws s3 cp "sensechat_backup_${BACKUP_NAME}.tar.gz" "s3://$S3_BACKUP_BUCKET/backups/"
    echo "✅ S3アップロード完了: s3://$S3_BACKUP_BUCKET/backups/sensechat_backup_${BACKUP_NAME}.tar.gz"
fi

echo "🎉 バックアップ完了!"
echo "📁 バックアップファイル: $BACKUP_DIR/sensechat_backup_${BACKUP_NAME}.tar.gz"
echo "📋 バックアップ情報: $BACKUP_DIR/backup_info_${BACKUP_NAME}.txt"

# バックアップサイズの表示
BACKUP_SIZE=$(du -h "$BACKUP_DIR/sensechat_backup_${BACKUP_NAME}.tar.gz" | cut -f1)
echo "📊 バックアップサイズ: $BACKUP_SIZE"

#!/bin/bash

# SenseChat MVP セットアップスクリプト
# 家族内使用・技術検証版

set -e

echo "🚀 SenseChat MVP セットアップを開始します..."

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 関数定義
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 前提条件チェック
print_step "前提条件をチェックしています..."

# Docker チェック
if ! command -v docker &> /dev/null; then
    print_error "Docker がインストールされていません"
    echo "Docker をインストールしてください: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker Compose チェック
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose がインストールされていません"
    echo "Docker Compose をインストールしてください: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "前提条件チェック完了"

# 環境設定ファイルの作成
print_step "環境設定ファイルを作成しています..."

if [ ! -f .env ]; then
    cp env.example .env
    print_success ".env ファイルを作成しました"
    print_warning "API キーを設定してください: nano .env"
else
    print_warning ".env ファイルは既に存在します"
fi

# ディレクトリ構造の作成
print_step "ディレクトリ構造を作成しています..."

mkdir -p data
mkdir -p logs
mkdir -p config
mkdir -p frontend
mkdir -p backend

print_success "ディレクトリ構造作成完了"

# ユーザー設定ファイルの確認
print_step "ユーザー設定ファイルを確認しています..."

if [ ! -f config/users.json ]; then
    print_error "config/users.json が見つかりません"
    echo "ユーザー設定ファイルを作成してください"
    exit 1
fi

print_success "ユーザー設定ファイル確認完了"

# Docker イメージのビルド
print_step "Docker イメージをビルドしています..."

docker-compose build

print_success "Docker イメージビルド完了"

# データベースの初期化
print_step "データベースを初期化しています..."

docker-compose --profile init run --rm db-init

print_success "データベース初期化完了"

# サービスの起動
print_step "サービスを起動しています..."

docker-compose up -d

print_success "サービス起動完了"

# 起動確認
print_step "起動確認中..."

sleep 10

# ヘルスチェック
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "バックエンド API が正常に起動しています"
else
    print_warning "バックエンド API の起動を確認できませんでした"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_success "フロントエンドが正常に起動しています"
else
    print_warning "フロントエンドの起動を確認できませんでした"
fi

# 完了メッセージ
echo ""
echo "🎉 SenseChat MVP のセットアップが完了しました！"
echo ""
echo "📱 アクセス情報:"
echo "  フロントエンド: http://localhost:3000"
echo "  API: http://localhost:8000"
echo "  API文書: http://localhost:8000/docs"
echo ""
echo "🔧 管理コマンド:"
echo "  ログ確認: docker-compose logs -f"
echo "  停止: docker-compose down"
echo "  再起動: docker-compose restart"
echo ""
echo "⚠️  次のステップ:"
echo "  1. .env ファイルでAPIキーを設定"
echo "  2. config/users.json でユーザーを設定"
echo "  3. ブラウザで http://localhost:3000 にアクセス"
echo ""
echo "📚 詳細な使用方法は README.md を参照してください"

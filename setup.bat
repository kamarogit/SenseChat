@echo off
REM SenseChat MVP セットアップスクリプト (Windows版)
REM 家族内使用・技術検証版

setlocal enabledelayedexpansion

echo 🚀 SenseChat MVP セットアップを開始します...

REM 前提条件チェック
echo 📋 前提条件をチェックしています...

REM Docker チェック
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker がインストールされていません
    echo Docker をインストールしてください: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Docker Compose チェック
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose がインストールされていません
    echo Docker Compose をインストールしてください: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ 前提条件チェック完了

REM 環境設定ファイルの作成
echo 📋 環境設定ファイルを作成しています...

if not exist .env (
    copy env.example .env
    echo ✅ .env ファイルを作成しました
    echo ⚠️  API キーを設定してください: notepad .env
) else (
    echo ⚠️  .env ファイルは既に存在します
)

REM ディレクトリ構造の作成
echo 📋 ディレクトリ構造を作成しています...

if not exist data mkdir data
if not exist logs mkdir logs
if not exist config mkdir config
if not exist frontend mkdir frontend
if not exist backend mkdir backend

echo ✅ ディレクトリ構造作成完了

REM ユーザー設定ファイルの確認
echo 📋 ユーザー設定ファイルを確認しています...

if not exist config\users.json (
    echo ❌ config\users.json が見つかりません
    echo ユーザー設定ファイルを作成してください
    pause
    exit /b 1
)

echo ✅ ユーザー設定ファイル確認完了

REM Docker イメージのビルド
echo 📋 Docker イメージをビルドしています...

docker-compose build
if %errorlevel% neq 0 (
    echo ❌ Docker イメージのビルドに失敗しました
    pause
    exit /b 1
)

echo ✅ Docker イメージビルド完了

REM データベースの初期化
echo 📋 データベースを初期化しています...

docker-compose --profile init run --rm db-init
if %errorlevel% neq 0 (
    echo ⚠️  データベース初期化に失敗しましたが、続行します
)

echo ✅ データベース初期化完了

REM サービスの起動
echo 📋 サービスを起動しています...

docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ サービスの起動に失敗しました
    pause
    exit /b 1
)

echo ✅ サービス起動完了

REM 起動確認
echo 📋 起動確認中...

timeout /t 10 /nobreak >nul

REM ヘルスチェック
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ バックエンド API が正常に起動しています
) else (
    echo ⚠️  バックエンド API の起動を確認できませんでした
)

curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ フロントエンドが正常に起動しています
) else (
    echo ⚠️  フロントエンドの起動を確認できませんでした
)

REM 完了メッセージ
echo.
echo 🎉 SenseChat MVP のセットアップが完了しました！
echo.
echo 📱 アクセス情報:
echo   フロントエンド: http://localhost:3000
echo   API: http://localhost:8000
echo   API文書: http://localhost:8000/docs
echo.
echo 🔧 管理コマンド:
echo   ログ確認: docker-compose logs -f
echo   停止: docker-compose down
echo   再起動: docker-compose restart
echo.
echo ⚠️  次のステップ:
echo   1. .env ファイルでAPIキーを設定
echo   2. config\users.json でユーザーを設定
echo   3. ブラウザで http://localhost:3000 にアクセス
echo.
echo 📚 詳細な使用方法は README.md を参照してください
echo.
pause

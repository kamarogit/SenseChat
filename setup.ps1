# SenseChat MVP セットアップスクリプト (PowerShell版)
# 家族内使用・技術検証版

param(
    [switch]$SkipDockerCheck,
    [switch]$Force
)

# エラー時停止
$ErrorActionPreference = "Stop"

# カラー関数
function Write-Step { param($Message) Write-Host "📋 $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Write-Host "🚀 SenseChat MVP セットアップを開始します..." -ForegroundColor Cyan

try {
    # 前提条件チェック
    Write-Step "前提条件をチェックしています..."
    
    if (-not $SkipDockerCheck) {
        # Docker チェック
        try {
            $dockerVersion = docker --version 2>$null
            if (-not $dockerVersion) { throw "Docker not found" }
            Write-Success "Docker が見つかりました: $dockerVersion"
        }
        catch {
            Write-Error "Docker がインストールされていません"
            Write-Host "Docker をインストールしてください: https://docs.docker.com/get-docker/" -ForegroundColor Yellow
            exit 1
        }
        
        # Docker Compose チェック
        try {
            $composeVersion = docker-compose --version 2>$null
            if (-not $composeVersion) { throw "Docker Compose not found" }
            Write-Success "Docker Compose が見つかりました: $composeVersion"
        }
        catch {
            Write-Error "Docker Compose がインストールされていません"
            Write-Host "Docker Compose をインストールしてください: https://docs.docker.com/compose/install/" -ForegroundColor Yellow
            exit 1
        }
    }
    
    Write-Success "前提条件チェック完了"
    
    # 環境設定ファイルの作成
    Write-Step "環境設定ファイルを作成しています..."
    
    if (-not (Test-Path ".env") -or $Force) {
        if (Test-Path "env.example") {
            Copy-Item "env.example" ".env"
            Write-Success ".env ファイルを作成しました"
            Write-Warning "API キーを設定してください: notepad .env"
        } else {
            Write-Error "env.example ファイルが見つかりません"
            exit 1
        }
    } else {
        Write-Warning ".env ファイルは既に存在します"
    }
    
    # ディレクトリ構造の作成
    Write-Step "ディレクトリ構造を作成しています..."
    
    $directories = @("data", "logs", "config", "frontend", "backend")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
        }
    }
    
    Write-Success "ディレクトリ構造作成完了"
    
    # ユーザー設定ファイルの確認
    Write-Step "ユーザー設定ファイルを確認しています..."
    
    if (-not (Test-Path "config\users.json")) {
        Write-Error "config\users.json が見つかりません"
        Write-Host "ユーザー設定ファイルを作成してください" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Success "ユーザー設定ファイル確認完了"
    
    # Docker イメージのビルド
    Write-Step "Docker イメージをビルドしています..."
    
    docker-compose build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker イメージのビルドに失敗しました"
        exit 1
    }
    
    Write-Success "Docker イメージビルド完了"
    
    # データベースの初期化
    Write-Step "データベースを初期化しています..."
    
    docker-compose --profile init run --rm db-init
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "データベース初期化に失敗しましたが、続行します"
    }
    
    Write-Success "データベース初期化完了"
    
    # サービスの起動
    Write-Step "サービスを起動しています..."
    
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Error "サービスの起動に失敗しました"
        exit 1
    }
    
    Write-Success "サービス起動完了"
    
    # 起動確認
    Write-Step "起動確認中..."
    
    Start-Sleep -Seconds 10
    
    # ヘルスチェック
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "バックエンド API が正常に起動しています"
        }
    }
    catch {
        Write-Warning "バックエンド API の起動を確認できませんでした"
    }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "フロントエンドが正常に起動しています"
        }
    }
    catch {
        Write-Warning "フロントエンドの起動を確認できませんでした"
    }
    
    # 完了メッセージ
    Write-Host ""
    Write-Host "🎉 SenseChat MVP のセットアップが完了しました！" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 アクセス情報:" -ForegroundColor Cyan
    Write-Host "  フロントエンド: http://localhost:3000" -ForegroundColor White
    Write-Host "  API: http://localhost:8000" -ForegroundColor White
    Write-Host "  API文書: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 管理コマンド:" -ForegroundColor Cyan
    Write-Host "  ログ確認: docker-compose logs -f" -ForegroundColor White
    Write-Host "  停止: docker-compose down" -ForegroundColor White
    Write-Host "  再起動: docker-compose restart" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  次のステップ:" -ForegroundColor Yellow
    Write-Host "  1. .env ファイルでAPIキーを設定" -ForegroundColor White
    Write-Host "  2. config\users.json でユーザーを設定" -ForegroundColor White
    Write-Host "  3. ブラウザで http://localhost:3000 にアクセス" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 詳細な使用方法は README.md を参照してください" -ForegroundColor Cyan
    Write-Host ""
    
    # ブラウザで開くかどうか確認
    $openBrowser = Read-Host "ブラウザでアプリケーションを開きますか？ (y/N)"
    if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
        Start-Process "http://localhost:3000"
    }
}
catch {
    Write-Error "セットアップ中にエラーが発生しました: $($_.Exception.Message)"
    exit 1
}

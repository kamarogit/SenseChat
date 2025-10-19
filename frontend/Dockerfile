FROM node:18-alpine

# 作業ディレクトリの設定
WORKDIR /app

# パッケージファイルのコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm ci --only=production

# アプリケーションコードのコピー
COPY . .

# ビルド
RUN npm run build

# ポートの公開
EXPOSE 3000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# アプリケーションの起動
CMD ["npm", "start"]

"""
カスタム例外クラス
"""

class SenseChatException(Exception):
    """SenseChat 基底例外クラス"""
    pass

class EmbeddingError(SenseChatException):
    """Embedding生成エラー"""
    pass

class LLMAPICallError(SenseChatException):
    """LLM API呼び出しエラー"""
    pass

class VectorSearchError(SenseChatException):
    """ベクトル検索エラー"""
    pass

class DatabaseError(SenseChatException):
    """データベースエラー"""
    pass

class ValidationError(SenseChatException):
    """バリデーションエラー"""
    pass

def setup_exception_handlers(app):
    """例外ハンドラーの設定（middleware.pyで実装）"""
    pass

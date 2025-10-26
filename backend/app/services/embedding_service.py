"""
Embedding サービス
sentence-transformers を使用したローカル処理
"""

import numpy as np
from typing import List, Tuple, Dict, Any
import json
import os
from datetime import datetime
import warnings

# sentence-transformersのインポートを安全に行う
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: sentence-transformers not available: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

class EmbeddingService:
    """Embedding生成サービス"""
    
    def __init__(self):
        # 軽量モデルの読み込み
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.vector_dimension = 384
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(self.model_name)
                print(f"✅ SentenceTransformer loaded: {self.model_name}")
            except Exception as e:
                print(f"❌ Failed to load SentenceTransformer: {e}")
                self.model = None
        else:
            self.model = None
            print("⚠️  SentenceTransformer not available, using fallback")
        
    async def summarize_text(self, text: str, lang_hint: str = "auto") -> str:
        """テキスト要約（簡易版）"""
        # 簡易要約ロジック（実際の実装ではより高度な要約を使用）
        if len(text) <= 100:
            return text
        
        # 最初の文と最後の文を抽出
        sentences = text.split('。')
        if len(sentences) >= 2:
            summary = sentences[0] + '。' + sentences[-1] + '。'
        else:
            summary = text[:100] + '...'
        
        return summary
    
    async def create_embedding(self, text: str, lang_hint: str = "auto") -> Tuple[str, np.ndarray]:
        """テキストのベクトル化"""
        try:
            if self.model is not None:
                # sentence-transformersを使用
                vector = self.model.encode(text)
            else:
                # フォールバック: 簡単なハッシュベースのベクトル
                vector = self._create_fallback_embedding(text)
            
            # ベクトルID生成
            vector_id = f"vec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text) % 10000}"
            
            return vector_id, vector
            
        except Exception as e:
            print(f"Embedding生成エラー: {e}")
            # フォールバック
            vector = self._create_fallback_embedding(text)
            vector_id = f"vec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text) % 10000}"
            return vector_id, vector
    
    def _create_fallback_embedding(self, text: str) -> np.ndarray:
        """フォールバック用の簡単なベクトル生成"""
        # テキストのハッシュを基にした固定次元のベクトル
        text_hash = hash(text)
        vector = np.zeros(self.vector_dimension)
        
        # ハッシュ値を基にベクトルを生成
        for i in range(self.vector_dimension):
            vector[i] = (text_hash + i) % 1000 / 1000.0
        
        return vector.astype(np.float32)
    
    async def extract_slots(self, text: str, existing_slots: Dict[str, Any] = None) -> Dict[str, Any]:
        """スロット抽出（簡易版）"""
        slots = existing_slots or {}
        
        # 基本的なスロット抽出
        slots.update({
            "intent": self._extract_intent(text),
            "entities": self._extract_entities(text),
            "urgency": self._extract_urgency(text),
            "sentiment": self._extract_sentiment(text)
        })
        
        return slots
    
    def _extract_intent(self, text: str) -> str:
        """意図抽出（簡易版）"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["お願い", "please", "依頼", "request"]):
            return "request"
        elif any(word in text_lower for word in ["質問", "question", "？", "?"]):
            return "question"
        elif any(word in text_lower for word in ["報告", "report", "連絡", "contact"]):
            return "report"
        else:
            return "general"
    
    def _extract_entities(self, text: str) -> List[str]:
        """エンティティ抽出（簡易版）"""
        entities = []
        
        # 日付パターン
        import re
        date_pattern = r'\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2}'
        dates = re.findall(date_pattern, text)
        entities.extend(dates)
        
        # 時間パターン
        time_pattern = r'\d{1,2}:\d{2}|\d{1,2}時\d{2}分'
        times = re.findall(time_pattern, text)
        entities.extend(times)
        
        return entities
    
    def _extract_urgency(self, text: str) -> str:
        """緊急度抽出（簡易版）"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["緊急", "urgent", "急ぎ", "asap"]):
            return "high"
        elif any(word in text_lower for word in ["重要", "important", "優先"]):
            return "medium"
        else:
            return "normal"
    
    def _extract_sentiment(self, text: str) -> str:
        """感情抽出（簡易版）"""
        positive_words = ["ありがとう", "thank", "嬉しい", "happy", "良い", "good"]
        negative_words = ["困った", "problem", "問題", "issue", "悪い", "bad"]
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in positive_words):
            return "positive"
        elif any(word in text_lower for word in negative_words):
            return "negative"
        else:
            return "neutral"

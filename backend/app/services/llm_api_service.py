"""
LLM API サービス
Google PaLM API をメインに、フォールバック機能付き
"""

import httpx
import json
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime

class LLMAPIService:
    """LLM API サービス"""
    
    def __init__(self):
        self.providers = {
            'openai_gpt4': OpenAIClient(),
            'openrouter_claude': OpenRouterClient('anthropic/claude-3.5-sonnet'),
            'openrouter_gpt4o': OpenRouterClient('openai/gpt-4o'),
            'openrouter_gemini': OpenRouterClient('google/gemini-pro')
        }
        # 環境変数からデフォルトプロバイダーを取得
        self.current_provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai_gpt4")
        self.last_token_count = 0
        
    async def reconstruct_message(
        self, 
        summary: str, 
        slots: Dict[str, Any], 
        style_preset: str, 
        language: str, 
        neighbors: List[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """メッセージ再構成"""
        
        # プロンプト構築
        prompt = self._build_reconstruction_prompt(
            summary, slots, style_preset, language, neighbors
        )
        
        # フォールバック機能付きAPI呼び出し
        for provider_name, provider in self.providers.items():
            try:
                response = await provider.generate(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.7
                )
                
                self.current_provider = provider_name
                self.last_token_count = response.get('token_count', 0)
                
                return response['text'], response.get('confidence', 0.8)
                
            except Exception as e:
                print(f"Provider {provider_name} failed: {e}")
                continue
        
        # すべてのプロバイダーが失敗した場合のフォールバック
        print("⚠️  All LLM providers failed, using fallback reconstruction")
        return self._fallback_reconstruction(summary, style_preset, language)
    
    def _build_reconstruction_prompt(
        self, 
        summary: str, 
        slots: Dict[str, Any], 
        style_preset: str, 
        language: str, 
        neighbors: List[Dict[str, Any]]
    ) -> str:
        """再構成用プロンプトを構築"""
        
        style_instructions = {
            'biz_formal': 'ビジネス用の丁寧な敬語で、結論を先に述べ、署名を付けてください。',
            'emoji_casual': 'カジュアルで親しみやすい文体で、適度に絵文字を使ってください。',
            'technical': '技術的で正確な表現を使い、専門用語を適切に使用してください。'
        }
        
        prompt = f"""
以下の要約を{language}で{style_instructions.get(style_preset, '自然な文体で')}再構成してください。

要約: {summary}
スロット: {json.dumps(slots, ensure_ascii=False)}
参考情報: {json.dumps(neighbors, ensure_ascii=False)}

制約:
- 元の意味を保持する
- 指定されたスタイルに従う
- 100文字以内
- 自然で読みやすい文章にする
"""
        return prompt
    
    def _fallback_reconstruction(self, summary: str, style_preset: str, language: str) -> Tuple[str, float]:
        """フォールバック用の簡単な再構成"""
        
        # スタイルに応じた簡単な変換
        if style_preset == 'emoji_casual':
            if language == 'ja':
                reconstructed = f"こんにちは！😊 {summary} について何かお話ししたいことがあるの？"
            else:
                reconstructed = f"Hi! 😊 What would you like to talk about regarding {summary}?"
        elif style_preset == 'biz_formal':
            if language == 'ja':
                reconstructed = f"お疲れ様です。{summary} についてご相談がございます。"
            else:
                reconstructed = f"Good day. I would like to discuss {summary} with you."
        else:  # technical or default
            if language == 'ja':
                reconstructed = f"技術的な内容について: {summary}"
            else:
                reconstructed = f"Technical discussion: {summary}"
        
        return reconstructed, 0.5  # 低い信頼度

class OpenRouterClient:
    """OpenRouter API クライアント"""
    
    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
    async def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> Dict[str, Any]:
        """OpenRouter API でテキスト生成"""
        if not self.api_key:
            raise Exception("OpenRouter API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sensechat-mvp.local",
            "X-Title": "SenseChat MVP"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            
            return {
                "text": text,
                "confidence": 0.9,
                "token_count": data["usage"]["total_tokens"]
            }

class OpenAIClient:
    """OpenAI API クライアント（GPT-4）"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        
    async def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> Dict[str, Any]:
        """OpenAI GPT-4 API でテキスト生成"""
        if not self.api_key:
            raise Exception("OpenAI API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            
            return {
                "text": text,
                "confidence": 0.95,
                "token_count": data["usage"]["total_tokens"]
            }

# AnthropicClient は OpenRouterClient に統合されたため削除

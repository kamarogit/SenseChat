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
            'google_palm': GooglePaLMClient(),
            'openai': OpenAIClient(),
            'anthropic': AnthropicClient()
        }
        self.current_provider = 'google_palm'
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
        
        raise Exception("All LLM providers failed")
    
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

class GooglePaLMClient:
    """Google PaLM API クライアント"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PALM_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    async def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> Dict[str, Any]:
        """Google PaLM API でテキスト生成"""
        if not self.api_key:
            raise Exception("Google PaLM API key not configured")
        
        url = f"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            return {
                "text": text,
                "confidence": 0.8,
                "token_count": len(prompt.split()) + len(text.split())
            }

class OpenAIClient:
    """OpenAI API クライアント"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        
    async def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> Dict[str, Any]:
        """OpenAI API でテキスト生成"""
        if not self.api_key:
            raise Exception("OpenAI API key not configured")
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": "gpt-3.5-turbo",
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
                "confidence": 0.9,
                "token_count": data["usage"]["total_tokens"]
            }

class AnthropicClient:
    """Anthropic Claude API クライアント"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        
    async def generate(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> Dict[str, Any]:
        """Anthropic Claude API でテキスト生成"""
        if not self.api_key:
            raise Exception("Anthropic API key not configured")
        
        url = f"{self.base_url}/messages"
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            text = data["content"][0]["text"]
            
            return {
                "text": text,
                "confidence": 0.85,
                "token_count": data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
            }

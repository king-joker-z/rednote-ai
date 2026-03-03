"""OpenAI GPT LLM"""

import os
import httpx
from typing import List
from .base import BaseLLM, Message


class OpenAILLM(BaseLLM):
    """OpenAI GPT API"""
    
    provider = "openai"
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str = None,
        base_url: str = "https://api.openai.com/v1",
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """调用 OpenAI API"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        chat_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""

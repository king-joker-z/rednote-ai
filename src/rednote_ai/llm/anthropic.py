"""Anthropic Claude LLM"""

import os
import httpx
from typing import List
from .base import BaseLLM, Message


class AnthropicLLM(BaseLLM):
    """Anthropic Claude API"""
    
    provider = "anthropic"
    
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str = None,
        base_url: str = "https://api.anthropic.com",
    ):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """调用 Claude API"""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        system = None
        chat_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})
        
        payload = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return ""

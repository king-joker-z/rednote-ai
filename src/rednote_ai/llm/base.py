"""LLM 基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, AsyncIterator


@dataclass
class Message:
    """聊天消息"""
    role: str  # system / user / assistant
    content: str


class BaseLLM(ABC):
    """LLM 基类"""
    
    provider: str = "base"
    model: str = ""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """同步聊天"""
        pass
    
    async def generate(
        self,
        prompt: str,
        system: str = None,
        **kwargs
    ) -> str:
        """简单生成接口"""
        messages = []
        if system:
            messages.append(Message(role="system", content=system))
        messages.append(Message(role="user", content=prompt))
        return await self.chat(messages, **kwargs)

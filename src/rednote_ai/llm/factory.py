"""LLM 工厂"""

from .base import BaseLLM
from .anthropic import AnthropicLLM
from .openai import OpenAILLM


def create_llm(
    provider: str = "anthropic",
    model: str = None,
    api_key: str = None,
    base_url: str = None,
) -> BaseLLM:
    """创建 LLM 实例"""
    
    if provider == "anthropic":
        return AnthropicLLM(
            model=model or "claude-3-5-sonnet-20241022",
            api_key=api_key,
            base_url=base_url or "https://api.anthropic.com",
        )
    elif provider == "openai":
        return OpenAILLM(
            model=model or "gpt-4o-mini",
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

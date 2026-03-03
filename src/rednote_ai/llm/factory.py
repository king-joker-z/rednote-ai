"""LLM 工厂 - 支持自定义 base_url 和 model"""

import os
from typing import Optional
from .base import BaseLLM
from .anthropic import AnthropicLLM
from .openai import OpenAILLM


def create_llm(
    provider: str = "anthropic",
    model: str = None,
    api_key: str = None,
    base_url: str = None,
    **kwargs,
) -> BaseLLM:
    """
    创建 LLM 实例
    
    Args:
        provider: 提供商 (anthropic / openai / openai_compatible)
        model: 模型名称
        api_key: API Key（可从环境变量读取）
        base_url: API 地址（可自定义代理或兼容 API）
        
    Examples:
        # 默认 Claude
        llm = create_llm()
        
        # 自定义 OpenAI 兼容 API
        llm = create_llm(
            provider="openai",
            model="deepseek-chat",
            api_key="sk-xxx",
            base_url="https://api.deepseek.com/v1"
        )
        
        # 从配置字典创建
        llm = create_llm(**config["llm"]["writer"])
    """
    
    # 支持 openai_compatible 别名
    if provider == "openai_compatible":
        provider = "openai"
    
    if provider == "anthropic":
        return AnthropicLLM(
            model=model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url=base_url or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
        )
    
    elif provider == "openai":
        return OpenAILLM(
            model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: anthropic, openai")


def create_llm_from_config(config: dict) -> BaseLLM:
    """从配置字典创建 LLM"""
    return create_llm(
        provider=config.get("provider", "anthropic"),
        model=config.get("model"),
        api_key=config.get("api_key"),
        base_url=config.get("base_url"),
    )

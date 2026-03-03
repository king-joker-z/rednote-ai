"""Twitter/X 信息源"""

from typing import List
from .base import BaseSource, NewsItem


class TwitterSource(BaseSource):
    """Twitter/X AI 热点抓取"""
    
    name = "twitter"
    
    # AI 领域值得关注的账号
    AI_ACCOUNTS = [
        "OpenAI",
        "AnthropicAI", 
        "GoogleDeepMind",
        "ylecun",
        "kaboroevite",  # Karpathy
        "sama",  # Sam Altman
        "EMostaque",
        "hardmaru",
    ]
    
    def __init__(self, cookies: str = None):
        self.cookies = cookies
    
    async def fetch(self, limit: int = 20) -> List[NewsItem]:
        """抓取 AI 大 V 最新推文"""
        # TODO: 使用 xreach CLI 抓取
        pass
    
    async def search(self, query: str, limit: int = 20) -> List[NewsItem]:
        """搜索 AI 相关推文"""
        # TODO: 使用 xreach CLI 搜索
        pass

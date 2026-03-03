"""GitHub Trending 信息源"""

from typing import List
from .base import BaseSource, NewsItem


class GithubSource(BaseSource):
    """GitHub Trending 抓取"""
    
    name = "github"
    
    async def fetch(self, limit: int = 20) -> List[NewsItem]:
        """抓取 GitHub Trending"""
        # TODO: 使用 gh CLI 或爬虫抓取
        pass
    
    async def search(self, query: str, limit: int = 20) -> List[NewsItem]:
        """搜索仓库"""
        # TODO: 使用 gh search repos
        pass

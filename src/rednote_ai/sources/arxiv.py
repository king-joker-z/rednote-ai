"""Arxiv 论文信息源"""

import feedparser
from typing import List
from datetime import datetime
from .base import BaseSource, NewsItem


class ArxivSource(BaseSource):
    """Arxiv AI 论文抓取"""
    
    name = "arxiv"
    
    # AI 相关分类
    CATEGORIES = [
        "cs.AI",   # Artificial Intelligence
        "cs.LG",   # Machine Learning
        "cs.CL",   # Computation and Language (NLP)
        "cs.CV",   # Computer Vision
    ]
    
    async def fetch(self, limit: int = 20) -> List[NewsItem]:
        """抓取最新 AI 论文"""
        items = []
        for cat in self.CATEGORIES:
            url = f"http://export.arxiv.org/rss/{cat}"
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit // len(self.CATEGORIES)]:
                items.append(NewsItem(
                    id=entry.id,
                    title=entry.title,
                    summary=entry.summary,
                    url=entry.link,
                    source="arxiv",
                    published_at=datetime.now(),
                    tags=[cat],
                ))
        return items[:limit]
    
    async def search(self, query: str, limit: int = 20) -> List[NewsItem]:
        """搜索论文"""
        # TODO: 使用 arxiv API 搜索
        pass

"""RSS/Atom 信息源"""

import feedparser
from typing import List
from datetime import datetime
from .base import BaseSource, NewsItem


class RSSSource(BaseSource):
    """RSS/Atom 订阅源"""
    
    name = "rss"
    
    def __init__(self, feeds: List[str] = None):
        self.feeds = feeds or []
    
    async def fetch(self, limit: int = 20) -> List[NewsItem]:
        """抓取所有订阅源"""
        items = []
        for feed_url in self.feeds:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                items.append(NewsItem(
                    id=entry.get("id", entry.link),
                    title=entry.title,
                    summary=entry.get("summary", ""),
                    url=entry.link,
                    source=feed.feed.get("title", "rss"),
                    published_at=datetime.now(),
                ))
        return sorted(items, key=lambda x: x.published_at, reverse=True)[:limit]
    
    async def search(self, query: str, limit: int = 20) -> List[NewsItem]:
        """RSS 不支持搜索"""
        return []

"""信息源基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class NewsItem:
    """新闻/热点条目"""
    id: str
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    score: float = 0.0  # 热度分数
    tags: List[str] = None
    raw_data: dict = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.raw_data is None:
            self.raw_data = {}


class BaseSource(ABC):
    """信息源基类"""
    
    name: str = "base"
    
    @abstractmethod
    async def fetch(self, limit: int = 20) -> List[NewsItem]:
        """抓取最新内容"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[NewsItem]:
        """搜索内容"""
        pass

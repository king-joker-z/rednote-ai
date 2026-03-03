"""核心业务逻辑 - 串联各模块"""

import asyncio
from typing import List, Optional
from dataclasses import dataclass

from .sources.base import NewsItem
from .sources.twitter import TwitterSource
from .sources.arxiv import ArxivSource
from .sources.github import GithubSource
from .sources.rss import RSSSource
from .analyze.trending import TrendingAnalyzer, TrendingScore
from .generate.writer import XiaohongshuWriter, GeneratedContent, ContentStyle
from .llm import create_llm


@dataclass
class ContentDraft:
    """内容草稿"""
    id: str
    content: GeneratedContent
    score: float
    status: str = "draft"  # draft / approved / published


class RedNoteAI:
    """RedNote AI 主类"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # 初始化信息源
        self.sources = {
            "twitter": TwitterSource(),
            "arxiv": ArxivSource(),
            "github": GithubSource(),
        }
        
        # 初始化分析器
        self.analyzer = TrendingAnalyzer()
        
        # 初始化生成器
        llm_config = self.config.get("llm", {}).get("writer", {})
        self.writer = XiaohongshuWriter(llm_config=llm_config if llm_config else None)
        
        # 草稿存储
        self.drafts: List[ContentDraft] = []
    
    async def fetch_all(self, limit: int = 20) -> List[NewsItem]:
        """从所有源抓取内容"""
        all_items = []
        
        tasks = []
        for name, source in self.sources.items():
            if self.config.get("sources", {}).get(name, {}).get("enabled", True):
                tasks.append(source.fetch(limit=limit // len(self.sources)))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                print(f"Fetch error: {result}")
        
        return all_items
    
    async def fetch_source(self, source_name: str, limit: int = 20) -> List[NewsItem]:
        """从指定源抓取"""
        source = self.sources.get(source_name)
        if source:
            return await source.fetch(limit=limit)
        return []
    
    async def analyze_trending(self, items: List[NewsItem]) -> List[TrendingScore]:
        """分析热点排序"""
        return await self.analyzer.analyze(items)
    
    async def generate_content(
        self,
        item: NewsItem,
        style: ContentStyle = ContentStyle.NEWS,
    ) -> GeneratedContent:
        """生成单条内容"""
        return await self.writer.generate_single(item, style)
    
    async def generate_digest(
        self,
        items: List[NewsItem],
        max_items: int = 5,
    ) -> GeneratedContent:
        """生成日报"""
        return await self.writer.generate_digest(items, max_items)
    
    async def run_pipeline(
        self,
        sources: List[str] = None,
        limit: int = 20,
        top_n: int = 5,
        generate_digest: bool = True,
    ) -> List[ContentDraft]:
        """运行完整流程"""
        
        print("📡 Step 1: 抓取内容...")
        if sources:
            all_items = []
            for source in sources:
                items = await self.fetch_source(source, limit=limit)
                all_items.extend(items)
        else:
            all_items = await self.fetch_all(limit=limit)
        
        print(f"   获取到 {len(all_items)} 条内容")
        
        if not all_items:
            print("   ⚠️ 没有获取到内容")
            return []
        
        print("🧠 Step 2: 分析热点...")
        scored_items = await self.analyze_trending(all_items)
        top_items = scored_items[:top_n]
        
        print(f"   Top {len(top_items)} 热点:")
        for i, scored in enumerate(top_items):
            print(f"   {i+1}. [{scored.total:.2f}] {scored.news_item.title[:50]}...")
        
        print("✍️ Step 3: 生成内容...")
        drafts = []
        
        if generate_digest and len(top_items) >= 3:
            # 生成日报
            news_items = [s.news_item for s in top_items]
            content = await self.generate_digest(news_items)
            draft = ContentDraft(
                id=f"digest-{len(self.drafts)}",
                content=content,
                score=sum(s.total for s in top_items) / len(top_items),
            )
            drafts.append(draft)
            print(f"   📰 生成日报: {content.title}")
        
        # 生成单条内容
        for scored in top_items[:3]:
            content = await self.generate_content(scored.news_item)
            draft = ContentDraft(
                id=f"single-{len(self.drafts) + len(drafts)}",
                content=content,
                score=scored.total,
            )
            drafts.append(draft)
            print(f"   📝 生成内容: {content.title}")
        
        self.drafts.extend(drafts)
        
        print(f"✅ 完成！生成 {len(drafts)} 篇草稿")
        return drafts

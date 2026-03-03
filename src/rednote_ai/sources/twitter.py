"""Twitter/X 信息源 - 使用 xreach CLI"""

import json
import subprocess
import asyncio
from typing import List, Optional
from datetime import datetime
from .base import BaseSource, NewsItem


class TwitterSource(BaseSource):
    """Twitter/X AI 热点抓取（通过 xreach CLI）"""
    
    name = "twitter"
    
    # AI 领域值得关注的账号
    AI_ACCOUNTS = [
        "OpenAI", "AnthropicAI", "GoogleDeepMind", "xaboroevitch",
        "sama", "ylecun", "kaboroevich", "EMostaque", "hardmaru",
        "ai_for_success", "bindureddy", "TheAIGRID",
    ]
    
    # AI 相关搜索关键词
    AI_KEYWORDS = [
        "GPT-5", "Claude", "Gemini", "LLM", "AI agent",
        "ChatGPT", "Sora", "text to video", "multimodal",
    ]
    
    def __init__(self, cookies: str = None):
        self.cookies = cookies
        self._check_xreach()
    
    def _check_xreach(self):
        """检查 xreach CLI 是否可用"""
        try:
            result = subprocess.run(
                ["xreach", "--version"],
                capture_output=True, text=True, timeout=10
            )
            self.xreach_available = result.returncode == 0
        except Exception:
            self.xreach_available = False
    
    def _run_xreach(self, args: List[str]) -> Optional[str]:
        """运行 xreach 命令"""
        if not self.xreach_available:
            return None
        try:
            result = subprocess.run(
                ["xreach"] + args + ["--json"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            print(f"xreach error: {e}")
        return None
    
    async def fetch(self, limit: int = 20) -> List[NewsItem]:
        """抓取 AI 大 V 最新推文"""
        items = []
        
        # 搜索 AI 相关推文
        for keyword in self.AI_KEYWORDS[:3]:  # 只搜前 3 个关键词
            output = self._run_xreach(["search", keyword, "--limit", str(limit // 3)])
            if output:
                items.extend(self._parse_tweets(output, keyword))
        
        # 去重并返回
        seen = set()
        unique_items = []
        for item in items:
            if item.id not in seen:
                seen.add(item.id)
                unique_items.append(item)
        
        return unique_items[:limit]
    
    async def fetch_from_user(self, username: str, limit: int = 10) -> List[NewsItem]:
        """抓取指定用户的推文"""
        output = self._run_xreach(["user", username, "--limit", str(limit)])
        if output:
            return self._parse_tweets(output, f"@{username}")
        return []
    
    async def search(self, query: str, limit: int = 20) -> List[NewsItem]:
        """搜索推文"""
        output = self._run_xreach(["search", query, "--limit", str(limit)])
        if output:
            return self._parse_tweets(output, query)
        return []
    
    def _parse_tweets(self, json_output: str, source_tag: str) -> List[NewsItem]:
        """解析 xreach JSON 输出"""
        items = []
        try:
            data = json.loads(json_output)
            tweets = data if isinstance(data, list) else data.get("tweets", [])
            
            for tweet in tweets:
                items.append(NewsItem(
                    id=tweet.get("id", ""),
                    title=tweet.get("text", "")[:100],
                    summary=tweet.get("text", ""),
                    url=tweet.get("url", f"https://x.com/i/status/{tweet.get('id', '')}"),
                    source="twitter",
                    published_at=self._parse_date(tweet.get("created_at")),
                    score=self._calc_score(tweet),
                    tags=[source_tag],
                    raw_data=tweet,
                ))
        except json.JSONDecodeError:
            pass
        return items
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期"""
        if not date_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now()
    
    def _calc_score(self, tweet: dict) -> float:
        """计算推文热度分数"""
        likes = tweet.get("likes", 0) or 0
        retweets = tweet.get("retweets", 0) or 0
        replies = tweet.get("replies", 0) or 0
        
        # 简单加权计算
        return (likes * 1 + retweets * 2 + replies * 1.5) / 100

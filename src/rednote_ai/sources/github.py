"""GitHub Trending 信息源"""

import subprocess
import json
import re
from typing import List, Optional
from datetime import datetime
from .base import BaseSource, NewsItem


class GithubSource(BaseSource):
    """GitHub Trending 和 AI 相关仓库抓取"""
    
    name = "github"
    
    # AI 相关搜索词
    AI_TOPICS = ["llm", "ai-agent", "gpt", "langchain", "rag", "embedding"]
    
    def __init__(self):
        self._check_gh()
    
    def _check_gh(self):
        """检查 gh CLI 是否可用"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True, text=True, timeout=10
            )
            self.gh_available = result.returncode == 0
        except Exception:
            self.gh_available = False
    
    def _run_gh(self, args: List[str]) -> Optional[str]:
        """运行 gh 命令"""
        if not self.gh_available:
            return None
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            print(f"gh error: {e}")
        return None
    
    async def fetch(self, limit: int = 20) -> List[NewsItem]:
        """抓取 AI 相关热门仓库"""
        items = []
        
        for topic in self.AI_TOPICS[:3]:
            output = self._run_gh([
                "search", "repos", topic,
                "--sort", "stars",
                "--limit", str(limit // 3),
                "--json", "name,owner,description,url,stargazersCount,updatedAt"
            ])
            if output:
                items.extend(self._parse_repos(output, topic))
        
        # 按 stars 排序去重
        seen = set()
        unique_items = []
        for item in sorted(items, key=lambda x: x.score, reverse=True):
            if item.id not in seen:
                seen.add(item.id)
                unique_items.append(item)
        
        return unique_items[:limit]
    
    async def search(self, query: str, limit: int = 20) -> List[NewsItem]:
        """搜索仓库"""
        output = self._run_gh([
            "search", "repos", query,
            "--sort", "stars",
            "--limit", str(limit),
            "--json", "name,owner,description,url,stargazersCount,updatedAt"
        ])
        if output:
            return self._parse_repos(output, query)
        return []
    
    async def get_trending(self, language: str = None, since: str = "daily") -> List[NewsItem]:
        """获取 Trending（通过 API 或爬虫）"""
        # GitHub 没有官方 Trending API，这里用搜索近期高星项目代替
        query = "stars:>100 pushed:>2024-01-01"
        if language:
            query += f" language:{language}"
        return await self.search(query, limit=20)
    
    def _parse_repos(self, json_output: str, source_tag: str) -> List[NewsItem]:
        """解析 gh JSON 输出"""
        items = []
        try:
            repos = json.loads(json_output)
            
            for repo in repos:
                owner = repo.get("owner", {})
                owner_login = owner.get("login", "") if isinstance(owner, dict) else str(owner)
                
                items.append(NewsItem(
                    id=f"{owner_login}/{repo.get('name', '')}",
                    title=f"{owner_login}/{repo.get('name', '')}",
                    summary=repo.get("description", "") or "No description",
                    url=repo.get("url", ""),
                    source="github",
                    published_at=self._parse_date(repo.get("updatedAt")),
                    score=repo.get("stargazersCount", 0) / 1000,  # 归一化
                    tags=[source_tag, "github"],
                    raw_data=repo,
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

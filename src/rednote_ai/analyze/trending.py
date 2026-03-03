"""热点分析与打分"""

from typing import List
from dataclasses import dataclass
from ..sources.base import NewsItem


@dataclass
class TrendingScore:
    """热点评分"""
    news_item: NewsItem
    relevance: float    # AI 相关度 0-1
    freshness: float    # 新鲜度 0-1
    engagement: float   # 互动潜力 0-1
    total: float        # 综合分数


class TrendingAnalyzer:
    """热点分析器"""
    
    # AI 相关关键词
    AI_KEYWORDS = [
        "GPT", "Claude", "LLM", "大模型", "AI", "人工智能",
        "机器学习", "深度学习", "神经网络", "Transformer",
        "ChatGPT", "OpenAI", "Anthropic", "Google", "Meta",
        "Agent", "RAG", "向量", "Embedding", "Fine-tune",
        "多模态", "AIGC", "Sora", "视频生成", "图像生成",
    ]
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
    
    def score_relevance(self, item: NewsItem) -> float:
        """计算 AI 相关度"""
        text = f"{item.title} {item.summary}".lower()
        matches = sum(1 for kw in self.AI_KEYWORDS if kw.lower() in text)
        return min(matches / 5, 1.0)
    
    def score_freshness(self, item: NewsItem) -> float:
        """计算新鲜度"""
        # TODO: 基于发布时间计算
        return 0.8
    
    async def analyze(self, items: List[NewsItem]) -> List[TrendingScore]:
        """分析并排序热点"""
        scores = []
        for item in items:
            relevance = self.score_relevance(item)
            freshness = self.score_freshness(item)
            engagement = 0.5  # TODO: 使用 LLM 预测互动潜力
            
            total = relevance * 0.4 + freshness * 0.3 + engagement * 0.3
            
            scores.append(TrendingScore(
                news_item=item,
                relevance=relevance,
                freshness=freshness,
                engagement=engagement,
                total=total,
            ))
        
        return sorted(scores, key=lambda x: x.total, reverse=True)

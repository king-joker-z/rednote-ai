"""小红书风格文案生成"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ContentStyle(Enum):
    """内容风格"""
    NEWS = "news"           # 新闻速递
    TUTORIAL = "tutorial"   # 教程干货
    REVIEW = "review"       # 测评体验
    OPINION = "opinion"     # 观点输出


@dataclass
class GeneratedContent:
    """生成的内容"""
    title: str              # 标题（带 emoji）
    content: str            # 正文
    tags: List[str]         # 话题标签
    cover_prompt: str       # 封面图生成 prompt
    image_prompts: List[str] = None  # 内页图 prompts
    
    def __post_init__(self):
        if self.image_prompts is None:
            self.image_prompts = []


class XiaohongshuWriter:
    """小红书风格文案生成器"""
    
    # 爆文标题模板
    TITLE_TEMPLATES = [
        "🔥 {topic}，{highlight}！",
        "❗️ {topic}来了！{highlight}",
        "💡 {number}个{topic}技巧，{highlight}",
        "😱 {topic}竟然{highlight}？",
        "✨ {year}年{topic}，{highlight}",
    ]
    
    # 小红书风格 prompt
    SYSTEM_PROMPT = """你是一个专业的小红书 AI 科技博主，擅长将复杂的 AI 技术用通俗易懂的方式讲解。

写作风格要求：
1. 标题：带 emoji，≤20字，使用数字/反问/惊叹吸引点击
2. 开头：直接抛出价值点或痛点，不要寒暄
3. 正文：
   - 分段清晰，每段≤3行
   - 适当使用 emoji 增加可读性
   - 用「」标注关键词
   - 复杂概念用类比解释
4. 结尾：引导互动（点赞/收藏/评论）
5. 标签：3-5个相关话题标签

请用轻松活泼但专业的语气，让普通人也能看懂 AI 技术。"""

    def __init__(self, llm_client=None):
        self.llm = llm_client
    
    async def generate(
        self,
        news_item,
        style: ContentStyle = ContentStyle.NEWS,
        reference_posts: List[str] = None,
    ) -> GeneratedContent:
        """生成小红书内容"""
        # TODO: 调用 LLM 生成内容
        pass
    
    async def generate_variants(
        self,
        news_item,
        count: int = 3,
    ) -> List[GeneratedContent]:
        """生成多个版本供选择"""
        # TODO: 生成多个变体
        pass

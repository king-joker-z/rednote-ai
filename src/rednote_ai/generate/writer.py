"""小红书风格文案生成"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from ..llm import BaseLLM, Message, create_llm
from ..sources.base import NewsItem


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
    source_item: NewsItem = None  # 原始素材
    image_prompts: List[str] = field(default_factory=list)


class XiaohongshuWriter:
    """小红书风格文案生成器"""
    
    # 系统 Prompt
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

    # 新闻速递 Prompt
    NEWS_PROMPT = """请将以下 AI 新闻/热点转化为小红书风格的图文内容。

新闻素材：
{news_content}

要求：
1. 标题要吸引眼球，带 emoji
2. 用通俗语言解释技术要点
3. 说明这对普通用户的影响
4. 添加个人观点或评价
5. 结尾引导互动

请直接输出，格式如下：
【标题】
(标题内容)

【正文】
(正文内容，分段，带emoji)

【标签】
#标签1 #标签2 #标签3

【封面图描述】
(用于 AI 生成封面图的英文描述)"""

    # 多条新闻汇总 Prompt
    DIGEST_PROMPT = """请将以下多条 AI 新闻整理成一篇小红书「AI 日报」。

新闻列表：
{news_list}

要求：
1. 标题：如「🔥 AI日报｜今日X条大事」
2. 开头列出要点速览
3. 逐条简要解读
4. 结尾总结 + 互动引导

请直接输出，格式如下：
【标题】
(标题内容)

【正文】
(正文内容)

【标签】
#AI日报 #人工智能 ...

【封面图描述】
(英文描述)"""

    def __init__(self, llm: BaseLLM = None, llm_config: dict = None):
        if llm:
            self.llm = llm
        elif llm_config:
            self.llm = create_llm(**llm_config)
        else:
            self.llm = create_llm(provider="anthropic")
    
    async def generate_single(
        self,
        news_item: NewsItem,
        style: ContentStyle = ContentStyle.NEWS,
    ) -> GeneratedContent:
        """从单条新闻生成内容"""
        
        news_content = f"""标题：{news_item.title}
来源：{news_item.source}
内容：{news_item.summary}
链接：{news_item.url}"""
        
        prompt = self.NEWS_PROMPT.format(news_content=news_content)
        
        result = await self.llm.generate(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            temperature=0.8,
        )
        
        return self._parse_result(result, news_item)
    
    async def generate_digest(
        self,
        news_items: List[NewsItem],
        max_items: int = 5,
    ) -> GeneratedContent:
        """从多条新闻生成日报"""
        
        news_list = "\n\n".join([
            f"{i+1}. 【{item.title}】\n   {item.summary[:200]}...\n   来源：{item.source}"
            for i, item in enumerate(news_items[:max_items])
        ])
        
        prompt = self.DIGEST_PROMPT.format(news_list=news_list)
        
        result = await self.llm.generate(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            temperature=0.8,
        )
        
        return self._parse_result(result, news_items[0] if news_items else None)
    
    async def generate_variants(
        self,
        news_item: NewsItem,
        count: int = 3,
    ) -> List[GeneratedContent]:
        """生成多个版本供选择"""
        variants = []
        for i in range(count):
            content = await self.generate_single(
                news_item,
                style=ContentStyle.NEWS,
            )
            variants.append(content)
        return variants
    
    def _parse_result(self, result: str, source_item: NewsItem = None) -> GeneratedContent:
        """解析 LLM 输出"""
        title = ""
        content = ""
        tags = []
        cover_prompt = ""
        
        sections = result.split("【")
        for section in sections:
            if section.startswith("标题】"):
                title = section.replace("标题】", "").strip().split("\n")[0]
            elif section.startswith("正文】"):
                content = section.replace("正文】", "").strip()
                # 移除可能的后续 section
                if "【标签】" in content:
                    content = content.split("【标签】")[0].strip()
                if "【封面" in content:
                    content = content.split("【封面")[0].strip()
            elif section.startswith("标签】"):
                tag_text = section.replace("标签】", "").strip().split("\n")[0]
                tags = [t.strip() for t in tag_text.replace("#", " #").split("#") if t.strip()]
            elif "封面" in section and "描述】" in section:
                cover_prompt = section.split("描述】")[-1].strip().split("\n")[0]
        
        return GeneratedContent(
            title=title,
            content=content,
            tags=tags,
            cover_prompt=cover_prompt,
            source_item=source_item,
        )

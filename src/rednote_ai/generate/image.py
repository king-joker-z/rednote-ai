"""配图生成模块"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ImageStyle(Enum):
    """图片风格"""
    TECH = "tech"           # 科技感
    MINIMAL = "minimal"     # 简约风
    CARTOON = "cartoon"     # 卡通风
    GRADIENT = "gradient"   # 渐变背景


@dataclass
class GeneratedImage:
    """生成的图片"""
    url: str                # 图片 URL
    prompt: str             # 使用的 prompt
    style: ImageStyle       # 风格
    width: int = 1080
    height: int = 1440      # 小红书 3:4 比例


class ImageGenerator:
    """配图生成器"""
    
    # 小红书封面图 prompt 模板
    COVER_TEMPLATES = {
        ImageStyle.TECH: "modern tech blog cover, {topic}, futuristic, clean design, blue and purple gradient, minimalist, professional",
        ImageStyle.MINIMAL: "minimalist blog cover, {topic}, white background, simple icons, elegant typography",
        ImageStyle.CARTOON: "cute cartoon illustration, {topic}, kawaii style, pastel colors, friendly characters",
        ImageStyle.GRADIENT: "gradient background, {topic}, modern design, bold text overlay, social media style",
    }
    
    def __init__(self, provider: str = "dalle", api_key: str = None):
        self.provider = provider
        self.api_key = api_key
    
    async def generate_cover(
        self,
        topic: str,
        style: ImageStyle = ImageStyle.TECH,
    ) -> GeneratedImage:
        """生成封面图"""
        # TODO: 调用图片生成 API
        pass
    
    async def generate_content_images(
        self,
        content: str,
        count: int = 3,
    ) -> List[GeneratedImage]:
        """生成内页配图"""
        # TODO: 根据内容生成配图
        pass

"""图片生成模块 - 用于生成小红书封面和内页配图"""

import os
import httpx
import base64
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GeneratedImage:
    """生成的图片"""
    path: str           # 本地保存路径
    url: Optional[str]  # 远程 URL（如果有）
    prompt: str         # 使用的 prompt
    width: int = 1080
    height: int = 1440  # 小红书推荐 3:4


class ImageGenerator:
    """AI 配图生成器"""
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "dall-e-3",
        api_key: str = None,
        base_url: str = None,
        output_dir: str = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.output_dir = Path(output_dir or "./output/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_cover(
        self,
        prompt: str,
        style: str = "tech",
        draft_id: str = None,
    ) -> Optional[GeneratedImage]:
        """生成封面图"""
        
        # 增强 prompt，适配小红书风格
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        if self.provider == "openai":
            return await self._generate_openai(enhanced_prompt, draft_id, "cover")
        else:
            print(f"Unsupported provider: {self.provider}")
            return None
    
    async def generate_content_images(
        self,
        prompts: List[str],
        draft_id: str = None,
    ) -> List[GeneratedImage]:
        """生成内页配图"""
        images = []
        for i, prompt in enumerate(prompts):
            img = await self._generate_openai(prompt, draft_id, f"content_{i}")
            if img:
                images.append(img)
        return images
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """增强 prompt，适配小红书风格"""
        
        style_suffixes = {
            "tech": "modern tech style, clean design, gradient background, professional, minimalist, suitable for social media",
            "cute": "cute kawaii style, pastel colors, rounded corners, friendly, Instagram aesthetic",
            "minimal": "minimalist design, white space, elegant typography, clean lines",
            "gradient": "beautiful gradient background, modern design, vibrant colors, social media ready",
        }
        
        suffix = style_suffixes.get(style, style_suffixes["tech"])
        
        return f"{prompt}, {suffix}, 3:4 aspect ratio, high quality"
    
    async def _generate_openai(
        self,
        prompt: str,
        draft_id: str = None,
        image_type: str = "cover",
    ) -> Optional[GeneratedImage]:
        """使用 OpenAI DALL-E 生成图片"""
        
        if not self.api_key:
            print("OpenAI API key not set")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",  # DALL-E 3 支持的尺寸
                        "quality": "standard",
                        "response_format": "b64_json",  # 返回 base64
                    },
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    img_data = data["data"][0]
                    
                    # 保存图片
                    filename = f"{draft_id or 'img'}_{image_type}.png"
                    filepath = self.output_dir / filename
                    
                    if "b64_json" in img_data:
                        img_bytes = base64.b64decode(img_data["b64_json"])
                        with open(filepath, "wb") as f:
                            f.write(img_bytes)
                    elif "url" in img_data:
                        # 下载图片
                        img_response = await client.get(img_data["url"])
                        with open(filepath, "wb") as f:
                            f.write(img_response.content)
                    
                    return GeneratedImage(
                        path=str(filepath),
                        url=img_data.get("url"),
                        prompt=prompt,
                    )
                    
        except Exception as e:
            print(f"Image generation failed: {e}")
            return None
        
        return None
    
    async def generate_text_image(
        self,
        title: str,
        subtitle: str = None,
        style: str = "gradient",
        draft_id: str = None,
    ) -> Optional[GeneratedImage]:
        """生成文字封面图（使用 Pillow）"""
        
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            print("Pillow not installed. Run: pip install Pillow")
            return None
        
        # 创建渐变背景
        width, height = 1080, 1440
        img = Image.new('RGB', (width, height))
        
        # 渐变色
        gradients = {
            "gradient": [(102, 126, 234), (118, 75, 162)],  # 紫色渐变
            "tech": [(59, 130, 246), (37, 99, 235)],        # 蓝色
            "cute": [(244, 114, 182), (251, 146, 60)],      # 粉橙
        }
        colors = gradients.get(style, gradients["gradient"])
        
        # 绘制渐变
        for y in range(height):
            ratio = y / height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            for x in range(width):
                img.putpixel((x, y), (r, g, b))
        
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except Exception:
            title_font = ImageFont.load_default()
            subtitle_font = title_font
        
        # 绘制标题（居中）
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        title_y = height // 2 - 50
        
        # 文字阴影
        draw.text((title_x + 2, title_y + 2), title, font=title_font, fill=(0, 0, 0, 128))
        draw.text((title_x, title_y), title, font=title_font, fill=(255, 255, 255))
        
        # 绘制副标题
        if subtitle:
            sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            sub_width = sub_bbox[2] - sub_bbox[0]
            sub_x = (width - sub_width) // 2
            sub_y = title_y + 100
            draw.text((sub_x, sub_y), subtitle, font=subtitle_font, fill=(255, 255, 255, 200))
        
        # 保存
        filename = f"{draft_id or 'text'}_cover.png"
        filepath = self.output_dir / filename
        img.save(filepath, "PNG")
        
        return GeneratedImage(
            path=str(filepath),
            url=None,
            prompt=f"Text cover: {title}",
            width=width,
            height=height,
        )

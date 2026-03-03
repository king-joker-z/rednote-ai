"""小红书发布模块 - 支持 MCP 和浏览器自动化"""

import os
import json
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from ..generate.writer import GeneratedContent


class PublishMethod(Enum):
    """发布方式"""
    MCP = "mcp"           # 通过 xiaohongshu-mcp 服务
    BROWSER = "browser"   # 通过浏览器自动化
    MANUAL = "manual"     # 手动复制


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    method: PublishMethod
    note_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class XiaohongshuPublisher:
    """小红书发布器"""
    
    def __init__(
        self,
        mcp_url: str = None,
        cookies: str = None,
        method: PublishMethod = PublishMethod.MCP,
    ):
        self.mcp_url = mcp_url or os.getenv("XHS_MCP_URL", "http://localhost:18060/mcp")
        self.cookies = cookies or os.getenv("XHS_COOKIES")
        self.method = method
        
        # mcporter CLI 路径
        self.mcporter_available = self._check_mcporter()
    
    def _check_mcporter(self) -> bool:
        """检查 mcporter 是否可用"""
        import subprocess
        try:
            result = subprocess.run(["mcporter", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    async def publish(
        self,
        content: GeneratedContent,
        images: List[str] = None,
        method: PublishMethod = None,
    ) -> PublishResult:
        """
        发布内容到小红书
        
        Args:
            content: 生成的内容
            images: 图片路径列表（封面 + 内页）
            method: 发布方式（默认使用初始化时的方式）
        """
        method = method or self.method
        
        if method == PublishMethod.MCP:
            return await self._publish_via_mcp(content, images)
        elif method == PublishMethod.BROWSER:
            return await self._publish_via_browser(content, images)
        else:
            return self._generate_manual_content(content)
    
    async def _publish_via_mcp(
        self,
        content: GeneratedContent,
        images: List[str] = None,
    ) -> PublishResult:
        """通过 MCP 服务发布"""
        
        if not self.mcporter_available:
            return PublishResult(
                success=False,
                method=PublishMethod.MCP,
                error="mcporter CLI not available. Run: npm install -g mcporter"
            )
        
        try:
            # 构建发布参数
            note_content = self._format_note_content(content)
            
            # 使用 mcporter 调用小红书 MCP
            import subprocess
            
            # 先检查小红书 MCP 是否配置
            check_result = subprocess.run(
                ["mcporter", "config", "list"],
                capture_output=True, text=True, timeout=10
            )
            
            if "xiaohongshu" not in check_result.stdout:
                return PublishResult(
                    success=False,
                    method=PublishMethod.MCP,
                    error="xiaohongshu MCP not configured. Run:\n"
                          "docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp\n"
                          "mcporter config add xiaohongshu http://localhost:18060/mcp"
                )
            
            # 调用发布接口
            publish_params = json.dumps({
                "title": content.title,
                "content": note_content,
                "tags": content.tags,
                "images": images or [],
            })
            
            result = subprocess.run(
                ["mcporter", "call", f"xiaohongshu.create_note({publish_params})"],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                # 解析返回结果
                try:
                    response = json.loads(result.stdout)
                    return PublishResult(
                        success=True,
                        method=PublishMethod.MCP,
                        note_id=response.get("note_id"),
                        url=response.get("url"),
                    )
                except json.JSONDecodeError:
                    return PublishResult(
                        success=True,
                        method=PublishMethod.MCP,
                        note_id=None,
                        url=None,
                    )
            else:
                return PublishResult(
                    success=False,
                    method=PublishMethod.MCP,
                    error=result.stderr or result.stdout or "Unknown error"
                )
                
        except Exception as e:
            return PublishResult(
                success=False,
                method=PublishMethod.MCP,
                error=str(e)
            )
    
    async def _publish_via_browser(
        self,
        content: GeneratedContent,
        images: List[str] = None,
    ) -> PublishResult:
        """通过浏览器自动化发布"""
        
        # 需要 playwright 或 selenium
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return PublishResult(
                success=False,
                method=PublishMethod.BROWSER,
                error="playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        
        try:
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(headless=False)  # 需要登录，所以用有头模式
                context = await browser.new_context()
                
                # 如果有 cookies，先注入
                if self.cookies:
                    await self._inject_cookies(context, self.cookies)
                
                page = await context.new_page()
                
                # 导航到创作中心
                await page.goto("https://creator.xiaohongshu.com/publish/publish")
                await page.wait_for_load_state("networkidle")
                
                # 检查是否需要登录
                if "login" in page.url:
                    await browser.close()
                    return PublishResult(
                        success=False,
                        method=PublishMethod.BROWSER,
                        error="需要登录。请先在浏览器中登录小红书创作中心"
                    )
                
                # 上传图片
                if images:
                    upload_input = await page.query_selector('input[type="file"]')
                    if upload_input:
                        await upload_input.set_input_files(images)
                        await asyncio.sleep(3)  # 等待上传
                
                # 填写标题
                title_input = await page.query_selector('[placeholder*="标题"]')
                if title_input:
                    await title_input.fill(content.title)
                
                # 填写正文
                content_input = await page.query_selector('[placeholder*="正文"], .ql-editor, [contenteditable="true"]')
                if content_input:
                    note_text = self._format_note_content(content)
                    await content_input.fill(note_text)
                
                # 添加话题标签
                for tag in content.tags[:5]:
                    tag_input = await page.query_selector('[placeholder*="话题"], [placeholder*="标签"]')
                    if tag_input:
                        await tag_input.fill(f"#{tag}")
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(0.5)
                
                # 点击发布（先不自动点击，让用户确认）
                # publish_btn = await page.query_selector('button:has-text("发布")')
                # if publish_btn:
                #     await publish_btn.click()
                
                # 等待用户确认
                await asyncio.sleep(5)
                
                await browser.close()
                
                return PublishResult(
                    success=True,
                    method=PublishMethod.BROWSER,
                    note_id=None,
                    url=None,
                )
                
        except Exception as e:
            return PublishResult(
                success=False,
                method=PublishMethod.BROWSER,
                error=str(e)
            )
    
    async def _inject_cookies(self, context, cookies_str: str):
        """注入 cookies"""
        try:
            cookies = json.loads(cookies_str) if isinstance(cookies_str, str) else cookies_str
            await context.add_cookies(cookies)
        except Exception:
            pass
    
    def _generate_manual_content(self, content: GeneratedContent) -> PublishResult:
        """生成手动发布内容"""
        note_text = self._format_note_content(content)
        
        manual_guide = f"""
========== 小红书发布内容 ==========

【标题】
{content.title}

【正文】
{note_text}

【话题标签】
{' '.join('#' + t for t in content.tags)}

【封面图 Prompt】
{content.cover_prompt}

===================================

请手动复制以上内容到小红书创作中心发布
创作中心地址: https://creator.xiaohongshu.com/publish/publish
"""
        
        print(manual_guide)
        
        return PublishResult(
            success=True,
            method=PublishMethod.MANUAL,
            note_id=None,
            url=None,
        )
    
    def _format_note_content(self, content: GeneratedContent) -> str:
        """格式化笔记正文"""
        text = content.content
        
        # 添加话题标签到末尾
        if content.tags:
            tags_text = " ".join(f"#{tag}" for tag in content.tags[:5])
            text = f"{text}\n\n{tags_text}"
        
        return text
    
    async def check_status(self) -> Dict[str, Any]:
        """检查小红书发布能力状态"""
        status = {
            "mcporter": self.mcporter_available,
            "mcp_url": self.mcp_url,
            "mcp_configured": False,
            "cookies_set": bool(self.cookies),
            "recommended_method": None,
        }
        
        # 检查 MCP 配置
        if self.mcporter_available:
            import subprocess
            try:
                result = subprocess.run(
                    ["mcporter", "config", "list"],
                    capture_output=True, text=True, timeout=10
                )
                status["mcp_configured"] = "xiaohongshu" in result.stdout
            except Exception:
                pass
        
        # 推荐发布方式
        if status["mcp_configured"]:
            status["recommended_method"] = "mcp"
        elif status["cookies_set"]:
            status["recommended_method"] = "browser"
        else:
            status["recommended_method"] = "manual"
        
        return status

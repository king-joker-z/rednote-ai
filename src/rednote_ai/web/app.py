"""Web 控制台 - FastAPI 应用"""

import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel

from ..core import RedNoteAI, ContentDraft
from ..sources.base import NewsItem
from ..generate.writer import ContentStyle

# 初始化
app = FastAPI(title="RedNote AI", description="小红书 AI 内容自动化")
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(templates_dir))

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 全局实例
rednote: Optional[RedNoteAI] = None


def get_rednote() -> RedNoteAI:
    global rednote
    if rednote is None:
        rednote = RedNoteAI()
    return rednote


# ============================================================================
# 数据模型
# ============================================================================

class FetchRequest(BaseModel):
    sources: List[str] = ["arxiv"]
    limit: int = 20


class GenerateRequest(BaseModel):
    source: str = "arxiv"
    limit: int = 10
    top_n: int = 5
    generate_digest: bool = True


class DraftResponse(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    cover_prompt: str
    score: float
    status: str
    created_at: str


class NewsItemResponse(BaseModel):
    id: str
    title: str
    summary: str
    url: str
    source: str
    score: float


# ============================================================================
# 页面路由
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 - 仪表盘"""
    rn = get_rednote()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "drafts_count": len(rn.drafts),
        "sources": list(rn.sources.keys()),
    })


@app.get("/fetch", response_class=HTMLResponse)
async def fetch_page(request: Request):
    """抓取页面"""
    return templates.TemplateResponse("fetch.html", {
        "request": request,
        "sources": ["arxiv", "github", "twitter", "rss"],
    })


@app.get("/drafts", response_class=HTMLResponse)
async def drafts_page(request: Request):
    """草稿列表页面"""
    rn = get_rednote()
    return templates.TemplateResponse("drafts.html", {
        "request": request,
        "drafts": rn.drafts,
    })


@app.get("/drafts/{draft_id}", response_class=HTMLResponse)
async def draft_detail_page(request: Request, draft_id: str):
    """草稿详情页面"""
    rn = get_rednote()
    draft = next((d for d in rn.drafts if d.id == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return templates.TemplateResponse("draft_detail.html", {
        "request": request,
        "draft": draft,
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """设置页面"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
    })




@app.get("/publish", response_class=HTMLResponse)
async def publish_page(request: Request, draft_id: str = None):
    """发布页面"""
    return templates.TemplateResponse("publish.html", {
        "request": request,
        "draft_id": draft_id,
    })

# ============================================================================
# API 路由
# ============================================================================

@app.post("/api/fetch")
async def api_fetch(req: FetchRequest):
    """抓取热点"""
    rn = get_rednote()
    
    all_items = []
    for source in req.sources:
        if source in rn.sources:
            items = await rn.fetch_source(source, limit=req.limit // len(req.sources))
            all_items.extend(items)
    
    # 分析排序
    scored = await rn.analyze_trending(all_items)
    
    return {
        "success": True,
        "count": len(scored),
        "items": [
            NewsItemResponse(
                id=s.news_item.id,
                title=s.news_item.title,
                summary=s.news_item.summary[:200],
                url=s.news_item.url,
                source=s.news_item.source,
                score=s.total,
            ).dict()
            for s in scored[:20]
        ]
    }


@app.post("/api/generate")
async def api_generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    """生成内容"""
    rn = get_rednote()
    
    try:
        drafts = await rn.run_pipeline(
            sources=[req.source] if req.source != "all" else None,
            limit=req.limit,
            top_n=req.top_n,
            generate_digest=req.generate_digest,
        )
        
        return {
            "success": True,
            "count": len(drafts),
            "drafts": [
                DraftResponse(
                    id=d.id,
                    title=d.content.title,
                    content=d.content.content,
                    tags=d.content.tags,
                    cover_prompt=d.content.cover_prompt,
                    score=d.score,
                    status=d.status,
                    created_at=datetime.now().isoformat(),
                ).dict()
                for d in drafts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/drafts")
async def api_list_drafts():
    """获取草稿列表"""
    rn = get_rednote()
    return {
        "success": True,
        "count": len(rn.drafts),
        "drafts": [
            DraftResponse(
                id=d.id,
                title=d.content.title,
                content=d.content.content[:200] + "...",
                tags=d.content.tags,
                cover_prompt=d.content.cover_prompt[:100],
                score=d.score,
                status=d.status,
                created_at=datetime.now().isoformat(),
            ).dict()
            for d in rn.drafts
        ]
    }


@app.get("/api/drafts/{draft_id}")
async def api_get_draft(draft_id: str):
    """获取草稿详情"""
    rn = get_rednote()
    draft = next((d for d in rn.drafts if d.id == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return {
        "success": True,
        "draft": DraftResponse(
            id=draft.id,
            title=draft.content.title,
            content=draft.content.content,
            tags=draft.content.tags,
            cover_prompt=draft.content.cover_prompt,
            score=draft.score,
            status=draft.status,
            created_at=datetime.now().isoformat(),
        ).dict()
    }


@app.put("/api/drafts/{draft_id}")
async def api_update_draft(draft_id: str, title: str = None, content: str = None, tags: List[str] = None):
    """更新草稿"""
    rn = get_rednote()
    draft = next((d for d in rn.drafts if d.id == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if title:
        draft.content.title = title
    if content:
        draft.content.content = content
    if tags:
        draft.content.tags = tags
    
    return {"success": True, "message": "Draft updated"}


@app.post("/api/drafts/{draft_id}/approve")
async def api_approve_draft(draft_id: str):
    """审核通过草稿"""
    rn = get_rednote()
    draft = next((d for d in rn.drafts if d.id == draft_id), None)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    draft.status = "approved"
    return {"success": True, "message": "Draft approved"}


@app.delete("/api/drafts/{draft_id}")
async def api_delete_draft(draft_id: str):
    """删除草稿"""
    rn = get_rednote()
    rn.drafts = [d for d in rn.drafts if d.id != draft_id]
    return {"success": True, "message": "Draft deleted"}


@app.get("/api/status")
async def api_status():
    """系统状态"""
    rn = get_rednote()
    return {
        "success": True,
        "status": {
            "sources": list(rn.sources.keys()),
            "drafts_count": len(rn.drafts),
            "approved_count": len([d for d in rn.drafts if d.status == "approved"]),
        }
    }


# ============================================================================
# 小红书发布 API
# ============================================================================

class PublishRequest(BaseModel):
    draft_id: str
    method: str = "manual"  # mcp / browser / manual
    generate_cover: bool = False
    cover_style: str = "tech"


@app.get("/api/publish/status")
async def api_publish_status():
    """获取发布能力状态"""
    from ..publish.xiaohongshu import XiaohongshuPublisher
    
    publisher = XiaohongshuPublisher()
    status = await publisher.check_status()
    
    return {
        "success": True,
        "status": status
    }


@app.post("/api/publish")
async def api_publish(req: PublishRequest):
    """发布内容到小红书"""
    from ..publish.xiaohongshu import XiaohongshuPublisher, PublishMethod
    from ..publish.image import ImageGenerator
    
    rn = get_rednote()
    draft = next((d for d in rn.drafts if d.id == req.draft_id), None)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    images = []
    
    # 生成封面图
    if req.generate_cover:
        try:
            img_gen = ImageGenerator()
            cover = await img_gen.generate_text_image(
                title=draft.content.title[:20],
                style=req.cover_style,
                draft_id=draft.id,
            )
            if cover:
                images.append(cover.path)
        except Exception as e:
            print(f"Cover generation failed: {e}")
    
    # 发布
    method_map = {
        "mcp": PublishMethod.MCP,
        "browser": PublishMethod.BROWSER,
        "manual": PublishMethod.MANUAL,
    }
    
    publisher = XiaohongshuPublisher(method=method_map.get(req.method, PublishMethod.MANUAL))
    result = await publisher.publish(draft.content, images=images)
    
    if result.success:
        draft.status = "published"
    
    return {
        "success": result.success,
        "method": result.method.value,
        "note_id": result.note_id,
        "url": result.url,
        "error": result.error,
    }


@app.post("/api/generate-cover/{draft_id}")
async def api_generate_cover(draft_id: str, style: str = "tech", use_ai: bool = False):
    """生成封面图"""
    from ..publish.image import ImageGenerator
    
    rn = get_rednote()
    draft = next((d for d in rn.drafts if d.id == draft_id), None)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    img_gen = ImageGenerator()
    
    if use_ai and draft.content.cover_prompt:
        # 使用 AI 生成
        cover = await img_gen.generate_cover(
            prompt=draft.content.cover_prompt,
            style=style,
            draft_id=draft_id,
        )
    else:
        # 使用文字封面
        cover = await img_gen.generate_text_image(
            title=draft.content.title[:15],
            subtitle="AI 热点速递",
            style=style,
            draft_id=draft_id,
        )
    
    if cover:
        return {
            "success": True,
            "image": {
                "path": cover.path,
                "url": cover.url,
                "prompt": cover.prompt,
            }
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to generate cover")

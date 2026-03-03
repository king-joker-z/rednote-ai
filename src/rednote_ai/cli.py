"""命令行入口"""

import asyncio
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="RedNote AI - 小红书 AI 内容自动化")
console = Console()


@app.command()
def fetch(
    sources: str = typer.Option("all", help="信息源: all/twitter/arxiv/github/rss"),
    limit: int = typer.Option(20, help="抓取数量"),
):
    """抓取热点内容"""
    from .core import RedNoteAI
    
    console.print("[bold green]📡 抓取热点中...[/bold green]")
    
    async def run():
        rednote = RedNoteAI()
        
        if sources == "all":
            items = await rednote.fetch_all(limit=limit)
        else:
            items = await rednote.fetch_source(sources, limit=limit)
        
        if not items:
            console.print("[yellow]⚠️ 没有获取到内容[/yellow]")
            return
        
        table = Table(title=f"获取到 {len(items)} 条内容")
        table.add_column("来源", style="cyan")
        table.add_column("标题", style="white")
        table.add_column("分数", style="green")
        
        for item in items[:20]:
            table.add_row(
                item.source,
                item.title[:60] + "..." if len(item.title) > 60 else item.title,
                f"{item.score:.2f}"
            )
        
        console.print(table)
    
    asyncio.run(run())


@app.command()
def generate(
    source: str = typer.Option("arxiv", help="信息源"),
    limit: int = typer.Option(10, help="抓取数量"),
    top: int = typer.Option(3, help="生成 Top N"),
    digest: bool = typer.Option(True, help="是否生成日报"),
    provider: str = typer.Option(None, help="LLM 提供商: anthropic/openai"),
    model: str = typer.Option(None, help="模型名称"),
    api_key: str = typer.Option(None, envvar=["ANTHROPIC_API_KEY", "OPENAI_API_KEY"], help="API Key"),
    base_url: str = typer.Option(None, help="API Base URL"),
):
    """生成小红书内容"""
    from .core import RedNoteAI
    from .config import Config
    
    console.print("[bold green]🚀 启动内容生成流程...[/bold green]\n")
    
    llm_config = {}
    if provider:
        llm_config["provider"] = provider
    if model:
        llm_config["model"] = model
    if api_key:
        llm_config["api_key"] = api_key
    if base_url:
        llm_config["base_url"] = base_url
    
    if not llm_config:
        config = Config()
        llm_config = config.llm_writer
    
    async def run():
        rednote = RedNoteAI(config={"llm": {"writer": llm_config}})
        
        drafts = await rednote.run_pipeline(
            sources=[source] if source != "all" else None,
            limit=limit,
            top_n=top,
            generate_digest=digest,
        )
        
        console.print("\n" + "=" * 60 + "\n")
        
        for draft in drafts:
            content = draft.content
            
            panel = Panel(
                f"[bold]{content.title}[/bold]\n\n"
                f"{content.content[:500]}...\n\n"
                f"[dim]标签: {' '.join('#' + t for t in content.tags)}[/dim]\n"
                f"[dim]封面: {content.cover_prompt[:100]}...[/dim]",
                title=f"📝 草稿 {draft.id}",
                subtitle=f"分数: {draft.score:.2f}",
            )
            console.print(panel)
            console.print()
    
    asyncio.run(run())


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="监听地址"),
    port: int = typer.Option(8000, help="端口"),
    reload: bool = typer.Option(False, help="开发模式自动重载"),
):
    """启动 Web 控制台"""
    console.print(f"[bold green]🌐 启动 Web 控制台...[/bold green]")
    console.print(f"  地址: http://{host}:{port}")
    console.print(f"  按 Ctrl+C 停止\n")
    
    import uvicorn
    uvicorn.run(
        "rednote_ai.web:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="显示当前配置"),
    init: bool = typer.Option(False, "--init", help="初始化配置文件"),
):
    """配置管理"""
    from .config import get_config_path, load_config
    
    config_path = get_config_path()
    
    if init:
        example_path = Path(__file__).parent.parent.parent / "config" / "config.example.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if example_path.exists():
            import shutil
            shutil.copy(example_path, config_path)
            console.print(f"[green]✓ 配置文件已创建: {config_path}[/green]")
        else:
            console.print("[yellow]⚠️ 找不到示例配置文件[/yellow]")
        return
    
    if show:
        if config_path.exists():
            console.print(f"[bold]配置文件: {config_path}[/bold]\n")
            cfg = load_config(config_path)
            
            import json
            def mask_sensitive(obj):
                if isinstance(obj, dict):
                    return {k: mask_sensitive(v) if "key" not in k.lower() else "***" for k, v in obj.items()}
                return obj
            
            console.print(json.dumps(mask_sensitive(cfg), indent=2, ensure_ascii=False))
        else:
            console.print(f"[yellow]配置文件不存在: {config_path}[/yellow]")
            console.print("运行 [bold]rednote-ai config --init[/bold] 创建")
        return
    
    console.print(f"配置文件路径: {config_path}")
    console.print(f"存在: {'是' if config_path.exists() else '否'}")


@app.command()
def doctor():
    """检查环境配置"""
    import subprocess
    
    console.print("[bold]🔍 检查环境配置...[/bold]\n")
    
    checks = []
    
    try:
        result = subprocess.run(["xreach", "--version"], capture_output=True, timeout=5)
        checks.append(("xreach CLI", result.returncode == 0, "Twitter 抓取"))
    except Exception:
        checks.append(("xreach CLI", False, "Twitter 抓取"))
    
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=5)
        checks.append(("gh CLI", result.returncode == 0, "GitHub 抓取"))
    except Exception:
        checks.append(("gh CLI", False, "GitHub 抓取"))
    
    checks.append(("ANTHROPIC_API_KEY", bool(os.getenv("ANTHROPIC_API_KEY")), "Claude 文案生成"))
    checks.append(("OPENAI_API_KEY", bool(os.getenv("OPENAI_API_KEY")), "GPT 备选"))
    
    # 检查 Web 依赖
    try:
        import uvicorn
        import fastapi
        checks.append(("Web 依赖", True, "uvicorn + fastapi"))
    except ImportError:
        checks.append(("Web 依赖", False, "pip install rednote-ai[web]"))
    
    from .config import get_config_path
    config_path = get_config_path()
    checks.append(("配置文件", config_path.exists(), str(config_path)))
    
    table = Table(title="环境检查")
    table.add_column("组件", style="cyan")
    table.add_column("状态")
    table.add_column("用途", style="dim")
    
    for name, ok, usage in checks:
        status = "[green]✅ 可用[/green]" if ok else "[yellow]⬜ 未配置[/yellow]"
        table.add_row(name, status, usage)
    
    console.print(table)


if __name__ == "__main__":
    app()

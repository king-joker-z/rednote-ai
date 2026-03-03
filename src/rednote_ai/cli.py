"""命令行入口"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

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
):
    """生成小红书内容"""
    from .core import RedNoteAI
    
    console.print("[bold green]🚀 启动内容生成流程...[/bold green]\n")
    
    async def run():
        rednote = RedNoteAI()
        
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
):
    """启动 Web 控制台"""
    console.print(f"[bold green]🌐 启动 Web 控制台...[/bold green]")
    console.print(f"  地址: http://{host}:{port}")
    console.print("[yellow]⚠️ Web 控制台尚未实现[/yellow]")


@app.command()
def doctor():
    """检查环境配置"""
    import subprocess
    import os
    
    console.print("[bold]🔍 检查环境配置...[/bold]\n")
    
    checks = []
    
    # 检查 xreach
    try:
        result = subprocess.run(["xreach", "--version"], capture_output=True, timeout=5)
        checks.append(("xreach CLI", result.returncode == 0, "Twitter 抓取"))
    except Exception:
        checks.append(("xreach CLI", False, "Twitter 抓取"))
    
    # 检查 gh
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, timeout=5)
        checks.append(("gh CLI", result.returncode == 0, "GitHub 抓取"))
    except Exception:
        checks.append(("gh CLI", False, "GitHub 抓取"))
    
    # 检查 API Keys
    checks.append(("ANTHROPIC_API_KEY", bool(os.getenv("ANTHROPIC_API_KEY")), "Claude 文案生成"))
    checks.append(("OPENAI_API_KEY", bool(os.getenv("OPENAI_API_KEY")), "GPT 备选"))
    
    table = Table(title="环境检查")
    table.add_column("组件", style="cyan")
    table.add_column("状态")
    table.add_column("用途", style="dim")
    
    for name, ok, usage in checks:
        status = "[green]✅ 可用[/green]" if ok else "[red]❌ 缺失[/red]"
        table.add_row(name, status, usage)
    
    console.print(table)


if __name__ == "__main__":
    app()

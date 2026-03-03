"""命令行入口"""

import typer
from rich.console import Console

app = typer.Typer(help="RedNote AI - 小红书 AI 内容自动化")
console = Console()


@app.command()
def fetch(
    sources: str = typer.Option("all", help="信息源: all/twitter/arxiv/github/rss"),
    limit: int = typer.Option(20, help="抓取数量"),
):
    """抓取热点内容"""
    console.print(f"[bold green]📡 抓取热点中...[/bold green]")
    console.print(f"  来源: {sources}")
    console.print(f"  数量: {limit}")
    # TODO: 实现抓取逻辑


@app.command()
def generate(
    topic: str = typer.Argument(None, help="指定话题"),
    style: str = typer.Option("news", help="风格: news/tutorial/review/opinion"),
    variants: int = typer.Option(3, help="生成变体数量"),
):
    """生成小红书内容"""
    console.print(f"[bold green]✍️ 生成内容中...[/bold green]")
    # TODO: 实现生成逻辑


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="监听地址"),
    port: int = typer.Option(8000, help="端口"),
):
    """启动 Web 控制台"""
    console.print(f"[bold green]🌐 启动 Web 控制台...[/bold green]")
    console.print(f"  地址: http://{host}:{port}")
    # TODO: 启动 FastAPI


@app.command()
def publish(
    draft_id: str = typer.Argument(..., help="草稿 ID"),
    schedule: str = typer.Option(None, help="定时发布时间"),
):
    """发布到小红书"""
    console.print(f"[bold green]📤 发布内容...[/bold green]")
    # TODO: 实现发布逻辑


if __name__ == "__main__":
    app()

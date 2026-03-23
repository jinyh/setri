"""Setri CLI — 命令行入口"""

import json

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Setri — 配电网业扩智能评审副驾驶")
console = Console()

# ─── P1 子命令 ───

p1_app = typer.Typer(help="P1 规范库构建")
app.add_typer(p1_app, name="p1")


@p1_app.command("scan")
def p1_scan(
    keywords: str = typer.Option(..., help="逗号分隔的关键词（如 '开关站,KT站'）"),
    slug: str = typer.Option("kaiguanzhan", help="输出目录名"),
    subject: str = typer.Option("配电网开关站", help="专题名称"),
    pdf_dir: str = typer.Option(None, help="PDF 目录（默认：技术规范文件/）"),
):
    """Phase 1: 关键词扫描 PDF"""
    from .p1_regulations.pipeline import run_scan

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    result = run_scan(subject, slug, kw_list, pdf_dir=pdf_dir)

    console.print(f"\n[bold green]扫描完成[/]")
    console.print(f"  扫描 PDF 数：{result['total_pdfs_scanned']}")
    console.print(f"  命中 PDF 数：{result['total_pdfs_with_hits']}")

    if result["results"]:
        table = Table(title="命中结果")
        table.add_column("文件", style="cyan")
        table.add_column("命中数", justify="right")
        table.add_column("页码")
        table.add_column("类型")
        for r in result["results"]:
            tag = "图像" if r["is_image_only"] else "文本"
            table.add_row(
                r["file"],
                str(r["total_hits"]),
                str(r["hit_pages"]),
                tag,
            )
        console.print(table)


@p1_app.command("conflicts")
def p1_conflicts(
    slug: str = typer.Option("kaiguanzhan", help="规范库目录名"),
):
    """Phase 4a: 冲突预筛"""
    from .p1_regulations.pipeline import run_pre_screen

    result = run_pre_screen(slug)
    console.print(f"\n[bold green]冲突预筛完成[/]")
    console.print(f"  条款数：{result['total_clauses']}")
    console.print(f"  候选冲突：{result['total_candidates']}")


@p1_app.command("assemble")
def p1_assemble(
    slug: str = typer.Option("kaiguanzhan", help="规范库目录名"),
    subject: str = typer.Option("配电网开关站", help="专题名称"),
    keywords: str = typer.Option("", help="逗号分隔的关键词"),
):
    """Phase 5: 组装输出"""
    from .p1_regulations.pipeline import run_assemble

    result, errors = run_assemble(subject, slug, keywords)
    m = result["metadata"]
    console.print(f"\n[bold green]组装完成[/]")
    console.print(f"  来源：{m['sources_count']} 份")
    console.print(f"  条款：{m['total_clauses']} 条")
    console.print(f"  冲突：{m['total_conflicts']} 个")
    if errors:
        console.print(f"  [yellow]校验问题：{len(errors)} 个[/]")
        for e in errors:
            console.print(f"    ⚠ {e}")
    else:
        console.print("  校验：全部通过 ✓")


# ─── P2 子命令（阶段 C 实现）───

p2_app = typer.Typer(help="P2 文件整理")
app.add_typer(p2_app, name="p2")


@p2_app.command("run")
def p2_run(
    project: str = typer.Option(..., help="项目 ID（如 C109HZ22A062）"),
):
    """整理项目文件到标准目录结构"""
    console.print("[yellow]P2 文件整理模块尚在阶段 C 实现中[/]")
    raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()

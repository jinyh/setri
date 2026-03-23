"""P1 规范库 — 关键词扫描

对 .claude/skills/reg-extractor/scripts/scan_sources.py 的封装。
核心函数直接导入复用，本模块提供 Pythonic 接口。
"""

import sys
from pathlib import Path

# 将 skills 脚本目录加入 sys.path 以复用现有代码
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent.parent / ".claude" / "skills" / "reg-extractor" / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from scan_sources import scan_directory, scan_pdf  # noqa: E402


def scan(
    pdf_dir: str | Path,
    keywords: list[str],
    *,
    context_chars: int = 50,
) -> dict:
    """扫描目录下所有 PDF，返回结构化结果。

    Args:
        pdf_dir: PDF 文件目录
        keywords: 关键词列表
        context_chars: 上下文截取字符数

    Returns:
        {
            "keywords": [...],
            "pdf_dir": "...",
            "total_pdfs_scanned": N,
            "total_pdfs_with_hits": M,
            "results": [...],  # 有命中的 PDF
            "no_hit_files": [...],  # 无命中的文件名
        }
    """
    results = scan_directory(str(pdf_dir), keywords, context_chars)

    hit_results = [r for r in results if r["total_hits"] > 0]
    no_hit_results = [r for r in results if r["total_hits"] == 0]

    return {
        "keywords": keywords,
        "pdf_dir": str(pdf_dir),
        "total_pdfs_scanned": len(results),
        "total_pdfs_with_hits": len(hit_results),
        "results": hit_results,
        "no_hit_files": [r["file"] for r in no_hit_results],
    }

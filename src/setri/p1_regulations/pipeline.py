"""P1 规范库 — 管道编排器"""

import json
from pathlib import Path

from ..config import REGULATIONS_DIR, SPECS_DIR
from .assemble import assemble_regulations
from .conflicts import pre_screen
from .scan import scan


def run_scan(subject: str, slug: str, keywords: list[str], *, pdf_dir: str | Path | None = None) -> dict:
    """运行 P1 Phase 1：关键词扫描。

    Args:
        subject: 专题名称（如"配电网开关站"）
        slug: 输出目录名（如"kaiguanzhan"）
        keywords: 关键词列表
        pdf_dir: PDF 目录，默认为技术规范文件/

    Returns:
        scan_result dict
    """
    pdf_dir = Path(pdf_dir) if pdf_dir else SPECS_DIR
    output_dir = REGULATIONS_DIR / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    result = scan(pdf_dir, keywords)

    output_path = output_dir / "scan_result.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def run_pre_screen(slug: str) -> dict:
    """运行 P1 Phase 4a：冲突预筛。

    需要 clauses_draft.json 已存在。
    """
    input_dir = REGULATIONS_DIR / slug
    clauses_path = input_dir / "clauses_draft.json"

    if not clauses_path.exists():
        raise FileNotFoundError(f"条款文件不存在：{clauses_path}")

    with open(clauses_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    clauses = data if isinstance(data, list) else data.get("clauses", [])
    result = pre_screen(clauses)

    output_path = input_dir / "conflict_candidates.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def run_assemble(subject: str, slug: str, keywords: str = "") -> tuple[dict, list[str]]:
    """运行 P1 Phase 5：组装输出。"""
    input_dir = REGULATIONS_DIR / slug
    result, errors = assemble_regulations(input_dir, subject, slug, keywords)

    output_path = input_dir / "regulations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result, errors

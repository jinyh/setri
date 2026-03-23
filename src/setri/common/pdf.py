"""PDF 文本提取工具

对 pdfplumber 的轻量封装，提供统一接口。
"""

from pathlib import Path

import pdfplumber


def extract_text(pdf_path: str | Path, *, pages: list[int] | None = None) -> list[dict]:
    """提取 PDF 文本，返回按页组织的结果。

    Args:
        pdf_path: PDF 文件路径
        pages: 指定页码列表（1-based），None 表示全部页

    Returns:
        [{"page": 1, "text": "...", "char_count": 123}, ...]
    """
    results = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            if pages and page_num not in pages:
                continue
            text = page.extract_text() or ""
            results.append({
                "page": page_num,
                "text": text,
                "char_count": len(text),
            })
    return results


def is_image_only(pdf_path: str | Path, *, min_chars: int = 20) -> bool:
    """判断 PDF 是否为纯图像（无可提取文本）"""
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text) >= min_chars:
                return False
    return True


def get_page_count(pdf_path: str | Path) -> int:
    """获取 PDF 总页数"""
    with pdfplumber.open(str(pdf_path)) as pdf:
        return len(pdf.pages)

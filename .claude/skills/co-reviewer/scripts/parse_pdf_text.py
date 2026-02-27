"""PDF 文本逐页提取

用 pdfplumber 逐页提取 PDF 文本，识别章节结构，输出 JSON。
"""

import argparse
import json
import os
import re
import sys

import pdfplumber

# 章节标题模式（常见工程文档格式）
SECTION_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十\d]+[章节篇][\s\S]{0,40}"),
    re.compile(r"^[一二三四五六七八九十]+[、.]\s*\S+"),
    re.compile(r"^\d+[、.．]\d*\s*\S+"),
    re.compile(r"^[（(]\d+[）)]\s*\S+"),
]


def extract_pdf(pdf_path: str, max_pages: int = 0) -> dict:
    """提取 PDF 全文，返回逐页文本和章节索引"""
    pages = []
    sections = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            limit = min(total, max_pages) if max_pages > 0 else total

            for i, page in enumerate(pdf.pages[:limit]):
                text = page.extract_text() or ""
                page_info = {
                    "page": i + 1,
                    "text": text,
                    "char_count": len(text),
                }
                pages.append(page_info)

                # 检测章节标题
                for line in text.split("\n")[:5]:
                    line = line.strip()
                    if not line:
                        continue
                    for pat in SECTION_PATTERNS:
                        if pat.match(line):
                            sections.append({
                                "title": line[:60],
                                "page": i + 1,
                            })
                            break

    except Exception as e:
        return {"error": str(e), "file": pdf_path, "pages": [], "sections": []}

    is_image_only = all(p["char_count"] < 20 for p in pages) if pages else False

    return {
        "file": os.path.basename(pdf_path),
        "path": pdf_path,
        "total_pages": len(pages),
        "total_chars": sum(p["char_count"] for p in pages),
        "is_image_only": is_image_only,
        "sections": sections,
        "pages": pages,
    }


def extract_project_pdfs(project_dir: str, max_pages: int = 0) -> list[dict]:
    """提取项目目录下所有 PDF 的文本"""
    results = []
    for dirpath, _, filenames in os.walk(project_dir):
        for fn in sorted(filenames):
            if fn.endswith(".pdf") and not fn.startswith("."):
                fp = os.path.join(dirpath, fn)
                info = extract_pdf(fp, max_pages=max_pages)
                results.append(info)
    return results


def main():
    parser = argparse.ArgumentParser(description="提取 PDF 文本")
    parser.add_argument("--input", required=True, help="PDF 文件或目录")
    parser.add_argument("--output", type=str, help="输出 JSON 路径")
    parser.add_argument("--max-pages", type=int, default=0, help="每个 PDF 最大页数")
    parser.add_argument("--summary", action="store_true", help="仅输出摘要")
    args = parser.parse_args()

    if os.path.isfile(args.input):
        results = [extract_pdf(args.input, max_pages=args.max_pages)]
    elif os.path.isdir(args.input):
        results = extract_project_pdfs(args.input, max_pages=args.max_pages)
    else:
        print(f"无效输入: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.summary:
        for r in results:
            tag = "[图像]" if r.get("is_image_only") else "[文本]"
            print(f"{tag} {r['file']}: {r['total_pages']}页, {r['total_chars']}字, {len(r['sections'])}个章节")
        return

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"已提取 {len(results)} 个 PDF 到 {args.output}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

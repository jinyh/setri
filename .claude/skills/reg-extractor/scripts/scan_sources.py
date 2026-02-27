"""PDF 关键词扫描

遍历指定目录下所有 PDF，用 pdfplumber 逐页提取文本，
按关键词列表统计命中，输出 scan_result.json。
"""

import argparse
import json
import os
import sys

import pdfplumber


def scan_pdf(pdf_path: str, keywords: list[str], context_chars: int = 50) -> dict:
    """扫描单个 PDF，返回关键词命中统计"""
    hits = []
    total_chars = 0
    is_image_only = True

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                total_chars += len(text)
                if len(text) >= 20:
                    is_image_only = False

                for kw in keywords:
                    start = 0
                    while True:
                        pos = text.find(kw, start)
                        if pos == -1:
                            break
                        ctx_start = max(0, pos - context_chars)
                        ctx_end = min(len(text), pos + len(kw) + context_chars)
                        snippet = text[ctx_start:ctx_end].replace("\n", " ")
                        hits.append({
                            "keyword": kw,
                            "page": i + 1,
                            "position": pos,
                            "context": snippet,
                        })
                        start = pos + len(kw)
    except Exception as e:
        return {
            "file": os.path.basename(pdf_path),
            "path": pdf_path,
            "error": str(e),
            "hits": [],
        }

    # 按页码汇总
    hit_pages = sorted(set(h["page"] for h in hits))
    keyword_counts = {}
    for h in hits:
        keyword_counts[h["keyword"]] = keyword_counts.get(h["keyword"], 0) + 1

    return {
        "file": os.path.basename(pdf_path),
        "path": pdf_path,
        "total_chars": total_chars,
        "is_image_only": is_image_only,
        "total_hits": len(hits),
        "hit_pages": hit_pages,
        "keyword_counts": keyword_counts,
        "hits": hits,
    }


def scan_directory(pdf_dir: str, keywords: list[str], context_chars: int = 50) -> list[dict]:
    """扫描目录下所有 PDF"""
    results = []
    for dirpath, _, filenames in os.walk(pdf_dir):
        for fn in sorted(filenames):
            if fn.lower().endswith(".pdf") and not fn.startswith("."):
                fp = os.path.join(dirpath, fn)
                result = scan_pdf(fp, keywords, context_chars)
                results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description="PDF 关键词扫描")
    parser.add_argument("--keywords", required=True, help="逗号分隔的关键词列表")
    parser.add_argument("--pdf-dir", required=True, help="PDF 源目录")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    parser.add_argument("--context-chars", type=int, default=50, help="上下文字符数")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        print("错误：关键词列表为空", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.pdf_dir):
        print(f"错误：目录不存在 {args.pdf_dir}", file=sys.stderr)
        sys.exit(1)

    results = scan_directory(args.pdf_dir, keywords, args.context_chars)

    # 过滤无命中的 PDF
    hit_results = [r for r in results if r["total_hits"] > 0]
    no_hit_results = [r for r in results if r["total_hits"] == 0]

    output = {
        "keywords": keywords,
        "pdf_dir": args.pdf_dir,
        "total_pdfs_scanned": len(results),
        "total_pdfs_with_hits": len(hit_results),
        "results": hit_results,
        "no_hit_files": [r["file"] for r in no_hit_results],
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 摘要输出
    print(f"扫描完成：{len(results)} 个 PDF，{len(hit_results)} 个命中")
    for r in hit_results:
        tag = "[图像]" if r["is_image_only"] else "[文本]"
        print(f"  {tag} {r['file']}: {r['total_hits']} 次命中, 页码 {r['hit_pages']}")
    if no_hit_results:
        print(f"  未命中: {len(no_hit_results)} 个 PDF")


if __name__ == "__main__":
    main()

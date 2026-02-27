"""规范文件按条款切分 → JSON

读取规范索引表 xlsx，结合规范 PDF 文件，按条款编号模式切分为结构化 JSON。
"""

import argparse
import json
import os
import re
import sys

import openpyxl
import pdfplumber

# 项目根目录
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
REG_DIR = os.path.join(ROOT, "业扩项目相关技术规范文件")
DEFAULT_INDEX = os.path.join(REG_DIR, "【0】业扩项目相关技术规范文件.xlsx")

# 条款编号模式
CLAUSE_PATTERNS = [
    re.compile(r"^(\d+(?:\.\d+)+)\s+(.+)"),           # 1.2.3 标题
    re.compile(r"^第([一二三四五六七八九十\d]+)条\s*(.*)"),  # 第X条
    re.compile(r"^([一二三四五六七八九十]+)[、.]\s*(.+)"),   # 一、标题
    re.compile(r"^(\d+)[、.]\s*(.+)"),                   # 1、标题
]


def parse_index(index_path: str = None) -> list[dict]:
    """解析规范索引表，返回规范列表"""
    path = index_path or DEFAULT_INDEX
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active

    standards = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue  # 跳过表头
        vals = [str(v).strip() if v else "" for v in row]
        if not vals[0] or vals[0] == "序号":
            continue

        standards.append({
            "seq": vals[0],
            "standard_id": vals[1],
            "category": vals[2],       # 政策类|管理类|技术类
            "standard_name": vals[3],
            "summary": vals[4],
            "knowledge_req": vals[5] if len(vals) > 5 else "",
            "pdf_path": "",            # 后续匹配填充
        })

    wb.close()
    return standards


def match_pdf_files(standards: list[dict]) -> list[dict]:
    """为每个规范匹配对应的 PDF 文件"""
    pdf_files = []
    for dirpath, _, fns in os.walk(REG_DIR):
        for fn in fns:
            if fn.endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, fn))

    for std in standards:
        sid = std["standard_id"]
        name = std["standard_name"]
        for fp in pdf_files:
            fn = os.path.basename(fp)
            # 用标准编号或名称关键词匹配
            if sid and sid in fn:
                std["pdf_path"] = fp
                break
            # 用名称中的关键词模糊匹配
            keywords = [w for w in re.split(r"[（()）\s]", name) if len(w) >= 4]
            if any(kw in fn for kw in keywords):
                std["pdf_path"] = fp
                break

    return standards


def split_clauses(pdf_path: str, max_pages: int = 0) -> list[dict]:
    """将 PDF 按条款切分"""
    clauses = []
    current = None

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            limit = min(total, max_pages) if max_pages > 0 else total

            for i, page in enumerate(pdf.pages[:limit]):
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    matched = False
                    for pat in CLAUSE_PATTERNS:
                        m = pat.match(line)
                        if m:
                            if current:
                                clauses.append(current)
                            current = {
                                "clause_id": m.group(1),
                                "title": m.group(2)[:80] if m.group(2) else "",
                                "page": i + 1,
                                "text": line,
                            }
                            matched = True
                            break

                    if not matched and current:
                        current["text"] += "\n" + line

    except Exception as e:
        return [{"error": str(e), "file": pdf_path}]

    if current:
        clauses.append(current)

    # 截断过长文本
    for c in clauses:
        if len(c["text"]) > 2000:
            c["text"] = c["text"][:2000] + "..."

    return clauses


def build_regulation_db(index_path: str = None, max_pages: int = 50) -> dict:
    """构建完整的结构化规范库"""
    standards = parse_index(index_path)
    standards = match_pdf_files(standards)

    index_data = []
    all_clauses = {}

    for std in standards:
        sid = std["standard_id"]
        entry = {
            "standard_id": sid,
            "standard_name": std["standard_name"],
            "category": std["category"],
            "summary": std["summary"],
            "has_pdf": bool(std["pdf_path"]),
            "clause_count": 0,
        }

        if std["pdf_path"]:
            clauses = split_clauses(std["pdf_path"], max_pages=max_pages)
            entry["clause_count"] = len(clauses)
            all_clauses[sid] = {
                "standard_id": sid,
                "standard_name": std["standard_name"],
                "category": std["category"],
                "pdf_file": os.path.basename(std["pdf_path"]),
                "clauses": clauses,
            }

        index_data.append(entry)

    return {"index": index_data, "clauses": all_clauses}


def main():
    parser = argparse.ArgumentParser(description="解析规范文件")
    parser.add_argument("--index-file", type=str, help="规范索引表 xlsx 路径")
    parser.add_argument("--output-dir", type=str, help="输出目录")
    parser.add_argument("--max-pages", type=int, default=50, help="每个 PDF 最大页数")
    parser.add_argument("--index-only", action="store_true", help="仅输出索引")
    args = parser.parse_args()

    if args.index_only:
        standards = parse_index(args.index_file)
        standards = match_pdf_files(standards)
        for s in standards:
            tag = "✓" if s["pdf_path"] else "✗"
            print(f"  {tag} [{s['category']}] {s['standard_id']} {s['standard_name']}")
        return

    db = build_regulation_db(args.index_file, max_pages=args.max_pages)

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        clauses_dir = os.path.join(args.output_dir, "clauses")
        os.makedirs(clauses_dir, exist_ok=True)

        # 写入索引
        idx_path = os.path.join(args.output_dir, "index.json")
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(db["index"], f, ensure_ascii=False, indent=2)

        # 写入各规范条款
        for sid, data in db["clauses"].items():
            safe_name = re.sub(r"[^\w\-]", "_", sid)
            cp = os.path.join(clauses_dir, f"{safe_name}.json")
            with open(cp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        total_clauses = sum(e["clause_count"] for e in db["index"])
        print(f"已输出 {len(db['index'])} 个规范, {total_clauses} 个条款到 {args.output_dir}")
    else:
        print(json.dumps(db["index"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


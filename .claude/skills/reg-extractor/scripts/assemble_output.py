"""输出组装与校验

合并 metadata + sources + categories + clauses + conflicts → regulations.json，
校验所有 ID 引用完整性，输出统计摘要。
"""

import argparse
import json
import os
import sys
from datetime import date


def load_json(path: str) -> dict | list | None:
    """安全加载 JSON 文件，不存在则返回 None"""
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_references(data: dict) -> list[str]:
    """校验所有 ID 引用完整性，返回错误列表"""
    errors = []

    source_ids = {s["source_id"] for s in data.get("sources", [])}
    category_ids = {c["id"] for c in data.get("categories", [])}
    clause_ids = {c["clause_id"] for c in data.get("clauses", [])}

    # 校验条款引用
    for cl in data.get("clauses", []):
        if cl.get("source_id") and cl["source_id"] not in source_ids:
            errors.append(f"{cl['clause_id']}: source_id '{cl['source_id']}' 不在 sources 中")
        if cl.get("category_id") and cl["category_id"] not in category_ids:
            errors.append(f"{cl['clause_id']}: category_id '{cl['category_id']}' 不在 categories 中")

    # 校验冲突引用
    for conf in data.get("conflicts", []):
        for cid in conf.get("involved_clauses", []):
            if cid not in clause_ids:
                errors.append(f"{conf['conflict_id']}: involved_clause '{cid}' 不在 clauses 中")
        if conf.get("category_id") and conf["category_id"] not in category_ids:
            errors.append(f"{conf['conflict_id']}: category_id '{conf['category_id']}' 不在 categories 中")
        eff = conf.get("resolution", {}).get("effective_clause_id", "")
        if eff and eff not in clause_ids:
            errors.append(f"{conf['conflict_id']}: effective_clause_id '{eff}' 不在 clauses 中")

    return errors


def assemble(input_dir: str, subject: str, slug: str, keywords: str) -> dict:
    """从中间文件组装最终 regulations.json"""
    # 加载各阶段输出
    scan = load_json(os.path.join(input_dir, "scan_result.json"))
    clauses_data = load_json(os.path.join(input_dir, "clauses_draft.json"))
    categories = load_json(os.path.join(input_dir, "categories.json"))
    conflicts_data = load_json(os.path.join(input_dir, "conflict_candidates.json"))

    # 条款：支持数组或含 clauses 字段的对象
    if isinstance(clauses_data, list):
        clauses = clauses_data
    elif isinstance(clauses_data, dict):
        clauses = clauses_data.get("clauses", [])
    else:
        clauses = []

    # 冲突：取已裁决的 conflicts（由 Claude 写入），否则取 candidates
    if isinstance(conflicts_data, dict):
        conflicts = conflicts_data.get("conflicts", conflicts_data.get("candidates", []))
    elif isinstance(conflicts_data, list):
        conflicts = conflicts_data
    else:
        conflicts = []

    # 从 scan_result 提取 sources（如果有独立 sources.json 则优先）
    sources_data = load_json(os.path.join(input_dir, "sources.json"))
    if sources_data:
        sources = sources_data if isinstance(sources_data, list) else sources_data.get("sources", [])
    elif scan:
        # 从 scan_result 中提取有命中的 PDF 作为 sources 骨架
        sources = []
        for i, r in enumerate(scan.get("results", []), 1):
            sources.append({
                "source_id": f"SRC-{i:02d}",
                "standard_id": "",
                "standard_name": r["file"].replace(".pdf", ""),
                "year": 0,
                "pdf_filename": r["file"],
            })
    else:
        # 从条款中反推 sources
        seen = {}
        for cl in clauses:
            sid = cl.get("source_id", "")
            if sid and sid not in seen:
                seen[sid] = {"source_id": sid}
        sources = list(seen.values())

    if not categories:
        categories = []

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []

    result = {
        "metadata": {
            "subject": subject,
            "slug": slug,
            "keywords": kw_list,
            "generated_at": date.today().isoformat(),
            "total_clauses": len(clauses),
            "total_conflicts": len(conflicts),
            "sources_count": len(sources),
        },
        "sources": sources,
        "categories": categories,
        "clauses": clauses,
        "conflicts": conflicts,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="输出组装与校验")
    parser.add_argument("--subject", required=True, help="专题名称")
    parser.add_argument("--slug", default="", help="输出目录名")
    parser.add_argument("--keywords", default="", help="逗号分隔的关键词")
    parser.add_argument("--input-dir", required=True, help="中间文件目录")
    parser.add_argument("--output", required=True, help="输出 regulations.json 路径")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"错误：目录不存在 {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    result = assemble(args.input_dir, args.subject, args.slug, args.keywords)

    # 校验引用完整性
    errors = validate_references(result)
    if errors:
        print(f"引用校验发现 {len(errors)} 个问题：", file=sys.stderr)
        for e in errors:
            print(f"  ⚠ {e}", file=sys.stderr)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    m = result["metadata"]
    print(f"组装完成: {args.output}")
    print(f"  专题: {m['subject']}")
    print(f"  来源: {m['sources_count']} 份")
    print(f"  条款: {m['total_clauses']} 条")
    print(f"  冲突: {m['total_conflicts']} 个")
    if errors:
        print(f"  校验问题: {len(errors)} 个")
    else:
        print("  校验: 全部通过 ✓")


if __name__ == "__main__":
    main()

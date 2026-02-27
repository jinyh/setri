"""冲突候选预筛

读取 Claude 提取的条款 JSON，在同 category 内跨 source 的条款
两两比较数值特征和强度词差异，输出候选冲突列表。
"""

import argparse
import json
import os
import re
import sys
from itertools import combinations

# 数值特征正则：匹配 "12回"、"1250kVA"、"3×240mm²"、"18.4m" 等
NUM_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*"
    r"(回|kVA|kV|MVA|MW|mm²|mm|m|cm|台|个|条|%|kA|A|V)"
)

# 范围模式：匹配 "6～14回"、"800kVA～1250kVA"
RANGE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:～|~|-|—|至)\s*(\d+(?:\.\d+)?)\s*"
    r"(回|kVA|kV|MVA|MW|mm²|mm|m|cm|台|个|条|%|kA|A|V)"
)

# 强度词及其等级（数值越大越强制）
STRENGTH_LEVELS = {
    "不得": 5, "严禁": 5, "必须": 5,
    "应": 4,
    "不宜": 3, "不应": 3,
    "宜": 2,
    "可": 1,
    "一般": 1,
}

STRENGTH_PATTERN = re.compile(
    r"(不得|严禁|必须|不应|不宜|应|宜|可|一般)"
)


def extract_numbers(text: str) -> list[dict]:
    """从文本中提取数值特征"""
    results = []
    for m in RANGE_PATTERN.finditer(text):
        results.append({
            "type": "range",
            "low": float(m.group(1)),
            "high": float(m.group(2)),
            "unit": m.group(3),
            "raw": m.group(0),
        })
    for m in NUM_PATTERN.finditer(text):
        # 跳过已被范围模式捕获的
        raw = m.group(0)
        if any(raw in r["raw"] for r in results):
            continue
        results.append({
            "type": "single",
            "value": float(m.group(1)),
            "unit": m.group(2),
            "raw": raw,
        })
    return results


def extract_strengths(text: str) -> list[str]:
    """从文本中提取强度词"""
    return STRENGTH_PATTERN.findall(text)


def numbers_differ(nums_a: list[dict], nums_b: list[dict]) -> list[str]:
    """比较两组数值特征，返回差异描述"""
    diffs = []
    units_a = {n["unit"] for n in nums_a}
    units_b = {n["unit"] for n in nums_b}
    common_units = units_a & units_b

    for unit in common_units:
        vals_a = [n for n in nums_a if n["unit"] == unit]
        vals_b = [n for n in nums_b if n["unit"] == unit]
        raws_a = sorted(n["raw"] for n in vals_a)
        raws_b = sorted(n["raw"] for n in vals_b)
        if raws_a != raws_b:
            diffs.append(f"{unit}: {', '.join(raws_a)} vs {', '.join(raws_b)}")
    return diffs


def strengths_differ(strengths_a: list[str], strengths_b: list[str]) -> list[str]:
    """比较两组强度词，返回差异描述"""
    diffs = []
    set_a = set(strengths_a)
    set_b = set(strengths_b)
    if set_a != set_b:
        levels_a = [STRENGTH_LEVELS.get(s, 0) for s in set_a]
        levels_b = [STRENGTH_LEVELS.get(s, 0) for s in set_b]
        max_a = max(levels_a) if levels_a else 0
        max_b = max(levels_b) if levels_b else 0
        if max_a != max_b:
            diffs.append(
                f"强度词: {'/'.join(sorted(set_a))}(级别{max_a}) "
                f"vs {'/'.join(sorted(set_b))}(级别{max_b})"
            )
    return diffs


def detect_conflicts(clauses: list[dict]) -> list[dict]:
    """在同 category 内跨 source 检测候选冲突"""
    # 按 category_id 分组
    by_category: dict[str, list[dict]] = {}
    for cl in clauses:
        cat = cl.get("category_id", "")
        if cat:
            by_category.setdefault(cat, []).append(cl)

    candidates = []
    conflict_seq = 0

    for cat_id, cat_clauses in sorted(by_category.items()):
        # 只比较不同 source 的条款
        for cl_a, cl_b in combinations(cat_clauses, 2):
            if cl_a["source_id"] == cl_b["source_id"]:
                continue

            nums_a = extract_numbers(cl_a["text"])
            nums_b = extract_numbers(cl_b["text"])
            str_a = extract_strengths(cl_a.get("strength", "") + " " + cl_a["text"])
            str_b = extract_strengths(cl_b.get("strength", "") + " " + cl_b["text"])

            num_diffs = numbers_differ(nums_a, nums_b)
            str_diffs = strengths_differ(str_a, str_b)

            if num_diffs or str_diffs:
                conflict_seq += 1
                candidates.append({
                    "candidate_id": f"CAND-{conflict_seq:03d}",
                    "category_id": cat_id,
                    "clause_a": cl_a["clause_id"],
                    "clause_b": cl_b["clause_id"],
                    "source_a": cl_a["source_id"],
                    "source_b": cl_b["source_id"],
                    "subject_a": cl_a.get("subject", ""),
                    "subject_b": cl_b.get("subject", ""),
                    "number_diffs": num_diffs,
                    "strength_diffs": str_diffs,
                    "text_a": cl_a["text"],
                    "text_b": cl_b["text"],
                })

    return candidates


def main():
    parser = argparse.ArgumentParser(description="冲突候选预筛")
    parser.add_argument("--input", required=True, help="条款 JSON 路径 (clauses_draft.json)")
    parser.add_argument("--output", required=True, help="输出候选冲突 JSON 路径")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"错误：文件不存在 {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 支持两种输入格式：直接数组或含 clauses 字段的对象
    if isinstance(data, list):
        clauses = data
    else:
        clauses = data.get("clauses", [])

    candidates = detect_conflicts(clauses)

    output = {
        "total_clauses": len(clauses),
        "total_candidates": len(candidates),
        "candidates": candidates,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"冲突预筛完成：{len(clauses)} 条条款，{len(candidates)} 个候选冲突")
    for c in candidates:
        diffs = c["number_diffs"] + c["strength_diffs"]
        print(f"  {c['candidate_id']}: {c['clause_a']} vs {c['clause_b']} — {'; '.join(diffs)}")


if __name__ == "__main__":
    main()

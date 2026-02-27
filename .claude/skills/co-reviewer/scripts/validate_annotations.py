"""标注数据校验引擎

实现 13 条校验规则：完整性(V01-V04)、一致性(V05-V08)、语义(V09-V11)、置信度(V12-V13)。
"""

import argparse
import json
import os
import sys
from difflib import SequenceMatcher


def load_annotations(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate(annotations_data: dict, context: dict = None) -> dict:
    """对标注数据执行全部校验规则，返回校验报告"""
    ctx = context or {}
    annotations = annotations_data.get("annotations", [])
    issues = []

    for ann in annotations:
        oid = ann.get("opinion_id", "?")
        # 完整性校验
        issues.extend(_v01_required_fields(ann, oid))
        issues.extend(_v02_opinion_text(ann, oid))
        issues.extend(_v03_document_ref(ann, oid))
        issues.extend(_v04_regulation_ref(ann, oid))
        # 一致性校验
        issues.extend(_v05_file_exists(ann, oid, ctx))
        issues.extend(_v06_page_range(ann, oid, ctx))
        issues.extend(_v07_standard_exists(ann, oid, ctx))
        issues.extend(_v08_opinion_id_format(ann, oid))
        # 语义校验
        issues.extend(_v09_snippet_match(ann, oid, ctx))
        issues.extend(_v10_type_consistency(ann, oid))
        issues.extend(_v11_severity_valid(ann, oid))
        # 置信度校验
        issues.extend(_v12_confidence_range(ann, oid))
        issues.extend(_v13_confidence_grade(ann, oid))

    report = _build_report(annotations_data, issues)
    return report


# === 完整性校验 V01-V04 ===

def _v01_required_fields(ann: dict, oid: str) -> list:
    """V01: 顶层必填字段非空"""
    issues = []
    for field in ("project_id", "opinion_id", "opinion"):
        if not ann.get(field):
            issues.append(_issue(oid, "V01", "error", f"缺少必填字段: {field}"))
    return issues


def _v02_opinion_text(ann: dict, oid: str) -> list:
    """V02: 意见文本非空"""
    op = ann.get("opinion", {})
    if not op.get("text", "").strip():
        return [_issue(oid, "V02", "error", "意见文本为空")]
    return []


def _v03_document_ref(ann: dict, oid: str) -> list:
    """V03: 文件引用至少有 file 字段"""
    doc = ann.get("document", {})
    if not doc.get("file", "").strip():
        return [_issue(oid, "V03", "warning", "文件引用缺少 file 字段")]
    return []


def _v04_regulation_ref(ann: dict, oid: str) -> list:
    """V04: 规范引用至少有 standard_id 或 standard_name"""
    reg = ann.get("regulation", {})
    if not reg.get("standard_id") and not reg.get("standard_name"):
        return [_issue(oid, "V04", "warning", "规范引用缺少 standard_id 和 standard_name")]
    return []


# === 一致性校验 V05-V08 ===

def _v05_file_exists(ann: dict, oid: str, ctx: dict) -> list:
    """V05: 引用的文件名在项目文件清单中存在"""
    doc = ann.get("document", {})
    fname = doc.get("file", "")
    known_files = ctx.get("known_files", set())
    if fname and known_files and fname not in known_files:
        return [_issue(oid, "V05", "warning", f"引用文件不在项目清单中: {fname}")]
    return []


def _v06_page_range(ann: dict, oid: str, ctx: dict) -> list:
    """V06: 页码在文件实际页数范围内"""
    doc = ann.get("document", {})
    page = doc.get("page", 0)
    fname = doc.get("file", "")
    page_counts = ctx.get("page_counts", {})
    if fname and page and fname in page_counts:
        if page > page_counts[fname] or page < 1:
            return [_issue(oid, "V06", "warning", f"页码 {page} 超出 {fname} 范围(1-{page_counts[fname]})")]
    return []


def _v07_standard_exists(ann: dict, oid: str, ctx: dict) -> list:
    """V07: 引用的标准编号在规范库中存在"""
    reg = ann.get("regulation", {})
    sid = reg.get("standard_id", "")
    known_standards = ctx.get("known_standards", set())
    if sid and known_standards and sid not in known_standards:
        return [_issue(oid, "V07", "warning", f"标准编号不在规范库中: {sid}")]
    return []


def _v08_opinion_id_format(ann: dict, oid: str) -> list:
    """V08: opinion_id 格式为 OP-{project_id}-{seq}"""
    import re
    pid = ann.get("project_id", "")
    if oid and pid and not re.match(rf"OP-{re.escape(pid)}-\d+", oid):
        return [_issue(oid, "V08", "info", f"opinion_id 格式不规范，期望 OP-{pid}-XX")]
    return []


# === 语义校验 V09-V11 ===

def _v09_snippet_match(ann: dict, oid: str, ctx: dict) -> list:
    """V09: snippet 在对应 PDF 页面文本中模糊匹配"""
    doc = ann.get("document", {})
    snippet = doc.get("snippet", "")
    fname = doc.get("file", "")
    page = doc.get("page", 0)
    page_texts = ctx.get("page_texts", {})

    if not snippet or not fname or not page:
        return []

    key = f"{fname}:{page}"
    if key not in page_texts:
        return []

    page_text = page_texts[key]
    ratio = SequenceMatcher(None, snippet[:200], page_text[:2000]).ratio()
    if ratio < 0.3:
        return [_issue(oid, "V09", "warning", f"snippet 与页面文本匹配度低 ({ratio:.2f})")]
    return []


def _v10_type_consistency(ann: dict, oid: str) -> list:
    """V10: opinion.type 在允许值范围内"""
    valid_types = {"材料选型", "工程量", "技术标准", "造价", "形式审查", ""}
    op = ann.get("opinion", {})
    t = op.get("type", "")
    if t and t not in valid_types:
        return [_issue(oid, "V10", "info", f"意见类型 '{t}' 不在预定义范围内")]
    return []


def _v11_severity_valid(ann: dict, oid: str) -> list:
    """V11: severity 在 error/warning/info 范围内"""
    valid = {"error", "warning", "info"}
    op = ann.get("opinion", {})
    s = op.get("severity", "info")
    if s not in valid:
        return [_issue(oid, "V11", "warning", f"severity '{s}' 无效，应为 error/warning/info")]
    return []


# === 置信度校验 V12-V13 ===

def _v12_confidence_range(ann: dict, oid: str) -> list:
    """V12: 置信度在 0-1 范围内"""
    meta = ann.get("metadata", {})
    issues = []
    for key in ("confidence", "confidence_doc", "confidence_reg"):
        val = meta.get(key, 0)
        if not isinstance(val, (int, float)) or val < 0 or val > 1:
            issues.append(_issue(oid, "V12", "error", f"{key}={val} 不在 [0,1] 范围内"))
    return issues


def _v13_confidence_grade(ann: dict, oid: str) -> list:
    """V13: 置信度分级标记 high(>=0.85)/medium(0.6-0.85)/low(<0.6)"""
    meta = ann.get("metadata", {})
    conf = meta.get("confidence", 0)
    if not isinstance(conf, (int, float)):
        return []
    if conf >= 0.85:
        grade = "high"
    elif conf >= 0.6:
        grade = "medium"
    else:
        grade = "low"
    # 仅标记 low 置信度记录供人工审核
    if grade == "low":
        return [_issue(oid, "V13", "info", f"低置信度记录 ({conf:.2f})，建议人工审核")]
    return []


# === 辅助函数 ===

def _issue(opinion_id: str, rule: str, level: str, message: str) -> dict:
    return {
        "opinion_id": opinion_id,
        "rule": rule,
        "level": level,
        "message": message,
    }


def _build_report(annotations_data: dict, issues: list) -> dict:
    """构建校验报告"""
    total = len(annotations_data.get("annotations", []))
    by_level = {"error": 0, "warning": 0, "info": 0}
    by_rule = {}
    for iss in issues:
        by_level[iss["level"]] = by_level.get(iss["level"], 0) + 1
        by_rule[iss["rule"]] = by_rule.get(iss["rule"], 0) + 1

    # 需要人工审核的记录
    review_ids = set()
    for iss in issues:
        if iss["level"] in ("error", "warning"):
            review_ids.add(iss["opinion_id"])

    return {
        "project_id": annotations_data.get("project_id", ""),
        "total_annotations": total,
        "total_issues": len(issues),
        "by_level": by_level,
        "by_rule": by_rule,
        "needs_review": sorted(review_ids),
        "needs_review_count": len(review_ids),
        "pass_rate": round((total - len(review_ids)) / total, 2) if total else 0,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description="校验标注数据")
    parser.add_argument("--input", required=True, help="标注 JSON 文件路径")
    parser.add_argument("--output", type=str, help="输出校验报告路径")
    parser.add_argument("--context-dir", type=str, help="上下文目录（含 PDF 文本等）")
    args = parser.parse_args()

    data = load_annotations(args.input)

    # 构建上下文（如果提供了上下文目录）
    ctx = {}
    if args.context_dir and os.path.isdir(args.context_dir):
        ctx = _load_context(args.context_dir)

    report = validate(data, ctx)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"校验完成: {report['total_annotations']} 条标注, {report['total_issues']} 个问题")
        print(f"  error: {report['by_level']['error']}, warning: {report['by_level']['warning']}, info: {report['by_level']['info']}")
        print(f"  通过率: {report['pass_rate']}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


def _load_context(context_dir: str) -> dict:
    """从上下文目录加载辅助数据"""
    ctx = {"known_files": set(), "page_counts": {}, "known_standards": set(), "page_texts": {}}

    # 加载规范索引
    idx_path = os.path.join(context_dir, "regulations", "index.json")
    if os.path.isfile(idx_path):
        with open(idx_path, "r", encoding="utf-8") as f:
            for entry in json.load(f):
                ctx["known_standards"].add(entry.get("standard_id", ""))

    return ctx


if __name__ == "__main__":
    main()



"""项目目录自动发现：扫描项目测试数据目录，提取项目信息和文件清单"""

import argparse
import json
import os
import re
import sys

# 项目根目录
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
DATA_DIR = os.path.join(ROOT, "项目测试数据")

# 从目录名提取项目ID的正则，如 C1092323N6S8、C109HZ22A062
PROJECT_ID_RE = re.compile(r"[（(](C[A-Z0-9]+)[）)]")


def find_projects(base_dir: str = None, variant: str = "修改后") -> list[dict]:
    """扫描项目目录，返回项目信息列表"""
    base = base_dir or os.path.join(DATA_DIR, variant)
    if not os.path.isdir(base):
        print(f"目录不存在: {base}", file=sys.stderr)
        return []

    projects = []
    for entry in sorted(os.listdir(base)):
        full = os.path.join(base, entry)
        if not os.path.isdir(full) or not entry.startswith("成果资料"):
            continue

        m = PROJECT_ID_RE.search(entry)
        project_id = m.group(1) if m else entry
        # 提取项目名称（去掉"成果资料("前缀和项目ID后缀）
        name = entry.replace("成果资料(", "").replace("成果资料（", "")
        name = PROJECT_ID_RE.sub("", name).rstrip("）)").strip()

        project = {
            "project_id": project_id,
            "project_name": name,
            "dir": full,
            "files": _scan_files(full),
        }
        projects.append(project)

    return projects


def _scan_files(project_dir: str) -> dict:
    """扫描项目目录，按类别归类文件"""
    result = {
        "opinions": [],       # 专家意见 .xls
        "design_docs": [],    # 设计文件 PDF
        "budgets": [],        # 概算书
        "others": [],
    }
    assets_dir = os.path.join(project_dir, "成果资料")
    if not os.path.isdir(assets_dir):
        assets_dir = project_dir

    for dirpath, _, filenames in os.walk(assets_dir):
        rel_dir = os.path.relpath(dirpath, project_dir)
        for fn in filenames:
            if fn.startswith(".") or fn.startswith("~"):
                continue
            fp = os.path.join(dirpath, fn)
            info = {"name": fn, "path": fp, "rel_dir": rel_dir}

            if "专家意见" in fn and fn.endswith(".xls"):
                info["stage"] = _detect_stage(rel_dir)
                result["opinions"].append(info)
            elif fn.endswith(".pdf"):
                if "初设" in fn or "报告" in fn or "图纸" in fn or "说明" in fn:
                    result["design_docs"].append(info)
                elif "概算" in fn or "预算" in fn:
                    result["budgets"].append(info)
                else:
                    result["design_docs"].append(info)
            elif fn.endswith((".xlsx", ".xls")) and "概算" in fn:
                result["budgets"].append(info)
            else:
                result["others"].append(info)

    return result


def _detect_stage(rel_dir: str) -> str:
    """从目录路径推断评审阶段"""
    if "预审" in rel_dir:
        return "预审"
    elif "收口" in rel_dir:
        return "收口评审"
    elif "正式" in rel_dir:
        return "正式评审"
    return ""


def main():
    parser = argparse.ArgumentParser(description="发现项目测试数据")
    parser.add_argument("--all", action="store_true", help="显示所有项目")
    parser.add_argument("--project-id", type=str, help="只显示指定项目ID")
    parser.add_argument("--variant", default="修改后", help="修改前/修改后")
    parser.add_argument("--output", type=str, help="输出 JSON 文件路径")
    args = parser.parse_args()

    projects = find_projects(variant=args.variant)

    if args.project_id:
        projects = [p for p in projects if p["project_id"] == args.project_id]

    if not projects:
        print("未发现任何项目", file=sys.stderr)
        sys.exit(1)

    for p in projects:
        ops = len(p["files"]["opinions"])
        docs = len(p["files"]["design_docs"])
        buds = len(p["files"]["budgets"])
        print(f"[{p['project_id']}] {p['project_name']}")
        print(f"  专家意见: {ops}, 设计文件: {docs}, 概算: {buds}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        print(f"\n已输出到 {args.output}")
    elif args.all:
        print(json.dumps(projects, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

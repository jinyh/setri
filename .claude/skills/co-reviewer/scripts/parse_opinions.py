"""XLS 专家意见解析 → JSON

读取 .xls 格式的专家意见文件，提取结构化意见数据。
列结构：序号 | 意见类型 | 填写时间 | 填写人 | 专业名称 | 审核结果 | 审核意见 | 意见说明
"""

import argparse
import json
import os
import sys

import xlrd

# 意见类型 → 评审阶段映射
STAGE_MAP = {
    "预审意见": "预审",
    "正式意见": "正式评审",
    "收口意见": "收口评审",
}

# 列索引
COL_SEQ = 0
COL_TYPE = 1
COL_TIME = 2
COL_EXPERT = 3
COL_ROLE = 4
COL_RESULT = 5
COL_OPINION = 6
COL_DESC = 7


def parse_opinion_xls(xls_path: str, stage_hint: str = "") -> list[dict]:
    """解析单个专家意见 XLS 文件"""
    wb = xlrd.open_workbook(xls_path)
    sh = wb.sheet_by_index(0)

    opinions = []
    for r in range(1, sh.nrows):
        def cell(c):
            return str(sh.cell_value(r, c)).strip() if c < sh.ncols else ""

        seq = cell(COL_SEQ)
        if not seq or seq == "序号":
            continue

        opinion_type = cell(COL_TYPE)
        stage = STAGE_MAP.get(opinion_type, stage_hint or opinion_type)
        opinion_text = cell(COL_OPINION)
        description = cell(COL_DESC)

        # 合并意见和说明
        full_text = opinion_text
        if description:
            full_text = f"{opinion_text}；{description}" if opinion_text else description

        # 判断严重程度
        result = cell(COL_RESULT)
        if "不通过" in result or "否决" in result:
            severity = "error"
        elif opinion_text == "原则同意" and not description:
            severity = "info"
        else:
            severity = "warning" if description else "info"

        opinions.append({
            "seq": int(float(seq)) if seq.replace(".", "").isdigit() else r,
            "text": full_text,
            "opinion_type": opinion_type,
            "severity": severity,
            "review_stage": stage,
            "expert_name": cell(COL_EXPERT),
            "expert_role": cell(COL_ROLE),
            "review_result": result,
            "timestamp": cell(COL_TIME),
        })

    return opinions


def parse_project_opinions(project_dir: str) -> dict:
    """解析一个项目下所有评审阶段的专家意见"""
    assets_dir = os.path.join(project_dir, "成果资料")
    if not os.path.isdir(assets_dir):
        assets_dir = project_dir

    stage_dirs = {
        "预审专家意见": "预审",
        "正式评审专家意见": "正式评审",
        "收口评审专家意见": "收口评审",
    }

    all_opinions = []
    for dirname, stage in stage_dirs.items():
        d = os.path.join(assets_dir, dirname)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(".xls") and not fn.startswith("~"):
                fp = os.path.join(d, fn)
                ops = parse_opinion_xls(fp, stage_hint=stage)
                all_opinions.extend(ops)

    return {
        "total": len(all_opinions),
        "by_stage": _group_by(all_opinions, "review_stage"),
        "opinions": all_opinions,
    }


def _group_by(items: list, key: str) -> dict:
    groups = {}
    for item in items:
        g = item.get(key, "unknown")
        groups.setdefault(g, 0)
        groups[g] += 1
    return groups


def main():
    parser = argparse.ArgumentParser(description="解析专家意见 XLS")
    parser.add_argument("--input", required=True, help="XLS 文件路径或项目目录")
    parser.add_argument("--output", type=str, help="输出 JSON 路径")
    args = parser.parse_args()

    if os.path.isfile(args.input) and args.input.endswith(".xls"):
        result = {"opinions": parse_opinion_xls(args.input), "total": 0}
        result["total"] = len(result["opinions"])
    elif os.path.isdir(args.input):
        result = parse_project_opinions(args.input)
    else:
        print(f"无效输入: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"已输出 {result['total']} 条意见到 {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

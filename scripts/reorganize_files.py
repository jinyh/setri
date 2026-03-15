#!/usr/bin/env python3
"""
文件整理脚本 - 将测试项目文件按 PRD §4.3.8 存储规范整理到标准化目录结构
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# 项目根目录
BASE_DIR = Path("/Users/jinyh/Documents/AIProjects/setri")

# 同义词映射表（基于 PRD §4.3.6）
SYNONYMS = {
    # 辅助文件
    "A-01": ["设计中标通知书或委托书", "设计委托书"],
    "A-02": ["内审意见", "内审意见及签到单"],
    "A-03": ["其它依据", "其他依据", "其他"],
    "A-04": ["投资汇总表"],
    "A-05": ["财务审核表"],
    "A-06": ["供电方案审核单"],
    "A-07": ["通信方案确认单"],
    "A-08": ["主要设备材料清册", "主要设备材料清册（pdf、word版）"],
    "A-09": ["案例分析报告"],
    "A-10": ["可行性研究报告", "初设报告", "设计报告", "说明书"],

    # 专业图纸关键词
    "D-01": ["KT站", "开关站"],
    "D-02": ["PT", "PML", "街坊站"],
    "D-03": ["站内电缆"],
    "D-04": ["内线电缆-10kV", "10kV电缆", "（10kV电缆）"],
    "D-05": ["内线电缆-0.4kV", "0.4kV电缆", "（0.4kV电缆）"],
    "D-06": ["内线通信", "通信", "（通信）"],
    "D-07": ["信息采集", "用电信息采集", "（信息采集）"],

    # 工程估算
    "E-xx": ["工程估算书", "工程概算书"],

    # 子目录
    "materials": ["主要建设材料表", "主要设备材料清册", "材料清册", "设备材料清册"],
    "demolition": ["拆除设备清单"],
    "references": ["其他图纸", "图纸资料", "设计图纸"],
}

# 标准化目录名映射
STANDARD_NAMES = {
    "A-01": "A-01_design_commission",
    "A-02": "A-02_internal_review",
    "A-03": "A-03_other_references",
    "A-04": "A-04_investment_summary",
    "A-05": "A-05_financial_review",
    "A-06": "A-06_power_supply_approval",
    "A-07": "A-07_telecom_approval",
    "A-08": "A-08_equipment_list",
    "A-09": "A-09_case_analysis",
    "D-01": "D-01_switchgear",
    "D-02": "D-02_substation",
    "D-03": "D-03_station_cable",
    "D-04": "D-04_hv_cable",
    "D-05": "D-05_lv_cable",
    "D-06": "D-06_telecom",
    "D-07": "D-07_metering",
    "E-01": "E-01_switchgear",
    "E-02": "E-02_substation",
    "E-03": "E-03_station_cable",
    "E-04": "E-04_hv_cable",
    "E-05": "E-05_lv_cable",
    "E-06": "E-06_telecom",
    "E-07": "E-07_metering",
}

# 文件类型过滤
VALID_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ofd"}
EXCLUDE_EXTENSIONS = {".bdd3", ".bpz17", ".DS_Store", ".db", ".tmp"}


def match_directory(dir_name: str, type_id: str) -> bool:
    """模糊匹配目录名到文件类型"""
    if type_id not in SYNONYMS:
        return False

    dir_lower = dir_name.lower()
    for synonym in SYNONYMS[type_id]:
        if synonym.lower() in dir_lower:
            return True
    return False


def is_valid_file(file_path: Path) -> bool:
    """检查文件是否应该被复制"""
    ext = file_path.suffix.lower()
    if ext in EXCLUDE_EXTENSIONS:
        return False
    if ext in VALID_EXTENSIONS:
        return True
    return False


def copy_files_recursive(src_dir: Path, dst_dir: Path, file_mapping: List) -> int:
    """递归复制目录中的有效文件"""
    if not src_dir.exists():
        return 0

    count = 0
    for item in src_dir.rglob("*"):
        if item.is_file() and is_valid_file(item):
            rel_path = item.relative_to(src_dir)
            dst_file = dst_dir / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst_file)

            # 记录映射
            file_mapping.append({
                "source": str(item.relative_to(BASE_DIR)),
                "target": str(dst_file.relative_to(BASE_DIR))
            })
            count += 1

    return count


def scan_and_map_project(source_dir: Path, version: str) -> Dict:
    """扫描项目目录结构并生成映射"""
    structure = {
        "auxiliary": {},
        "feasibility": [],
        "drawings": {},
        "estimates": {},
        "materials": {},
        "demolition": {},
        "references": {}
    }

    if not source_dir.exists():
        return structure

    for item in source_dir.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue

        dir_name = item.name

        # 匹配辅助文件 A-01 ~ A-09
        for aid in [f"A-{i:02d}" for i in range(1, 10)]:
            if match_directory(dir_name, aid):
                structure["auxiliary"][aid] = str(item.relative_to(BASE_DIR))
                break

        # 匹配可研报告 A-10
        if match_directory(dir_name, "A-10"):
            structure["feasibility"].append(str(item.relative_to(BASE_DIR)))

        # 匹配专业图纸 D-01 ~ D-07
        for did in [f"D-{i:02d}" for i in range(1, 8)]:
            if match_directory(dir_name, did):
                if did not in structure["drawings"]:
                    structure["drawings"][did] = []
                structure["drawings"][did].append({
                    "path": str(item.relative_to(BASE_DIR)),
                    "name": dir_name
                })

                # 扫描专业目录内部
                for subitem in item.iterdir():
                    if not subitem.is_dir():
                        continue

                    sub_name = subitem.name

                    # 工程估算
                    if match_directory(sub_name, "E-xx"):
                        eid = did.replace("D-", "E-")
                        if eid not in structure["estimates"]:
                            structure["estimates"][eid] = []
                        structure["estimates"][eid].append(str(subitem.relative_to(BASE_DIR)))

                    # 材料清册
                    elif match_directory(sub_name, "materials"):
                        if did not in structure["materials"]:
                            structure["materials"][did] = []
                        structure["materials"][did].append(str(subitem.relative_to(BASE_DIR)))

                    # 拆除清单
                    elif match_directory(sub_name, "demolition"):
                        if did not in structure["demolition"]:
                            structure["demolition"][did] = []
                        structure["demolition"][did].append(str(subitem.relative_to(BASE_DIR)))

                    # 其他图纸/依据
                    elif match_directory(sub_name, "references"):
                        if did not in structure["references"]:
                            structure["references"][did] = []
                        structure["references"][did].append(str(subitem.relative_to(BASE_DIR)))

                    # 可研报告（在专业目录内）
                    elif match_directory(sub_name, "A-10"):
                        structure["feasibility"].append(str(subitem.relative_to(BASE_DIR)))

                break

    return structure


def reorganize_project(project_config: Dict) -> Dict:
    """整理单个项目的文件"""
    project_id = project_config["project_id"]
    project_name = project_config["project_name"]

    print(f"\n{'='*60}")
    print(f"开始整理项目: {project_name} ({project_id})")
    print(f"{'='*60}")

    # 源路径
    source_submitted = BASE_DIR / project_config["source_submitted"]
    source_approved = BASE_DIR / project_config["source_approved"]

    # 目标路径
    target_dir = BASE_DIR / project_config["target"]
    target_dir.mkdir(parents=True, exist_ok=True)

    # 文件映射记录
    file_mapping = []
    stats = {
        "auxiliary": 0,
        "feasibility_submitted": 0,
        "feasibility_approved": 0,
        "drawings_submitted": 0,
        "drawings_approved": 0,
        "estimates_submitted": 0,
        "estimates_approved": 0,
        "materials_submitted": 0,
        "materials_approved": 0,
        "demolition_submitted": 0,
        "demolition_approved": 0,
        "references_submitted": 0,
        "references_approved": 0,
    }

    # 扫描送审版和审定版
    print("\n[Phase 1] 扫描目录结构...")
    submitted_structure = scan_and_map_project(source_submitted, "submitted")
    approved_structure = scan_and_map_project(source_approved, "approved")

    # 创建目标目录结构
    print("\n[Phase 2] 创建目标目录结构...")
    (target_dir / "design" / "auxiliary").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "submitted" / "feasibility_report").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "submitted" / "drawings").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "submitted" / "estimates").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "submitted" / "materials").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "submitted" / "demolition").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "submitted" / "references").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "approved" / "feasibility_report").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "approved" / "drawings").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "approved" / "estimates").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "approved" / "materials").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "approved" / "demolition").mkdir(parents=True, exist_ok=True)
    (target_dir / "design" / "approved" / "references").mkdir(parents=True, exist_ok=True)

    # 复制辅助文件（共享，从送审版复制）
    print("\n[Phase 3] 复制辅助文件 (A-01 ~ A-09)...")
    for aid, src_path in submitted_structure["auxiliary"].items():
        dst_dir = target_dir / "design" / "auxiliary" / STANDARD_NAMES[aid]
        dst_dir.mkdir(parents=True, exist_ok=True)
        count = copy_files_recursive(BASE_DIR / src_path, dst_dir, file_mapping)
        stats["auxiliary"] += count
        print(f"  {aid}: {count} 个文件")

    # 复制可研报告（版本敏感）
    print("\n[Phase 4] 复制可研报告 (A-10)...")

    # 送审版可研报告（去重）
    feasibility_files_submitted = set()
    for src_path in submitted_structure["feasibility"]:
        src_dir = BASE_DIR / src_path
        for file in src_dir.rglob("*"):
            if file.is_file() and is_valid_file(file):
                feasibility_files_submitted.add(file.name)

    dst_dir = target_dir / "design" / "submitted" / "feasibility_report"
    for src_path in submitted_structure["feasibility"]:
        count = copy_files_recursive(BASE_DIR / src_path, dst_dir, file_mapping)
        stats["feasibility_submitted"] += count
    print(f"  送审版: {stats['feasibility_submitted']} 个文件（去重后）")

    # 审定版可研报告
    dst_dir = target_dir / "design" / "approved" / "feasibility_report"
    for src_path in approved_structure["feasibility"]:
        count = copy_files_recursive(BASE_DIR / src_path, dst_dir, file_mapping)
        stats["feasibility_approved"] += count
    print(f"  审定版: {stats['feasibility_approved']} 个文件")

    # 复制专业图纸
    print("\n[Phase 5] 复制专业图纸 (D-01 ~ D-07)...")
    for version, structure, version_name in [
        ("submitted", submitted_structure, "送审版"),
        ("approved", approved_structure, "审定版")
    ]:
        print(f"\n  {version_name}:")
        for did, drawings in structure["drawings"].items():
            for idx, drawing in enumerate(drawings, 1):
                # 处理多个同类型（如多个街坊站）
                if len(drawings) > 1:
                    suffix = f"_{idx:02d}"
                else:
                    suffix = ""

                dst_dir = target_dir / "design" / version / "drawings" / f"{STANDARD_NAMES[did]}{suffix}"
                dst_dir.mkdir(parents=True, exist_ok=True)

                count = copy_files_recursive(BASE_DIR / drawing["path"], dst_dir, file_mapping)
                stats[f"drawings_{version}"] += count
                print(f"    {did}{suffix}: {count} 个文件")

    # 复制工程估算
    print("\n[Phase 6] 复制工程估算 (E-01 ~ E-07)...")
    for version, structure, version_name in [
        ("submitted", submitted_structure, "送审版"),
        ("approved", approved_structure, "审定版")
    ]:
        print(f"\n  {version_name}:")
        for eid, estimates in structure["estimates"].items():
            # 处理多个同类型
            if len(estimates) > 1:
                for idx, src_path in enumerate(estimates, 1):
                    suffix = f"_{idx:02d}"
                    dst_dir = target_dir / "design" / version / "estimates" / f"{STANDARD_NAMES[eid]}{suffix}"
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    count = copy_files_recursive(BASE_DIR / src_path, dst_dir, file_mapping)
                    stats[f"estimates_{version}"] += count
                    print(f"    {eid}{suffix}: {count} 个文件")
            else:
                dst_dir = target_dir / "design" / version / "estimates" / STANDARD_NAMES[eid]
                dst_dir.mkdir(parents=True, exist_ok=True)
                count = copy_files_recursive(BASE_DIR / estimates[0], dst_dir, file_mapping)
                stats[f"estimates_{version}"] += count
                print(f"    {eid}: {count} 个文件")

    # 复制材料清册
    print("\n[Phase 7] 复制材料清册...")
    for version, structure, version_name in [
        ("submitted", submitted_structure, "送审版"),
        ("approved", approved_structure, "审定版")
    ]:
        print(f"\n  {version_name}:")
        for did, materials in structure["materials"].items():
            for src_path in materials:
                # 使用完整的 D-xx_{专业类型} 格式
                dst_dir = target_dir / "design" / version / "materials" / STANDARD_NAMES[did]
                dst_dir.mkdir(parents=True, exist_ok=True)
                count = copy_files_recursive(BASE_DIR / src_path, dst_dir, file_mapping)
                stats[f"materials_{version}"] += count
        print(f"    总计: {stats[f'materials_{version}']} 个文件")

    # 复制拆除清单
    print("\n[Phase 8] 复制拆除清单...")
    for version, structure, version_name in [
        ("submitted", submitted_structure, "送审版"),
        ("approved", approved_structure, "审定版")
    ]:
        print(f"\n  {version_name}:")
        for did, demolitions in structure["demolition"].items():
            for src_path in demolitions:
                dst_dir = target_dir / "design" / version / "demolition" / STANDARD_NAMES[did]
                dst_dir.mkdir(parents=True, exist_ok=True)
                count = copy_files_recursive(BASE_DIR / src_path, dst_dir, file_mapping)
                stats[f"demolition_{version}"] += count
        print(f"    总计: {stats[f'demolition_{version}']} 个文件")

    # 复制其他图纸/依据
    print("\n[Phase 9] 复制其他图纸/依据...")
    for version, structure, version_name in [
        ("submitted", submitted_structure, "送审版"),
        ("approved", approved_structure, "审定版")
    ]:
        print(f"\n  {version_name}:")
        for did, references in structure["references"].items():
            for src_path in references:
                dst_dir = target_dir / "design" / version / "references" / STANDARD_NAMES[did]
                dst_dir.mkdir(parents=True, exist_ok=True)
                count = copy_files_recursive(BASE_DIR / src_path, dst_dir, file_mapping)
                stats[f"references_{version}"] += count
        print(f"    总计: {stats[f'references_{version}']} 个文件")

    # 生成 meta.json
    print("\n[Phase 10] 生成 meta.json...")
    meta = {
        "project_id": project_id,
        "project_name": project_name,
        "source_paths": {
            "submitted": str(source_submitted.relative_to(BASE_DIR)),
            "approved": str(source_approved.relative_to(BASE_DIR))
        },
        "path_mapping": file_mapping,
        "statistics": stats
    }

    with open(target_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"\n完成! 总计复制 {sum(stats.values())} 个文件")

    return meta


def main():
    """主函数"""
    # 加载项目配置
    config_file = BASE_DIR / "tmp/reorganize_mapping.json"
    with open(config_file) as f:
        config = json.load(f)

    print(f"\n开始整理 {len(config['projects'])} 个测试项目...")

    all_results = []
    for project in config["projects"]:
        result = reorganize_project(project)
        all_results.append(result)

    # 生成总体报告
    print(f"\n{'='*60}")
    print("整理完成! 总体统计:")
    print(f"{'='*60}")

    for result in all_results:
        print(f"\n{result['project_name']} ({result['project_id']}):")
        total = sum(result['statistics'].values())
        print(f"  总文件数: {total}")
        for key, value in result['statistics'].items():
            if value > 0:
                print(f"    {key}: {value}")

    # 验证目录命名
    print(f"\n{'='*60}")
    print("验证目录命名规范...")
    print(f"{'='*60}")

    projects_dir = BASE_DIR / "data/projects"

    # 检查是否有不符合规范的目录（materials/demolition/references 下应该是 D-xx_xxx 格式）
    invalid_dirs = []
    for subdir in ["materials", "demolition", "references"]:
        pattern = f"*/{subdir}/D-0[1-7]"
        for path in projects_dir.glob(f"**/design/*/{subdir}/*"):
            if path.is_dir() and not path.name.startswith("D-"):
                invalid_dirs.append(str(path.relative_to(BASE_DIR)))

    if invalid_dirs:
        print(f"\n⚠️  发现 {len(invalid_dirs)} 个不符合规范的目录:")
        for d in invalid_dirs:
            print(f"  - {d}")
    else:
        print("\n✅ 所有目录命名符合规范")

    print(f"\n{'='*60}")
    print("全部完成!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

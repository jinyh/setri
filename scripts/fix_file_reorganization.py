#!/usr/bin/env python3
"""
修复 data/projects 目录结构的脚本
补充缺失的：
1. 站内电缆（D-03）子目录中的文件
2. 审定版（approved）所有文件
3. 生成 meta.json
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import re

# 项目注册表
PROJECTS = {
    "C109HZ22A062": {
        "short_name": "崇明盛世新苑",
        "full_name": "上海崇明城桥置业高岛路170弄盛世新苑10kV普通住宅红线内接入工程"
    },
    "C1092322A133": {
        "short_name": "奉贤悦景名筑",
        "full_name": "上海奉贤翀溢置业庄良路60弄悦景名筑10kV普通住宅红线内接入工程"
    },
    "C1092323N6S8": {
        "short_name": "奉贤咉懿佳园",
        "full_name": "上海奉贤陕名置业正旭路80弄咉懿佳园10kV普通住宅红线内接入工程"
    }
}

SOURCE_DIR = Path("项目测试数据")
TARGET_DIR = Path("data/projects")

# 文件类型过滤
ALLOWED_EXTENSIONS = {'.pdf', '.xlsx', '.xls', '.docx', '.doc', '.pptx', '.ofd'}
EXCLUDED_EXTENSIONS = {'.bdd3', '.bpz17', '.ds_store', '.db', '.tmp'}

# 专业类型映射（用于识别目录）
SPECIALTY_KEYWORDS = {
    'D-01': ['KT站', '开关站电气一次', '开关站'],
    'D-02': ['PT', 'PML', '街坊站电气一次', '零一街坊站', '零二街坊站', '零三街坊站', '零四街坊站', '零五街坊站'],
    'D-03': ['站内电缆', '-10kV站内电缆'],
    'D-04': ['内线电缆-10kV', '10kV电缆', '（10kV电缆）'],
    'D-05': ['内线电缆-0.4kV', '0.4kV电缆', '（0.4kV电缆）'],
    'D-06': ['内线通信', '通信', '（通信）'],
    'D-07': ['信息采集', '用电信息采集', '（信息采集）']
}


def should_process_file(file_path: Path) -> bool:
    """判断文件是否应该被处理"""
    ext = file_path.suffix.lower()
    if ext in EXCLUDED_EXTENSIONS:
        return False
    if ext in ALLOWED_EXTENSIONS:
        return True
    return False


def match_specialty_type(dir_name: str) -> str:
    """匹配专业类型"""
    dir_name_lower = dir_name.lower()

    # 特殊处理：站内电缆 vs 高压电缆
    if '站内电缆' in dir_name or '-10kv站内电缆' in dir_name_lower:
        return 'D-03'

    for type_id, keywords in SPECIALTY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in dir_name_lower:
                return type_id

    return None


def copy_files_recursive(src_dir: Path, dst_dir: Path, file_count: dict, file_mapping: list):
    """递归复制符合条件的文件，并记录映射"""
    if not src_dir.exists():
        return

    for item in src_dir.iterdir():
        if item.is_file() and should_process_file(item):
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_file = dst_dir / item.name
            shutil.copy2(item, dst_file)
            file_count['total'] += 1

            # 记录文件映射（使用相对于项目根目录的路径）
            file_mapping.append({
                "source": str(item),
                "target": str(dst_file)
            })
        elif item.is_dir():
            copy_files_recursive(item, dst_dir, file_count, file_mapping)


def process_specialty_dir(src_dir: Path, target_base: Path, specialty_type: str, index: int, version: str, file_count: dict, file_mapping: list):
    """处理专业子项目录"""
    # 确定目标子目录后缀
    suffix = f"_{index:02d}" if specialty_type in ['D-02', 'D-03', 'E-02', 'E-03'] and index > 0 else ""

    # 处理图纸（drawings）
    drawings_src = src_dir / "设计图纸"
    if drawings_src.exists():
        drawings_dst = target_base / version / "drawings" / f"{specialty_type}{suffix}"
        copy_files_recursive(drawings_src, drawings_dst, file_count, file_mapping)

    # 处理工程估算（estimates）
    for estimate_dir_name in ["工程概算书（PDF版）", "工程概算书", "工程估算书（PDF版）", "工程估算书"]:
        estimate_src = src_dir / estimate_dir_name
        if estimate_src.exists():
            estimate_type = specialty_type.replace('D-', 'E-')
            estimate_dst = target_base / version / "estimates" / f"{estimate_type}{suffix}"
            copy_files_recursive(estimate_src, estimate_dst, file_count, file_mapping)
            break

    # 处理可研报告（feasibility_report）
    for report_dir_name in ["初设报告", "可研报告", "可行性研究报告", "设计报告"]:
        report_src = src_dir / report_dir_name
        if report_src.exists():
            report_dst = target_base / version / "feasibility_report"
            copy_files_recursive(report_src, report_dst, file_count, file_mapping)
            break

    # 处理材料清册（materials）
    for material_dir_name in ["主要建设材料表", "主要材料清册", "设备材料清册", "设备材料清册（PDF版）"]:
        material_src = src_dir / material_dir_name
        if material_src.exists():
            material_dst = target_base / version / "materials" / f"{specialty_type}{suffix}"
            copy_files_recursive(material_src, material_dst, file_count, file_mapping)
            break

    # 处理拆除设备清单（demolition）
    for demolition_dir_name in ["拆除设备清单", "拆除设备材料清单"]:
        demolition_src = src_dir / demolition_dir_name
        if demolition_src.exists():
            demolition_dst = target_base / version / "demolition" / f"{specialty_type}{suffix}"
            copy_files_recursive(demolition_src, demolition_dst, file_count, file_mapping)
            break


def process_project(project_id: str, project_info: dict):
    """处理单个项目"""
    print(f"\n{'='*60}")
    print(f"处理项目: {project_info['short_name']} ({project_id})")
    print(f"{'='*60}")

    full_name = project_info['full_name']
    target_base = TARGET_DIR / project_id / "design"

    file_count = {'total': 0}
    file_mapping = []  # 新增：收集所有文件映射

    # 处理送审版和审定版
    for version_cn, version_en in [("修改前", "submitted"), ("修改后", "approved")]:
        print(f"\n处理 {version_cn} ({version_en})...")

        # 构造源路径
        src_base = SOURCE_DIR / version_cn / f"成果资料({full_name}（{project_id}）)" / "成果资料"
        version_src = src_base / ("送审版" if version_cn == "修改前" else "审定版")

        if not version_src.exists():
            print(f"  ⚠️  源目录不存在: {version_src}")
            continue

        # 扫描专业子项目录
        specialty_dirs = {}
        for item in version_src.iterdir():
            if not item.is_dir():
                continue

            specialty_type = match_specialty_type(item.name)
            if specialty_type:
                if specialty_type not in specialty_dirs:
                    specialty_dirs[specialty_type] = []
                specialty_dirs[specialty_type].append(item)

        # 按专业类型处理
        for specialty_type, dirs in sorted(specialty_dirs.items()):
            dirs.sort(key=lambda x: x.name)  # 按目录名排序
            for idx, dir_path in enumerate(dirs, start=1):
                print(f"  处理 {specialty_type} #{idx}: {dir_path.name}")
                process_specialty_dir(dir_path, target_base, specialty_type, idx, version_en, file_count, file_mapping)

    print(f"\n✅ 项目 {project_info['short_name']} 处理完成，共复制 {file_count['total']} 个文件")

    # 生成 meta.json，传入文件映射
    generate_meta_json(project_id, project_info, file_mapping)


def generate_meta_json(project_id: str, project_info: dict, path_mapping: list = None):
    """生成 meta.json"""
    meta_path = TARGET_DIR / project_id / "meta.json"

    meta = {
        "project_id": project_id,
        "project_name": project_info['full_name'],
        "short_name": project_info['short_name'],
        "imported_at": datetime.now().isoformat(),
        "source_paths": {
            "submitted": f"项目测试数据/修改前/成果资料({project_info['full_name']}（{project_id}）)/成果资料/",
            "approved": f"项目测试数据/修改后/成果资料({project_info['full_name']}（{project_id}）)/成果资料/"
        },
        "file_type_filter": list(ALLOWED_EXTENSIONS),
        "path_mapping": path_mapping if path_mapping else [],
        "note": "此文件由 fix_file_reorganization.py 生成，记录文件整理的元信息"
    }

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"  生成 meta.json: {meta_path}")


def main():
    print("开始修复 data/projects 目录结构...")
    print(f"源目录: {SOURCE_DIR.absolute()}")
    print(f"目标目录: {TARGET_DIR.absolute()}")

    for project_id, project_info in PROJECTS.items():
        process_project(project_id, project_info)

    print(f"\n{'='*60}")
    print("✅ 所有项目处理完成")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

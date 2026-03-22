#!/usr/bin/env python3
"""
清理 data/projects 中的重复目录
保留符合 PRD 规范的完整命名（如 D-01_switchgear），删除简短命名（如 D-01）
"""

import shutil
from pathlib import Path

TARGET_DIR = Path("data/projects")

# 定义重复目录映射：简短名 -> 完整名
DUPLICATE_MAPPINGS = {
    'D-01': 'D-01_switchgear',
    'D-02_01': 'D-02_substation_01',
    'D-02_02': 'D-02_substation_02',
    'D-02_03': 'D-02_substation_03',
    'D-02_04': 'D-02_substation_04',
    'D-02_05': 'D-02_substation_05',
    'D-03_01': 'D-03_station_cable_01',
    'D-03_02': 'D-03_station_cable_02',
    'D-03_03': 'D-03_station_cable_03',
    'D-03_04': 'D-03_station_cable_04',
    'D-03_05': 'D-03_station_cable_05',
    'D-03_06': 'D-03_station_cable_06',
    'D-04': 'D-04_hv_cable',
    'D-05': 'D-05_lv_cable',
    'D-06': 'D-06_telecom',
    'D-07': 'D-07_metering',
    'E-01': 'E-01_switchgear',
    'E-02_01': 'E-02_substation_01',
    'E-02_02': 'E-02_substation_02',
    'E-02_03': 'E-02_substation_03',
    'E-02_04': 'E-02_substation_04',
    'E-02_05': 'E-02_substation_05',
    'E-03_01': 'E-03_station_cable_01',
    'E-03_02': 'E-03_station_cable_02',
    'E-03_03': 'E-03_station_cable_03',
    'E-03_04': 'E-03_station_cable_04',
    'E-03_05': 'E-03_station_cable_05',
    'E-03_06': 'E-03_station_cable_06',
    'E-04': 'E-04_hv_cable',
    'E-05': 'E-05_lv_cable',
    'E-06': 'E-06_telecom',
    'E-07': 'E-07_metering',
}


def cleanup_project(project_dir: Path):
    """清理单个项目的重复目录"""
    print(f"\n处理项目: {project_dir.name}")

    removed_count = 0

    # 处理 submitted 和 approved
    for version in ['submitted', 'approved']:
        for category in ['drawings', 'estimates']:
            category_dir = project_dir / 'design' / version / category
            if not category_dir.exists():
                continue

            # 查找并删除重复目录
            for short_name, full_name in DUPLICATE_MAPPINGS.items():
                short_dir = category_dir / short_name
                full_dir = category_dir / full_name

                if short_dir.exists() and full_dir.exists():
                    # 两个目录都存在，删除简短命名的
                    print(f"  删除重复目录: {version}/{category}/{short_name}")
                    shutil.rmtree(short_dir)
                    removed_count += 1
                elif short_dir.exists() and not full_dir.exists():
                    # 只有简短命名存在，重命名为完整命名
                    print(f"  重命名: {version}/{category}/{short_name} -> {full_name}")
                    short_dir.rename(full_dir)

    print(f"  共删除 {removed_count} 个重复目录")


def main():
    print("开始清理重复目录...")

    for project_dir in TARGET_DIR.iterdir():
        if project_dir.is_dir() and project_dir.name.startswith('C'):
            cleanup_project(project_dir)

    print("\n✅ 清理完成")


if __name__ == "__main__":
    main()

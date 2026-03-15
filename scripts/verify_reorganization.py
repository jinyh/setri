#!/usr/bin/env python3
"""
验证脚本 - 验证 file-reorganizer 执行结果的正确性

基于 PRD §4.3.8 存储规范，验证项目文件整理结果的完整性、准确性和规范性。

使用方式:
    python scripts/verify_reorganization.py --project C109HZ22A062
    python scripts/verify_reorganization.py --all
    python scripts/verify_reorganization.py --project C109HZ22A062 --format json
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ValidationResult:
    """验证结果"""
    status: str  # "pass", "warning", "error"
    score: int  # 0-100
    details: Dict
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """验证报告"""
    project_id: str
    project_name: str
    validation_time: str
    overall_score: int
    results: Dict[str, ValidationResult]

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "validation_time": self.validation_time,
            "overall_score": self.overall_score,
            "results": {
                name: {
                    "status": result.status,
                    "score": result.score,
                    "details": result.details,
                    "issues": result.issues,
                    "warnings": result.warnings
                }
                for name, result in self.results.items()
            }
        }


class DirectoryStructureValidator:
    """目录结构验证器"""

    # 必备目录结构（支持中文和英文两种命名）
    REQUIRED_DIRS = [
        ["设计文件", "design"],
        ["设计文件/送审版", "design/submitted"],
        ["设计文件/送审版/项目级", "design/auxiliary"],
        ["设计文件/审定版", "design/approved"],
        ["设计文件/审定版/项目级", "design/auxiliary"],
    ]

    # 项目级必备文件（支持同义词）
    REQUIRED_PROJECT_FILES = {
        "设计委托书": ["设计委托书", "委托书", "智方委托书", "设计中标通知书"],
        "内审意见": ["内审意见", "内审意见及签到单", "评审意见"],
        "投资汇总表": ["投资汇总表", "投资费用汇总表"],
        "主要设备材料清册": ["主要设备材料清册", "设备材料清册", "主要材料清册"],
    }

    # 可选项目级文件
    OPTIONAL_PROJECT_FILES = [
        "财务审核表",
        "供电方案审核单",
        "通信方案确认单",
        "案例分析",
        "中标通知书",
    ]

    # 必备分项（至少应该存在）
    REQUIRED_SUBPROJECTS = [
        "开关站",
        "高压电缆",
        "低压电缆",
        "通信",
        "信息采集",
    ]

    # 分项子目录（每个分项应该有的子目录）
    SUBPROJECT_SUBDIRS = [
        "工程图纸",
        "建筑图纸",
        "工程估算书",
        "材料清册",
    ]

    def _find_file_by_synonyms(self, directory: Path, synonyms: List[str]) -> bool:
        """根据同义词列表查找文件（支持递归查找子目录）"""
        for synonym in synonyms:
            # 先在当前目录查找
            matches = list(directory.glob(f"*{synonym}*"))
            if matches:
                return True
            # 如果当前目录没找到，递归查找子目录
            matches = list(directory.glob(f"*/*{synonym}*"))
            if matches:
                return True
        return False

    def validate(self, project_path: Path) -> ValidationResult:
        """验证目录结构"""
        issues = []
        warnings = []
        details = {
            "required_dirs_present": True,
            "hierarchy_correct": True,
            "subprojects_found": [],
            "optional_files_found": []
        }

        # 检查必备目录（支持中文和英文两种路径）
        missing_required = []
        for dir_paths in self.REQUIRED_DIRS:
            found = False
            for dir_path in dir_paths:
                full_path = project_path / dir_path
                if full_path.exists():
                    found = True
                    break
            if not found:
                missing_required.append(" 或 ".join(dir_paths))

        if missing_required:
            details["required_dirs_present"] = False
            issues.extend([f"缺失必备目录: {d}" for d in missing_required])

        # 检查项目级必备文件（送审版和审定版）
        # 支持中文路径和英文路径
        for version_cn, version_en in [("送审版", "submitted"), ("审定版", "approved")]:
            # 尝试中文路径
            project_level_path = project_path / "设计文件" / version_cn / "项目级"
            # 如果中文路径不存在，尝试英文路径（auxiliary 是共享的项目级文件）
            if not project_level_path.exists():
                project_level_path = project_path / "design" / "auxiliary"

            if project_level_path.exists():
                for file_name, synonyms in self.REQUIRED_PROJECT_FILES.items():
                    # 查找匹配的文件（支持同义词）
                    if not self._find_file_by_synonyms(project_level_path, synonyms):
                        issues.append(f"缺失必备项目级文件 ({version_cn}): {file_name}")
            else:
                issues.append(f"项目级目录不存在: 设计文件/{version_cn}/项目级 或 design/auxiliary")

        # 检查可研报告目录
        for version_cn, version_en in [("送审版", "submitted"), ("审定版", "approved")]:
            # 尝试中文路径
            feasibility_path = project_path / "设计文件" / version_cn / "项目级" / "可研报告"
            # 如果中文路径不存在，尝试英文路径
            if not feasibility_path.exists():
                feasibility_path = project_path / "design" / version_en / "feasibility_report"

            if not feasibility_path.exists() or not any(feasibility_path.iterdir()):
                warnings.append(f"可研报告目录为空或不存在 ({version_cn})")

        # 检查必备分项
        for version_cn, version_en in [("送审版", "submitted"), ("审定版", "approved")]:
            # 尝试中文路径
            version_path = project_path / "设计文件" / version_cn
            # 如果中文路径不存在，尝试英文路径
            if not version_path.exists():
                version_path = project_path / "design" / version_en

            if version_path.exists():
                for subproject in self.REQUIRED_SUBPROJECTS:
                    subproject_path = version_path / subproject
                    if subproject_path.exists():
                        if version_cn == "送审版":
                            details["subprojects_found"].append(subproject)

                        # 检查分项子目录
                        for subdir in self.SUBPROJECT_SUBDIRS:
                            subdir_path = subproject_path / subdir
                            if not subdir_path.exists():
                                warnings.append(f"分项子目录缺失 ({version_cn}/{subproject}): {subdir}")
                    else:
                        if version_cn == "送审版":
                            issues.append(f"缺失必备分项 ({version_cn}): {subproject}")

        # 检查可选项目级文件
        for version in ["送审版", "审定版"]:
            project_level_path = project_path / "设计文件" / version / "项目级"
            if project_level_path.exists():
                for file_pattern in self.OPTIONAL_PROJECT_FILES:
                    matching_files = list(project_level_path.glob(f"*{file_pattern}.*"))
                    if matching_files and version == "送审版":
                        details["optional_files_found"].append(file_pattern)

        # 计算分数
        total_checks = (
            len(self.REQUIRED_DIRS) +
            len(self.REQUIRED_PROJECT_FILES) * 2 +  # 送审版 + 审定版
            len(self.REQUIRED_SUBPROJECTS) * 2  # 送审版 + 审定版
        )
        failed_checks = len(missing_required) + len([i for i in issues if "缺失" in i])
        score = max(0, int(100 * (1 - failed_checks / total_checks)))

        status = "pass" if score >= 95 else ("warning" if score >= 80 else "error")

        return ValidationResult(
            status=status,
            score=score,
            details=details,
            issues=issues,
            warnings=warnings
        )


class FileMappingValidator:
    """文件映射验证器"""

    def validate(self, project_path: Path, meta_json_path: Path) -> ValidationResult:
        """验证文件映射"""
        issues = []
        warnings = []
        details = {
            "total_mappings": 0,
            "source_exists": 0,
            "target_exists": 0,
            "size_match": 0,
            "success_rate": 0.0
        }

        # 读取 meta.json
        if not meta_json_path.exists():
            return ValidationResult(
                status="error",
                score=0,
                details=details,
                issues=["meta.json 文件不存在"],
                warnings=[]
            )

        try:
            with open(meta_json_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception as e:
            return ValidationResult(
                status="error",
                score=0,
                details=details,
                issues=[f"无法读取 meta.json: {e}"],
                warnings=[]
            )

        # 检查 path_mapping 字段
        if "path_mapping" not in meta:
            return ValidationResult(
                status="error",
                score=0,
                details=details,
                issues=["meta.json 缺少 path_mapping 字段"],
                warnings=[]
            )

        path_mapping = meta["path_mapping"]
        details["total_mappings"] = len(path_mapping)

        if details["total_mappings"] == 0:
            warnings.append("path_mapping 为空，没有文件映射记录")

        # 验证每条映射
        for mapping in path_mapping:
            source = mapping.get("source")
            target = mapping.get("target")

            if not source or not target:
                issues.append(f"映射记录缺少 source 或 target 字段: {mapping}")
                continue

            # 检查源文件（相对于项目根目录）
            source_path = Path(source)
            if source_path.exists():
                details["source_exists"] += 1
            else:
                issues.append(f"源文件不存在: {source}")

            # 检查目标文件（target 已经是完整的相对路径）
            target_path = Path(target)
            if target_path.exists():
                details["target_exists"] += 1

                # 检查文件大小
                if source_path.exists():
                    source_size = source_path.stat().st_size
                    target_size = target_path.stat().st_size
                    if source_size == target_size:
                        details["size_match"] += 1
                    else:
                        warnings.append(f"文件大小不一致: {target} (源: {source_size}, 目标: {target_size})")
            else:
                issues.append(f"目标文件不存在: {target}")

        # 计算成功率
        if details["total_mappings"] > 0:
            details["success_rate"] = details["target_exists"] / details["total_mappings"]

        # 计算分数
        score = int(details["success_rate"] * 100)
        status = "pass" if score >= 95 else ("warning" if score >= 80 else "error")

        return ValidationResult(
            status=status,
            score=score,
            details=details,
            issues=issues,
            warnings=warnings
        )


class CompletenessValidator:
    """文件完整性验证器"""

    # 必备项目级文件（支持同义词匹配）
    REQUIRED_PROJECT_FILES = {
        "设计委托书": ["设计委托书", "委托书", "智方委托书", "设计中标通知书"],
        "内审意见": ["内审意见", "内审意见及签到单"],
        "投资汇总表": ["投资汇总表", "投资费用汇总表"],
        "主要设备材料清册": ["主要设备材料清册", "设备材料清册"],
    }

    # 必备分项
    REQUIRED_SUBPROJECTS = [
        "开关站",
        "高压电缆",
        "低压电缆",
        "通信",
        "信息采集",
    ]

    # 分项子目录
    SUBPROJECT_SUBDIRS = [
        "工程图纸",
        "建筑图纸",
        "工程估算书",
        "材料清册",
    ]

    def _find_file_by_synonyms(self, directory: Path, synonyms: List[str]) -> bool:
        """根据同义词列表查找文件（支持递归查找子目录）"""
        for synonym in synonyms:
            # 先在当前目录查找
            matches = list(directory.glob(f"*{synonym}*"))
            if matches:
                return True
            # 如果当前目录没找到，递归查找子目录
            matches = list(directory.glob(f"*/*{synonym}*"))
            if matches:
                return True
        return False

    def validate(self, project_path: Path) -> ValidationResult:
        """验证文件完整性"""
        issues = []
        warnings = []
        details = {
            "project_files": {"required": len(self.REQUIRED_PROJECT_FILES), "present": 0, "missing": []},
            "feasibility_report": {"submitted": False, "approved": False},
            "subprojects": {"required": len(self.REQUIRED_SUBPROJECTS), "present": 0, "missing": []},
            "subproject_completeness": {}
        }

        # 检查项目级文件（送审版）
        # 支持中文路径和英文路径
        project_level_path = project_path / "设计文件" / "送审版" / "项目级"
        if not project_level_path.exists():
            project_level_path = project_path / "design" / "auxiliary"

        if project_level_path.exists():
            for file_name, synonyms in self.REQUIRED_PROJECT_FILES.items():
                if self._find_file_by_synonyms(project_level_path, synonyms):
                    details["project_files"]["present"] += 1
                else:
                    details["project_files"]["missing"].append(file_name)
        else:
            issues.append("项目级目录不存在: 设计文件/送审版/项目级 或 design/auxiliary")

        # 检查可研报告（送审版和审定版）
        for version_cn, version_en, version_key in [("送审版", "submitted", "submitted"), ("审定版", "approved", "approved")]:
            # 尝试中文路径
            feasibility_path = project_path / "设计文件" / version_cn / "项目级" / "可研报告"
            # 如果中文路径不存在，尝试英文路径
            if not feasibility_path.exists():
                feasibility_path = project_path / "design" / version_en / "feasibility_report"

            if feasibility_path.exists() and any(feasibility_path.iterdir()):
                details["feasibility_report"][version_key] = True
            else:
                warnings.append(f"可研报告目录为空或不存在: 设计文件/{version_cn}/项目级/可研报告 或 design/{version_en}/feasibility_report")

        # 检查必备分项（送审版）
        version_path = project_path / "设计文件" / "送审版"
        use_english_structure = False
        if not version_path.exists():
            version_path = project_path / "design" / "submitted"
            use_english_structure = True

        if version_path.exists():
            # 定义分项到英文目录的映射
            subproject_mapping = {
                "开关站": ["D-01_switchgear", "D-01"],
                "高压电缆": ["D-04_hv_cable", "D-04"],
                "低压电缆": ["D-05_lv_cable", "D-05"],
                "通信": ["D-06_telecom", "D-06"],
                "信息采集": ["D-07_metering", "D-07"],
            }

            for subproject in self.REQUIRED_SUBPROJECTS:
                found = False

                if use_english_structure:
                    # 英文结构：在 drawings/ 目录下查找对应的专业目录
                    drawings_path = version_path / "drawings"
                    if drawings_path.exists():
                        # 尝试匹配对应的英文目录名
                        for eng_name in subproject_mapping.get(subproject, []):
                            matching_dirs = list(drawings_path.glob(f"{eng_name}*"))
                            if matching_dirs:
                                found = True
                                details["subprojects"]["present"] += 1
                                break
                else:
                    # 中文结构：直接查找分项目录
                    subproject_path = version_path / subproject
                    if subproject_path.exists():
                        found = True
                        details["subprojects"]["present"] += 1

                        # 检查分项子目录完整性
                        subdir_status = {}
                        for subdir in self.SUBPROJECT_SUBDIRS:
                            subdir_path = subproject_path / subdir
                            if subdir_path.exists() and any(subdir_path.iterdir()):
                                subdir_status[subdir] = True
                            else:
                                subdir_status[subdir] = False

                        details["subproject_completeness"][subproject] = subdir_status

                        # 如果子目录不完整，发出警告
                        missing_subdirs = [k for k, v in subdir_status.items() if not v]
                        if missing_subdirs:
                            warnings.append(f"分项 {subproject} 缺少子目录或为空: {', '.join(missing_subdirs)}")

                if not found:
                    details["subprojects"]["missing"].append(subproject)
                    issues.append(f"缺失必备分项: {subproject}")
        else:
            issues.append("送审版目录不存在: 设计文件/送审版 或 design/submitted")

        # 计算分数
        total_required = (
            len(self.REQUIRED_PROJECT_FILES) +
            2 +  # 可研报告（送审版+审定版）
            len(self.REQUIRED_SUBPROJECTS)
        )
        present_count = (
            details["project_files"]["present"] +
            (1 if details["feasibility_report"]["submitted"] else 0) +
            (1 if details["feasibility_report"]["approved"] else 0) +
            details["subprojects"]["present"]
        )

        score = int(100 * present_count / total_required) if total_required > 0 else 0
        status = "pass" if score >= 95 else ("warning" if score >= 80 else "error")

        return ValidationResult(
            status=status,
            score=score,
            details=details,
            issues=issues,
            warnings=warnings
        )


class MetadataValidator:
    """元数据验证器"""

    REQUIRED_FIELDS = ["project_id", "project_name", "source_paths", "path_mapping"]

    def validate(self, project_path: Path, meta_json_path: Path) -> ValidationResult:
        """验证元数据"""
        issues = []
        warnings = []
        details = {
            "required_fields_present": True,
            "statistics_accurate": True,
            "deviation_rate": 0.0
        }

        # 读取 meta.json
        if not meta_json_path.exists():
            return ValidationResult(
                status="error",
                score=0,
                details=details,
                issues=["meta.json 文件不存在"],
                warnings=[]
            )

        try:
            with open(meta_json_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception as e:
            return ValidationResult(
                status="error",
                score=0,
                details=details,
                issues=[f"无法读取 meta.json: {e}"],
                warnings=[]
            )

        # 检查必备字段
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in meta]
        if missing_fields:
            details["required_fields_present"] = False
            issues.extend([f"缺少必备字段: {field}" for field in missing_fields])

        # 验证统计数据（如果存在）
        if "statistics" in meta:
            stats = meta["statistics"]

            # 实际扫描文件数量
            actual_count = sum(1 for _ in project_path.rglob("*") if _.is_file() and _.name != "meta.json")

            # 比对统计数据
            if "total_files" in stats:
                reported_count = stats["total_files"]
                if actual_count != reported_count:
                    deviation = abs(actual_count - reported_count) / max(actual_count, 1)
                    details["deviation_rate"] = deviation

                    if deviation > 0.05:  # 超过 5% 偏差
                        details["statistics_accurate"] = False
                        warnings.append(f"统计数据偏差: meta.json 记录 {reported_count} 个文件，实际扫描 {actual_count} 个文件")

        # 计算分数
        score = 100
        if not details["required_fields_present"]:
            score -= 50
        if not details["statistics_accurate"]:
            score -= 20

        score = max(0, score)
        status = "pass" if score == 100 else ("warning" if score >= 80 else "error")

        return ValidationResult(
            status=status,
            score=score,
            details=details,
            issues=issues,
            warnings=warnings
        )


class NamingValidator:
    """命名规范验证器"""

    # 中文命名规范（基于 file-reorganizer skill）
    VALID_SUBPROJECTS = [
        "开关站", "街坊站-1", "街坊站-2", "街坊站-3", "街坊站-4",
        "站内电缆", "高压电缆", "低压电缆", "通信", "信息采集"
    ]

    VALID_SUBDIRS = ["工程图纸", "建筑图纸", "工程估算书", "材料清册"]

    def validate(self, project_path: Path) -> ValidationResult:
        """验证命名规范"""
        issues = []
        warnings = []
        details = {
            "subproject_naming": {"total": 0, "valid": 0, "invalid": []},
            "subdir_naming": {"total": 0, "valid": 0, "invalid": []},
            "illegal_chars": False
        }

        # 检查分项命名
        for version in ["送审版", "审定版"]:
            version_path = project_path / "设计文件" / version
            if version_path.exists():
                for item in version_path.iterdir():
                    if item.is_dir() and item.name != "项目级":
                        details["subproject_naming"]["total"] += 1

                        # 检查是否为有效的分项名称
                        if item.name in self.VALID_SUBPROJECTS or item.name.startswith("街坊站-"):
                            details["subproject_naming"]["valid"] += 1
                        else:
                            details["subproject_naming"]["invalid"].append(item.name)
                            warnings.append(f"分项命名不规范 ({version}): {item.name}")

                        # 检查分项子目录命名
                        for subdir in item.iterdir():
                            if subdir.is_dir():
                                details["subdir_naming"]["total"] += 1
                                if subdir.name in self.VALID_SUBDIRS:
                                    details["subdir_naming"]["valid"] += 1
                                else:
                                    details["subdir_naming"]["invalid"].append(f"{item.name}/{subdir.name}")
                                    warnings.append(f"子目录命名不规范 ({version}/{item.name}): {subdir.name}")

        # 计算分数
        total_items = details["subproject_naming"]["total"] + details["subdir_naming"]["total"]
        valid_items = details["subproject_naming"]["valid"] + details["subdir_naming"]["valid"]

        score = int(100 * valid_items / total_items) if total_items > 0 else 100
        status = "pass" if score >= 95 else ("warning" if score >= 80 else "error")

        return ValidationResult(
            status=status,
            score=score,
            details=details,
            issues=issues,
            warnings=warnings
        )


class ValidationOrchestrator:
    """验证编排器"""

    def __init__(self):
        self.dir_validator = DirectoryStructureValidator()
        self.mapping_validator = FileMappingValidator()
        self.completeness_validator = CompletenessValidator()
        self.metadata_validator = MetadataValidator()
        self.naming_validator = NamingValidator()

    def run_all_validations(self, project_id: str, project_path: Path) -> ValidationReport:
        """运行所有验证器"""
        meta_json_path = project_path / "meta.json"

        # 读取项目名称
        project_name = project_id
        if meta_json_path.exists():
            try:
                with open(meta_json_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    project_name = meta.get("project_name", project_id)
            except:
                pass

        # 运行各个验证器
        results = {
            "directory_structure": self.dir_validator.validate(project_path),
            "file_mapping": self.mapping_validator.validate(project_path, meta_json_path),
            "completeness": self.completeness_validator.validate(project_path),
            "metadata": self.metadata_validator.validate(project_path, meta_json_path),
            "naming": self.naming_validator.validate(project_path)
        }

        # 计算总分
        overall_score = sum(r.score for r in results.values()) // len(results)

        return ValidationReport(
            project_id=project_id,
            project_name=project_name,
            validation_time=datetime.now().isoformat(),
            overall_score=overall_score,
            results=results
        )


def print_console_report(report: ValidationReport):
    """打印控制台报告"""
    print("=" * 80)
    print("项目验证报告")
    print("=" * 80)
    print(f"项目ID: {report.project_id}")
    print(f"项目名称: {report.project_name}")
    print(f"验证时间: {report.validation_time}")
    print()

    # 验证结果
    validator_names = {
        "directory_structure": "目录结构验证",
        "file_mapping": "文件映射验证",
        "completeness": "文件完整性验证",
        "metadata": "元数据验证",
        "naming": "命名规范验证"
    }

    for i, (key, name) in enumerate(validator_names.items(), 1):
        result = report.results[key]
        status_icon = "✓" if result.status == "pass" else ("○" if result.status == "warning" else "✗")
        print(f"[{i}/5] {name}...")
        print(f"  {status_icon} 状态: {result.status.upper()} (分数: {result.score}/100)")

        if result.issues:
            for issue in result.issues[:3]:  # 只显示前3个问题
                print(f"    - 问题: {issue}")
            if len(result.issues) > 3:
                print(f"    - ... 还有 {len(result.issues) - 3} 个问题")

        if result.warnings:
            for warning in result.warnings[:2]:  # 只显示前2个警告
                print(f"    - 警告: {warning}")
            if len(result.warnings) > 2:
                print(f"    - ... 还有 {len(result.warnings) - 2} 个警告")
        print()

    # 总体结果
    print("=" * 80)
    overall_status = "✅ 通过" if report.overall_score >= 95 else ("⚠️  警告" if report.overall_score >= 80 else "❌ 失败")
    print(f"验证结果: {overall_status} ({report.overall_score}/100)")
    print("=" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="验证 file-reorganizer 执行结果")
    parser.add_argument("--project", help="项目ID")
    parser.add_argument("--all", action="store_true", help="验证所有项目")
    parser.add_argument("--format", choices=["console", "json"], default="console", help="输出格式")
    parser.add_argument("--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 确定项目列表
    projects_dir = Path("data/projects")
    if not projects_dir.exists():
        print(f"错误: 项目目录不存在: {projects_dir}")
        sys.exit(1)

    if args.all:
        project_ids = [d.name for d in projects_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    elif args.project:
        project_ids = [args.project]
    else:
        parser.print_help()
        sys.exit(1)

    # 运行验证
    orchestrator = ValidationOrchestrator()
    reports = []

    for project_id in project_ids:
        project_path = projects_dir / project_id
        if not project_path.exists():
            print(f"警告: 项目目录不存在: {project_path}")
            continue

        report = orchestrator.run_all_validations(project_id, project_path)
        reports.append(report)

        # 输出报告
        if args.format == "console":
            print_console_report(report)
            print()
        elif args.format == "json":
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))

        # 保存 JSON 报告
        report_path = project_path / "validation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

        if args.format == "console":
            print(f"详细报告已保存至: {report_path}")
            print()

    # 汇总报告（如果验证多个项目）
    if len(reports) > 1 and args.format == "console":
        print("=" * 80)
        print("汇总报告")
        print("=" * 80)
        print(f"验证项目数: {len(reports)}")
        avg_score = sum(r.overall_score for r in reports) / len(reports)
        print(f"平均分数: {avg_score:.1f}/100")

        passed = sum(1 for r in reports if r.overall_score >= 95)
        warned = sum(1 for r in reports if 80 <= r.overall_score < 95)
        failed = sum(1 for r in reports if r.overall_score < 80)

        print(f"通过: {passed}, 警告: {warned}, 失败: {failed}")
        print("=" * 80)


if __name__ == "__main__":
    main()

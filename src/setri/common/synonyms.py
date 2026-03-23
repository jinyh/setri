"""同义词映射表

从 file-reorganizer SKILL.md 提取的单一真相源。
所有目录名匹配逻辑都基于此表。
"""

# 过程管理文件映射（P-01 到 P-10）
# 标准目录名 → 匹配关键词列表
PROCESS_MANAGEMENT = {
    "关键节点时间": ["关键节点时间", "关键节点"],
    "项目概况信息": ["项目概况信息", "项目概况"],
    "设计人员信息": ["设计人员信息", "设计人员"],
    "预审专家意见": ["预审专家意见", "预审"],
    "正式评审专家意见": ["正式评审专家意见", "正式评审"],
    "收口评审专家意见": ["收口评审专家意见", "收口"],
    "评审意见": ["评审意见"],  # 不含"预审""正式""收口"修饰词
    "发文意见": ["发文意见", "发文意见（WORD版）"],
    "项目评审记录": ["项目评审记录", "评审记录"],
    "评分文件": ["评分文件", "评分"],
}

# 项目级文件映射
PROJECT_LEVEL = {
    "设计委托书": ["设计中标通知书或委托书", "设计委托书", "设计中标通知书"],
    "可研报告": ["可行性研究报告", "初设报告", "设计报告", "说明书"],
    "中标通知书": ["中标通知书"],
    "供电方案审核单": ["供电方案审核单", "供电方案"],
    "财务审核表": ["财务审核表", "财务审核"],
    "内审意见": ["内审意见", "内审意见及签到单"],
    "投资汇总表": ["投资汇总表", "投资汇总"],
    "主要设备材料清册": ["主要设备材料清册", "主要设备材料清册（pdf、word版）"],
    "其他依据": ["其他依据", "其它依据", "其他"],
}

# 专业分项映射
SPECIALTIES = {
    "开关站": ["KT站", "开关站电气一次", "开关站"],
    "街坊站": ["PT-x站", "PML", "街坊站电气一次", "零x街坊站", "PT站"],
    "站内电缆": ["站内电缆", "-10kV站内电缆"],
    "高压电缆": ["内线电缆-10kV", "10kV电缆", "（10kV电缆）"],
    "低压电缆": ["内线电缆-0.4kV", "0.4kV电缆", "（0.4kV电缆）"],
    "通信": ["内线通信", "通信", "（通信）"],
    "信息采集": ["信息采集", "用电信息采集", "（信息采集）"],
}

# 分项子目录映射
SUB_DIRECTORIES = {
    "工程图纸": ["其他图纸", "设计图纸", "图纸资料", "电缆通道断面图"],
    "建筑图纸": ["土建总平面及竖向布置图", "土建总平面图", "竖向布置图"],
    "工程估算书": ["工程估算书", "工程概算书", "工程估算书(PDF版)", "工程概算书（PDF版）"],
    "材料清册": ["主要建设材料表", "主要材料清册", "设备材料清册", "材料表", "拆除设备清单", "拆除设备材料清单"],
}

# 说明书归并关键词（子目录名含这些关键词时，内容归并到"可研报告"）
REPORT_MERGE_KEYWORDS = ["说明书", "可研报告", "初设报告", "设计报告"]

# 项目注册表
PROJECTS = {
    "C109HZ22A062": {
        "short_name": "崇明盛世新苑",
        "full_name": "上海崇明城桥置业高岛路170弄盛世新苑10kV普通住宅红线内接入工程",
    },
    "C1092322A133": {
        "short_name": "奉贤悦景名筑",
        "full_name": "上海奉贤翀溢置业庄良路60弄悦景名筑10kV普通住宅红线内接入工程",
    },
    "C1092323N6S8": {
        "short_name": "奉贤咉懿佳园",
        "full_name": "上海奉贤陕名置业正旭路80弄咉懿佳园10kV普通住宅红线内接入工程",
    },
}


def match_synonym(name: str, mapping: dict[str, list[str]]) -> str | None:
    """在同义词映射表中查找匹配项。

    匹配逻辑：
    1. 精确匹配：name 与某个同义词完全相同
    2. 包含匹配：name 包含某个同义词，或某个同义词包含 name

    对"评审意见"做特殊处理：如果 name 包含"预审"、"正式评审"或"收口"，
    则不匹配通用的"评审意见"。

    Returns:
        匹配到的标准名称，未匹配返回 None
    """
    name_normalized = name.strip()

    # 第一轮：精确匹配
    for standard_name, synonyms in mapping.items():
        for syn in synonyms:
            if name_normalized == syn:
                return standard_name

    # 第二轮：包含匹配（按同义词长度降序，优先匹配更具体的）
    candidates = []
    for standard_name, synonyms in mapping.items():
        for syn in sorted(synonyms, key=len, reverse=True):
            if syn in name_normalized or name_normalized in syn:
                candidates.append((standard_name, syn))
                break

    if not candidates:
        return None

    # 特殊处理："评审意见"不应匹配包含"预审""正式评审""收口"的目录名
    if len(candidates) == 1 and candidates[0][0] == "评审意见":
        if any(prefix in name_normalized for prefix in ["预审", "正式评审", "正式", "收口"]):
            return None

    # 如果有多个候选，返回同义词最长的那个（更精确的匹配）
    candidates.sort(key=lambda x: len(x[1]), reverse=True)
    return candidates[0][0]


def extract_specialty_keyword(dirname: str) -> str | None:
    """从长命名目录中提取专业关键词。

    识别模式：
    - 括号内容：`...工程（KT站）` → `KT站`
    - 空格后内容：`...工程 内线电缆-0.4kV` → `内线电缆-0.4kV`
    """
    import re

    # 尝试匹配各种括号
    patterns = [
        r"[（(]([^）)]+)[）)]",  # 中文/英文括号
    ]
    for pat in patterns:
        match = re.search(pat, dirname)
        if match:
            return match.group(1).strip()

    # 尝试空格分隔
    parts = dirname.rsplit(" ", 1)
    if len(parts) == 2 and len(parts[1]) >= 2:
        return parts[1].strip()

    return None

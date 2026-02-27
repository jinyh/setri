# Reg-Extractor 技术规范专题条款提取 Skill

## 触发条件

当用户提到以下关键词时激活本 Skill：
- 条款提取、规范提取、extract regulations
- 专题提取、topic extraction
- reg-extractor

## 概述

本 Skill 从多份技术规范 PDF 中，按指定专题（如"开关站"、"站内电缆"、"10kV电缆"）提取相关条款，自动分类并检测跨规范冲突，输出结构化 JSON。

核心原则：**LLM 负责语义理解和裁决，Python 脚本负责确定性扫描和校验**。
- Python 脚本：关键词扫描、数值/强度词预筛、输出组装校验
- Claude：条款提取、分类归纳、冲突语义裁决

## 输出结构

```
data/regulations/{slug}/
├── scan_result.json        # Phase 1 输出：PDF 关键词命中统计
├── clauses_draft.json      # Phase 2 输出：提取的条款列表
├── categories.json         # Phase 3 输出：分类体系
├── conflict_candidates.json # Phase 4 输出：冲突候选
└── regulations.json        # Phase 5 输出：最终合并结果
```

## Phase 0: 参数确认

Claude 与用户确认以下参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| subject | 专题名称 | 配电网开关站 |
| slug | 输出目录名（英文） | kaiguanzhan |
| keywords | 关键词列表（逗号分隔） | 开关站,K型站,KT站 |
| pdf_dir | PDF 源目录 | 技术规范文件 |

Claude 应主动扩展同义词关键词。例如：
- "开关站" → ["开关站", "K型站", "KT站", "KF站"]
- "站内电缆" → ["站内电缆", "电缆敷设", "电缆选型"]
- "用电信息采集" → ["用电信息采集", "采集终端", "集中器", "智能电表"]

确认后创建输出目录：
```bash
mkdir -p data/regulations/{slug}
```

## Phase 1: 源文件扫描（Python + Claude）

### 1a. 关键词扫描（Python）
```bash
python3 .claude/skills/reg-extractor/scripts/scan_sources.py \
  --keywords "{keywords}" \
  --pdf-dir "{pdf_dir}" \
  --output "data/regulations/{slug}/scan_result.json"
```

输出每份 PDF 的命中页码、命中次数、上下文片段（关键词前后50字）。

### 1b. 人工审查（Claude）

读取 scan_result.json，执行：
1. 排除误命中（如仅在目录/参考文献中出现的 PDF）
2. 排除纯图像 PDF（`is_image_only: true`）
3. 确定最终 sources 列表，为每份 PDF 分配 `source_id`（格式 `SRC-{nn}`）
4. 向用户展示 sources 列表，确认后进入 Phase 2

## Phase 2: 条款提取（Claude）

逐份读取 sources 列表中的 PDF（复用 co-reviewer 的 parse_pdf_text.py）：
```bash
python3 .claude/skills/co-reviewer/scripts/parse_pdf_text.py \
  --input "{pdf_path}" \
  --output "data/regulations/{slug}/pdf_{source_id}.json"
```

对每份 PDF 的文本，Claude 执行：
1. 逐页扫描，定位与专题相关的条款段落
2. 对每个条款提取以下字段：

```json
{
  "clause_id": "CL-{nnn}",
  "source_id": "SRC-{nn}",
  "source_clause_ref": "7.2.1.1",
  "category_id": "",
  "domain_tags": {},
  "subject": "开关站接线方式",
  "text": "开关站应采用单母线分段的接线方式。",
  "strength": "应",
  "page": 8
}
```

字段说明：
- `source_clause_ref`：原文中的条款编号（如 7.2.1.1、五(一)）
- `domain_tags`：领域标签字典，不同专题可有不同 key
  - 开关站专题：`{"voltage_level": "10kV"}`
  - 电缆专题：`{"cable_spec": "10kV XLPE", "voltage_level": "10kV"}`
  - 采集专题：`{"device_type": "集中器"}`
- `strength`：强度词（应/宜/不宜/可/不得/一般）
- `page`：条款所在页码

提取完成后将全部条款写入 `data/regulations/{slug}/clauses_draft.json`。

## Phase 3: 分类体系（Claude）

审视 clauses_draft.json 中的全部条款，动态归纳分类体系：

1. 参考"开关站"专题的 14 个分类作为模板（定义类、接线方式、进出线回路数...）
2. 根据当前专题条款内容归纳 8~20 个分类
3. 为每个分类分配 `category_id`（格式 `CAT-{nn}`）
4. 为每条条款分配 `category_id`

输出 `data/regulations/{slug}/categories.json`：
```json
[
  {"id": "CAT-01", "name": "定义类"},
  {"id": "CAT-02", "name": "接线方式"}
]
```

同时更新 clauses_draft.json 中每条条款的 `category_id`。

## Phase 4: 冲突检测（Python + Claude）

### 4a. 数值/强度词预筛（Python）
```bash
python3 .claude/skills/reg-extractor/scripts/detect_conflicts.py \
  --input "data/regulations/{slug}/clauses_draft.json" \
  --output "data/regulations/{slug}/conflict_candidates.json"
```

脚本在同 category 内跨 source 的条款两两比较，提取数值特征和强度词差异。

### 4b. 语义裁决（Claude）

读取 conflict_candidates.json，对每个候选冲突：
1. 回读原文上下文，判断是否为真实冲突（排除表述差异但含义一致的情况）
2. 对真实冲突确定 resolution，优先级规则：
   - 地方标准 > 企业标准 > 行业标准（同等级别时）
   - 新版 > 旧版
   - 强制性条款 > 推荐性条款
3. 输出冲突记录：

```json
{
  "conflict_id": "CONF-{nnn}",
  "category_id": "CAT-{nn}",
  "subject": "冲突主题描述",
  "involved_clauses": ["CL-001", "CL-015"],
  "description": "差异描述",
  "resolution": {
    "effective_clause_id": "CL-015",
    "effective_source": "DB31/T 1557-2025",
    "rationale": "裁决理由"
  }
}
```

## Phase 5: 组装输出（Python + Claude）

### 5a. 合并与校验（Python）
```bash
python3 .claude/skills/reg-extractor/scripts/assemble_output.py \
  --subject "{subject}" \
  --slug "{slug}" \
  --keywords "{keywords}" \
  --input-dir "data/regulations/{slug}" \
  --output "data/regulations/{slug}/regulations.json"
```

脚本合并 metadata + sources + categories + clauses + conflicts → regulations.json，并校验所有 ID 引用完整性。

### 5b. 最终审查（Claude）

读取 regulations.json，输出摘要统计：
- 总条款数、来源数、分类数、冲突数
- 各来源条款分布
- 各分类条款分布
- domain_tags 覆盖情况

向用户确认结果无误后，标记提取完成。

## 与 co-reviewer 集成

reg-extractor 输出的字段可直接映射到 co-reviewer 的 RegulationRef：
- `source_id` → `standard_id`（通过 sources 表查找）
- `source_clause_ref` → `clause`
- `text` → `text`
- categories 中的 `name` → `category`

## 已知限制

1. **纯图像 PDF**：无法提取文本，scan_sources.py 会标记 `is_image_only`，需人工处理。
2. **关键词扫描精度**：关键词可能出现在无关上下文中（如目录、参考文献），需 Claude 在 Phase 1b 排除误命中。
3. **分类体系主观性**：不同专题的分类维度差异大，Claude 归纳的分类可能需要用户调整。
4. **冲突检测覆盖率**：Python 预筛基于数值和强度词，语义层面的隐含冲突仍依赖 Claude 识别。

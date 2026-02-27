# Co-Reviewer 三元关联标注 Skill

## 触发条件

当用户提到以下关键词时激活本 Skill：
- 标注、三元关联、annotate、annotation
- 校验标注、validate annotation
- co-reviewer、评审副驾驶
- 专家意见分析、意见关联

## 概述

本 Skill 辅助完成配网业扩项目评审中"专家意见 ↔ 设计文件 ↔ 引用规范"三元关联的自动标注生成和质量校验。

核心原则：**LLM 负责感知和推理，工具负责确定性计算**。
- Python 脚本：文件解析、数据校验（确定性工作）
- Claude：语义推理、三元关联匹配（不确定性工作）

## 前置条件

运行环境检查：
```bash
python3 .claude/skills/co-reviewer/scripts/setup.py
```

## 工作流 A：自动标注生成

用户说"对项目 X 生成三元关联标注"或"标注项目 X"时执行。

### Phase 0: 环境检查
```bash
python3 .claude/skills/co-reviewer/scripts/setup.py
```
如果失败，提示用户安装缺失依赖后重试。

### Phase 1: 项目发现
```bash
python3 .claude/skills/co-reviewer/scripts/discover_project.py --all
```
如果用户指定了项目 ID，加 `--project-id {ID}`。
将输出保存供后续步骤使用。

### Phase 2: 文件解析（Python 脚本）

按顺序执行三个解析任务：

**2a. 解析专家意见：**
```bash
python3 .claude/skills/co-reviewer/scripts/parse_opinions.py --input "{项目目录}" --output "data/annotations/{project_id}/opinions_raw.json"
```

**2b. 提取设计文件文本：**
```bash
python3 .claude/skills/co-reviewer/scripts/parse_pdf_text.py --input "{项目目录}/成果资料/审定版" --output "data/annotations/{project_id}/doc_texts.json" --summary
```
注意：`--summary` 先看概况，如果文件过多（>50个PDF），与用户确认是否全量提取。

**2c. 解析规范库：**
```bash
python3 .claude/skills/co-reviewer/scripts/parse_regulations.py --output-dir "data/regulations"
```
规范库只需构建一次，多个项目共享。如果 `data/regulations/index.json` 已存在则跳过。

### Phase 3: 三元关联推理（Claude 语义推理）

这是本 Skill 的核心步骤，由 Claude 完成语义推理。

**输入：** 读取 Phase 2 生成的三个 JSON 文件。

**对每条专家意见，执行两个子任务：**

**子任务 A — 意见→设计文件定位：**
1. 读取意见文本，理解其关注点（材料选型/工程量/技术标准/造价/形式审查）
2. 在 doc_texts.json 中搜索最相关的页面/章节/文本片段
3. 输出：file, page, section, snippet, doc_type
4. 给出 confidence_doc（0-1）

**子任务 B — 意见→规范匹配：**
1. 读取意见文本，判断涉及哪类规范要求
2. 在 regulations/clauses/*.json 中找最相关的条款
3. 输出：standard_id, standard_name, clause, text, category
4. 给出 confidence_reg（0-1）

**推理策略：**
- 对"原则同意"类简单意见：confidence 设为 0.3，document/regulation 留空，标记为 low
- 对有具体内容的意见：逐条分析，先定位文件再匹配规范
- confidence = min(confidence_doc, confidence_reg)

**输出格式：** 按 schema.py 中的 Annotation 结构，生成 annotations_draft.json：
```json
{
  "project_id": "{project_id}",
  "project_name": "{project_name}",
  "total": N,
  "annotations": [...]
}
```
opinion_id 格式：`OP-{project_id}-{seq:02d}`

### Phase 4: 输出与摘要

1. 将结果写入 `data/annotations/{project_id}/annotations_draft.json`
2. 输出摘要统计：
   - 总意见数、各阶段分布
   - 置信度分布：high/medium/low 各多少条
   - 图像类 PDF（无法文本定位）的数量

## 工作流 B：标注质量校验

用户说"校验标注"或"validate annotations"时执行。

### Phase 1: 加载标注数据
确认要校验的文件路径（draft 或 reviewed）：
```
data/annotations/{project_id}/annotations_draft.json
data/annotations/{project_id}/annotations_reviewed.json
```

### Phase 2: 自动校验（Python 脚本）
```bash
python3 .claude/skills/co-reviewer/scripts/validate_annotations.py --input "{标注文件}" --output "data/annotations/{project_id}/validation_report.json" --context-dir "data"
```

13 条校验规则：
| 编号 | 类别 | 规则 |
|------|------|------|
| V01 | 完整性 | 顶层必填字段非空 |
| V02 | 完整性 | 意见文本非空 |
| V03 | 完整性 | 文件引用有 file 字段 |
| V04 | 完整性 | 规范引用有 standard_id 或 standard_name |
| V05 | 一致性 | 引用文件名在项目清单中 |
| V06 | 一致性 | 页码在文件页数范围内 |
| V07 | 一致性 | 标准编号在规范库中 |
| V08 | 一致性 | opinion_id 格式规范 |
| V09 | 语义 | snippet 与 PDF 页面文本模糊匹配 |
| V10 | 语义 | opinion.type 在预定义范围内 |
| V11 | 语义 | severity 值有效 |
| V12 | 置信度 | 置信度在 [0,1] 范围 |
| V13 | 置信度 | 低置信度记录标记 |

### Phase 3: Claude 语义校验

对 validation_report.json 中 medium/low 置信度的记录：
1. 重新审视意见文本与关联的文件/规范
2. 判断关联是否合理，给出修正建议
3. 对明显错误的关联提供替代方案

### Phase 4: 输出
1. 更新 validation_report.json
2. 输出分级审核清单：
   - 需人工审核的记录列表
   - 通过率统计
   - 建议修正项

## 数据 Schema

核心字段定义见 `scripts/schema.py`，JSON 格式：
```json
{
  "project_id": "C1092323N6S8",
  "opinion_id": "OP-C1092323N6S8-01",
  "opinion": { "text": "", "type": "", "severity": "error|warning|info", "review_stage": "" },
  "document": { "file": "", "page": 0, "section": "", "snippet": "", "doc_type": "" },
  "regulation": { "standard_id": "", "standard_name": "", "clause": "", "text": "", "category": "" },
  "metadata": { "confidence": 0.0, "confidence_doc": 0.0, "confidence_reg": 0.0, "source": "ai_draft" }
}
```

## 已知限制

1. **无 VLM 能力**：图纸类纯图像 PDF 无法提取文本，文件定位对这类文档效果有限。parse_pdf_text.py 会标记 `is_image_only`。
2. **测试数据局限**：当前 3 个测试项目的专家意见均为"原则同意"，缺少有具体问题的意见样本。对这类意见三元关联价值有限。
3. **规范 PDF 切分精度**：条款切分基于正则匹配，对格式不规范的文档可能遗漏或错切。
4. **xlrd 仅支持 .xls**：新版 .xlsx 格式的专家意见需改用 openpyxl 读取。

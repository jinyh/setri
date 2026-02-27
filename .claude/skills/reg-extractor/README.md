# Reg-Extractor

技术规范专题条款提取工具 — 从多份技术规范 PDF 中按专题提取条款、自动分类、检测跨规范冲突。

## 工作原理

LLM 负责语义理解和裁决，Python 脚本负责确定性扫描和校验。

工作流分 6 个阶段：

| Phase | 执行者 | 职责 |
|-------|--------|------|
| 0 | Claude | 确认专题参数，扩展同义词关键词 |
| 1 | Python + Claude | 关键词扫描 PDF，审查排除误命中 |
| 2 | Claude | 逐份读取 PDF，提取相关条款 |
| 3 | Claude | 审视全部条款，动态归纳分类体系 |
| 4 | Python + Claude | 数值/强度词预筛冲突，语义裁决 |
| 5 | Python + Claude | 组装 regulations.json，校验引用完整性 |

## 脚本

```
scripts/
├── scan_sources.py       # Phase 1: PDF 关键词扫描
├── detect_conflicts.py   # Phase 4: 冲突候选预筛
└── assemble_output.py    # Phase 5: 输出组装与校验
```

### scan_sources.py

```bash
python3 scripts/scan_sources.py \
  --keywords "开关站,K型站,KT站" \
  --pdf-dir "技术规范文件" \
  --output "data/scan_result.json"
```

### detect_conflicts.py

```bash
python3 scripts/detect_conflicts.py \
  --input "data/clauses_draft.json" \
  --output "data/conflict_candidates.json"
```

### assemble_output.py

```bash
python3 scripts/assemble_output.py \
  --subject "配电网开关站" \
  --slug "kaiguanzhan" \
  --keywords "开关站,K型站,KT站" \
  --input-dir "data/" \
  --output "data/regulations.json"
```

## 依赖

- Python 3.10+
- pdfplumber

## 作为 Claude Code Skill 使用

将本仓库内容放入 `.claude/skills/reg-extractor/` 目录，详见 [SKILL.md](SKILL.md)。

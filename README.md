# Setri - 配电网业扩项目评审辅助系统

基于 LLM 的配电网业扩工程评审辅助工具，实现技术规范条款提取、跨规范冲突检测，以及专家意见与设计文件、技术规范的自动三元关联标注。

## 核心能力

- **Reg-Extractor**：从多份技术规范 PDF 中按专题提取条款、自动分类、检测跨规范冲突

## 项目结构

```
.claude/skills/
└── reg-extractor/        # 技术规范条款提取 Skill
    ├── README.md
    ├── SKILL.md          # 6 Phase 工作流定义
    └── scripts/
        ├── scan_sources.py       # PDF 关键词扫描
        ├── detect_conflicts.py   # 冲突候选预筛
        └── assemble_output.py    # 输出组装与校验
```

## 设计原则

- LLM 负责语义理解和推理，Python 脚本负责确定性计算和校验
- 半自动工作流：工具预筛 + LLM 裁决 + 人工确认

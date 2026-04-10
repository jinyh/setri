# Setri

配电网项目智能审查/核查工作台的文档与早期管道原型仓库。

当前仓库的主线已经切换到“统一交付演示系统”文档基线，用于承接业扩项目智能评审、技经资料预审与评审、开关站专家知识库、工程智慧进度管控和竣工资料智能核查等能力。仓库中同时保留了早期 Python 管道原型，主要覆盖 P1 规范库构建和部分 P2 文件整理入口。

## 当前状态

- 主产品定义以 [docs/prd.md](docs/prd.md) 为准。
- 需求、重构和里程碑文档已统一收敛到 `docs/`。
- P3-P5 的方法层约束已下沉到 `docs/architecture/`。
- `src/` 里的 Python 代码仍是旧阶段原型，不代表统一交付系统的最终工程形态。

## 关键文档

- [主 PRD](docs/prd.md)
- [统一交付演示系统需求文档](docs/统一交付演示系统需求文档.md)
- [统一交付演示系统重构计划](docs/统一交付演示系统重构计划.md)
- [统一交付演示系统 Milestone 计划](docs/统一交付演示系统-Milestone计划.md)
- [合同承接矩阵](docs/合同承接矩阵.md)
- [多模态审核技术路线说明](docs/architecture/多模态审核技术路线说明.md)
- [专家知识库与规则演化设计](docs/architecture/专家知识库与规则演化设计.md)
- [评测与执行底座工程设计](docs/architecture/评测与执行底座工程设计.md)
- [归档版旧 PRD v0.8](docs/archive/prd-v0.8-20260410-pre-rewrite.md)

## 仓库结构

```text
docs/
  architecture/             P3-P5 方法层设计文档
  archive/                  旧版 PRD、分析和归档材料
  *.md                      主 PRD、需求、重构计划、矩阵等

src/setri/
  cli.py                    早期 CLI 入口
  p1_regulations/           P1 规范库构建原型
  p2_reorganize/            P2 文件整理原型入口
  common/                   共享 schema、PDF、同义词等

data/                       样例数据与产物
技术规范文件/                规范源文件
合同/                        合同与项目材料
```

## Python 原型

仓库当前提供一个早期的 Python CLI 原型：

```bash
pip install -e .
setri --help
```

已暴露的命令主要集中在 P1：

```bash
setri p1 scan --keywords "开关站,KT站"
setri p1 conflicts
setri p1 assemble
```

`setri p2 run` 目前仍是占位入口。

## 设计原则

- 统一交付系统优先以文档定义系统边界、对象约束和演进路线。
- 模型负责感知、抽取、编排和表达，确定性工具负责规则执行与最终判定。
- 自动化能力必须保留证据链、置信度和执行 trace。
- 专家知识库用于校准、解释增强和反馈闭环，不替代规则库对设计文件的主评审链路。

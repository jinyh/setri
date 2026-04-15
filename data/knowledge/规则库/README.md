# 规则库

规则库是统一交付演示系统 P4 交叉提炼的核心产出，采用"Markdown 定义 + JSON 编译执行"的三层架构。

## 架构概览

### 三层架构

```
第1层：规则定义（Markdown）
    ↓
第2层：规则编译（Markdown → JSON）
    ↓
第3层：规则执行（LLM Agent 读取 JSON）
```

- **第1层：规则定义**：人类可读可编辑的 Markdown 源文件
- **第2层：规则编译**：将 Markdown 转换为结构化 JSON 执行格式
- **第3层：规则执行**：LLM Agent 读取 JSON 并执行规则检查

### 为什么需要三层架构？

- **Markdown**：人类友好，易于编写和审阅，LLM 容易生成
- **JSON**：机器友好，精确执行，支持结构化检查
- **编译过程**：连接两者，类似"源代码 → 字节码"

## 目录结构

```
规则库/
├── source/              # 第1层：Markdown 规则源文件（人类编辑）
│   ├── 开关站/
│   │   ├── 01-设备选型/
│   │   │   └── R-KGZ-EQ-001.md
│   │   ├── 02-安全距离/
│   │   ├── 03-造价核查/
│   │   │   └── R-KGZ-CS-002.md
│   │   └── README.md
│   ├── 技经资料/
│   │   ├── 01-字段抽取/
│   │   ├── 02-一致性校验/
│   │   └── README.md
│   └── index.json       # 源文件索引
│
├── compiled/            # 第2层：JSON 编译规则（机器执行）
│   ├── 开关站/
│   ├── 技经资料/
│   └── index.json       # 编译文件索引
│
├── versions/            # 规则版本历史
│   ├── v1.0.0/
│   │   ├── compiled/
│   │   ├── changelog.md
│   │   └── metadata.json
│   └── v1.1.0/
│
├── templates/           # 规则模板
│   ├── simple-rule-template.md
│   ├── complex-rule-template.md
│   └── README.md
│
└── README.md           # 本文件
```

## 规则类型

### 简单规则（Simple Rules）

**特征**：
- `complexity: simple`
- `execution_mode: structured`
- 输入字段明确、判断逻辑可用公式表达
- 不需要跨文档推理或语义理解

**示例**：
- 数值范围校验（容量、距离、面积）
- 简单计算校验（功率、电流、负荷）
- 枚举值匹配（设备型号、材料规格）

**执行方式**：
编译为结构化 JSON，由规则引擎快速执行（毫秒级）

**示例规则**：`source/开关站/01-设备选型/R-KGZ-EQ-001.md`

### 复杂规则（Complex Rules）

**特征**：
- `complexity: complex`
- `execution_mode: llm_reasoning`
- 需要多模态解析、跨文档推理、语义理解
- 输入字段不固定或需要动态提取

**示例**：
- 跨文档一致性校验
- 设计方案合理性评估
- 图纸与清册对比

**执行方式**：
保留 Markdown 引用，由 LLM Agent 推理执行（秒级）

**示例规则**：`source/开关站/03-造价核查/R-KGZ-CS-002.md`

## 规则编写指南

### 1. 选择模板

根据规则特点选择合适的模板：
- 简单规则：使用 `templates/simple-rule-template.md`
- 复杂规则：使用 `templates/complex-rule-template.md`

详细选择标准参见 `templates/README.md`

### 2. 规则 ID 命名规范

格式：`R-{专题代码}-{类别代码}-{序号}`

**专题代码**：
- `KGZ`：开关站
- `JJ`：技经资料
- `JG`：竣工资料

**类别代码**：
- `EQ`：设备选型
- `SF`：安全距离
- `CS`：造价核查
- `FE`：字段抽取
- `CC`：一致性校验

**示例**：
- `R-KGZ-EQ-001`：开关站 > 设备选型 > 第1条规则
- `R-JJ-CC-005`：技经资料 > 一致性校验 > 第5条规则

### 3. 编写流程

1. 复制对应的模板文件
2. 填写 frontmatter 元数据
3. 编写规则内容（描述、依据、条件、模板）
4. 添加测试用例
5. 更新分类目录的 README
6. 更新 `source/index.json`

### 4. 版本管理

规则修订时需要：
- 更新 `version` 字段（遵循语义化版本）
- 更新 `updated_at` 字段
- 在"变更历史"章节添加变更记录
- 重大变更时归档旧版本到 `versions/`

## 规则编译流程

### 首期策略

首期为"产品骨架"，编译流程为**手工执行**：
1. 编写 Markdown 规则源文件
2. 手工创建对应的 JSON 编译文件
3. 更新 `compiled/index.json`

### 后续优化

后续可开发自动化编译工具：
```bash
# 编译所有规则
python -m setri.p4_rules.compiler compile-all

# 编译单个规则
python -m setri.p4_rules.compiler compile source/开关站/01-设备选型/R-KGZ-EQ-001.md

# 验证规则
python -m setri.p4_rules.compiler validate source/开关站/01-设备选型/R-KGZ-EQ-001.md
```

### 编译逻辑

**简单规则**：
- Markdown 源文件 → 结构化 JSON
- 提取 frontmatter 为元数据
- 解析检查条件为 `check_logic` 对象
- 解析结果模板为 `result_templates` 对象

**复杂规则**：
- Markdown 源文件 → JSON 引用
- 提取 frontmatter 为元数据
- 保留 `rule_file` 字段指向源文件

## 规则执行方式

### 简单规则执行

```python
# 伪代码
for rule in compiled_rules:
    if rule.execution_mode == "structured":
        # 结构化检查（快速、精确）
        file_data = parse_file(rule.target_file)
        if not check_condition(file_data, rule.check_logic):
            opinions.append(fill_template(rule.result_template, file_data))
```

### 复杂规则执行

```python
# 伪代码
for rule in compiled_rules:
    if rule.execution_mode == "llm_reasoning":
        # LLM 推理检查（慢、灵活）
        rule_content = read_markdown(rule.rule_file)
        file_content = read_file(rule.target_file)
        opinion = llm.check(rule_content, file_content)
        if opinion:
            opinions.append(opinion)
```

## 规则演化闭环

规则库支持持续演化和优化：

```
1. 初版规则（基于规范条款和专家知识）
    ↓
2. 规则编译（Markdown → JSON）
    ↓
3. 真实文件运行（记录命中结果与 trace）
    ↓
4. 专家反馈（采纳、忽略、修改、补充）
    ↓
5. 分类反馈（误报、漏报、表达不当、范围不准）
    ↓
6. 规则修订（更新条件、模板、范围、例外）
    ↓
7. 回归验证（新版本测试）
    ↓
8. 版本发布（替换旧版本）
```

## 首期交付策略

### 首期完成

- ✅ 规则对象位：完整定义 Rule、RuleResult、ExpertFeedback 数据模型
- ✅ 目录结构：建立 source/、compiled/、versions/、templates/ 目录
- ✅ 模板文件：提供简单规则和复杂规则的 Markdown 模板
- ✅ 示例规则：手工编写 2 条示例规则（1 简单 + 1 复杂）
- ✅ 编译工具框架：提供编译器骨架（可以不实现真编译逻辑）

### 首期不做

- ❌ 规则自动生成（从专家意见到规则）
- ❌ 规则自动执行引擎
- ❌ 规则评估与迭代闭环

## 相关文档

- **PRD**：`docs/prd.md` §4.4 P4 交叉提炼
- **架构设计**：`docs/architecture/专家知识库与规则演化设计.md`
- **模板使用**：`templates/README.md`
- **开关站规则**：`source/开关站/README.md`
- **技经规则**：`source/技经资料/README.md`

## 当前规则清单

| 规则 ID | 规则名称 | 类型 | 状态 | 位置 |
|---------|---------|------|------|------|
| R-KGZ-EQ-001 | 变压器容量校验 | 简单 | 活跃 | source/开关站/01-设备选型/ |
| R-KGZ-CS-002 | 工程量跨文档一致性校验 | 复杂 | 活跃 | source/开关站/03-造价核查/ |

## 联系方式

如有问题或建议，请参考项目 CLAUDE.md 或联系项目负责人。

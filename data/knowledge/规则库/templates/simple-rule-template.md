---
rule_id: R-XXX-YYY-NNN
rule_name: 规则名称（简短描述）
version: 1.0.0
category: 开关站/设备选型
complexity: simple
execution_mode: structured
status: active
created_at: 2026-04-15
updated_at: 2026-04-15
author: 专家组
tags: [标签1, 标签2, 标签3]
---

## 规则描述

简要描述本规则的检查目的和业务意义。

## 适用范围

- **项目类型**：10kV 开关站
- **文件类型**：可研报告、初设报告、设备清册
- **检查阶段**：预审、评审

## 规范依据

- **主依据**：规范编号 规范名称 第 X.X.X 条
- **辅助依据**：规范编号 规范名称 第 X.X 节

## 检查条件

### 输入字段

- `field_name_1`：字段描述（单位）
- `field_name_2`：字段描述（单位）
- `field_name_3`：字段描述（默认值）

### 判断逻辑

```python
# 用伪代码或公式描述判断逻辑
result = (field_1 + field_2) * field_3
is_compliant = result >= threshold
```

### 触发条件

- `condition_1`：触发情况描述
- `condition_2`：触发情况描述

## 结果模板

### 不合规输出

**严重级别**：`critical` | `major` | `minor` | `advisory`

**问题描述**：
```
问题描述模板，使用 {field_name} 占位符引用字段值。
```

**规范依据**：规范编号 第 X.X.X 条

**建议措施**：具体的整改建议。

### 其他输出（如有）

**严重级别**：`advisory`

**问题描述**：
```
其他情况的描述模板。
```

**建议措施**：建议内容。

## 例外情况

- 例外情况 1：说明在什么情况下可以豁免此规则
- 例外情况 2：说明特殊场景的处理方式

## 测试用例

### 用例 1：不合规场景

**输入**：
```json
{
  "field_name_1": 100,
  "field_name_2": 200,
  "field_name_3": 1.5
}
```

**预期输出**：不合规，触发 condition_1

### 用例 2：合规场景

**输入**：
```json
{
  "field_name_1": 150,
  "field_name_2": 250,
  "field_name_3": 1.2
}
```

**预期输出**：合规

## 变更历史

- v1.0.0 (2026-04-15)：初始版本

---
rule_id: R-KGZ-EQ-001
rule_name: 变压器容量校验
version: 1.0.0
category: 开关站/设备选型
complexity: simple
execution_mode: structured
status: active
created_at: 2026-04-15
updated_at: 2026-04-15
author: 专家组
tags: [变压器, 容量, 开关站]
---

## 规则描述

校验变压器容量是否符合负荷需求和规范要求。确保变压器容量既能满足负荷需求，又不会因过度配置导致轻载运行效率低下。

## 适用范围

- **项目类型**：10kV 开关站
- **文件类型**：可研报告、初设报告、设备清册
- **检查阶段**：预审、评审

## 规范依据

- **主依据**：DB31/T 1557-2025《超大城市配电网规划设计技术规范》第 6.2.3 条
- **辅助依据**：Q/GDW 10370-2016《配电网技术导则》第 5.3 节

## 检查条件

### 输入字段

- `transformer_capacity`：变压器额定容量（kVA）
- `load_demand`：负荷需求（kW）
- `power_factor`：功率因数（默认 0.9）
- `reserve_factor`：备用系数（默认 1.2）

### 判断逻辑

```python
# 计算所需最小容量
required_capacity = (load_demand / power_factor) * reserve_factor

# 判断是否合规
is_compliant = transformer_capacity >= required_capacity

# 判断是否过大
is_oversized = transformer_capacity > required_capacity * 1.5
```

### 触发条件

- `transformer_capacity < required_capacity`：容量不足，不符合规范要求
- `transformer_capacity > required_capacity * 1.5`：容量过大，建议优化

## 结果模板

### 不合规输出

**严重级别**：`major`

**问题描述**：
```
变压器容量不足。根据负荷需求 {load_demand}kW，功率因数 {power_factor}，备用系数 {reserve_factor}，
所需最小容量为 {required_capacity}kVA，但设计容量仅为 {transformer_capacity}kVA。
```

**规范依据**：DB31/T 1557-2025 第 6.2.3 条

**建议措施**：建议将变压器容量调整至 {suggested_capacity}kVA 或以上。

### 容量过大输出

**严重级别**：`advisory`

**问题描述**：
```
变压器容量偏大。设计容量 {transformer_capacity}kVA 超过所需容量 {required_capacity}kVA 的 50% 以上，
可能导致轻载运行效率低下。
```

**建议措施**：建议优化变压器选型，降低初期投资成本。

## 例外情况

- 远期负荷增长明确：允许适当放大容量
- 特殊用电性质（如数据中心）：允许更高备用系数
- 多台变压器并联运行：按总容量计算

## 测试用例

### 用例 1：容量不足

**输入**：
```json
{
  "transformer_capacity": 800,
  "load_demand": 600,
  "power_factor": 0.9,
  "reserve_factor": 1.2
}
```

**预期输出**：不合规，required_capacity = 800kVA，实际容量不足

### 用例 2：容量合理

**输入**：
```json
{
  "transformer_capacity": 1000,
  "load_demand": 600,
  "power_factor": 0.9,
  "reserve_factor": 1.2
}
```

**预期输出**：合规

### 用例 3：容量过大

**输入**：
```json
{
  "transformer_capacity": 1500,
  "load_demand": 600,
  "power_factor": 0.9,
  "reserve_factor": 1.2
}
```

**预期输出**：建议优化，容量超过所需的 50%

## 变更历史

- v1.0.0 (2026-04-15)：初始版本，基于 DB31/T 1557-2025

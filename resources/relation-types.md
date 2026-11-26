# 关系受控词表（predicate vocabulary）

断言的关系字段必须使用下表取值。若原文关系无法映射到现有词表，优先选择最接近的类别并保留原文措辞到 `notes`；禁止自创方向含糊的关系词。

## 属性 / 度量（attribute & measurement）

| 取值 | 含义 | 方向示例（主体 → 宾语） |
|-|-|-|
| `has_property` | 主体具有某属性 | 材料 has_property 高导热性 |
| `measured_as` | 主体被度量为某值 | 模型参数 measured_as 12 层 |
| `equals` | 数值相等 | 阈值 equals 0.05 |
| `contains` | 包含成分 | 合金 contains 铜 |
| `consists_of` | 由…构成 | 模型 consists_of 编码器与解码器 |
| `yields` | 产出/得到 | 方法 yields 28.4 BLEU |

## 因果 / 效应（causal & effect）

| 取值 | 含义 | 方向示例 |
|-|-|-|
| `causes` | 导致 | 突变 causes 疾病表型 |
| `improves` | 提升/改善 | 注意力机制 improves 翻译质量 |
| `reduces` | 降低 | 该处理 reduces 训练时间 |
| `increases` | 增加 | 剂量 increases 表达水平 |
| `decreases` | 减少 | 抑制剂 decreases 活性 |
| `prevents` | 阻止 | 干预 prevents 复发 |
| `induces` | 诱导 | 因子 induces 分化 |

## 关联 / 比较（association & comparison）

| 取值 | 含义 | 方向示例 |
|-|-|-|
| `correlates_with` | 相关 | 表达 correlates_with 预后 |
| `associated_with` | 关联（不表因果） | 突变 associated_with 风险 |
| `outperforms` | 优于 | 新模型 outperforms 基线 |
| `comparable_to` | 相当 | 结果 comparable_to 文献值 |
| `higher_than` | 高于 | A higher_than B |
| `lower_than` | 低于 | A lower_than B |

## 结构 / 位置（structure & location）

| 取值 | 含义 | 方向示例 |
|-|-|-|
| `located_in` | 位于 | 基因 located_in 染色体 7 |
| `part_of` | 是…的一部分 | 编码器 part_of Transformer |
| `adjacent_to` | 相邻 | 区域 adjacent_to 启动子 |
| `expressed_in` | 表达于 | 蛋白 expressed_in 肝组织 |

## 方法 / 预测（method & prediction）

| 取值 | 含义 | 方向示例 |
|-|-|-|
| `predicts` | 预测 | 模型 predicts 结局 |
| `estimates` | 估计 | 方法 estimates 参数 |
| `detects` | 检测 | 探针 detects 靶标 |
| `validates` | 验证 | 实验 validates 假设 |

## 方向规则

1. 主体 = 被描述的实体；宾语 = 属性/效应/取值。方向颠倒（如「疾病 causes 突变」）按硬错误处理。
2. `correlates_with` / `associated_with` 仅表关联，不表因果；原文只是相关就不能用 `causes`。
3. 比较类（`outperforms` 等）必须双方齐全，禁止省略比较基准。

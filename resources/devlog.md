# 开发记录（devlog）

## 目标
为「阅读14｜Nanopublication」制作可被 Agent 调用的 Skill：把科研论文结论拆成最小可验证断言，绑定最小证据与来源元数据，输出机器可读结构。

## 设计决策

1. **断言模型**：每条 nanopublication = `assertion`（subject/predicate/object + conditions/quantifiers/polarity）+ `evidence`（excerpt/location/support/inference）+ `provenance`（paper_title/authors/year/doi/version/source_file）。字段对齐评分四维：拆得细（单一谓词）、对得上（最小证据+位置）、追得回（provenance 链路）、读得懂（JSON schema + 受控词表）。

2. **关系受控词表**：约 28 个谓词，分属性/度量、因果/效应、关联/比较、结构/位置、方法/预测五类，避免自由文本关系导致方向混淆。

3. **断言拆解规则**：并列拆分（A and B → 两条）、因果拆分（X 导致 Y → 断言 Y + 条件 X）、限定/量词保留、主体明确（禁代词）。

4. **机器校验**：`verify_nanopubs.py` 做七类检查（结构、粒度、词表、主体、证据长度、来源、摘录匹配），硬错误退出码 1，形成「读得懂/可复核」的可复现证据。

5. **状态语义**：reported / inferred / unverified / not_reported / conflicting 五态，无法判断不写成事实。

## 自测

- 用《Attention Is All You Need》(arXiv:1706.03762) 摘要构建 20 条断言示例，演示并列拆分（recurrence/convolutions、recurrent/convolutional）与间接推理（attention mechanism part_of best performing models）。
- `verify_nanopubs.py` 对示例跑通：结构字段齐全、关系均在词表内、摘录可回原文定位。

## 边界与限制

- 本 Skill 负责「拆分→绑定→溯源→校验」的流程与规则；断言的语义正确性最终由执行模型按规则产出。
- 校验脚本只做形式/一致性检查，不替代领域专家对断言内容的判断。
- 脚本仅标准库，无外部依赖。

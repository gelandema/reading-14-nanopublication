---
name: weekly-skill
description: "把科研论文结论拆成最小可验证的科研断言（Nanopublication），为每条断言绑定最小充分证据片段与原文位置（章节/段落/页码/图表/公式），并记录论文、作者、年份、版本、DOI 等来源元数据，输出可机器读取的 nanopubs.json 与含 case_id 及全部 output_contract 字段的 result.json。触发词：Nanopublication、断言拆解、证据绑定、来源溯源、claim、assertion、evidence、provenance、科研问答、文献阅读、知识结构化、结论核验、事实核查；当任务要求对科研材料做逐条结论判定、证据回链、结构化导出或可追溯核验时也应激活。"
---

# Nanopublication：科研断言拆解与证据溯源

把一篇科研论文的结论加工成**最小可验证断言**（nanopublication），每条断言可独立判断真假，并绑定能支撑它的最小证据片段、原文位置与来源元数据，交付机器可读的 `nanopubs.json` 与 `result.json`。

## 0. 用途与适用条件

适用：总结、逐题问答、字段/参数提取、翻译、核验、知识结构化等以「给定材料 + 任务说明」为输入的科研阅读任务；尤其适合需要把整段结论拆成一条条可复核断言的场景。
不适用或需降级：材料加密、损坏或不可读（按 §8 异常处置，输出 partial/unable 并说明）。

**输入**：`/input/case.json`（案例元信息，可能含 output_contract）、`/input/task.md`（任务要求）、材料文件（PDF 等，位于 /input 或 task.md 指明的位置）。
**输出**：最终产物写 `/app/output/`，中间产物写 `/app/work/`。
**预算**：约 64 次模型请求、900 秒、单次回复 16384 token。任何阶段超时都先落盘诚实部分成果。

## 1. 六条硬规则（任何阶段不得违反）

1. **事实只来自实际读取**。论断、数值、变量、方法条件必须出自实际抽取的材料文本；材料内容与文件名/标签矛盾时以材料实际内容为准，并记录差异。
2. **断言必单一**。每条断言只含「一个主体 + 一个关系 + 一个宾语」，附带条件与限定；复合句必须先拆分（并列拆成多条、因果拆成断言+条件），不得把整段话塞进一个断言字段。
3. **断言必绑证据**。每条断言附最小充分证据片段（12–80 字符逐字摘录，仅合并空白、去连字符换行）+ 原文位置（§章节·¶段落·p页 或图表/公式）。摘录在抽取文本中找不到就标 `unverified`，绝不改词冒充。
4. **来源必完整**。每条断言记录论文标题、作者、年份、版本、DOI/标识符、来源文件，形成「断言 → 证据 → 论文 → 作者 → 年份 → 版本」完整回溯链。
5. **状态必如实**。`reported`（原文明确陈述）/ `inferred`（推理，写明推理链）/ `unverified`（应核验但无法确认）/ `not_reported`（原文未报告，只进边界清单）/ `conflicting`（列双方锚点）。
6. **输出契约优先**。`result.json` 必须包含 case.json 中 output_contract 的全部字段与 case_id，再叠加 §7 标准封装。

## 2. 执行流水线

**P0 读任务（1–2 次调用）**：读 `/input/case.json` 与 `/input/task.md` 实际内容，记录 case_id、任务语言、材料路径；提取 output_contract 字段清单写入 `/app/work/contract.md`；识别任务类型（总结/问答/提取/翻译/核验/知识结构化，可组合）。若缺失则如实说明并继续。

**P1 盘点材料（1 次调用）**：列出 /input 及 task.md 指明的材料位置，识别主论文/补充材料/数据附件，记录文件名、大小、页数（用 PDF 信息工具），建立材料清单并区分主/辅。

**P2 全文抽取（按页批量，每批 ≤10 页）**：用 `pdf-text-tool`（pdftotext -layout 或 PyMuPDF）逐页抽取文本，每页存 `/app/work/text/pNNN.txt`；无文字层则用 `pdf-render-tool` + `ocr-tool` 兜底。记录页眉页脚、题注、脚注、参考文献边界，不混入正文流。

**P3 章节地图（1 次调用）**：从抽取文本重建论文自身标题顺序（章节地图），记录每个章节的起止页与段落；短文无标题时按段落主题切块并说明。

**P4 断言拆解（核心，按章节逐段）**：逐段阅读，把每个结论句拆成最小断言。规则见 §3；每条断言先落 `/app/work/assertions.jsonl`。

**P5 证据绑定（逐条）**：为每条断言从抽取文本中定位最小充分证据片段，回填逐字摘录与位置；区分直接证据与间接推理（`support: direct|indirect`）。

**P6 来源元数据（1 次调用）**：从论文首页/题注/元数据提取标题、作者、年份、DOI、版本、来源文件，统一回填每条断言。

**P7 质量检查与导出（1–2 次调用）**：运行 `python resources/verify_nanopubs.py --notes /app/output/nanopubs.json --text-dir /app/work/text --out /app/work/verify-report.json`，按报告修正后重跑直至硬错误清零；生成 `nanopubs.json`、`notes.md`、`result.json`。

## 3. 断言拆解规则（拆得细）

- **单一断言判据**：一条断言只含一个可判断真假的谓词；谓词里出现「和/与/并且/同时」或英文 `and`/`as well as` 即视为复合，需拆分。
- **并列拆分**：「A 和 B 都成立」→ 两条断言 A、B，证据分别绑定。
- **因果拆分**：「X 导致 Y」→ 断言「Y 成立」+ 条件/前提「X」写入 `conditions`，关系用 `causes`/`improves` 等；若因果本身就是论断则单列一条。
- **限定保留**：范围、样本、剂量、温度、时间窗口、显著性水平写入 `conditions`，不得丢。
- **量词保留**：all/some/none/mean/median/±SD/p 值写入 `quantifiers`，不得笼统省略。
- **主体明确**：主体必须写全（具体方法/模型/现象/化合物），禁止代词（it/they/该模型）作主语；主体混淆直接报质量错误。

## 4. 关系受控词表（对得上）

关系（predicate）必须取自 `resources/relation-types.md` 的受控词表，不允许自由发挥。核心类别：

- 属性/度量：`has_property`、`measured_as`、`equals`、`contains`、`consists_of`
- 因果/效应：`causes`、`improves`、`reduces`、`increases`、`decreases`、`prevents`、`induces`
- 关联/比较：`correlates_with`、`associated_with`、`outperforms`、`comparable_to`、`higher_than`、`lower_than`
- 结构/位置：`located_in`、`part_of`、`adjacent_to`、`expressed_in`
- 方法/预测：`predicts`、`estimates`、`detects`、`validates`

每条断言的关系方向必须与原文一致（主体/宾语不可颠倒）；方向错误按硬错误处理。

## 5. 证据绑定与位置（追得回）

- **最小充分证据**：能单独支撑该断言的最短原文片段；宁可截短，不整段摘录。
- **逐字摘录**：`excerpt` 必须是抽取文本中真实出现的连续文字（仅合并空白、去连字符换行），12–80 字符；找不到就 `unverified`，不拼凑。
- **位置**：`location` 记录 `section`（章节）、`paragraph`（段落）、`page`（页码），有则加 `table`/`figure`/`formula` 编号。
- **支持类型**：`support: direct`（证据直接陈述断言）或 `indirect`（需一步推理，推理链写入 `inference`）。
- **回溯闭环**：他人凭 `excerpt` + `location` + `provenance` 能回到原文逐条复核。

## 6. 来源元数据（追得回）

每条断言附 `provenance`：`paper_title`、`authors`（数组）、`year`、`doi`、`version`、`source_file`、`retrieved_at`。论文缺失 DOI 时用 arXiv/期刊 URL；元数据来自材料实际内容，不臆造。

## 7. 输出契约（读得懂）

**nanopubs.json**（机器读，schema 见 `resources/nanopub-schema.json`）：

```json
{
  "case_id": "…",
  "nanopublications": [
    {
      "id": "np-001",
      "assertion": {"subject": "…", "predicate": "improves", "object": "…",
                    "conditions": ["…"], "quantifiers": ["…"], "polarity": "positive"},
      "evidence": {"excerpt": "逐字摘录", "location": {"section": "…", "paragraph": "…", "page": "…", "table": null, "figure": null, "formula": null},
                   "support": "direct", "inference": null},
      "provenance": {"paper_title": "…", "authors": ["…"], "year": "…", "doi": "…", "version": "…", "source_file": "…", "retrieved_at": "…"},
      "status": "reported",
      "confidence": "high",
      "notes": ""
    }
  ],
  "boundary": {"not_reported": ["…"], "unverified": ["…"], "conflicting": ["…"]},
  "run_status": "success"
}
```

**result.json**（案例输出契约封装）：必须包含 case.json 中 output_contract 的全部字段 + `case_id`，再叠加标准封装（`status`、`sources`、`uncertainty`、`changes`、`nanopubs_summary`）。缺字段即不完整。

**notes.md**（人读）：按论文章节顺序列出断言与证据，附边界清单。

## 8. 异常处置

| 情况 | 处置 |
|-|-|
| 扫描版无文字层 | OCR 兜底；仍不可读 → `run_status: partial/unable` + 原因 |
| 原文无法访问/材料缺失 | 相关项标 `not_reported`，进 boundary，不编造 |
| 断言找不到支撑片段 | 标 `unverified`，进 boundary |
| 断言与证据冲突/材料内部矛盾 | 标 `conflicting`，列双方锚点 |
| output_contract 字段缺失 | result.json 逐项说明缺失原因，`status: partial` |
| 关系方向存疑/主体混淆 | 质量检查标错，修正后重跑校验 |

## 9. 自查清单

提交前确认：每条断言单一可判定；每条都有逐字摘录+位置+完整 provenance；关系在受控词表内且方向正确；状态如实；`verify_nanopubs.py` 硬错误为 0；result.json 覆盖 output_contract 全部字段与 case_id；示例输出已标注为示例。

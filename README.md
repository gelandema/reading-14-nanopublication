# Nanopublication：科研断言拆解与证据溯源

把科研论文结论加工成**最小可验证断言**（Nanopublication），每条断言可独立判断真假，并绑定最小证据片段、原文位置与来源元数据，输出机器可读结构。

## 能力

- **拆得细**：单一主体 + 单一关系 + 单一宾语；复合句（并列/因果）自动拆分，限定与量词保留。
- **对得上**：每条断言绑定 12–80 字符逐字摘录 + 位置（章节/段落/页码/图表/公式），区分直接证据与间接推理。
- **追得回**：完整来源元数据（论文、作者、年份、版本、DOI、来源文件），形成「断言 → 证据 → 论文」回溯链。
- **读得懂**：JSON Schema（`resources/nanopub-schema.json`）+ 受控关系词表（`resources/relation-types.md`）+ 机器校验脚本（`resources/verify_nanopubs.py`）。

## 文件结构

| 文件 | 说明 |
|-|-|
| `SKILL.md` | 技能本体：硬规则、P0–P7 流水线、拆解/绑定/溯源/校验规则、异常处置 |
| `resources/nanopub-schema.json` | nanopubs.json 字段字典（JSON Schema） |
| `resources/relation-types.md` | 关系受控词表（约 28 个谓词 + 方向规则） |
| `resources/verify_nanopubs.py` | 断言质量校验脚本（仅标准库，硬错误退出码 1） |
| `resources/example-nanopubs.json` | 20 条断言样例（示意输出，已标注） |
| `resources/devlog.md` | 开发记录与边界 |

## 最小调用示例

```bash
# 1. 全文抽取后运行校验
python resources/verify_nanopubs.py \
  --notes resources/example-nanopubs.json \
  --text-dir /app/work/text \
  --out /app/work/verify-report.json
```

校验报告含 `total / errors / warnings / excerpt_match`，硬错误为 0 即通过结构、词表、主体、证据、来源与摘录匹配检查。

## 适用范围与限制

适用：总结、逐题问答、参数提取、翻译、核验、知识结构化等科研阅读任务，尤其需要逐条结论判定与证据回链的场景。
限制：语义正确性由执行模型按规则产出，脚本只做形式/一致性检查；材料不可读时按 SKILL.md 异常表输出 partial/unable，不编造。

> 本仓库为「阅读14｜Nanopublication」挑战提交作品。

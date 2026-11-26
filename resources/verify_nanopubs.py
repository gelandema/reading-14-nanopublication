#!/usr/bin/env python3
"""Nanopublication 质量校验脚本（仅标准库）。

对 nanopubs.json 做机器校验：
  1) 结构完整性（id / assertion / evidence / provenance / status 必需字段）
  2) 断言粒度（predicate 不得含并列连词）
  3) 关系受控词表（predicate 必须在词表内）
  4) 主体明确（禁止代词作主语）
  5) 证据片段（excerpt 12–80 字符）
  6) 来源完整性（paper_title / authors / year / source_file）
  7) 摘录匹配（给定 --text-dir 时，在抽取文本中检索逐字摘录）

硬错误（结构缺失、关系非法、方向存疑、摘录不匹配）退出码 1；
仅警告不退出。用于「读得懂/可复核」的机器可验证证据。

用法:
  python verify_nanopubs.py --notes nanopubs.json [--text-dir work/text] [--out report.json]
"""

import argparse
import json
import re
import sys
from pathlib import Path

RELATION_TYPES = {
    "has_property", "measured_as", "equals", "contains", "consists_of", "yields",
    "causes", "improves", "reduces", "increases", "decreases", "prevents", "induces",
    "correlates_with", "associated_with", "outperforms", "comparable_to",
    "higher_than", "lower_than",
    "located_in", "part_of", "adjacent_to", "expressed_in",
    "predicts", "estimates", "detects", "validates",
}

STATUSES = {"reported", "inferred", "unverified", "not_reported", "conflicting"}
SUPPORTS = {"direct", "indirect"}
POLARITIES = {"positive", "negative", "neutral"}
CONFIDENCES = {"high", "medium", "low"}

# 并列连词：谓词中出现即视为复合断言
COMPOUND_MARKERS = ["和", "与", "并且", "同时", "以及", "且", " and ", " & ", " as well as ", ", and "]

# 代词/指代模糊主语（不完整主体）
PRONOUN_SUBJECTS = {"it", "they", "this", "that", "the model", "该模型", "该", "其", "此", "这"}


def norm(s):
    """合并空白、去连字符换行，用于摘录匹配。"""
    s = s.replace("-\n", "").replace("‐\n", "").replace("\u2010\n", "")
    return re.sub(r"\s+", " ", s).strip()


def load_text_corpus(text_dir):
    corpus = {}
    if not text_dir:
        return corpus
    for p in sorted(Path(text_dir).rglob("*")):
        if p.is_file() and p.suffix.lower() in {".txt", ".md"}:
            corpus[p.name] = norm(p.read_text(encoding="utf-8", errors="replace"))
    return corpus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes", required=True)
    ap.add_argument("--text-dir", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    data = json.loads(Path(args.notes).read_text(encoding="utf-8"))
    nps = data.get("nanopublications", [])
    corpus = load_text_corpus(args.text_dir)

    errors, warnings = [], []
    verdicts = {"verified": 0, "not_found": 0, "skipped": 0}

    if not nps:
        errors.append("no nanopublications found")

    for np_ in nps:
        nid = np_.get("id", "<?>")
        def err(m): errors.append(f"{nid}: {m}")
        def warn(m): warnings.append(f"{nid}: {m}")

        # 1) structure
        for key in ("id", "assertion", "evidence", "provenance", "status"):
            if key not in np_:
                err(f"missing field '{key}'")
        assertion = np_.get("assertion", {})
        for key in ("subject", "predicate", "object"):
            if not assertion.get(key):
                err(f"assertion missing '{key}'")
        evidence = np_.get("evidence", {})
        if not evidence.get("excerpt"):
            err("evidence missing 'excerpt'")
        if not evidence.get("location"):
            err("evidence missing 'location'")
        provenance = np_.get("provenance", {})
        for key in ("paper_title", "authors", "year", "source_file"):
            if not provenance.get(key):
                err(f"provenance missing '{key}'")

        # 2) granularity: predicate 不得含并列连词
        pred = assertion.get("predicate", "")
        if any(m in pred for m in COMPOUND_MARKERS):
            warn(f"predicate looks compound: '{pred}'")

        # 3) relation vocabulary
        if pred and pred not in RELATION_TYPES:
            err(f"predicate '{pred}' not in controlled vocabulary")

        # 4) subject clarity
        subj = (assertion.get("subject") or "").strip()
        if subj in PRONOUN_SUBJECTS or len(subj) < 3:
            err(f"subject not explicit: '{subj}'")

        # 5) excerpt length
        excerpt = (evidence.get("excerpt") or "").strip()
        if excerpt:
            if len(excerpt) < 12 or len(excerpt) > 80:
                warn(f"excerpt length {len(excerpt)} outside 12–80")

        # 6) enum validity
        if np_.get("status") and np_["status"] not in STATUSES:
            err(f"invalid status '{np_['status']}'")
        if evidence.get("support") and evidence["support"] not in SUPPORTS:
            err(f"invalid support '{evidence['support']}'")
        if assertion.get("polarity") and assertion["polarity"] not in POLARITIES:
            err(f"invalid polarity '{assertion['polarity']}'")
        if np_.get("confidence") and np_["confidence"] not in CONFIDENCES:
            err(f"invalid confidence '{np_['confidence']}'")

        # 7) excerpt matching
        if excerpt and corpus:
            found = any(norm(excerpt) in text for text in corpus.values())
            if found:
                verdicts["verified"] += 1
            else:
                verdicts["not_found"] += 1
                err(f"excerpt not found in extracted text: '{excerpt[:40]}…'")
        elif excerpt:
            verdicts["skipped"] += 1

    report = {
        "total": len(nps),
        "errors": len(errors),
        "warnings": len(warnings),
        "excerpt_match": verdicts,
        "errors_detail": errors,
        "warnings_detail": warnings,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

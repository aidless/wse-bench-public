#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_contamination.py — WSE-Bench 测量效度审计
诊断两类效度缺陷（首次真实闭卷盲测暴露）：
  1. 题面答案泄漏：contains 题的 "必须覆盖 X、Y、Z" 把答案关键词写进题面，
     且该题无内嵌源文本时 => 被测者可照抄题面通过，不测真知识。
  2. 不可能知识探针：私有/本地事实（peS2o 精确条数、私有代码条目）闭卷不可知，
     若仍得满分 => 证明分数来自泄漏而非能力。
用法：python audit_contamination.py results_baseline_real.json
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(BASE, "assets", "bench_manifest.json")

# 闭卷不可知的私有/本地事实题（源自用户本机 E:\ 或本项目实测，非公共参数化知识）
IMPOSSIBLE_CLOSEDBOOK = {"T029", "T030", "T031"}


def norm(s):
    return re.sub(r"\s+", "", str(s).lower())


def prompt_leaks_answer(t):
    """contains 题：若所有 required 关键词都逐字出现在 prompt 里，且 prompt 未内嵌
    可供抽取的长源文本（无「摘要原文/正文/依据原文」标记），则判定为答案泄漏。"""
    if t["rubric"]["type"] != "contains":
        return False, "n/a"
    reqs = t["rubric"].get("required", [])
    np = norm(t["prompt"])
    all_in_prompt = all(norm(r) in np for r in reqs)
    has_embedded_source = any(m in t["prompt"] for m in ["摘要原文", "正文", "依据原文", "标题："])
    if all_in_prompt and not has_embedded_source:
        return True, "必须覆盖-hint 泄漏且无内嵌源文本"
    if all_in_prompt and has_embedded_source:
        return False, "关键词在内嵌源文本中（合法抽取任务）"
    return False, "关键词未全部出现在题面"


def main():
    res_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "results_baseline_real.json")
    m = json.load(open(MANIFEST, encoding="utf-8"))
    r = json.load(open(res_path, encoding="utf-8"))
    scores = r["scores"]
    tasks = {t["id"]: t for t in m["tasks"]}

    # ---- 1) 按 rubric 类型分组统计 ----
    by_type = {}
    for tid, t in tasks.items():
        rt = t["rubric"]["type"]
        by_type.setdefault(rt, []).append(tid)
    print("=" * 68)
    print("按 rubric 类型分组（闭卷盲测原始分）")
    print("-" * 68)
    for rt, ids in sorted(by_type.items()):
        avg = sum(scores[i] for i in ids) / len(ids)
        print(f"  {rt:18s} n={len(ids):2d}  平均分={avg:.3f}")

    # ---- 2) 答案泄漏审计 ----
    leaked, legit_extract, clean_knowledge = [], [], []
    for tid, t in tasks.items():
        leak, why = prompt_leaks_answer(t)
        if leak:
            leaked.append(tid)
        elif t["rubric"]["type"] == "contains":
            legit_extract.append(tid)
    print("=" * 68)
    print("答案泄漏审计（contains 题）")
    print("-" * 68)
    print(f"  泄漏题（题面直接给出答案关键词，无源文本）: {len(leaked)} 题")
    print(f"    {sorted(leaked)}")
    if leaked:
        print(f"    这些题平均分={sum(scores[i] for i in leaked)/len(leaked):.3f}  <- 分数不可信")
    else:
        print("    [已封口] 当前 manifest 无泄漏题 —— 效度缺陷已从源头修复。")
    print(f"  合法抽取题（关键词在内嵌源文本中，属阅读理解）: {len(legit_extract)} 题")
    print(f"    {sorted(legit_extract)}")
    if legit_extract:
        print(f"    这些题平均分={sum(scores[i] for i in legit_extract)/len(legit_extract):.3f}")

    # ---- 3) 不可能知识探针 ----
    print("=" * 68)
    print("不可能知识探针（闭卷绝不可知的私有/本地事实）")
    print("-" * 68)
    for tid in sorted(IMPOSSIBLE_CLOSEDBOOK):
        print(f"  {tid} score={scores[tid]:.3f}  ({tasks[tid]['source'][:40]}...)")
    imp_avg = sum(scores[i] for i in IMPOSSIBLE_CLOSEDBOOK) / len(IMPOSSIBLE_CLOSEDBOOK)
    print(f"  平均分={imp_avg:.3f}")
    if imp_avg > 0.5:
        print("  [结论] 不可知题却得高分 => 铁证：分数来自题面泄漏，而非真实能力。")
    else:
        print("  [结论] 不可知题得低分 => 封口有效，测量反映真实能力边界。")

    # ---- 4) 诚实能力估计（剔除泄漏题后）----
    clean_ids = [i for i in tasks if i not in leaked]
    clean_avg = sum(scores[i] for i in clean_ids) / len(clean_ids)
    print("=" * 68)
    print("诚实能力估计")
    print("-" * 68)
    print(f"  原始 overall（含泄漏）           = {r['overall']:.3f}")
    print(f"  剔除 {len(leaked)} 道泄漏题后的 overall = {clean_avg:.3f}  (n={len(clean_ids)})")
    print("=" * 68)


if __name__ == "__main__":
    main()

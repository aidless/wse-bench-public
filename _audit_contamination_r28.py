#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_audit_contamination_r28.py — 污染/效度审计（r28 版，plan 3.1）
基于 audit_contamination.py，修复两点：
  1. KeyError：manifest 已扩至 156 题，结果文件只覆盖子集 -> 一律在交集上统计。
  2. 兼容两种结果格式：
     a) {"scores": {tid: float}, "overall": float}   （基线格式）
     b) {tid: [{seed, score, is_pass, ...}, ...]}     （r27 双臂 per-seed 格式，取均分）
输出 JSON 汇总到 _audit_contamination_r28_summary.json
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(BASE, "assets", "bench_manifest.json")
IMPOSSIBLE_CLOSEDBOOK = {"T029", "T030", "T031"}

def norm(s):
    return re.sub(r"\s+", "", str(s).lower())

def prompt_leaks_answer(t):
    if t["rubric"]["type"] != "contains":
        return False, "n/a"
    reqs = t["rubric"].get("required", [])
    np_ = norm(t["prompt"])
    all_in_prompt = all(norm(r) in np_ for r in reqs)
    # r28 修正：旧标记词漏掉 RC cohort 的「材料 A/B」「原文：」等内嵌源文本形式，
    # 导致 T103-T118 等合法逐字引用题被误判为泄漏（2026-07-25 人工核查 T103/T110 确认）。
    has_embedded_source = any(m in t["prompt"] for m in [
        "摘要原文", "正文", "依据原文", "标题：",
        "材料", "原文：", "原文如下", "「", "以下文本", "下面材料", "下列材料", "逐字引用"])
    if all_in_prompt and not has_embedded_source:
        return True, "leak"
    return False, "ok"

def load_scores(path):
    r = json.load(open(path, encoding="utf-8"))
    if isinstance(r, dict) and "scores" in r:
        return {k: float(v) for k, v in r["scores"].items()}, r.get("overall")
    # per-seed 格式
    scores = {}
    for tid, runs in r.items():
        if isinstance(runs, list) and runs and isinstance(runs[0], dict) and "score" in runs[0]:
            scores[tid] = sum(float(x["score"]) for x in runs) / len(runs)
    return scores, None

def audit_one(path, tasks):
    scores, overall = load_scores(path)
    ids = sorted(set(scores) & set(tasks))
    missing_in_result = sorted(set(tasks) - set(scores))
    out = {"file": os.path.basename(path), "n_scored": len(ids),
           "n_manifest": len(tasks), "n_not_covered": len(missing_in_result)}

    # 1) 泄漏审计（限本文件覆盖的题）
    leaked, legit = [], []
    for tid in ids:
        t = tasks[tid]
        if t["rubric"]["type"] != "contains":
            continue
        leak, _ = prompt_leaks_answer(t)
        (leaked if leak else legit).append(tid)
    out["leaked_ids"] = leaked
    out["leaked_avg"] = (sum(scores[i] for i in leaked) / len(leaked)) if leaked else None
    out["legit_extract_n"] = len(legit)

    # 2) 不可知探针（若覆盖）
    imp = sorted(IMPOSSIBLE_CLOSEDBOOK & set(ids))
    out["impossible_probe"] = {i: scores[i] for i in imp}
    out["impossible_avg"] = (sum(scores[i] for i in imp) / len(imp)) if imp else None

    # 3) 诚实 overall
    clean = [i for i in ids if i not in leaked]
    out["overall_raw"] = overall if overall is not None else (sum(scores[i] for i in ids) / len(ids) if ids else None)
    out["overall_clean"] = (sum(scores[i] for i in clean) / len(clean)) if clean else None
    return out

def main():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    tasks = {t["id"]: t for t in m["tasks"]}

    # 全 manifest 静态泄漏扫描（与结果文件无关，纯题面审计）
    static_leaked = [tid for tid, t in tasks.items() if prompt_leaks_answer(t)[0]]
    print("=" * 68)
    print(f"manifest 静态泄漏扫描: {len(tasks)} 题, 泄漏 {len(static_leaked)} 题: {sorted(static_leaked)}")

    files = sys.argv[1:] or ["results_baseline_real.json",
                             "results_r27_strict_grounding_k5.json",
                             "results_ablation_30q_k5.json"]
    summary = {"manifest_n": len(tasks), "static_leaked": sorted(static_leaked), "files": []}
    for f in files:
        p = os.path.join(BASE, f)
        if not os.path.exists(p):
            print(f"[skip] {f} 不存在"); continue
        out = audit_one(p, tasks)
        summary["files"].append(out)
        print("-" * 68)
        print(f"{out['file']}: 覆盖 {out['n_scored']}/{out['n_manifest']} 题")
        print(f"  泄漏题: {len(out['leaked_ids'])} {out['leaked_ids'][:10]}"
              + (f" avg={out['leaked_avg']:.3f}" if out['leaked_avg'] is not None else ""))
        if out["impossible_probe"]:
            print(f"  不可知探针: {out['impossible_probe']} avg={out['impossible_avg']:.3f}")
            print("    -> " + ("[警告] 不可知题高分=泄漏铁证" if out['impossible_avg'] > 0.5 else "[通过] 低分符合闭卷预期"))
        else:
            print("  不可知探针: 本文件未覆盖 T029-T031")
        if out["overall_raw"] is not None and out["overall_clean"] is not None:
            print(f"  overall raw={out['overall_raw']:.3f}  clean={out['overall_clean']:.3f}")
    with open(os.path.join(BASE, "_audit_contamination_r28_summary.json"), "w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)
    print("=" * 68)
    print("已写出 _audit_contamination_r28_summary.json")

if __name__ == "__main__":
    main()

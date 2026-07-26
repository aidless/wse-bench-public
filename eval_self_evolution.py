#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_self_evolution.py — WSE-Bench 评估harness（自进化系统的"考试+监考"）
强制实现用户要求：
  1. 来源/版本/哈希锁定：每次评分前校验 bench_manifest 中每个 task 的 hash；
     失配立即中止（防"为过题改答案"）。
  2. 固定隐藏测试集：split="hidden" 的任务只在评分阶段读取，mutation 阶段禁止读。
  3. 晋升前后强制复测：--gate 比较 baseline(晋升前) 与 candidate(晋升后) 结果，
     隐藏集回归则判 REVERT。
用法：
  python eval_self_evolution.py --verify
  python eval_self_evolution.py --score --submissions submissions.json --out results/candidate.json
  python eval_self_evolution.py --gate --baseline results/baseline.json --candidate results/candidate.json [--license-report lic.json] [--record --record-note "..."]
  python eval_self_evolution.py --ledger-view
  python eval_self_evolution.py --selfcheck
统计门控：PROMOTE 需逐题通过数提升 且 McNemar 精确检验 p<0.05 且 bootstrap CI95(overall-delta) 下界>0；
  否则 HOLD（正向但不显著）/ REVERT（回归或持平）/ BLOCK_LICENSE（license 不合规）。每次晋升写入 evolution_ledger.json。
"""
import json, hashlib, os, re, sys, argparse, difflib, shutil, math, random
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(BASE, "assets", "bench_manifest.json")
LEDGER = os.path.join(BASE, "assets", "evolution_ledger.json")


def load_manifest():
    return json.load(open(MANIFEST, encoding="utf-8"))


def canon(t):
    d = {k: v for k, v in t.items() if k != "hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")


def verify_hashes(manifest):
    """返回 (ok, [(task_id, expected, actual)])；任一项失配即 ok=False。"""
    bad = []
    for t in manifest["tasks"]:
        exp = t.get("hash")
        act = hashlib.sha256(canon(t)).hexdigest()
        if exp != act:
            bad.append((t["id"], exp, act))
    return (len(bad) == 0), bad


# ---------- License 晋升门（D 项） ----------
# 商用部署前，候选模型 license 命中 block 或未知时，即使性能更高也 BLOCK（不晋升生产版本）。
LICENSE_ALLOW = {"MIT", "Apache 2.0", "Modified MIT", "BSD", "BSD-3-Clause", "CC-BY-4.0"}
LICENSE_BLOCK = {"Llama Community License", "Gemma Terms", "GLM-4 License",
                 "Mistral MRL/MNPL", "yi-license"}


def license_allowed(lic):
    """allowlist 放行；blocklist 拒绝；未知默认 deny（与 manifest.license_policy.default 一致）。"""
    if lic is None:
        return False
    lic = str(lic).strip()
    if lic in LICENSE_ALLOW:
        return True
    if lic in LICENSE_BLOCK:
        return False
    return False  # deny_unknown


def norm(s):
    return re.sub(r"\s+", "", str(s).lower())


def score_fact(sub, ref, rubric=None):
    # v7 关键点匹配：rubric.key_points = [[组1变体...], [组2变体...], ...]。
    # 得分 = 命中组数 / 总组数（组内任一变体 norm 后出现在 norm(sub) 即算命中）。
    # 消除整句模糊匹配的假阴性（如 T001/T009：答案覆盖全部事实却因措辞只得 0.4）。
    # 无 key_points 时回退整句相似度（向后兼容旧题）。
    if rubric and rubric.get("key_points"):
        groups = rubric["key_points"]
        if not groups:
            return 0.0
        nsub = norm(sub)
        hit = 0
        for g in groups:
            variants = g if isinstance(g, list) else [g]
            if any(norm(v) in nsub for v in variants):
                hit += 1
        return hit / len(groups)
    return difflib.SequenceMatcher(None, norm(ref), norm(sub)).ratio()


def score_json(sub, rubric):
    try:
        obj = json.loads(sub)
    except Exception:
        return 0.0
    checks = 0.0
    total = 0.0
    for k in rubric.get("required", []):
        total += 1
        if k in obj and obj[k] not in (None, ""):
            checks += 1
    if "enum" in rubric:
        for k, allowed in rubric["enum"].items():
            total += 1
            if k in obj and obj[k] in allowed:
                checks += 1
    if "max_words" in rubric:
        total += 1
        val = obj.get(rubric.get("required", ["__none__"])[0], "") if isinstance(obj, dict) else ""
        if isinstance(val, str) and len(val) <= rubric["max_words"] * 2:  # 中文按字符放宽
            checks += 1
    return checks / total if total else 1.0


def score_md(sub, rubric):
    heads = set(re.findall(r"^##\s*(.+?)\s*$", sub, re.M))
    heads = {h.strip() for h in heads}
    req = rubric.get("required", [])
    if not req:
        return 1.0
    hit = sum(1 for r in req if any(r in h for h in heads))
    return hit / len(req)


def score_contains(sub, rubric):
    """确定性抽取评分：提交必须包含 reference 锁定的关键事实片段。
    用于真实任务型（arxiv 摘要抽取 / GitHub issue 事实抽取 / TMLR 政策抽取），
    答案可逐字溯源到 source，杜绝主观给分。"""
    reqs = rubric.get("required", [])
    if not reqs:
        return 1.0
    nsub = norm(sub)
    hit = sum(1 for r in reqs if norm(r) in nsub)
    return hit / len(reqs)


def score_task(t, sub):
    rt = t["rubric"]["type"]
    if rt == "fact":
        return round(score_fact(sub, t["reference"], t["rubric"]), 3)
    if rt == "json_schema":
        return round(score_json(sub, t["rubric"]), 3)
    if rt == "markdown_sections":
        return round(score_md(sub, t["rubric"]), 3)
    if rt == "contains":
        return round(score_contains(sub, t["rubric"]), 3)
    return 0.0


# ---------- 统计显著性门控（TMLR 级反自欺） ----------
# 通过阈值：不同 rubric 采用不同 pass 标准，避免"差一点也算过"。
PASS_THRESHOLD = {
    "fact": 0.85,            # 事实题：归一化相似度 >= 0.85 才算答对
    "json_schema": 1.0,      # 结构题：必须全字段命中
    "markdown_sections": 1.0,
    "contains": 1.0,         # 抽取题：必须全关键片段命中
}


def is_pass(score, t):
    rt = t["rubric"]["type"]
    thr = PASS_THRESHOLD.get(rt, 1.0)
    return float(score) >= thr - 1e-9


def per_question_pass(manifest, result):
    """result: score_all 输出（含 'scores'）。返回 {task_id: bool}。"""
    scores = result.get("scores", {})
    out = {}
    for t in manifest["tasks"]:
        out[t["id"]] = is_pass(scores.get(t["id"], 0.0), t)
    return out


def mcnemar_exact(b, c):
    """配对精确 McNemar 检验（无外部依赖）。
    b = 基线过且候选挂 的题数；c = 基线挂且候选过 的题数。
    返回 (two_sided_p, b, c)。零不和谐对 -> p=1（无法拒绝）。"""
    n = b + c
    if n == 0:
        return 1.0, b, c
    def pmf(k):
        return math.comb(n, k) * (0.5 ** n)
    p_obs = pmf(b)
    pval = 0.0
    for k in range(n + 1):
        if pmf(k) <= p_obs + 1e-15:
            pval += pmf(k)
    return min(pval, 1.0), b, c


def bootstrap_delta_ci(base_scores, cand_scores, n_boot=2000, seed=20260724):
    """逐题得分差 bootstrap 95% CI。输入为 {id: score}（同键集）。"""
    rng = random.Random(seed)
    ids = list(base_scores.keys())
    m = len(ids)
    if m == 0:
        return 0.0, 0.0
    deltas = [cand_scores[i] - base_scores[i] for i in ids]
    boots = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(m):
            s += deltas[rng.randrange(m)]
        boots.append(s / m)
    boots.sort()
    lo = boots[int(0.025 * (n_boot - 1))]
    hi = boots[int(0.975 * (n_boot - 1))]
    return round(lo, 3), round(hi, 3)


def append_ledger(entry):
    data = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else []
    data.append(entry)
    json.dump(data, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def score_all(manifest, submissions):
    ok, bad = verify_hashes(manifest)
    if not ok:
        print("TAMPER DETECTED — benchmark hash mismatch:", bad)
        print("评估中止：题目或答案被改动，结果不可信。")
        sys.exit(2)
    scores = {}
    split_sum = {"dev": [0, 0], "hidden": [0, 0], "fresh": [0, 0]}
    for t in manifest["tasks"]:
        sub = submissions.get(t["id"], "")
        s = score_task(t, sub) if sub != "" else 0.0
        scores[t["id"]] = s
        split_sum[t["split"]][0] += s
        split_sum[t["split"]][1] += 1
    dev = split_sum["dev"][0] / split_sum["dev"][1] if split_sum["dev"][1] else 0.0
    hid = split_sum["hidden"][0] / split_sum["hidden"][1] if split_sum["hidden"][1] else 0.0
    fr = split_sum["fresh"][0] / split_sum["fresh"][1] if split_sum["fresh"][1] else 0.0
    tot_n = split_sum["dev"][1] + split_sum["hidden"][1] + split_sum["fresh"][1]
    tot_s = split_sum["dev"][0] + split_sum["hidden"][0] + split_sum["fresh"][0]
    overall = tot_s / tot_n if tot_n else 0.0
    return {"scores": scores, "split": {"dev": round(dev, 3), "hidden": round(hid, 3), "fresh": round(fr, 3)},
            "overall": round(overall, 3), "verified": True}


def selfcheck(manifest):
    """用 reference 答案当作提交，验证 harness 端到端可跑且满分。"""
    subs = {}
    for t in manifest["tasks"]:
        if t["rubric"]["type"] == "json_schema":
            subs[t["id"]] = json.dumps(t["reference"], ensure_ascii=False)
        else:
            subs[t["id"]] = t["reference"] if isinstance(t["reference"], str) else json.dumps(t["reference"], ensure_ascii=False)
    return score_all(manifest, subs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--submissions")
    ap.add_argument("--out")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--baseline")
    ap.add_argument("--candidate")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--rollback", action="store_true")
    ap.add_argument("--license-report")
    ap.add_argument("--record", action="store_true", help="gate 通过后写入纵向晋升账本")
    ap.add_argument("--record-baseline", help="把一份 results json 作为首条真实基线锚点写入账本")
    ap.add_argument("--record-note", default="", help="账本条目备注")
    ap.add_argument("--ledger-view", action="store_true", help="打印纵向晋升账本")
    ap.add_argument("--cohort-report", action="store_true", help="报告题库分片(cohort)轮换构成与季度轮换策略")
    ap.add_argument("--capability-report", nargs="?", const="__STRUCTURE__", metavar="RESULTS_JSON",
                    help="报告能力画像（各 capability 轴题数/覆盖/均分）；给 results.json 时附每轴均分并定位最弱轴")
    ap.add_argument("--propose-mutations", metavar="RESULTS_JSON",
                    help="据能力画像最弱轴 + 策略注册表，自提议针对性候选变异（排名+理由+下一步实验）")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--aggregate", nargs="+",
                    help="多 seed 聚合（预注册规则）：传入 K 份同配置 results json，逐题取中位数，重算 split/overall，写 --out。规则先于数据固定，防 p-hacking。")
    a = ap.parse_args()

    manifest = load_manifest()

    if a.verify:
        ok, bad = verify_hashes(manifest)
        print("HASH LOCK:", "OK" if ok else f"TAMPERED {bad}")
        sys.exit(0 if ok else 2)

    if a.selfcheck:
        r = selfcheck(manifest)
        print("SELFCHECK overall=%.3f dev=%.3f hidden=%.3f fresh=%.3f verified=%s" % (
            r["overall"], r["split"]["dev"], r["split"]["hidden"], r["split"]["fresh"], r["verified"]))
        print("Per-task:", r["scores"])
        return

    if a.score:
        subs = json.load(open(a.submissions, encoding="utf-8"))
        r = score_all(manifest, subs)
        if a.out:
            json.dump(r, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("SCORE overall=%.3f dev=%.3f hidden=%.3f fresh=%.3f verified=%s" % (
            r["overall"], r["split"]["dev"], r["split"]["hidden"], r["split"]["fresh"], r["verified"]))
        return

    if a.aggregate:
        # 预注册聚合规则（v6，先于数据固定）：
        #   1) 每题分数 = K 个 seed 分数的中位数（K 为偶数时取两中位均值）；
        #   2) split/overall 由聚合后的逐题分数重算；
        #   3) 所有输入必须 verified=True，否则中止；
        #   4) 聚合结果标注 seeds/aggregation，供账本审计。
        import statistics
        runs = []
        for f in a.aggregate:
            r = json.load(open(f, encoding="utf-8"))
            if not r.get("verified"):
                print("AGGREGATE ABORT: %s 未通过哈希校验" % f)
                sys.exit(2)
            runs.append(r)
        ids = [t["id"] for t in manifest["tasks"]]
        agg_scores = {}
        for tid in ids:
            vals = [r["scores"].get(tid, 0.0) for r in runs]
            agg_scores[tid] = round(statistics.median(vals), 3)
        split_sum = {"dev": [0, 0], "hidden": [0, 0], "fresh": [0, 0]}
        for t in manifest["tasks"]:
            split_sum[t["split"]][0] += agg_scores[t["id"]]
            split_sum[t["split"]][1] += 1
        out = {
            "scores": agg_scores,
            "split": {k: round(v[0] / v[1], 3) if v[1] else 0.0 for k, v in split_sum.items()},
            "overall": round(sum(agg_scores.values()) / len(agg_scores), 3),
            "verified": True,
            "seeds": len(runs),
            "aggregation": "per-task median (pre-registered v6)",
            "seed_files": [os.path.basename(f) for f in a.aggregate],
        }
        if a.out:
            json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("AGGREGATE K=%d overall=%.3f dev=%.3f hidden=%.3f fresh=%.3f -> %s" % (
            len(runs), out["overall"], out["split"]["dev"], out["split"]["hidden"], out["split"]["fresh"], a.out or "(stdout)"))
        # 逐题方差报告：跨 seed 不一致的题（存在生成方差）
        unstable = []
        for tid in ids:
            vals = [r["scores"].get(tid, 0.0) for r in runs]
            if max(vals) - min(vals) > 1e-9:
                unstable.append((tid, vals))
        print("UNSTABLE tasks (跨 seed 分数不一致): %d" % len(unstable))
        for tid, vals in unstable:
            print("  %s: %s -> median=%.3f" % (tid, vals, agg_scores[tid]))
        return

    if a.snapshot:
        snap = os.path.join(BASE, "assets", ".bench_snapshot.json")
        shutil.copy(MANIFEST, snap)
        print("SNAPSHOT saved ->", snap)
        return

    if a.rollback:
        snap = os.path.join(BASE, "assets", ".bench_snapshot.json")
        if not os.path.exists(snap):
            print("ROLLBACK: NO SNAPSHOT FOUND")
            sys.exit(2)
        shutil.copy(snap, MANIFEST)
        ok, _ = verify_hashes(load_manifest())
        print("ROLLBACK done -> restored from snapshot; HASH LOCK:", "OK" if ok else "TAMPERED")
        return

    if a.ledger_view:
        if os.path.exists(LEDGER):
            data = json.load(open(LEDGER, encoding="utf-8"))
            print("LEDGER entries: %d" % len(data))
            for i, e in enumerate(data, 1):
                # 非门控条目（如 CAPABILITY_EXTEND / BASELINE）字段可能为 None，逐项容错格式化
                def _f(x, spec, dash="—"):
                    return (spec % x) if isinstance(x, (int, float)) else dash
                bp = e.get("baseline_pass"); cp = e.get("candidate_pass"); n = e.get("n")
                passes = ("%s/%s -> %s/%s" % (bp, n, cp, n)) if bp is not None and cp is not None else "—"
                print("  #%d %s | decision=%s | delta=%s | p=%s | CI=[%s,%s] | pass=%s" % (
                    i, e.get("ts"), e.get("decision"), _f(e.get("delta_overall"), "%.3f"),
                    _f(e.get("p_value"), "%.4f"), _f(e.get("ci_low"), "%.3f"),
                    _f(e.get("ci_high"), "%.3f"), passes))
        else:
            print("LEDGER empty (no entries yet)")
        return

    if a.cohort_report:
        tasks = manifest["tasks"]
        # 按 cohort 聚合：题数、split 分布、状态
        from collections import defaultdict
        by_cohort = defaultdict(lambda: {"n": 0, "splits": defaultdict(int), "status": set(), "ids": []})
        for t in tasks:
            co = t.get("cohort", "(none)")
            by_cohort[co]["n"] += 1
            by_cohort[co]["splits"][t["split"]] += 1
            by_cohort[co]["status"].add(t.get("cohort_status", "unknown"))
            by_cohort[co]["ids"].append(t["id"])
        pol = manifest.get("evaluation_policy", {}).get("rotation_policy", {})
        print("COHORT REPORT (共 %d 题, %d 个 cohort)" % (len(tasks), len(by_cohort)))
        for co in sorted(by_cohort):
            d = by_cohort[co]
            splits = ", ".join("%s=%d" % (k, v) for k, v in sorted(d["splits"].items()))
            print("  [%s] n=%d status=%s | %s" % (
                co, d["n"], "/".join(sorted(d["status"])), splits))
            print("       ids: %s" % ", ".join(d["ids"]))
        if pol:
            print("ROTATION POLICY: enable=%s granularity=%s window=%s季度" % (
                pol.get("enable"), pol.get("granularity"), pol.get("window_quarters")))
            print("  active_cohorts  = %s" % pol.get("active_cohorts"))
            print("  archived_cohorts= %s" % pol.get("archived_cohorts"))
            print("  rule: %s" % pol.get("rule", ""))
        else:
            print("ROTATION POLICY: (未配置)")
        return

    if a.capability_report:
        AXES = ["fact_recall", "selective_retrieval", "reasoning",
                "structured_output", "reading_comprehension"]
        cap_of = {t["id"]: t.get("capability", "selective_retrieval") for t in manifest["tasks"]}
        n_by = {ax: 0 for ax in AXES}
        for t in manifest["tasks"]:
            n_by[cap_of[t["id"]]] = n_by.get(cap_of[t["id"]], 0) + 1
        res = None
        if a.capability_report != "__STRUCTURE__":
            res = json.load(open(a.capability_report, encoding="utf-8"))["scores"]
        print("CAPABILITY REPORT (共 %d 题, %d 轴)%s" % (
            len(manifest["tasks"]), len([x for x in AXES if n_by[x]]),
            "" if res is None else "  results=%s" % os.path.basename(a.capability_report)))
        rows = []
        for ax in AXES:
            n = n_by[ax]
            if res is None:
                print("  [%-21s] n=%d" % (ax, n))
                continue
            sc = [res[t["id"]] for t in manifest["tasks"] if cap_of[t["id"]] == ax and t["id"] in res]
            cov = (len(sc) / n) if n else 0.0
            mean = (sum(sc) / len(sc)) if sc else float("nan")
            rows.append((ax, n, len(sc), cov, mean))
            mean_s = "n/a " if not sc else "%.3f" % mean
            print("  [%-21s] n=%2d  scored=%d  cov=%.0f%%  mean=%s" % (
                ax, n, len(sc), cov * 100, mean_s))
        if res is not None and rows:
            # 关注排序：先"欠测量"(覆盖低)，再"欠表现"(均分低)。priority 越小越该补。
            def prio(r):
                _, n, scored, cov, mean = r
                m = 1.0 if mean != mean else mean  # nan -> 视为满(不因未测判低分)，靠 cov 反映
                return (round(cov, 3), round(m, 3))
            weak = sorted(rows, key=prio)[0]
            reason = "欠测量(覆盖%.0f%%)" % (weak[3] * 100) if weak[3] < 1.0 else "欠表现(均分%.3f)" % weak[4]
            print("WEAKEST AXIS -> %s  [%s]" % (weak[0], reason))
            print("  建议：`python eval_self_evolution.py --propose-mutations %s` 获取针对性候选变异。" %
                  os.path.basename(a.capability_report))
        return

    if a.propose_mutations:
        AXES = ["fact_recall", "selective_retrieval", "reasoning",
                "structured_output", "reading_comprehension"]
        cap_of = {t["id"]: t.get("capability", "selective_retrieval") for t in manifest["tasks"]}
        n_by = {ax: 0 for ax in AXES}
        for t in manifest["tasks"]:
            n_by[cap_of[t["id"]]] = n_by.get(cap_of[t["id"]], 0) + 1
        res = json.load(open(a.propose_mutations, encoding="utf-8"))["scores"]
        rows = []
        for ax in AXES:
            n = n_by[ax]
            sc = [res[t["id"]] for t in manifest["tasks"] if cap_of[t["id"]] == ax and t["id"] in res]
            cov = (len(sc) / n) if n else 0.0
            mean = (sum(sc) / len(sc)) if sc else 1.0  # 未测不判低分，靠覆盖反映
            rows.append((ax, n, len(sc), cov, mean))
        weak = sorted(rows, key=lambda r: (round(r[3], 3), round(r[4], 3)))[0]
        weak_ax = weak[0]
        under_measured = weak[3] < 1.0
        reg_path = os.path.join(os.path.dirname(MANIFEST), "strategy_registry.json")
        reg = json.load(open(reg_path, encoding="utf-8"))
        promoted = set(reg.get("promoted", []))
        gr, cr = reg["gain_rank"], reg["cost_rank"]
        cands = [s for s in reg["strategies"]
                 if s["target_axis"] == weak_ax and s["id"] not in promoted and not s.get("promoted")]
        cands.sort(key=lambda s: (-gr.get(s["expected_gain"], 0), cr.get(s["cost"], 9)))
        print("PROPOSE-MUTATIONS  (源画像=%s)" % os.path.basename(a.propose_mutations))
        print("  最弱轴 = %s  | 覆盖=%.0f%% 均分=%s | 判据=%s" % (
            weak_ax, weak[3] * 100, ("%.3f" % weak[4]) if weak[2] else "n/a",
            "欠测量：该轴部分题尚未盲测，须先补测建立基线" if under_measured else "欠表现：该轴均分偏低"))
        if under_measured:
            missing = [t["id"] for t in manifest["tasks"]
                       if cap_of[t["id"]] == weak_ax and t["id"] not in res]
            print("  [步骤0·先补测] 下轮闭环须对未测题做 K=5 盲测建立基线：%s" % ", ".join(missing))
        if not cands:
            print("  无对口未晋升候选（该轴策略或已全部晋升）。")
        else:
            print("  候选变异（按预期收益↓、成本↑ 排名）：")
            for i, s in enumerate(cands, 1):
                print("   #%d %s  [收益=%s 成本=%s]" % (i, s["id"], s["expected_gain"], s["cost"]))
                print("      机制: %s" % s["mechanism"])
                if s.get("note"):
                    print("      备注: %s" % s["note"])
            top = cands[0]
            print("  [下一步实验] 对候选配置施加策略 %s，按 K=5 协议双跑后送门：" % top["id"])
            print("      python eval_self_evolution.py --gate --baseline results_baseline_agg5.json \\")
            print("          --candidate results_%s_agg5.json --record --record-note \"试验 %s 补强 %s 轴\"" % (
                top["id"], top["id"], weak_ax))
        print("  硬边界：本命令只读能力画像聚合分（非 hidden/fresh 题面），只提议不改答案；"
              "候选须经统计显著性门(McNemar p<0.05 且 CI 下界>0)才可晋升。")
        return

    if a.record_baseline:
        r = json.load(open(a.record_baseline, encoding="utf-8"))
        if not r.get("verified"):
            print("RECORD-BASELINE: ABORT — 结果未通过哈希校验")
            sys.exit(2)
        pp = per_question_pass(manifest, r)
        n = len(pp); n_pass = sum(1 for v in pp.values() if v)
        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "type": "baseline_measurement",
            "baseline_overall": r["overall"], "candidate_overall": r["overall"],
            "split": r.get("split", {}),
            "n": n, "baseline_pass": n_pass, "candidate_pass": n_pass,
            "delta_overall": 0.0, "p_value": 1.0, "ci_low": 0.0, "ci_high": 0.0,
            "disc_base_pass_cand_fail": 0, "disc_base_fail_cand_pass": 0,
            "decision": "BASELINE", "license": None,
            "note": a.record_note or "首条真实基线锚点（闭卷盲测）"
        }
        append_ledger(entry)
        print("RECORD-BASELINE: overall=%.3f pass=%d/%d -> appended as ledger entry #%d (decision=BASELINE)" % (
            r["overall"], n_pass, n, len(json.load(open(LEDGER, encoding="utf-8")))))
        return

    if a.gate:
        b = json.load(open(a.baseline, encoding="utf-8"))
        c = json.load(open(a.candidate, encoding="utf-8"))
        if not (b.get("verified") and c.get("verified")):
            print("GATE: ABORT — 基线或候选未通过哈希校验")
            sys.exit(2)
        bd = b["split"].get("dev", 0.0); bh = b["split"].get("hidden", 0.0); bf = b["split"].get("fresh", 0.0)
        cd = c["split"].get("dev", 0.0); ch = c["split"].get("hidden", 0.0); cf = c["split"].get("fresh", 0.0)
        d_dev = round(cd - bd, 3); d_hid = round(ch - bh, 3); d_fr = round(cf - bf, 3)
        d_all = round(c["overall"] - b["overall"], 3)
        # 逐题通过率（配对 McNemar 检验）
        pb = per_question_pass(manifest, b); pc = per_question_pass(manifest, c)
        ids = list(pb.keys())
        b_pass = sum(1 for i in ids if pb[i]); c_pass = sum(1 for i in ids if pc[i])
        disc_b = sum(1 for i in ids if pb[i] and not pc[i])   # 基线过、候选挂
        disc_c = sum(1 for i in ids if not pb[i] and pc[i])   # 基线挂、候选过
        p_val, _, _ = mcnemar_exact(disc_b, disc_c)
        ci_lo, ci_hi = bootstrap_delta_ci(b["scores"], c["scores"])
        # 多目标门：safety + license
        safety = c.get("safety_violations", 0)
        lic_block = False; lic_name = None
        if a.license_report and os.path.exists(a.license_report):
            lr = json.load(open(a.license_report, encoding="utf-8"))
            lic_name = lr.get("license")
            if not license_allowed(lic_name):
                lic_block = True
        # v6 回归判据（预注册，2026-07-24；基于 K=3 多 seed 实测噪声底 sd(hidden mean)≈0.030-0.037）：
        #   旧判据 raw-mean < -0.001 远低于噪声底，会把生成方差误报为回归（v5 的 T020 教训）。
        #   新判据：hidden/fresh 上存在 pass->fail 翻转（聚合后仍翻，视为真回归），
        #           或 split 均值回退超过噪声底容差 NOISE_FLOOR=0.05（≈1.5×sd）。
        NOISE_FLOOR = 0.05
        split_of = {t["id"]: t["split"] for t in manifest["tasks"]}
        flip_hidfr = [i for i in ids if split_of[i] in ("hidden", "fresh") and pb[i] and not pc[i]]
        regress = bool(flip_hidfr) or (d_hid < -NOISE_FLOOR) or (d_fr < -NOISE_FLOOR)
        # 统计显著性门：PROMOTE 需 delta>0 且 p<0.05 且 CI 下界>0
        if lic_block:
            decision = "BLOCK_LICENSE"
        elif regress:
            decision = "REVERT"
        elif safety != 0:
            decision = "REVERT"
        elif c_pass <= b_pass:
            decision = "REVERT"
        elif p_val < 0.05 and ci_lo > 0:
            decision = "PROMOTE"
        else:
            decision = "HOLD"   # 正向变化但不显著，暂缓晋升
        # 成本/延迟报告（可选，若提交结果携带）
        cost_delta = round(c.get("cost", 0) - b.get("cost", 0), 3) if ("cost" in b or "cost" in c) else None
        lat_delta = round(c.get("latency_p95", 0) - b.get("latency_p95", 0), 3) if ("latency_p95" in b or "latency_p95" in c) else None
        print("GATE decision=%s" % decision)
        print("  baseline : dev=%.3f hidden=%.3f fresh=%.3f overall=%.3f pass=%d/%d" % (bd, bh, bf, b["overall"], b_pass, len(ids)))
        print("  candidate: dev=%.3f hidden=%.3f fresh=%.3f overall=%.3f pass=%d/%d" % (cd, ch, cf, c["overall"], c_pass, len(ids)))
        print("  delta    : dev=%+.3f hidden=%+.3f fresh=%+.3f overall=%+.3f" % (d_dev, d_hid, d_fr, d_all))
        print("  McNemar  : discordant(b,c)=(%d,%d) p=%.4f | bootstrap CI95 of overall-delta=[%.3f, %.3f]" % (disc_b, disc_c, p_val, ci_lo, ci_hi))
        print("  safety_violations(candidate)=%s" % safety)
        if cost_delta is not None: print("  cost delta=%+.3f" % cost_delta)
        if lat_delta is not None: print("  latency_p95 delta=%+.3f" % lat_delta)
        if lic_block:
            print("  原因：候选 license=%s 命中 block/未知，依 license_policy 拒绝晋升。" % lic_name)
        elif regress:
            print("  原因：隐藏集或新鲜集回归（pass->fail 翻转题=%s；均值回退阈=%.2f），可能过拟合或破坏既有能力。" % (flip_hidfr or "无", NOISE_FLOOR))
        elif safety != 0:
            print("  原因：候选触发安全违规。")
        elif decision == "HOLD":
            print("  原因：正向变化但未达统计显著（p>=0.05 或 CI 下界<=0），暂缓晋升。")
        if a.record:
            entry = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "baseline_overall": b["overall"], "candidate_overall": c["overall"],
                "n": len(ids), "baseline_pass": b_pass, "candidate_pass": c_pass,
                "delta_overall": d_all, "p_value": round(p_val, 4),
                "ci_low": ci_lo, "ci_high": ci_hi,
                "disc_base_pass_cand_fail": disc_b, "disc_base_fail_cand_pass": disc_c,
                "decision": decision, "license": lic_name,
                "note": a.record_note or ""
            }
            append_ledger(entry)
            print("  LEDGER: appended entry #%d" % len(json.load(open(LEDGER, encoding="utf-8"))))
        return


if __name__ == "__main__":
    main()

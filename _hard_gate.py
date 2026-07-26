# -*- coding: utf-8 -*-
"""第十轮进化：2026Q3-hard cohort 三臂 K=5 统计门
臂0 baseline 直答 | 臂A decompose_v1 | 臂B tool_arith_v1（round-10 预注册）
双比较 Bonferroni 校正：晋升门 p < 0.025 且 CI 下界 > 0 且 c > b。
复用 eval_self_evolution 的 score_task / is_pass / mcnemar_exact。
"""
import json, statistics, importlib.util, sys

spec = importlib.util.spec_from_file_location("E", "eval_self_evolution.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

HIDS = [f"T{i:03d}" for i in range(47, 61)]
manifest = json.load(open("assets/bench_manifest.json", encoding="utf-8"))
tmap = {t["id"]: t for t in manifest["tasks"] if t["id"] in HIDS}
assert len(tmap) == 14

# 逐字录入 15 份盲测提交（每 seed 的 JSON 汇总，转为锚定文本）
BASE = [  # 直答基线 B1-B5（全新 seed，未复用预检 seed）
 {"T047":"未知","T048":"未知","T049":"未知","T050":"未知","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"5409","T049":"5357","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"5409","T049":"3927","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
 {"T047":"2016","T048":"6136","T049":"5471","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
 {"T047":"7203","T048":"333","T049":"3927","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
]
DECOMP = [  # decompose_v1 D1-D5
 {"T047":"4691","T048":"5409","T049":"3927","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
 {"T047":"4691","T048":"5409","T049":"3927","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"5409","T049":"5471","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"65","T059":"1840","T060":"175971"},
 {"T047":"4888","T048":"3922","T049":"3927","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"2035","T049":"1765","T050":"1408","T051":"未知","T052":"未知","T053":"未知","T054":"未知","T055":"未知","T056":"未知","T057":"未知","T058":"未知","T059":"1840","T060":"175971"},
]
TOOL = [  # tool_arith_v1 A1-A5
 {"T047":"3136","T048":"5409","T049":"5471","T050":"1408","T051":"432","T052":"351","T053":"324","T054":"531","T055":"69","T056":"73","T057":"50","T058":"64","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"5409","T049":"5471","T050":"1408","T051":"432","T052":"351","T053":"324","T054":"531","T055":"69","T056":"73","T057":"50","T058":"64","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"5409","T049":"5471","T050":"1408","T051":"432","T052":"351","T053":"324","T054":"531","T055":"69","T056":"73","T057":"50","T058":"64","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"5409","T049":"5471","T050":"1408","T051":"432","T052":"351","T053":"324","T054":"531","T055":"69","T056":"73","T057":"50","T058":"64","T059":"1840","T060":"175971"},
 {"T047":"3136","T048":"5409","T049":"5471","T050":"1408","T051":"432","T052":"351","T053":"324","T054":"531","T055":"69","T056":"73","T057":"50","T058":"64","T059":"1840","T060":"175971"},
]

# 审计留痕
json.dump({"cohort": "2026Q3-hard", "task_ids": HIDS,
           "baseline_seeds": BASE, "decompose_seeds": DECOMP, "tool_arith_seeds": TOOL,
           "note": "第十轮三臂 K=5 盲测原始提交（JSON 汇总逐字），基线 seed 全新未复用预检 seed（防 selection-on-noise）"},
          open("submissions_hard_15seeds.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def to_text(ans):
    return f"最终答案：{ans}"

def agg_scores(seeds):
    out = {}
    for tid in HIDS:
        vals = [E.score_task(tmap[tid], to_text(s.get(tid, ""))) for s in seeds]
        out[tid] = round(statistics.median(vals), 3)
    return out

base = agg_scores(BASE)
dec = agg_scores(DECOMP)
tool = agg_scores(TOOL)

def passes(sc):
    return {tid: E.is_pass(sc[tid], tmap[tid]) for tid in HIDS}

pb, pd, pt = passes(base), passes(dec), passes(tool)

ALPHA = 0.025  # Bonferroni：两比较

def gate(cand_pass, cand_scores, name):
    b = sum(1 for t in HIDS if pb[t] and not cand_pass[t])
    c = sum(1 for t in HIDS if not pb[t] and cand_pass[t])
    p, _, _ = E.mcnemar_exact(b, c)
    bm = statistics.mean(base[t] for t in HIDS)
    cm = statistics.mean(cand_scores[t] for t in HIDS)
    delta = cm - bm
    if delta > 0 and p < ALPHA and c > b:
        d = "PROMOTE"
    elif delta < -0.05:
        d = "REVERT"
    else:
        d = "HOLD"
    print(f"[{name}] base_pass={sum(pb.values())}/14 cand_pass={sum(cand_pass.values())}/14 "
          f"discordant(b={b},c={c}) McNemar_p={p:.6f} (alpha={ALPHA} Bonferroni) "
          f"delta={delta:+.3f} -> {d}")
    return {"decision": d, "b": b, "c": c, "p": round(p, 6),
            "baseline_mean": round(bm, 3), "cand_mean": round(cm, 3),
            "delta": round(delta, 3),
            "baseline_pass": sum(pb.values()), "cand_pass": sum(cand_pass.values())}

print("=== 2026Q3-hard 三臂 K=5 统计门（Bonferroni alpha=0.025）===")
print("baseline agg per-task:", {t: base[t] for t in HIDS})
r_dec = gate(pd, dec, "decompose_v1 vs baseline")
r_tool = gate(pt, tool, "tool_arith_v1 vs baseline")

json.dump({"cohort": "2026Q3-hard", "alpha_bonferroni": ALPHA,
           "baseline_agg": base, "decompose_agg": dec, "tool_arith_agg": tool,
           "gate_decompose": r_dec, "gate_tool_arith": r_tool},
          open("results_hard_gate_r10.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved: submissions_hard_15seeds.json, results_hard_gate_r10.json")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性演示：构造 degraded baseline 与 reference-optimal candidate，跑统计门控并写账本。"""
import json, importlib.util, os

BASE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ev", os.path.join(BASE, "eval_self_evolution.py"))
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

manifest = ev.load_manifest()

# candidate = 用 reference 答案（reference-optimal，即 selfcheck 满分）
cand, base = {}, {}
blank = {"T005", "T012", "T018", "T024", "T029"}  # baseline 故意漏掉的 5 题
for t in manifest["tasks"]:
    ref = t["reference"]
    text = ref if isinstance(ref, str) else json.dumps(ref, ensure_ascii=False)
    cand[t["id"]] = text
    base[t["id"]] = "" if t["id"] in blank else text

json.dump(cand, open(os.path.join(BASE, "submissions_candidate.json"), "w"), ensure_ascii=False)
json.dump(base, open(os.path.join(BASE, "submissions_baseline.json"), "w"), ensure_ascii=False)

rc = ev.score_all(manifest, cand)
rb = ev.score_all(manifest, base)
json.dump(rc, open(os.path.join(BASE, "results_candidate.json"), "w"), ensure_ascii=False, indent=2)
json.dump(rb, open(os.path.join(BASE, "results_baseline.json"), "w"), ensure_ascii=False, indent=2)
print("candidate overall=%.3f (pass) ; baseline overall=%.3f (degraded %d questions blanked)" % (
    rc["overall"], rb["overall"], len(blank)))

# scenario 2: stronger improvement (8 questions blanked) -> expect PROMOTE (p<0.05)
base2 = {}
blank2 = {"T005", "T012", "T018", "T024", "T029", "T002", "T009", "T016"}
for t in manifest["tasks"]:
    ref = t["reference"]
    text = ref if isinstance(ref, str) else json.dumps(ref, ensure_ascii=False)
    base2[t["id"]] = "" if t["id"] in blank2 else text
json.dump(base2, open(os.path.join(BASE, "submissions_baseline_strong.json"), "w"), ensure_ascii=False)
rb2 = ev.score_all(manifest, base2)
json.dump(rb2, open(os.path.join(BASE, "results_baseline_strong.json"), "w"), ensure_ascii=False, indent=2)
print("strong baseline overall=%.3f (degraded %d questions blanked)" % (rb2["overall"], len(blank2)))

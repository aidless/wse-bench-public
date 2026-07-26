#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cluster-bootstrap 95% CI for the marginal pass-rate diff of #33, faithful to
the r18 preregistration rule ('overall-delta bootstrap CI lower > 0').
Resamples TASKS (clusters) with replacement, recomputes d=(c-b)/N over the
resampled per-seed pairs. Also reports the bootstrap-t version."""
import json
import numpy as np

RNG = np.random.default_rng(20260725)
B = 20000

cand = json.load(open('results_r27_strict_grounding_k5.json'))
base = json.load(open('results_ablation_30q_k5.json'))
tasks = sorted(cand.keys())

# build per-task pair arrays: +1 if (base fail, cand pass), -1 if (base pass, cand fail), 0 otherwise
task_pairs = {}
for t in tasks:
    cb = {r['seed']: r['is_pass'] for r in cand[t]}
    bb = {r['seed']: r['is_pass'] for r in base[t]}
    arr = []
    for seed in cb:
        if seed in bb:
            bp, cp = bb[seed], cb[seed]
            if (not bp) and cp:
                arr.append(1)      # favors candidate
            elif bp and (not cp):
                arr.append(-1)     # favors baseline
            else:
                arr.append(0)      # concordant
    task_pairs[t] = np.array(arr, dtype=np.int64)

def delta_of(clusters):
    allv = np.concatenate(clusters)
    return allv.sum() / allv.size   # (c - b) / N

obs = delta_of([task_pairs[t] for t in tasks])
print(f"observed delta (c-b)/N = {obs:+.4f} ({obs*100:+.1f}%)")

boot = np.empty(B)
for i in range(B):
    idx = RNG.integers(0, len(tasks), len(tasks))
    clusters = [task_pairs[tasks[j]] for j in idx]
    boot[i] = delta_of(clusters)

lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"cluster-bootstrap 95% CI = [{lo:+.4f}, {hi:+.4f}]  ({(lo*100):+.1f}%, {(hi*100):+.1f}%)")
print(f"CI lower > 0 ? {bool(lo > 0)}   -> preregistration promotion rule satisfied: {bool(lo > 0 and obs > 0)}")
frac_le0 = float((boot <= 0).mean())
print(f"fraction of bootstrap deltas <= 0 (bootstrap 1-sided p) = {frac_le0:.4f}")
print(f"bootstrap SE = {boot.std():.4f}")

# bootstrap-t (studentized) using bootstrap SE
se = boot.std()
t_boot = (boot - obs) / se
t_lo, t_hi = np.percentile(t_boot, [2.5, 97.5])
bc_lo, bc_hi = obs - t_hi * se, obs - t_lo * se
print(f"bootstrap-t 95% CI = [{bc_lo:+.4f}, {bc_hi:+.4f}]")

json.dump(dict(observed=float(obs), boot_ci=[float(lo), float(hi)], boot_se=float(se),
               boot_onesided_p=frac_le0,
               boot_t_ci=[float(bc_lo), float(bc_hi)], prereg_rule_pass=bool(lo > 0)),
          open('_r28_bootstrap_ci.json', 'w'), indent=2)
print("wrote _r28_bootstrap_ci.json")

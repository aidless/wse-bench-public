#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r28 — Effect-size / 95% CI / statistical-power analysis for the two strict
McNemar confirmations (#32 RC_V4_CONFIRM, #33 R27_STRICT_ABLATION) plus the
STRATEGY_AUDIT_V4 necessity margins.

Goals (per approved plan 1.2):
  1. Empirically VERIFY #33 by pairing the two per-seed result files
     (candidate +grounding vs baseline -grounding) and recomputing b/c/p.
  2. Report Cohen's g, discordant odds ratio, and exact conditional 95% CI
     for both McNemar confirms.
  3. Statistical power: post-hoc (observed effect) + prospective n for 80/90%.
  4. STRATEGY_AUDIT_V4 per-strategy necessity margins vs NOISE_FLOOR.

Convention (stated explicitly for the reader):
  b = #(baseline pass, candidate FAIL)   -- discordant, favors baseline
  c = #(baseline FAIL, candidate pass)   -- discordant, favors candidate(+grounding)
  k = b + c                              -- total discordant pairs (McNemar uses k)
  Cohen's g = (b - c) / (b + c)          -- negative => candidate better
  Odds ratio (candidate/baseline) = c/b  -- >1 => candidate better
  Marginal pass-rate diff  d = (c - b) / N_total_pairs
"""
import json, math
import numpy as np
from scipy import stats

ALPHA = 0.05
RNG = np.random.default_rng(20260725)
N_SIM = 20000

def exact_mcnemar_two_sided(b, c):
    """Exact two-sided McNemar p via Binomial(k=b+c, 0.5) on the smaller cell."""
    k = b + c
    m = min(b, c)
    # P(X <= m) under Bin(k,0.5); two-sided doubles (symmetry)
    p_low = stats.binom.cdf(m, k, 0.5)
    return 2.0 * p_low

def cohens_g(b, c):
    return (b - c) / (b + c)

def or_disc(b, c):
    """Candidate/baseline discordant odds ratio = c/b."""
    return c / b if b > 0 else float('inf')

def or_ci_exact(b, c, alpha=ALPHA):
    """Exact conditional 95% CI for theta = b/c (Miettinen/F-distribution).
    Returns (L_theta, U_theta) for theta=b/c; report OR=c/b with reciprocal CI."""
    dfn_u, dfd_u = 2 * (c + 1), 2 * b      # for L_theta
    dfn_v, dfd_v = 2 * (b + 1), 2 * c      # for U_theta
    F_u = stats.f.ppf(1 - alpha / 2, dfn_u, dfd_u)
    F_v = stats.f.ppf(1 - alpha / 2, dfn_v, dfd_v)
    L = b / ((c + 1) * F_u)
    U = ((b + 1) * F_v) / c
    return L, U

def or_ci_norm(b, c, bias_correct=True):
    """Normal-approx CI on log OR = log(c/b). SE = sqrt(1/b + 1/c) (or +0.5 BC)."""
    if b == 0 or c == 0:
        return (float('nan'), float('nan'))
    if bias_correct:
        se = math.sqrt(1.0 / (b + 0.5) + 1.0 / (c + 0.5))
    else:
        se = math.sqrt(1.0 / b + 1.0 / c)
    lor = math.log(c / b)
    return math.exp(lor - 1.96 * se), math.exp(lor + 1.96 * se)

def diff_ci(b, c, N):
    """95% CI for marginal pass-rate diff d=(c-b)/N (paired, normal approx)."""
    d = (c - b) / N
    se = math.sqrt((b + c) / (N ** 2) - ((b - c) ** 2) / (N ** 3))
    return d, d - 1.96 * se, d + 1.96 * se

def simulate_power(N_total, p_disc, q_cand, alpha=ALPHA, reps=N_SIM):
    """Simulate exact-McNemar power for a paired design.
    N_total pairs; each discordant w.p. p_disc; if discordant, candidate-pass w.p. q_cand.
    Returns (power, mean_b, mean_c, mean_k)."""
    rej = 0
    bs = np.empty(reps, dtype=np.int64)
    cs = np.empty(reps, dtype=np.int64)
    for i in range(reps):
        disc = RNG.random(N_total) < p_disc
        n_disc = int(disc.sum())
        cand_pass = RNG.random(n_disc) < q_cand
        b = int((~cand_pass).sum())   # baseline-pass / cand-fail
        c = int(cand_pass.sum())      # baseline-fail / cand-pass
        bs[i] = b; cs[i] = c
        k = b + c
        if k > 0:
            p = exact_mcnemar_two_sided(b, c)
            if p < alpha:
                rej += 1
    return rej / reps, bs.mean(), cs.mean(), (bs + cs).mean()

# ---------------------------------------------------------------------------
# PART 1 — Empirical verification of #33 (clean same-seed strict ablation)
# ---------------------------------------------------------------------------
print("=" * 72)
print("PART 1 — Empirical verification of ledger #33 (R27 strict ablation)")
print("=" * 72)

cand = json.load(open('results_r27_strict_grounding_k5.json'))
base = json.load(open('results_ablation_30q_k5.json'))
tasks = sorted(cand.keys())
assert set(tasks) == set(base.keys()), "task set mismatch"

b_cnt = c_cnt = 0
unpaired = 0
for t in tasks:
    cb = {r['seed']: r['is_pass'] for r in cand[t]}
    bb = {r['seed']: r['is_pass'] for r in base[t]}
    for seed in cb:
        if seed not in bb:
            unpaired += 1
            continue
        bp, cp = bb[seed], cb[seed]
        if bp and not cp:
            b_cnt += 1
        elif cp and not bp:
            c_cnt += 1
N_total = sum(len(cand[t]) for t in tasks)
k = b_cnt + c_cnt

p_emp = exact_mcnemar_two_sided(b_cnt, c_cnt)
print(f"  candidate arm tasks : {len(tasks)} ({tasks[0]}..{tasks[-1]})")
print(f"  total per-seed pairs: {N_total}  (K=5 x 16 tasks)")
print(f"  unpaired seeds      : {unpaired}")
print(f"  EMPIRICAL b (base+,cand-) = {b_cnt}")
print(f"  EMPIRICAL c (base-,cand+) = {c_cnt}")
print(f"  discordant k                = {k}")
print(f"  EMPIRICAL exact p (2-sided) = {p_emp:.6f}")
print(f"  LEDGER    b/c/p             = 14 / 29 / 0.031539")
print(f"  MATCH b/c : {b_cnt == 14 and c_cnt == 29}   MATCH p : {abs(p_emp - 0.031539) < 1e-3}")

# ---------------------------------------------------------------------------
# PART 2 — Effect sizes + 95% CI for both McNemar confirms
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("PART 2 — Effect sizes + exact 95% CI")
print("=" * 72)

# #33 from EMPIRICAL (verified) numbers
confirms = [
    ("#33 R27 strict ablation (T103-T118, K=5 same-seed)", b_cnt, c_cnt, N_total, True),
    ("#32 RC_V4 strict McNemar (30-task RC cohort, K=5+10 mixed)", 1, 8, 30, False),
]

eff_rows = []
for name, b, c, N, clean in confirms:
    g = cohens_g(b, c)
    orr = or_disc(b, c)
    L_t, U_t = or_ci_exact(b, c)
    L_or, U_or = or_ci_norm(b, c)
    # OR reported as candidate/baseline = c/b => CI = 1/U_t, 1/L_t
    or_lo_exact, or_hi_exact = 1.0 / U_t, 1.0 / L_t
    d, dlo, dhi = diff_ci(b, c, N)
    p = exact_mcnemar_two_sided(b, c)
    print(f"\n  [{name}]")
    print(f"    b={b}  c={c}  k={b+c}  exact p={p:.5f}  {'[VERIFIED]' if clean else '[stored]'}")
    print(f"    Cohen's g            = {g:+.4f}")
    print(f"    Odds ratio (cand/base) = {orr:.3f}   exact 95% CI = [{or_lo_exact:.3f}, {or_hi_exact:.3f}]")
    print(f"    (norm-approx 95% CI     = [{L_or:.3f}, {U_or:.3f}]  -- cross-check)")
    print(f"    Marginal pass diff d   = {d:+.4f}  ({(d*100):+.1f}%)  95% CI = [{dlo:+.4f}, {dhi:+.4f}]")
    eff_rows.append(dict(name=name, b=b, c=c, k=b+c, p=p, g=g, orr=orr,
                         or_lo=or_lo_exact, or_hi=or_hi_exact,
                         d=d, dlo=dlo, dhi=dhi, clean=clean))

# ---------------------------------------------------------------------------
# PART 3 — Statistical power
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("PART 3 — Statistical power")
print("=" * 72)

# #33 clean design: post-hoc (observed effect, observed n) + prospective half-effect
N33 = N_total                      # 80
p_disc33 = k / N33                 # discordant rate among pairs
q33 = c_cnt / k                    # prob discordant pair favors candidate
print(f"\n  [#33 clean design] N_total={N33}, p_disc={p_disc33:.4f}, q_cand={q33:.4f}")

post_hoc, mb, mc, mk = simulate_power(N33, p_disc33, q33, reps=N_SIM)
print(f"    Post-hoc power (observed effect, N={N33}): {post_hoc:.3f}")

# prospective: half the effect on log-OR scale
log_or_obs = math.log(q33 / (1 - q33)) - math.log(0.5 / 0.5)  # = log(q33/(1-q33)) since H0 q=0.5
# effect size on logit of discordant imbalance:
l0 = math.log(0.5 / (1 - 0.5))      # H0
l1 = math.log(q33 / (1 - q33))      # observed
l_half = 0.5 * (l1 - l0) + l0
q_half = 1.0 / (1.0 + math.exp(-l_half))
print(f"    Half-effect q_cand = {q_half:.4f}")
K_SEED = 5
for target in (0.80, 0.90):
    # find smallest N with simulated power >= target
    found = None
    for N in range(20, 2000, 10):
        pw, _, _, _ = simulate_power(N, p_disc33, q_half, reps=4000)
        if pw >= target:
            found = N
            break
    if found is None:
        print(f"    Prospective n for {int(target*100)}% power (half effect): >2000 pairs "
              f"(≈ >{2000//K_SEED} tasks @K=5)")
    else:
        print(f"    Prospective n for {int(target*100)}% power (half effect): ~{found} pairs "
              f"(≈ {math.ceil(found/K_SEED)} tasks @K=5)")

# #32: power indeterminate (K-inconsistent, task-aggregated). State explicitly.
print(f"\n  [#32 RC_V4] power NOT computable cleanly: design uses K=5+10 mixed,")
print(f"    task-aggregated b/c (b=1,c=8) with no per-pair raw file available.")
print(f"    Recommendation: re-run with same K (e.g. K=5) on 30 tasks for a")
print(f"    publishable power statement. Lower bound on detectable effect with")
print(f"    b=1,c=8 already achieved significance (p=0.039), so the *observed*")
print(f"    effect is real, but its precision (CI width) is wide (see Part 2).")

# ---------------------------------------------------------------------------
# PART 4 — STRATEGY_AUDIT_V4 necessity margins
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("PART 4 — STRATEGY_AUDIT_V4 necessity margins (vs NOISE_FLOOR=0.05)")
print("=" * 72)
NOISE = 0.05
v4 = [
    ("selective_retrieval_v1", 0.964, 0.688),
    ("tool_arith_v1",          1.000, 0.214),
    ("schema_guard_v1",        1.000, 0.750),
    ("self_verify_v1",         1.000, 0.667),
    ("citation_check_v1",      1.000, 0.683),
    ("verifier_v1",            1.000, 0.067),  # 5/6 tasks baseline 0/3 -> verifier recovers
]
print(f"  {'strategy':<22}{'from':>7}{'to':>7}{'drop':>8}{'margin':>9}")
for name, frm, to in v4:
    drop = frm - to
    margin = drop / NOISE
    print(f"  {name:<22}{frm:>7.3f}{to:>7.3f}{drop:>8.3f}{margin:>8.1f}x")
print(f"  NOTE: single-run within-system ablations (no K repetition) -> magnitude")
print(f"        vs pre-registered noise floor; NO variance/CI. For a publishable")
print(f"        NECESSARY claim each removal needs K=5 replication to get SE + CI.")

# ---------------------------------------------------------------------------
# Persist machine-readable summary
# ---------------------------------------------------------------------------
summary = dict(
    verified_33=dict(b=b_cnt, c=c_cnt, k=k, N_total=N_total, p=p_emp,
                     match_ledger=(b_cnt == 14 and c_cnt == 29)),
    effect_sizes=[{k_: v_ for k_, v_ in r.items()} for r in eff_rows],
    power=dict(
        post_hoc_33=post_hoc, q_half_33=q_half,
        note_32="indeterminate (K-inconsistent); needs same-K replication"),
    v4_noise_floor=NOISE,
    v4_margins=[dict(strategy=n, drop=round(f - t, 3), margin=round((f - t) / NOISE, 1))
                for n, f, t in v4],
)
json.dump(summary, open('_r28_effectsize_summary.json', 'w'), ensure_ascii=False, indent=2)
print("\nWrote _r28_effectsize_summary.json")

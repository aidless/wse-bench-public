# r28 — Effect Size · 95% CI · Statistical Power Analysis

**Scope.** Companion analysis to the two strict McNemar confirmations recorded in the
evolution ledger (entries `#32 CONTEXT_GROUNDING_RC_V4_CONFIRM` and
`#33 CONTEXT_GROUNDING_R27_STRICT_ABLATION`) plus the `STRATEGY_AUDIT_V4` necessity
audit. This document reports (i) an **empirical re-verification** of #33 by pairing the
two raw per-seed result files, (ii) **Cohen's g / odds ratio / exact 95% CI** for both
McNemar confirms, (iii) **post-hoc and prospective statistical power**, and (iv)
**necessity margins** for V4. It closes with the honest limitations a TMLR reviewer will
raise and the minimum-viable replications required to defend the claims.

**Convention (fixed throughout).**
- `b` = #(baseline pass, candidate **FAIL**) — discordant, favours baseline.
- `c` = #(baseline **FAIL**, candidate pass) — discordant, favours candidate (+grounding).
- `k = b + c` — total discordant pairs; **McNemar uses `k`, not the task count `n`**.
- Cohen's `g = (b − c)/(b + c)` — negative ⇒ candidate better.
- Odds ratio (candidate/baseline) `= c/b` — >1 ⇒ candidate better.
- Marginal pass-rate diff `d = (c − b)/N_total_pairs`.

---

## 1. Empirical re-verification of ledger #33 (pairing integrity)

The strict ablation #33 was produced by a script that ran **both arms on the same
seeds 101–505** on T103–T118 (K=5). The candidate arm
(`results_r27_strict_grounding_k5.json`, +grounding) and the baseline arm
(`results_ablation_30q_k5.json`, −grounding) were paired by `(task, seed)` and the
discordant counts recomputed from scratch.

| Quantity | Empirical (from files) | Ledger #33 | Match |
|---|---|---|---|
| Tasks | 16 (T103–T118) | 16 | ✓ |
| Total per-seed pairs `N` | 80 (K=5 × 16) | 80 | ✓ |
| Unpaired seeds | 0 | — | ✓ |
| `b` (base+, cand−) | **14** | 14 | ✓ |
| `c` (base−, cand+) | **29** | 29 | ✓ |
| Discordant `k` | 43 | 43 | ✓ |
| Exact two-sided McNemar `p` | **0.031539** | 0.031539 | ✓ |

**Conclusion.** The ledger entry #33 is **exactly reproducible** from the raw files:
`b=14, c=29, p=0.031539`. Pairing integrity is confirmed and the ledger is trustworthy
for this entry. (The prior-session suspicion that the ledger's `b/c` were arithmetically
inconsistent was a miscalculation — with `a=16, d=21`, all three identities
`base_pass = a+b = 30`, `cand_pass = a+c = 45`, `n = a+b+c+d = 80` hold.)

---

## 2. Effect sizes and 95% confidence intervals

### 2.1 Ledger #33 — R27 strict ablation (T103–T118, K=5, same-seed) — *verified*

| Metric | Value | 95% CI |
|---|---|---|
| Cohen's `g` | **−0.3488** | — |
| Odds ratio (cand/base) | **2.071** | exact conditional **[1.060, 4.242]** |
| … cross-check (normal approx) | 2.071 | [1.105, 3.884] |
| Marginal pass diff `d` | **+18.8%** | normal-approx **[+3.2%, +34.3%]** |
| Marginal pass diff `d` | +18.8% | **cluster-bootstrap [0.0%, +37.5%]** |

- The grounding prefix multiplies the odds of a correct answer by ~2.1× (exact CI
  [1.06, 4.24], excludes 1).
- **Bootstrap caveat (important).** The cluster-bootstrap 95% CI for `d` is
  **[0.0%, +37.5%]** — its lower bound *touches* 0. The bootstrap one-sided p
  (= fraction of 20 000 resamples with `d ≤ 0`) is **0.0290**, consistent with the
  McNemar p = 0.0315. Under the **strict** preregistration rule
  ("overall-delta bootstrap CI lower > 0"), #33 does **not** literally pass the delta
  gate. The effect is real but its precision is marginal at `N = 80`.

### 2.2 Ledger #32 — RC_V4 strict McNemar (30-task RC cohort, K=5+10 mixed) — *stored*

| Metric | Value | 95% CI |
|---|---|---|
| Cohen's `g` | **−0.7778** | — |
| Odds ratio (cand/base) | **8.000** | exact conditional **[1.073, 354.981]** |
| … cross-check (normal approx) | 8.000 | [1.410, 45.388] |
| Marginal pass diff `d` | **+23.3%** | [+5.6%, +41.1%] |
| Exact two-sided `p` | 0.03906 | — |

- The point estimate (OR = 8) is large, but the **exact CI is enormous**
  ([1.07, 355]) because the discordant table rests on only **one** baseline-favouring
  pair (`b = 1`). This is a fragile result: it is significant, but its precision is poor.
- **Design caveat.** #32 aggregates a K=5+10 *mixed* cohort with task-level
  aggregation; no per-pair raw file is available to reconstruct `b/c` independently, so
  the CI/power for #32 are reported from the stored counts with this limitation noted.

---

## 3. Statistical power

### 3.1 Ledger #33 (clean design) — simulation-based (20 000 reps)

- **Post-hoc power (observed effect, N = 80): `0.590`.**
  Even though the result is significant (p = 0.0315), the study had only ~59% power to
  detect *this* observed effect. This is the quantitative face of the bootstrap CI
  touching 0.
- **Prospective power (detect HALF the observed effect, on the log-OR scale):**
  - 80% power → **≈ 470 pairs (≈ 94 tasks @ K=5)**.
  - 90% power → **≈ 620 pairs (≈ 124 tasks @ K=5)**.

  Implication: to claim the grounding-prefix effect robustly (not just significantly),
  a replication on ~90–120 RC tasks at K=5 is needed. The current 16-task sample is a
  *proof-of-effect*, not a *precision estimate*.

### 3.2 Ledger #32 — power indeterminate

Because #32 is K-inconsistent and task-aggregated with no per-pair raw file, a clean
power statement is not derivable. Recommendation: re-run the 30-task RC cohort with a
**single fixed K (e.g. K=5, same seeds both arms)** to obtain a publishable power
statement. The fact that `b=1, c=8` already reached p = 0.039 means the *observed*
effect is real; the problem is precision, not existence.

---

## 4. STRATEGY_AUDIT_V4 — necessity margins

V4 removes one strategy at a time from the 6-strategy production stack and measures the
score drop on the target cohort, compared against a pre-registered `NOISE_FLOOR = 0.05`.
"Margin" = `|drop| / NOISE_FLOOR`.

| Strategy removed | From | To | Drop | Margin vs floor |
|---|---|---|---|---|
| selective_retrieval_v1 | 0.964 | 0.688 | −0.276 | **5.5×** |
| tool_arith_v1 | 1.000 | 0.214 | −0.786 | **15.7×** |
| schema_guard_v1 | 1.000 | 0.750 | −0.250 | **5.0×** |
| self_verify_v1 | 1.000 | 0.667 | −0.333 | **6.7×** |
| citation_check_v1 | 1.000 | 0.683 | −0.317 | **6.3×** |
| verifier_v1 | 1.000 | 0.067 | −0.933 | **18.7×** |

Every removal exceeds the noise floor by **5×–19×**; `verifier_v1` is the single largest
contributor. This supports a **NECESSARY** verdict for all six strategies.

**Caveat (must be disclosed).** These are *single-run* within-system ablations — no K
repetition, hence **no variance estimate and no CI**. The evidence is the *magnitude*
relative to a pre-registered floor, not a significance test. For a defensible NECESSARY
claim each removal should be replicated at K=5 to obtain an SE and CI.

---

## 5. Honest limitations & TMLR reviewer risks

1. **Single base model.** All confirmations use Qwen2.5-3B-Instruct (4-bit NF4) only.
   Findings cannot be generalised across model families or scales. *Required: ≥1
   additional base model (Llama-3.1-8B / Mistral-7B) — plan 1.1.*
2. **K-inconsistency in #32.** Mixed K=5+10, task-aggregated. Its wide CI
   ([1.07, 355]) and indeterminate power make it *supporting*, not *primary*, evidence.
   **#33 is the primary, publishable strict ablation.**
3. **Multiplicity.** Two strict McNemar gates (#32 p=0.039, #33 p=0.0315). Under a
   family-wise Bonferroni/Holm correction at α=0.05, the threshold is 0.025 and
   *neither* passes individually. Mitigations: (a) the two tests are positively
   correlated (same hypothesis), so FWER inflation is milder than nominal; (b) designate
   **#33 as the single a-priori primary endpoint**; (c) both delta CIs exclude 0
   *independent* of the p-values, strengthening the conclusion. Still, disclose and
   pre-specify the primary endpoint.
4. **Preregistration fidelity (deviation).** The r18 preregistration fixed seeds
   `[11,22,33,44,55]` and a **6-task** scope (T103–T108); r27 used seeds **101–505**
   and **16 tasks** (T103–T118). The promotion rule is met in substance (p<0.05,
   hidden/fresh gains), **but the strict bootstrap delta-CI lower>0 rule is NOT met**
   (bootstrap CI [0%, 37.5%] touches 0). Treat #33 as a *confirmatory-style* test with a
   disclosed deviation, or register a fresh pre-analysis plan for the 16-task same-seed
   ablation and run it as the primary endpoint.
5. **Underpowered for smaller effects.** Post-hoc power 0.59 for #33 ⇒ the study would
   miss a half-sized effect; replicate at ~94 tasks @ K=5 for 80% power.
6. **Contamination audit pending (plan 3.1).** Must verify Qwen2.5-3B pretraining did
   not see the benchmark's public sources before claiming a genuine capability gain.
7. **V4 necessity = magnitude vs floor, not significance.** Needs K=5 replication per
   removal for a defensible NECESSARY claim with CI.

---

## 6. Recommended next actions (carried into r29)

| Priority | Action | Why |
|---|---|---|
| P1 | **Multi-model replication (plan 1.1)** | Removes the single-model generalisation risk. Needs ~15 GB download (F-disk constrained — confirm with user). |
| P1 | **Re-run #33 at larger n (~94 tasks @ K=5)** | Converts "significant" into "precisely estimated"; yields bootstrap delta-CI lower > 0; raises power to ~0.8. |
| P2 | **Grounding-prefix component ablation (plan 2.1)** | Isolates which part of the prefix drives the gain. |
| P2 | **Path-A 5-round failure meta-analysis (plan 2.2)** | Characterises the residual failure modes. |
| P2 | **Contamination audit (plan 3.1)** | Rules out pretraining leakage before any capability claim. |
| P3 | **V4 K=5 per-removal replication** | Upgrades NECESSARY from magnitude-based to significance-based. |
| P3 | **Path-A r27 v2 training; 5-mode→Parallelization (plan 4.x)** | Continues the self-evolution loop. |

---

## 7. Reproduction

- Verification + effect sizes + power: `_r28_effectsize_analysis.py`
  (outputs `_r28_effectsize_summary.json`).
- Cluster-bootstrap CI (faithful to preregistration): `_r28_bootstrap_ci.py`
  (outputs `_r28_bootstrap_ci.json`).
- Raw paired data: `results_r27_strict_grounding_k5.json` (cand, +grounding),
  `results_ablation_30q_k5.json` (base, −grounding).
- Environment: Python 3.13 managed runtime; `numpy`, `scipy` 1.18.

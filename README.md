# WSE-Bench — Eval-Gated Self-Evolution Benchmark

[![CI](https://github.com/aidless/wse-bench-public/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/aidless/wse-bench-public/actions/workflows/secret-scan.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)  [![Data](https://img.shields.io/badge/data-CC--BY--4.0-lightgrey.svg)](LICENSE-DATA)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Reproducible: seeds+prompts locked](https://img.shields.io/badge/reproducible-seeds%2Bprompts-locked-green.svg)]()

A 156-task benchmark + per-round evolution ledger + auditing toolkit designed
to evaluate **eval-gated self-evolution loops** on small LLMs. Each task is
graded by a deterministic rubric and admits paired McNemar testing across
candidate vs. baseline system prompts.

## Repo status: data + report release, not a runnable package

This is a **release repository**: the benchmark manifest, the ledger, the
audit reports, and the exact scripts that produced them. It ships **no
install entry point and no test suite** — running `pytest` here finds
nothing, by design. The reproduction scripts keep their original
author-machine paths (e.g. `F:\hf_cache`) as provenance records of how the
numbers were produced; treat them as documentation, not as a supported
CLI. The canonical entry point is regenerating on your own machine via
the reproduction scripts below.

## 60-second release audit

No install, no model:

```bash
git clone https://github.com/aidless/wse-bench-public && cd wse-bench-public
python3 demo.py
```

![release audit terminal demo](docs/assets/demo.gif)

The audit checks 153 hash-locked tasks, names the 3 documented redactions
(T029–T031), counts the 37 ledger entries, and reprints the r28 paired-test
summary. It is read-only and is not a benchmark run. Strict
`eval_self_evolution.py --verify` still refuses the 3 redacted tasks by design;
the demo classifies them, it does not bless them. Counts come from
[`assets/bench_manifest.json`](assets/bench_manifest.json) (156 tasks; 153 hash-locked + 3 redactions)
and [`assets/evolution_ledger.json`](assets/evolution_ledger.json) (37 entries).

## What this repo gives you

| Component | Where | Purpose |
|---|---|---|
| Benchmark manifest | `assets/bench_manifest.json` | 156 tasks across 14 cohorts (core / ext / fact / hard / rc{1-4} / reason / struct / sv / verify / 2026Q4-core / 2026Q4-protocol) |
| Deterministic grader | `eval_self_evolution.py` | `score_task`, `is_pass`, `PASS_THRESHOLD` |
| Audit harness | `audit_contamination.py`, `_audit_contamination_r28.py` | Detects prompt-leakage bugs and impossible-closedbook probes |
| Per-round ledger | `assets/evolution_ledger.json` | Append-only audit log of every promotion/revert decision (37 entries, r17 → r28) |
| Reproduction scripts | `_r28_*` (without leading underscore) | Large-n replication, prefix component ablation, multi-model harness, DPO training |
| Generation protocol | `eval_self_evolution.py` + `_r27_strict_ablation.py` | Qwen2.5-3B-Instruct 4-bit NF4, T=0.7, top_p=0.9, max_new=128, rep_pen=1.05 |
| Analysis tools | `_r28_effectsize_analysis.py`, `_r28_bootstrap_ci.py`, `_r28_effectsize_summary.json` | Effect-size + 95% CI + power for paired McNemar |
| Research notes | `EFFECT_SIZE_CI_POWER_r28_FINAL.md`, `PATH_A_META_ANALYSIS_r28.md`, `SELF_AUDIT_r25_r26.md`, etc. | Honest negative results, methodology, scope |

## What's *not* in this repo (intentionally)

- **Per-seed model outputs / submissions** — these contain T029-T031 answers that
  leak the original author's private KB scale/path. After de-anonymising those
  tasks to `REPLACE_WITH_YOUR_*` placeholders, regenerating on your own machine
  via the reproduction scripts is the canonical entry point.
- **Private agent session notes** (`HANDOFF_NEW_CONVERSATION.md`,
  `self-evolution-overview.md`, `peS2o-self-evo-digest.md`,
  `workbuddy-workflows.md`) — kept locally, never published.
- **One-off paper-discovery helpers** (`_batch*_papers.py`) — hard-coded to
  the original author's local KB; not useful outside that environment.
- **Model weights / HF cache** — too large; download via the scripts.

## Reproduce the headline results

The headline finding is **ledger entry #33**: a +18.8% absolute gain on 16
RC-tasks (T103-T118) under a single grounding-prefix intervention, measured
via paired McNemar (b=14, c=29, p=0.0315) on Qwen2.5-3B-Instruct 4-bit NF4.
Raw per-task rows are in [`results_r27_strict_grounding_k5.json`](results_r27_strict_grounding_k5.json);
the derived b/c/p and aggregates are in
[`r27_strict_ablation_analysis.json`](r27_strict_ablation_analysis.json).

To reproduce:

```bash
# 1. Install dependencies (a Linux/macOS shell or WSL; tested on Python 3.11)
python -m venv .venv && source .venv/bin/activate
pip install torch==2.5.1 transformers==4.57.3 bitsandbytes peft trl scipy

# 2. Download Qwen2.5-3B-Instruct (≈6 GB)
python _download_qwen3b.py --out F:/hf_cache/models/Qwen--Qwen2.5-3B-Instruct

# 3. Run the strict ablation (paired base vs cand, K=5 seeds, 16 tasks)
# NOTE: _r27_strict_ablation.py was not committed; cand-arm (with grounding prefix) results are preserved in results_r28_prefix_ablation_k5.json
# NOTE: _ablation_30q_k5.py was not committed (only a macOS "._" shadow file); base-arm results are in ablation_comparison_30q.json and results_ablation_30q_k5.json

# 4. Effect size + CI + power
python _r28_effectsize_analysis.py    # writes _r28_effectsize_summary.json
python _r28_bootstrap_ci.py           # cluster bootstrap (B=20000)

# 5. Large-n replication (32 tasks × K=15)
python _r28_largen_replication.py     # writes _r28_largen_summary.json

# 6. Prefix component ablation (4 arms × 16 tasks × K=5)
python _r28_prefix_ablation.py        # writes _r28_prefix_ablation_summary.json
```

**Paths**: 20 of the 114 root scripts carry a `__WSE_REPO_ROOT__` placeholder.
All 20 read the `WSE_REPO_ROOT` env var first and fall back to the literal, so
no file editing is needed:

```bash
export WSE_REPO_ROOT="$(pwd)"
python tools/fix_repo_root.py     # prints the exact counts; exits 1 if any remain
```

(The other 93 scripts take `--corpus`/`--out` arguments or resolve relative to
`assets/bench_manifest.json`. An earlier revision of this README claimed *every*
script needed hand-patching — that was wrong on both counts and is why the tool
above exists.) The scripts use `torch.manual_seed(seed)` per call, so per-seed
outputs are bit-exact reproducible across runs on the same hardware.

## Recompute the numbers (reproduction ledger)

Every number quoted in this README has a committed source you can re-derive
without editing any file:

| Number | Recompute from | Command |
|---|---|---|
| 156 tasks / 14 cohorts | `assets/bench_manifest.json` | `python3 demo.py` (prints `manifest : 156 tasks · 14 cohorts`) |
| 153/156 hash-lock intact | `eval_self_evolution.verify_hashes` | `python3 demo.py` (prints `hash lock: 153/156 intact`) |
| 37 ledger entries | `assets/evolution_ledger.json` | `python3 demo.py` (prints `ledger   : 37 entries`) |
| #33 b=14, c=29, p=0.0315 | `_r28_effectsize_summary.json` `verified_33` | `python3 demo.py` (prints `r28 test : b=14 c=29 k=43 p=0.0315`) |
| OR=2.07 [1.06, 4.24], power=0.59 | `_r28_effectsize_summary.json` `effect_sizes[0]` / `power` | `python3 demo.py` (prints `effect   : OR=2.07 [1.06, 4.24] · power=0.59`) |
| Large-n Δ=+20.4% CI [+11.9%, +29.0%] p=2.16e-10 | `EFFECT_SIZE_CI_POWER_r28_FINAL.md` §0 / `_r28_largen_summary.json` | `python _r28_effectsize_analysis.py` (writes `_r28_effectsize_summary.json`) |
| Prefix ablation arms (base 30, quote 44, full 45) | `EFFECT_SIZE_CI_POWER_r28_FINAL.md` §2 | `python _r28_prefix_ablation.py` (writes `_r28_prefix_ablation_summary.json`) |

The `demo.py` path is read-only and makes 0 model calls. The two `_r28_*`
analysis scripts recompute the effect-size / CI / power numbers and rewrite
their `_r28_*_summary.json` outputs, which are committed and hash-stable. To
regenerate *model outputs* you additionally need the model weights (see the
reproduction section above) and the original per-seed generations, which are
not shipped (see "What's *not* in this repo").

## Run the tests

This is a **release repository**, so the tests are a read-only smoke gate
against the release contract — they do not run a model or download weights:

```bash
python3 -m pytest tests/ -q        # 8 passed
```

`tests/test_release_audit.py` asserts: the manifest holds 156 tasks across 14
cohorts; the hash lock is 153/156 intact with exactly 3 documented redactions
(T029–T031); the r28 headline paired McNemar recomputes to p=0.0315 from
b=14, c=29; the ledger has 37 entries; `demo.py` exits 0; and strict
`--verify` stays fail-closed (exit 2) on the redactions. The same numbers can
be re-derived directly with `python3 demo.py` (read-only, 0 model calls).

## What this proves — and what it does not

**Proves (within the evidence in this repo):**

- On Qwen2.5-3B-Instruct 4-bit NF4, a single grounding-prefix intervention on
  the RC cohort yields a **real, reproducible** improvement: the original #33
  paired McNemar (b=14, c=29, p=0.0315, Δ=+18.8%) survives a same-protocol
  re-test on fresh seeds (OLD16: Δ=+19.6%, CI [+6.3%, +33.8%]) and a 2×
  pool-size replication (FULL n=480: Δ=+20.4%, CI [+11.9%, +29.0%],
  p=2.16e-10). The held-out 16 tasks (NEW16, never used for #33) also show the
  effect (Δ=+21.3%, CI [+10.8%, +30.8%]), so it is not a within-sample
  artifact.
- The prefix component ablation attributes almost all of the gain to the
  `quote` component (C2): quote-only gives +17.5% vs. base; adding `role` (C1)
  or `abstain` (C3) on top does not materially change it.
- The harness is fail-closed: tampering with the benchmark is detected by the
  hash lock, and the 3 closed-source probe tasks are redacted to
  `REPLACE_WITH_YOUR_*` placeholders rather than silently dropped.

**Does not prove (honest boundary):**

- **Generality beyond this one model.** Qwen2.5-3B-Instruct is the *only* model
  for which the #33 evidence chain exists. Multi-model replication
  (Llama-3.1-8B, Mistral-7B) was attempted but could not complete on the
  available 6 GB-VRAM / 16 GB-RAM hardware (marked "未消" in
  `EFFECT_SIZE_CI_POWER_r28_FINAL.md` §4).
- **Causal mechanism.** The ablation shows *which* component drives the gain,
  not *why* it does. The `abstain` component (C3) even shows a slightly
  negative point estimate (−3.8%) on its own, which the current data cannot
  explain.
- **Statistical confirmation of the component attribution.** After Holm
  correction across the 4 new ablation arms, quote-only and quote+abstain sit
  at p=0.095 — above the family-wise α=0.05. The point estimates are stable,
  but the attribution is *exploratory*, not confirmatory.
- **Closed-source probes.** T029–T031 only verify a *probe ability* (that a
  model cannot answer a private/local fact from parametric memory alone) on
  your own KB; they say nothing about any specific KB's scale or path.
- **Production readiness.** No serving/API harness, no throughput or latency
  claims, no deployment story. This is a benchmark + audit release, not a
  product.

## Scope and known limits (honest disclosure)

- **Single-model evidence so far**: Qwen2.5-3B-Instruct is the only model for
  which all #33 evidence (r27 strict ablation + r28 large-n) was generated.
  Multi-model replication (Llama-3.1-8B, Mistral-7B) was attempted on a
  6 GB-VRAM / 16 GB-RAM development laptop but could not complete due to
  physical constraints (Llama 8-bit CPU load OOMs at shard 2/4; GPU cannot
  fit 8B 4-bit + KV cache + activation). The corresponding row in
  `EFFECT_SIZE_CI_POWER_r28_FINAL.md` §4 is explicitly marked "未消" (not
  closed), with cloud-grade compute required to close it.
- **Closed-source probes (T029-T031)** are kept in the manifest as
  `REPLACE_WITH_YOUR_*` placeholders that you instantiate on your own
  private KB. The probe ability (verify that a model cannot answer a
  private/local fact from parametric memory alone) is preserved without
  leaking any specific path or scale number from the original author's KB.
- **Power**: paired McNemar achieves ~0.59 at n=80 (the original #33 sample),
  ~0.92 at n=240 (r28 OLD16 replication), and >0.99 at n=480 (r28 FULL
  replication). Bootstrap CI lower bound on Δ crosses zero at n=80 but
  is [+6.3%, +33.8%] at n=240 and [+11.9%, +29.0%] at n=480.

## Methodology in one paragraph

Each round, the agent proposes a candidate system prompt (or LoRA / DPO
delta). We generate K≥5 samples per task for both candidate and baseline on
the same fixed seeds, score deterministically, and compute paired McNemar +
bootstrap-CI on the b/c discordant pair counts. A change is **promoted** to
the ledger only if (a) two-sided McNemar p<0.05 **and** (b) the cluster
bootstrap 95% CI lower bound on Δ is strictly positive. Anything else is
honestly marked HOLD, REVERT, FAILED, or STEADY_STATE_NO_PROMOTE with the
raw numbers in the ledger entry.

## Citation

```bibtex
@misc{wse-bench-2026,
  title  = {WSE-Bench: An Eval-Gated Self-Evolution Benchmark for Small LLMs},
  year   = {2026},
  note   = {Open-source release v1.0.0, see \url{https://github.com/aidless/wse-bench-public}}
}
```

## License

MIT — see `LICENSE`.

> **Dual license.** WSE-Bench releases the benchmark tasks, datasets, and evaluation results under
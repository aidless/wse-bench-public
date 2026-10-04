# WSE-Bench — Eval-Gated Self-Evolution Benchmark
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)  [![Data](https://img.shields.io/badge/data-CC--BY--4.0-lightgrey.svg)](LICENSE)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Reproducible: seeds+prompts locked](https://img.shields.io/badge/reproducible-seeds%2Bprompts-locked-green.svg)]()

A 156-task benchmark + per-round evolution ledger + auditing toolkit designed
to evaluate **eval-gated self-evolution loops** on small LLMs. Each task is
graded by a deterministic rubric and admits paired McNemar testing across
candidate vs. baseline system prompts.

## What this repo gives you

| Component | Where | Purpose |
|---|---|---|
| Benchmark manifest | `assets/bench_manifest.json` | 156 tasks across 14 cohorts (core / ext / fact / hard / rc{1-4} / reason / struct / sv / verify / 2026Q4-core / 2026Q4-protocol) |
| Deterministic grader | `eval_self_evolution.py` | `score_task`, `is_pass`, `PASS_THRESHOLD` |
| Audit harness | `audit_contamination.py`, `_audit_contamination_r28.py` | Detects prompt-leakage bugs and impossible-closedbook probes |
| Per-round ledger | `assets/evolution_ledger.json` | Append-only audit log of every promotion/revert decision (35 entries, r17 → r28) |
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

**Important**: every script uses `ROOT = Path(r'__WSE_REPO_ROOT__')` as a
placeholder for the absolute path of your local clone. Replace this with your
own clone path (or set `WSE_REPO_ROOT` env var and patch the `ROOT` line) before
running. The scripts use `torch.manual_seed(seed)` per call, so per-seed
outputs are bit-exact reproducible across runs on the same hardware.

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
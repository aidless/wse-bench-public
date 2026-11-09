# Failure modes

The offline audit (`python3 demo.py`, `python3 tools/check_release_drift.py`)
is a consistency check of files in this tree. It is not a live evolution run.
These are the failures it is supposed to tell apart.

## 1. Redaction refusal versus a broken verify

`python3 eval_self_evolution.py --verify` exits 2 on this release. The failing
ids are exactly T029, T030, and T031. Their stored hashes predate the
`REPLACE_WITH_YOUR_*` placeholder redaction, so the lock does not match the
text that was published. That exit is a **documented redaction refusal**.

`demo.py` and `tools/check_release_drift.py` treat that set as expected:
153 tasks stay hash-locked, and those three are named. Two nearby outcomes
are different failures:

- **Broken verify.** Any other task id fails `verify_hashes`. The task body
  changed and the stored hash did not. Both commands exit 1. Do not fold that
  into the redaction list.
- **Silent re-lock.** `--verify` exits 0, or one of T029–T031 suddenly
  matches. The published contract is 153 hash-locked tasks plus 3 redactions,
  not a clean 156/156 lock. The drift check fails closed on that too.

The placeholder strings themselves are a separate CI job
(`.github/workflows/security-audit.yml`). A hash failure with the placeholders
still present is the redaction case above, not evidence that the placeholders
were removed.

## 2. Ledger versus manifest drift

The sealed counts are:

| Figure | Value | Where it has to hold |
|---|---|---|
| Tasks | 156 | `assets/bench_manifest.json` |
| Cohorts | 14 | distinct `cohort` on those tasks |
| Hash-locked | 153 | tasks whose stored hash matches the canonical body |
| Redactions | T029, T030, T031 | the only hash failures |
| Ledger entries | 37 | `assets/evolution_ledger.json` |

`demo.py` used to print these numbers and still exit 0 if they moved. The
drift check now exits 1 when they move. A README sentence that still says
156 / 153 / 37 after the JSON has changed is the same class of drift; the
script checks the JSON, not the prose. `RELEASE_v1.0.0.md` previously said
35 ledger entries. The JSON has 37. The release note is aligned with the
JSON; the JSON was not edited to match the old sentence.

The r28 block has to agree across files, not only in a single summary:

- `_r28_effectsize_summary.json` `verified_33` (b=14, c=29, k=43, N=80)
- the prefix-ablation `full_prefix` arm (same b, c)
- the ledger strict-ablation entry (`mcnemar_b` / `mcnemar_c` / `p_value`)
- ledger entry `id` 35 (`verified_33`, `effect_33`, `effect_32`, `power_33`)
- `_r28_largen_summary.json` versus the ledger
  `R28_EFFECT_REPLICATION_COMPREHENSIVE` evidence block

The `match_ledger: true` flag is not trusted by itself. The check compares
the numbers, and it fails if the flag is true while b or c disagree.

Rounding tolerance, so display rounding is not reported as a new experiment:

- pass-rate delta: absolute 0.001
- Cohen's g and odds ratios: absolute 0.001
- bootstrap CI endpoints: absolute 0.002
- McNemar p ≥ 1e-3: absolute 5e-4 (covers 0.031539 versus 0.0315)
- smaller p: relative 0.02 (covers 2.16e-10 versus 2.157e-10)
- post-hoc power: absolute 0.005

On this tree the largest delta residual is the large-n full sample: the
ledger stores `0.2035` and `_r28_largen_summary.json` stores
`0.204166…`. The residual is about 6.7e-4, inside the 0.001 tolerance.
The pass line prints that residual. Neither file is rewritten to erase it.
A disagreement outside the tolerance fails the check.

## 3. McNemar overclaim on a small n

Ledger entry #33 is 16 tasks × K=5 = 80 pairs (b=14, c=29, k=43). The stored
exact p is about 0.0315. The stored post-hoc power is about 0.59. Ledger
entry 35 says the cluster-bootstrap CI on the pass-rate delta touches 0, so
the pre-registered rule (p<0.05 **and** CI lower bound > 0) was not met on
that sample. A p-value under 0.05 at n=80 is not a precise effect-size claim.

The later large-n summary (32 tasks × K=15, 480 pairs) is an author-committed
result in `_r28_largen_summary.json` and in the ledger. The offline audit
checks that those two copies agree inside the tolerance above. It does not
draw new samples, and it does not recompute the p-value with SciPy. Citing
`demo.py` as confirmation that the CI lower bound is above zero overclaims
what the command does.

The ledger's own `publication_readiness.reproducibility` text says CI can
re-run the result. CI re-runs the secret scan, the residue scan, a syntax
compile, the placeholder check, and this offline drift audit. It does not
regenerate model samples. That sentence in the ledger is stronger than the
workflows. The ledger entry is left as published; this file is the correction.

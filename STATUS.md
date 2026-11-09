# STATUS: WORK-IN-PROGRESS — not A yet

This repository is a sealed data and report release: 156 tasks, 153 of them
hash-locked, 3 documented redactions, and 37 ledger entries. The offline
audit below runs from a fresh clone with no install. It is not an independent
live reproduction of the eval-gated evolution loop, so this release does not
meet the A bar.

## What the offline path does

```bash
python3 demo.py
python3 tools/check_release_drift.py
```

Both use the Python standard library and `eval_self_evolution.verify_hashes`.
No package install, no model download, no network call. On a local run they
finish in seconds, inside a 15-minute fresh-clone budget. `demo.py` exits 0
only when the drift check exits 0.

CI (`.github/workflows/release-audit.yml`) runs those two commands. The other
workflows scan secrets, sensitive residue, Python syntax, and the T029–T031
placeholder strings. None of them rerun Qwen.

## Gaps

1. **No independent live reproduction.** Headline McNemar figures are the
   author's committed JSON. `demo.py` cross-checks that JSON. It does not
   generate samples, and this environment did not rerun
   Qwen2.5-3B-Instruct.
2. **`--verify` does not pass.** Exit 2 on T029–T031 is the documented
   redaction refusal (see `FAILURE_MODES.md`). A third party cannot treat the
   manifest as a clean hash lock.
3. **Live scripts are provenance, not a supported CLI.** Author-machine paths
   (`F:/hf_cache`, the literal `__WSE_REPO_ROOT__`) remain in the reproduction
   scripts on purpose. `_r27_strict_ablation.py` is named in older notes and
   is not in this tree. There is no install entry point and no PyPI metadata.
4. **Small-n McNemar is not a settled effect.** At n=80 the stored post-hoc
   power is about 0.59, and ledger entry 35 says the cluster-bootstrap CI
   lower bound touches 0. Large-n intervals are cross-checked as stored
   numbers, not recomputed here.
5. **The ledger overclaims what CI reruns.** `publication_readiness` on the
   comprehensive r28 entry says CI can re-run the result. CI re-runs the
   audit. The ledger text was not rewritten.
6. **Known rounding residue, left in place.** Ledger `large_n_full.delta` is
   `0.2035`. `_r28_largen_summary.json` has `0.204166…`. The drift check
   prints that residual and allows it inside absolute tolerance 0.001.
7. **No pytest suite, by design.** `pytest` finds nothing. That is not a
   hidden green test run.
8. **Multi-model replication is still open.** The ledger marks Llama-3.1-8B
   and Mistral-7B as `未消`. This release does not close that row.

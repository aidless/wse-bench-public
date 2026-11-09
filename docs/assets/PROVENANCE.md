# Demo asset provenance

- `demo.gif` / `demo.png`: rendered 2026-10-25 from a curated view of an earlier
  `python3 demo.py` stdout. They show the manifest, hash-lock, ledger, r28, and
  effect lines. They do not show the later `drift` line.
- `demo.txt`: raw stdout of the current `python3 demo.py`, including the drift
  line and the large-n rounding residual. No comment header. The gif does not
  include those newer lines.
- The audit is read-only: 153 hash-locked tasks + 3 documented redactions
  (T029–T031), the 37-entry ledger, and the committed r28 effect-size summary.
- No model calls, no API calls, no benchmark run, no live evolution run.

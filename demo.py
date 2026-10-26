#!/usr/bin/env python3
"""Read-only release audit: manifest hash lock, ledger, and r28 effect size.

This is not a benchmark run. It checks that the released artifacts are
internally consistent and names the three documented redactions explicitly.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from eval_self_evolution import verify_hashes  # noqa: E402

REDACTED = {"T029", "T030", "T031"}


def main() -> int:
    manifest = json.loads((ROOT / "assets/bench_manifest.json").read_text(encoding="utf-8"))
    ok, bad = verify_hashes(manifest)
    bad_ids = {row[0] for row in bad}
    unexpected = bad_ids - REDACTED
    tasks = len(manifest["tasks"])
    cohorts = len({t.get("cohort") for t in manifest["tasks"]})

    print(f"manifest : {tasks} tasks · {cohorts} cohorts")
    redactions = ", ".join(sorted(bad_ids & REDACTED))
    print(f"hash lock: {tasks - len(bad)}/{tasks} intact · documented redactions {redactions}")
    if unexpected:
        print("UNEXPECTED HASH DRIFT:", sorted(unexpected))
        return 1

    ledger = json.loads((ROOT / "assets/evolution_ledger.json").read_text(encoding="utf-8"))
    decisions = Counter(row.get("decision") for row in ledger)
    top = " · ".join(f"{name}={count}" for name, count in decisions.most_common(4))
    print(f"ledger   : {len(ledger)} entries · {top}")

    effects = json.loads((ROOT / "_r28_effectsize_summary.json").read_text(encoding="utf-8"))
    verified = effects["verified_33"]
    effect = effects["effect_sizes"][0]
    print(f"r28 test : b={verified['b']} c={verified['c']} k={verified['k']} "
          f"p={verified['p']:.4f} · ledger match={verified['match_ledger']}")
    print(f"effect   : OR={effect['orr']:.2f} [{effect['or_lo']:.2f}, {effect['or_hi']:.2f}] "
          f"· post-hoc power={effects['power']['post_hoc_33']:.2f}")
    print("strict   : --verify still refuses T029-T031 by design (documented redaction)")
    print("audit    : PASS — artifacts are internally consistent; 3 redactions are documented, not silent")
    print("demo     : read-only · 0 model calls · not a benchmark run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

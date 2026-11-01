"""Release audit tests for WSE-Bench (read-only, no model calls).

These tests lock in the *documented* release contract:

1. The manifest holds 156 tasks across 14 cohorts.
2. Hash-lock integrity: 153 tasks intact, 3 documented redactions (T029-T031)
   intentionally drift (they are `REPLACE_WITH_YOUR_*` placeholders).
3. The deterministic grader (`score_task` / `is_pass` / `mcnemar_exact`) agrees
   with the r28 effect-size summary: b=14, c=29 -> two-sided exact McNemar
   p = 0.0315 (the headline ledger entry #33).
4. `demo.py` (the read-only release audit) exits 0.
5. Strict `--verify` stays fail-closed on the 3 redacted tasks (exit 2).

Nothing here runs a model or downloads weights. It is the "does the release
actually hold together" smoke gate.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import eval_self_evolution as E  # noqa: E402

REDACTED = {"T029", "T030", "T031"}


def _manifest():
    return json.loads((ROOT / "assets/bench_manifest.json").read_text(encoding="utf-8"))


def _ledger():
    return json.loads((ROOT / "assets/evolution_ledger.json").read_text(encoding="utf-8"))


def test_manifest_size_and_cohorts():
    m = _manifest()
    assert len(m["tasks"]) == 156
    cohorts = {t.get("cohort") for t in m["tasks"]}
    assert len(cohorts) == 14


def test_hash_lock_redactions_documented():
    """The 3 redactions are expected drift; the other 153 must be intact."""
    m = _manifest()
    ok, bad = E.verify_hashes(m)
    bad_ids = {row[0] for row in bad}
    # Redactions are the ONLY allowed drift
    assert bad_ids == REDACTED
    # Non-redacted tasks must all verify
    clean = {"tasks": [t for t in m["tasks"] if t["id"] not in REDACTED]}
    ok_clean, bad_clean = E.verify_hashes(clean)
    assert ok_clean is True
    assert bad_clean == []
    # The 3 redacted ids exist in the manifest
    ids = {t["id"] for t in m["tasks"]}
    assert REDACTED <= ids


def test_mcnemar_r28_headline():
    """Ledger entry #33: b=14, c=29 -> two-sided exact McNemar p=0.0315."""
    p, b, c = E.mcnemar_exact(14, 29)
    assert b == 14 and c == 29
    assert abs(p - 0.03153949735315109) < 1e-9


def test_ledger_entry_count():
    ledger = _ledger()
    assert len(ledger) == 37


def test_r28_effectsize_summary_consistent():
    """The committed summary must match the recomputed McNemar p."""
    s = json.loads((ROOT / "_r28_effectsize_summary.json").read_text(encoding="utf-8"))
    v = s["verified_33"]
    p, _, _ = E.mcnemar_exact(v["b"], v["c"])
    assert abs(p - v["p"]) < 1e-12
    assert v["match_ledger"] is True
    # post-hoc power is ~0.59 at the original n=80 sample
    assert abs(s["power"]["post_hoc_33"] - 0.59) < 0.02


def test_demo_readonly_audit_exits_zero():
    """The documented '60-second release audit' entry point must run and pass."""
    r = subprocess.run(
        [sys.executable, "demo.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, f"demo.py failed:\n{r.stdout}\n{r.stderr}"
    assert "audit    : PASS" in r.stdout


def test_verify_stays_fail_closed():
    """Strict --verify must refuse the 3 redactions (fail-closed by design)."""
    r = subprocess.run(
        [sys.executable, "eval_self_evolution.py", "--verify"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 2
    assert "HASH LOCK: TAMPERED" in r.stdout


def test_pass_threshold_defined():
    assert E.PASS_THRESHOLD["fact"] == 0.85
    assert E.PASS_THRESHOLD["json_schema"] == 1.0

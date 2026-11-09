#!/usr/bin/env python3
"""Fail when the sealed release drifts from its published counts or r28 JSON.

Stdlib only. This does not score a model, rewrite a ledger entry, or install
a package. It compares files already in the tree.

Contract (v1 release, not a live rerun):
  * 156 manifest tasks, 14 cohorts
  * 153 hash-locked tasks
  * hash failures are exactly T029, T030, T031 (documented redaction)
  * eval_self_evolution.py --verify exits 2 on that same set
  * 37 ledger entries
  * r28 effect-size, prefix-ablation, and large-n summaries agree with the
    ledger inside the tolerances below

A hash failure outside T029–T031 is a broken verify, not a redaction.
A clean --verify (exit 0) also fails: this release is not a 156/156 hash lock.

Tolerances are display rounding, not a license to rewrite figures. On this
tree the largest delta residual is ledger large_n_full.delta 0.2035 versus
_r28_largen_summary.json full.delta 0.204166…, about 6.7e-4, inside
DELTA_ABS_TOL. Neither file is edited to hide that gap.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval_self_evolution import verify_hashes  # noqa: E402

EXPECTED_TASKS = 156
EXPECTED_COHORTS = 14
EXPECTED_LOCKED = 153
EXPECTED_LEDGER = 37
REDACTED = frozenset({"T029", "T030", "T031"})

# Display rounding between the ledger and the summary JSON. Not a rewrite.
DELTA_ABS_TOL = 0.001
RATE_ABS_TOL = 0.001  # Cohen's g, odds ratios printed to ~3 decimals
BOOT_ABS_TOL = 0.002
P_ABS_TOL = 5e-4  # p >= 1e-3, e.g. 0.031539 vs 0.0315
P_REL_TOL = 0.02  # smaller p, e.g. 2.16e-10 vs 2.157e-10
POWER_ABS_TOL = 0.005

TASK_ID = re.compile(r"T\d+")


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def close_p(left: float, right: float) -> bool:
    a, b = float(left), float(right)
    if max(abs(a), abs(b)) >= 1e-3:
        return abs(a - b) <= P_ABS_TOL
    scale = max(abs(a), abs(b), 1e-30)
    return abs(a - b) / scale <= P_REL_TOL


def _gap(name: str, left, right, ok: bool, detail: str, errors: list[str], notes: list[str]) -> None:
    residual = ""
    try:
        residual = f" residual={abs(float(left) - float(right)):.6g}"
    except (TypeError, ValueError):
        pass
    line = f"{name}: ledger/summary {left} vs {right}{residual} ({detail})"
    if ok:
        notes.append(line)
    else:
        errors.append(line)


def expect_close(name, left, right, tol, errors, notes) -> None:
    a, b = _as_float(left), _as_float(right)
    if a is None or b is None:
        errors.append(f"{name}: non-numeric {left!r} vs {right!r}")
        return
    ok = abs(a - b) <= tol
    _gap(name, left, right, ok, f"abs tol {tol}", errors, notes)


def expect_p(name, left, right, errors, notes) -> None:
    a, b = _as_float(left), _as_float(right)
    if a is None or b is None:
        errors.append(f"{name}: non-numeric p {left!r} vs {right!r}")
        return
    ok = close_p(a, b)
    kind = "abs" if max(abs(a), abs(b)) >= 1e-3 else "rel"
    tol = P_ABS_TOL if kind == "abs" else P_REL_TOL
    _gap(name, left, right, ok, f"{kind} tol {tol}", errors, notes)


def expect_eq(name, left, right, errors) -> None:
    if left != right:
        errors.append(f"{name}: {left!r} != {right!r}")


def classify_hash_failures(bad_ids: set[str]) -> list[str]:
    """Redaction refusal is exactly REDACTED. Anything else is a broken verify."""
    errors = []
    unexpected = bad_ids - REDACTED
    missing = REDACTED - bad_ids
    if unexpected:
        errors.append(
            "broken verify: hash mismatch outside the documented redactions: "
            + ", ".join(sorted(unexpected))
        )
    if missing:
        errors.append(
            "redaction contract changed: these ids no longer fail the hash lock: "
            + ", ".join(sorted(missing))
            + " (a clean lock of a redacted task is not this release)"
        )
    return errors


def _one(rows: list, desc: str, pred, errors: list[str]):
    hits = [row for row in rows if pred(row)]
    if len(hits) != 1:
        errors.append(f"expected exactly one ledger entry ({desc}), found {len(hits)}")
        return None
    return hits[0]


def _load(path: Path, errors: list[str]):
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT)}")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def check_stored(manifest, ledger, effects, largen, prefix, verify_rc, verify_text) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    tasks = manifest.get("tasks") if isinstance(manifest, dict) else None
    if not isinstance(tasks, list):
        errors.append("manifest.tasks is not a list")
        return errors, notes
    ids = [t.get("id") for t in tasks]
    if len(ids) != EXPECTED_TASKS:
        errors.append(f"manifest tasks: {len(ids)} != {EXPECTED_TASKS}")
    if len(set(ids)) != len(ids):
        errors.append("manifest task ids are not unique")
    cohorts = {t.get("cohort") for t in tasks}
    if len(cohorts) != EXPECTED_COHORTS or any(not isinstance(c, str) or not c for c in cohorts):
        errors.append(f"cohorts: {sorted(str(c) for c in cohorts)} (expected {EXPECTED_COHORTS} named cohorts)")
    for tid in sorted(REDACTED):
        if tid not in ids:
            errors.append(f"redacted id {tid} is not in the manifest")

    ok, bad = verify_hashes(manifest)
    bad_ids = {row[0] for row in bad}
    locked = len(tasks) - len(bad_ids)
    if locked != EXPECTED_LOCKED:
        errors.append(f"hash-locked tasks: {locked} != {EXPECTED_LOCKED}")
    errors.extend(classify_hash_failures(bad_ids))
    if ok:
        errors.append("verify_hashes reported a clean lock; this release documents 3 redactions")

    if not isinstance(ledger, list):
        errors.append("ledger is not a list")
        return errors, notes
    if len(ledger) != EXPECTED_LEDGER:
        errors.append(f"ledger entries: {len(ledger)} != {EXPECTED_LEDGER}")

    if verify_rc != 2:
        errors.append(
            f"eval_self_evolution.py --verify exited {verify_rc}, expected 2 "
            "(redaction refusal, not a clean hash lock)"
        )
    mentioned = set(TASK_ID.findall(verify_text or ""))
    if mentioned != set(REDACTED):
        errors.append(
            "--verify named "
            + (", ".join(sorted(mentioned)) or "(no task ids)")
            + "; redaction refusal must name exactly T029, T030, T031"
        )

    if not isinstance(effects, dict) or not isinstance(largen, dict) or not isinstance(prefix, dict):
        errors.append("r28 summary JSON missing or not an object")
        return errors, notes

    strict = _one(ledger, "STRICT_ABLATION_CONFIRM", lambda e: e.get("decision") == "STRICT_ABLATION_CONFIRM", errors)
    effect_entry = _one(ledger, "id=35", lambda e: e.get("id") == 35, errors)
    large_entry = _one(
        ledger,
        "R28_EFFECT_REPLICATION_COMPREHENSIVE",
        lambda e: e.get("type") == "R28_EFFECT_REPLICATION_COMPREHENSIVE",
        errors,
    )
    if strict is None or effect_entry is None or large_entry is None:
        return errors, notes

    verified = effects.get("verified_33") or {}
    expect_eq("verified_33.b", verified.get("b"), 14, errors)
    expect_eq("verified_33.c", verified.get("c"), 29, errors)
    expect_eq("verified_33.k", verified.get("k"), 43, errors)
    expect_eq("verified_33.N_total", verified.get("N_total"), 80, errors)
    expect_eq("verified_33.match_ledger", verified.get("match_ledger"), True, errors)
    expect_eq("ledger verified_33.b", (effect_entry.get("verified_33") or {}).get("b"), verified.get("b"), errors)
    expect_eq("ledger verified_33.c", (effect_entry.get("verified_33") or {}).get("c"), verified.get("c"), errors)
    expect_eq("ledger verified_33.match", (effect_entry.get("verified_33") or {}).get("match"), True, errors)
    expect_p("ledger verified_33.p", (effect_entry.get("verified_33") or {}).get("p"), verified.get("p"), errors, notes)
    expect_eq("strict ablation b", strict.get("mcnemar_b"), verified.get("b"), errors)
    expect_eq("strict ablation c", strict.get("mcnemar_c"), verified.get("c"), errors)
    expect_eq("strict ablation N", strict.get("baseline_n"), verified.get("N_total"), errors)
    expect_eq("strict ablation N candidate", strict.get("candidate_n"), verified.get("N_total"), errors)
    expect_p("strict ablation p", strict.get("p_value"), verified.get("p"), errors, notes)
    b_cell, c_cell, n_pairs = verified.get("b"), verified.get("c"), verified.get("N_total")
    if isinstance(b_cell, (int, float)) and isinstance(c_cell, (int, float)) and isinstance(n_pairs, (int, float)) and n_pairs:
        expect_close(
            "strict ablation delta",
            strict.get("delta_overall"),
            (c_cell - b_cell) / n_pairs,
            DELTA_ABS_TOL,
            errors,
            notes,
        )

    arms = effects.get("effect_sizes") or []
    if len(arms) < 2:
        errors.append("effect_sizes needs the #33 and #32 rows")
    else:
        arm33, arm32 = arms[0], arms[1]
        if "#33" not in str(arm33.get("name", "")):
            errors.append(f"effect_sizes[0] is not the #33 row: {arm33.get('name')!r}")
        expect_eq("#33 effect b", arm33.get("b"), verified.get("b"), errors)
        expect_eq("#33 effect c", arm33.get("c"), verified.get("c"), errors)
        expect_p("#33 effect p", arm33.get("p"), verified.get("p"), errors, notes)
        stored33 = effect_entry.get("effect_33") or {}
        expect_close("#33 OR", arm33.get("orr"), stored33.get("OR"), RATE_ABS_TOL, errors, notes)
        expect_close("#33 OR lo", arm33.get("or_lo"), (stored33.get("OR_ci_exact") or [None, None])[0], RATE_ABS_TOL, errors, notes)
        expect_close("#33 OR hi", arm33.get("or_hi"), (stored33.get("OR_ci_exact") or [None, None])[1], RATE_ABS_TOL, errors, notes)
        expect_close("#33 g", arm33.get("g"), stored33.get("g"), RATE_ABS_TOL, errors, notes)
        power = (effects.get("power") or {}).get("post_hoc_33")
        expect_close("#33 power", power, (effect_entry.get("power_33") or {}).get("posthoc"), POWER_ABS_TOL, errors, notes)

        stored32 = effect_entry.get("effect_32") or {}
        expect_eq("#32 effect b", arm32.get("b"), stored32.get("b"), errors)
        expect_eq("#32 effect c", arm32.get("c"), stored32.get("c"), errors)
        expect_p("#32 effect p", arm32.get("p"), stored32.get("p"), errors, notes)
        expect_close("#32 OR", arm32.get("orr"), stored32.get("OR"), RATE_ABS_TOL, errors, notes)

    full_arm = None
    for arm in prefix.get("arms") or []:
        if str(arm.get("arm", "")).startswith("full_prefix"):
            full_arm = arm
            break
    if full_arm is None:
        errors.append("prefix ablation has no full_prefix arm")
    else:
        expect_eq("prefix full b", full_arm.get("b"), 14, errors)
        expect_eq("prefix full c", full_arm.get("c"), 29, errors)
        expect_p("prefix full p", full_arm.get("p_raw"), verified.get("p"), errors, notes)
        expect_close("prefix full delta", full_arm.get("delta"), 0.1875, DELTA_ABS_TOL, errors, notes)

    evidence = large_entry.get("evidence") or {}
    pairs = (
        ("full", "large_n_full"),
        ("replication_old16", "replication_old16"),
        ("heldout_new16", "heldout_new16"),
    )
    for summary_key, ledger_key in pairs:
        src = largen.get(summary_key) or {}
        dst = evidence.get(ledger_key) or {}
        if not src or not dst:
            errors.append(f"missing large-n block {summary_key}/{ledger_key}")
            continue
        expect_eq(f"{ledger_key} n_pairs", dst.get("n_pairs"), src.get("n_pairs"), errors)
        expect_eq(f"{ledger_key} prereg", dst.get("prereg_rule_pass"), src.get("prereg_rule_pass"), errors)
        expect_close(f"{ledger_key} delta", dst.get("delta"), src.get("delta"), DELTA_ABS_TOL, errors, notes)
        expect_close(f"{ledger_key} g", dst.get("cohens_g"), src.get("cohens_g"), RATE_ABS_TOL, errors, notes)
        expect_p(f"{ledger_key} p", dst.get("mcnemar_p"), src.get("mcnemar_p"), errors, notes)
        src_ci = src.get("boot_ci95") or [None, None]
        dst_ci = dst.get("boot_ci95") or [None, None]
        expect_close(f"{ledger_key} ci lo", dst_ci[0], src_ci[0], BOOT_ABS_TOL, errors, notes)
        expect_close(f"{ledger_key} ci hi", dst_ci[1], src_ci[1], BOOT_ABS_TOL, errors, notes)

    headline = (evidence.get("prefix_component_ablation") or {}).get("full", "")
    if "+18.8%" not in str(headline):
        errors.append(
            "ledger prefix headline does not contain +18.8% "
            f"(stored full arm delta is 0.1875): {headline!r}"
        )
    return errors, notes


def run_verify() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "eval_self_evolution.py"), "--verify"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def check() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    manifest = _load(ROOT / "assets" / "bench_manifest.json", errors)
    ledger = _load(ROOT / "assets" / "evolution_ledger.json", errors)
    effects = _load(ROOT / "_r28_effectsize_summary.json", errors)
    largen = _load(ROOT / "_r28_largen_summary.json", errors)
    prefix = _load(ROOT / "_r28_prefix_ablation_summary.json", errors)
    if errors:
        return errors, []
    verify_rc, verify_text = run_verify()
    return check_stored(manifest, ledger, effects, largen, prefix, verify_rc, verify_text)


def main() -> int:
    errors, notes = check()
    if errors:
        print("drift    : FAIL")
        for item in errors:
            print(f"  {item}")
        return 1
    print(
        "drift    : PASS — tasks=156 hash-locked=153 redactions=T029,T030,T031 "
        "ledger=37 · r28 summary matches the ledger inside rounding tolerance"
    )
    print("verify   : --verify exit 2 · refusal set T029,T030,T031 · not a clean hash lock")
    # One line for the worst stored rounding gap. A pass must not look like
    # the two files were edited until they matched.
    parsed = []
    for note in notes:
        if "residual=" not in note:
            continue
        raw = note.split("residual=", 1)[1].split()[0]
        try:
            parsed.append((float(raw), note))
        except ValueError:
            parsed.append((float("inf"), note))
    nonzero = [item for item in parsed if item[0] > 0]
    if nonzero:
        worst = max(nonzero, key=lambda item: item[0])
        print(f"rounded  : {len(nonzero)} stored fields differ inside tolerance")
        print(f"rounded  : largest · {worst[1]}")
    print("scope    : stored JSON only · 0 model calls · not a live evolution run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

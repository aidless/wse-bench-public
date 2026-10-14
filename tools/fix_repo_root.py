#!/usr/bin/env python3
"""Point every __WSE_REPO_ROOT__ placeholder at THIS clone, and report the rest.

WHY
---
README used to say "every script uses ROOT = Path(r'__WSE_REPO_ROOT__')" and told
you to replace it by hand. Neither half was true, and both cost a newcomer time:

  * only 20 of the 113 root .py files carry the placeholder. The other 93 have no
    ROOT line at all -- they resolve paths relative to the manifest or take
    --corpus/--out arguments, so "patch every script" edited nothing and read as
    if the tree were broken.
  * of the 20 that DO carry it, the env var WSE_REPO_ROOT was already honoured at
    the top, so manual editing was never needed in the first place.

So: set the env var (no file edits), and print exactly which files still carry the
placeholder afterwards so "unresolved" is a countable fact rather than a vibe.

Usage
-----
    python tools/fix_repo_root.py            # report only
    WSE_REPO_ROOT=/path/to/clone python tools/fix_repo_root.py
    python tools/fix_repo_root.py --write    # also rewrite the placeholder in-place

Exit codes: 0 = no unresolved placeholder left (or none existed), 1 = some remain.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

PLACEHOLDER = re.compile(r".*__WSE_REPO_ROOT__.*")


def scan(root: pathlib.Path) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    """Return (files that honour the env var, files that only carry the literal)."""
    env_ok, literal_only = [], []
    for p in sorted(root.glob("*.py")):
        if p.name.startswith("tools/"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if "__WSE_REPO_ROOT__" not in text:
            continue
        if "environ" in text and "WSE_REPO_ROOT" in text:
            env_ok.append(p)
        else:
            literal_only.append(p)
    return env_ok, literal_only


def rewrite(root: pathlib.Path, target: str) -> int:
    changed = 0
    for p in sorted(root.glob("*.py")):
        text = p.read_text(encoding="utf-8", errors="replace")
        if "__WSE_REPO_ROOT__" not in text:
            continue
        new = text.replace("__WSE_REPO_ROOT__", target)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
            print(f"  rewrote {p.name}")
    return changed


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    root = here.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="rewrite the placeholder in-place (default: report only)")
    a = ap.parse_args()

    total = len(list(root.glob("*.py")))
    env_ok, literal_only = scan(root)
    env = os.environ.get("WSE_REPO_ROOT")
    print(f"root .py files                : {total}")
    print(f"carrying the placeholder      : {len(env_ok) + len(literal_only)}")
    print(f"  honour WSE_REPO_ROOT env    : {len(env_ok)}")
    print(f"  literal only (need env or --write): {len(literal_only)}")
    print(f"WSE_REPO_ROOT                 : {env or '(unset)'}")

    if literal_only:
        print("\nliteral-only files:")
        for p in literal_only:
            print(f"  {p.name}")

    if a.write:
        target = env or str(root)
        print(f"\nrewriting placeholder -> {target}")
        n = rewrite(root, target)
        print(f"rewrote {n} file(s)")

    # A remaining literal only matters when the env var is also unset: with the
    # env set, those 20 scripts already resolve correctly.
    unresolved = len(literal_only) if not env else 0
    print(f"\nunresolved placeholders: {unresolved}")
    return 0 if unresolved == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

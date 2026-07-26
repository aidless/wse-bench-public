#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb_retriever.py — Generic local arxiv-style KB retriever wrapper.

The original v1 was hard-coded to the author's private peS2o KB at
``E:/peS2o_kb_faiss`` (a 540k-paper FAISS index built from peS2o dumps).
The v2 published here is a thin generic wrapper: users point
``KB_DIR`` (env var or edit below) at any local KB that exposes a
``kb_search.search(query, n, ...) -> list[dict]`` function with the
expected result schema (paper_id, title, year, categories, source,
score, text_prefix), and use this script as a JSON-emitting front-end.

Usage:
  KB_DIR=/path/to/your/local/kb \\
  VENV="$KB_DIR/.venv/Scripts/python.exe" \\
  "$VENV" /path/to/kb_retriever.py "probability calibration large language models" -n 5

Safety boundary (mirrors v1):
- Read-only: never write the KB's papers.db / papers.index / trigger rebuilds.
- Use the KB's own isolated venv so dependencies do not pollute the host.
- Only forwards ``kb_search.search()`` results; no answer generation/rewrite.

Output: single-line JSON to stdout with fields query / total / results.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

# v2 generic: resolve KB_DIR from env, fall back to a clearly fake placeholder.
KB_DIR = Path(os.environ.get("WSE_KB_DIR", "/REPLACE/WITH/YOUR/LOCAL/KB/PATH"))
sys.path.insert(0, str(KB_DIR))

# Avoid network calls for offline model loads if the local KB has its own cache.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def main() -> None:
    ap = argparse.ArgumentParser(description="Read-only local-KB retriever (generic)")
    ap.add_argument("query", help="检索 query")
    ap.add_argument("-n", type=int, default=5, help="返回数量")
    ap.add_argument("--year-min", type=int, default=None)
    ap.add_argument("--year-max", type=int, default=None)
    ap.add_argument("--category", default=None, help="arxiv 类别过滤，如 cs.LG")
    ap.add_argument("--source", default=None)
    ap.add_argument("--must-cite", action="store_true", help="排除已引用文献（需 --existing-refs）")
    ap.add_argument("--existing-refs", default=None, help="现有 .bib 路径，逗号分隔")
    ap.add_argument("--no-smart", action="store_true", help="关闭 query 扩展 + rerank")
    ap.add_argument("--timeout", type=float, default=30.0, help="检索总超时（秒）")
    args = ap.parse_args()

    import kb_search  # must import after sys.path update

    # 捕获 kb_search 内部的打印噪声，仅输出干净 JSON。
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        results = kb_search.search(
            args.query,
            n=args.n,
            year_min=args.year_min,
            year_max=args.year_max,
            source=args.source,
            category=args.category,
            must_cite=args.must_cite,
            existing_refs=[p.strip() for p in args.existing_refs.split(",")]
            if args.existing_refs else None,
            smart=not args.no_smart,
            total_timeout=args.timeout,
        )
    finally:
        sys.stdout = old_stdout

    payload = {
        "query": args.query,
        "total": len(results),
        "results": [
            {
                "paper_id": r.get("paper_id"),
                "id_display": r.get("id_display") or r.get("paper_id"),
                "id_source": r.get("id_source"),
                "title": r.get("title"),
                "year": (r.get("year") or "")[:4],
                "categories": r.get("categories"),
                "source": r.get("source"),
                "score": r.get("score"),
                "text_prefix": (r.get("text_prefix") or r.get("abstract") or "")[:400],
            }
            for r in results
        ],
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()

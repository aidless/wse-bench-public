"""Build a clean, self-contained bench_manifest.json with 118 tasks (including T109-T118).
This bypasses the syntax mess in build_bench.py by using a fresh Python script that
constructs the manifest directly from the existing 108-task manifest + new RC3 tasks.
"""
import json, os, sys
from pathlib import Path

ROOT = Path(r"F:\test\2026-07-24-08-21-57")
sys.path.insert(0, str(ROOT))
import eval_self_evolution as E

manifest = E.load_manifest()
ok, bad = E.verify_hashes(manifest)
assert ok, bad

# Build T109-T118 (rc3) task dicts. Hash will be computed by E.hsh(canon(t)) via the script,
# so we don't need to pre-fill hash here. We'll add them in the same format as T103-T108.
RC3_TASKS = [
    {
        "id": "T109", "split": "dev",
        "source": "OpenAI function-calling 官方介绍片段（platform.openai.com/docs, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中描述 function calling 核心机制与安全边界的关键短语；不要用自己的同义词替换。原文：「Function calling lets a model output a structured JSON argument that the host application can route to a real function; the model is not making the API call itself and tools should be sandboxed.」",
        "rubric": {"type": "contains", "required": ["structured JSON argument", "host application", "tools should be sandboxed"]},
        "reference": "structured JSON argument / host application / tools should be sandboxed。",
    },
    {
        "id": "T110", "split": "hidden",
        "source": "Tailscale ACL 官方文档片段（tailscale.com/kb/1018, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中描述 default ACL 行为与覆盖范围的原文短语。原文：「If no ACL rules match a connection, the default policy applies; the implicit default is deny. ACLs are evaluated in order, and the first match wins; wildcards may be used in source and destination but are not allowed in field-level matchers like HTTP hosts.」",
        "rubric": {"type": "contains", "required": ["the default policy applies", "the first match wins", "not allowed in field-level matchers like HTTP hosts"]},
        "reference": "the default policy applies / the first match wins / not allowed in field-level matchers like HTTP hosts。",
    },
    {
        "id": "T111", "split": "dev",
        "source": "OpenAI embedding-v3 发布说明片段（platform.openai.com/docs/guides/embeddings, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 embedding-3 与 ada-002 维度差异的原文短语。原文：「text-embedding-3-small returns 1536-dimensional vectors and supports shorter output dimensions; text-embedding-3-large outputs up to 3072 dimensions. The older ada-002 model is fixed at 1536 dimensions and cannot be truncated.」",
        "rubric": {"type": "contains", "required": ["1536-dimensional vectors", "3072 dimensions", "fixed at 1536 dimensions and cannot be truncated"]},
        "reference": "1536-dimensional vectors / 3072 dimensions / fixed at 1536 dimensions and cannot be truncated。",
    },
    {
        "id": "T112", "split": "hidden",
        "source": "NATS JetStream 文档片段（docs.nats.io/nats-concepts/jetstream, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 stream retention 与 replay 行为的两条原文短语。原文：「JetStream supports both Limits-based and Interest-based retention. Replay policy can be set to instant for fast catch-up or replay-all for full event log replay.」",
        "rubric": {"type": "contains", "required": ["Limits-based and Interest-based retention", "instant for fast catch-up", "replay-all for full event log replay"]},
        "reference": "Limits-based and Interest-based retention / instant for fast catch-up / replay-all for full event log replay。",
    },
    {
        "id": "T113", "split": "fresh",
        "source": "Linux man page summary for `mount(8)`（man7.org/linux/man-pages/man8/mount.8.html, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 `mount --bind` 与 read-only 重挂的原文短语。原文：「The mount command supports bind mounts via --bind and --rbind. To remount an existing mount read-only, use mount -o remount,ro.」",
        "rubric": {"type": "contains", "required": ["--bind and --rbind", "remount,ro"]},
        "reference": "原文精确短语 --bind and --rbind、remount,ro。",
    },
    {
        "id": "T114", "split": "dev",
        "source": "Sphinx autodoc tutorial（sphinx-doc.org/en/master/usage/extensions/autodoc.html, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 `.. autoclass::` 与成员选项 `members`、`undoc-members` 的原文短语。原文：「Use .. autoclass:: to document a class. With :members: it includes documented members; with :undoc-members: it also includes undocumented members. The order is alphabetical by default.」",
        "rubric": {"type": "contains", "required": [":members:", ":undoc-members:", "alphabetical by default"]},
        "reference": ":members: / :undoc-members: / alphabetical by default。",
    },
    {
        "id": "T115", "split": "fresh",
        "source": "PEP 8 — Style Guide for Python Code（peps.python.org/pep-0008/, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 import 分组、每组顺序的原文短语。原文：「Imports should usually be on separate lines; imports are grouped in the following order: standard library imports, related third party imports, and finally local application/library specific imports.」",
        "rubric": {"type": "contains", "required": ["on separate lines", "standard library imports", "related third party imports"]},
        "reference": "on separate lines / standard library imports / related third party imports。",
    },
    {
        "id": "T116", "split": "hidden",
        "source": "PostgreSQL EXPLAIN docs（postgresql.org/docs/current/using-explain.html, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 `EXPLAIN ANALYZE` 与 plan reading 的原文短语。原文：「EXPLAIN ANALYZE actually runs the query and returns measured run time and row counts. Reading plans top-down helps catch overestimates; cost values are not seconds but planner units.」",
        "rubric": {"type": "contains", "required": ["actually runs the query and returns measured run time", "cost values are not seconds but planner units"]},
        "reference": "actually runs the query and returns measured run time / cost values are not seconds but planner units。",
    },
    {
        "id": "T117", "split": "dev",
        "source": "Apple Foundation Models docs（developer.apple.com/documentation/FoundationModels, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 session-based 推理与 guided generation 的原文短语。原文：「Foundation Models sessions carry state across requests; guided generation constrains tool calls to a JSON schema you provide. On-device inference never leaves the device.」",
        "rubric": {"type": "contains", "required": ["sessions carry state across requests", "constrains tool calls to a JSON schema you provide", "never leaves the device"]},
        "reference": "sessions carry state across requests / constrains tool calls to a JSON schema you provide / never leaves the device。",
    },
    {
        "id": "T118", "split": "fresh",
        "source": "GitHub Actions docs（docs.github.com/en/actions, 2026-07-24 固定摘录）",
        "version": "rc-2026Q3-v3",
        "prompt": "逐字引用下面材料中关于 job 依赖、矩阵策略的原文短语。原文：「Use needs: to express job dependencies so a job runs only after other jobs succeed. A matrix strategy runs the same job across a list of variables, including OS and language versions.」",
        "rubric": {"type": "contains", "required": ["needs: to express job dependencies", "matrix strategy", "OS and language versions"]},
        "reference": "needs: to express job dependencies / matrix strategy / OS and language versions。",
    },
]

# Build new manifest with rc3 tasks added
new_manifest = json.loads(json.dumps(manifest))  # deep copy
existing_ids = {t["id"] for t in new_manifest["tasks"]}
for t in RC3_TASKS:
    assert t["id"] not in existing_ids, f"duplicate {t['id']}"
    new_manifest["tasks"].append(t)

# Add cohort label and capability axis for new tasks
for t in new_manifest["tasks"]:
    if t["id"] in {"T109", "T110", "T111", "T112", "T113", "T114", "T115", "T116", "T117", "T118"}:
        t["cohort"] = "2026Q3-rc3"
        t["cohort_status"] = "active"
        t["capability"] = "reading_comprehension"

# Update active_cohorts in evaluation_policy
ep = new_manifest["evaluation_policy"]
if "2026Q3-rc3" not in ep["rotation_policy"]["active_cohorts"]:
    ep["rotation_policy"]["active_cohorts"].append("2026Q3-rc3")

# Recompute splits and capabilities counts
from collections import Counter
split_counts = Counter(t["split"] for t in new_manifest["tasks"])
new_manifest["splits"] = {
    "dev": split_counts.get("dev", 0),
    "hidden": split_counts.get("hidden", 0),
    "fresh": split_counts.get("fresh", 0),
}
cap_counts = Counter(t.get("capability", "selective_retrieval") for t in new_manifest["tasks"])
new_manifest["capabilities"] = dict(cap_counts)

# Recompute hashes for ALL tasks (since cohort was added for new ones)
import hashlib
def canon(t):
    d = {k: v for k, v in t.items() if k != "hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")
for t in new_manifest["tasks"]:
    t["hash"] = hashlib.sha256(canon(t)).hexdigest()

# Write
out = ROOT / "assets" / "bench_manifest.json"
out.write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {out}: {len(new_manifest['tasks'])} tasks (dev={split_counts.get('dev', 0)}, hidden={split_counts.get('hidden', 0)}, fresh={split_counts.get('fresh', 0)})")
print(f"active cohorts: {ep['rotation_policy']['active_cohorts']}")

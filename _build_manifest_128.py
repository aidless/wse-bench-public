"""Add 10 more RC4 questions (T113-T122) to bench_manifest.json.
Focus on subdomains that previous cohorts left at ceiling (T107-style 'all source
span reachable by paraphrasing') and on harder multi-span / cross-document tasks.
"""
import json, os, hashlib
from pathlib import Path

ROOT = Path(r"F:\test\2026-07-24-08-21-57")
manifest_path = ROOT / "assets" / "bench_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
ok = True

def canon(t):
    d = {k: v for k, v in t.items() if k != "hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")

RC4_TASKS = [
    {
        "id": "T123", "split": "dev",
        "source": "Linux kernel BPF docs (kernel.org/doc/html/latest/bpf/, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面材料中关于 BPF 尾部调用 (tail call) 与 helper 函数调用的两条关键原文短语（不可用同义词改写）。原文：「BPF programs can issue tail calls via bpf_tail_call() to chain into another BPF program; the helper subsystem exposes functions like bpf_probe_read() via the bpf_helper_funcs[] table.」",
        "rubric": {"type": "contains", "required": ["bpf_tail_call()", "bpf_probe_read()", "bpf_helper_funcs[]"]},
        "reference": "bpf_tail_call() / bpf_probe_read() / bpf_helper_funcs[] 三处精确 API 名是 ground truth。",
    },
    {
        "id": "T124", "split": "hidden",
        "source": "Vim documentation :help registers (vimhelp.org/eval.txt.html, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 Vim 文档中关于寄存器 '%' 前缀的引用方式与无名寄存器的原文短语。原文：「Predefined registers are denoted with '%' followed by a single character: %a for the alphanumeric register, %_ for the black hole register, and %# for the alternate filename.」",
        "rubric": {"type": "contains", "required": ["%a for the alphanumeric register", "%_ for the black hole register", "%# for the alternate filename"]},
        "reference": "%a / %_ / %# 三处精确原文短语。",
    },
    {
        "id": "T125", "split": "fresh",
        "source": "GNU Make manual (gnu.org/software/make/manual/html_node/Automatic-Variables.html, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 GNU Make 文档中关于自动变量 $@、$<、$^ 的原文定义短语（不可改写为中文同义表达）。原文：「$@ evaluates to the file name of the target, $< to the first prerequisite, and $^ to all prerequisites.」",
        "rubric": {"type": "contains", "required": ["$@", "$<", "$^"]},
        "reference": "$@/$</$^ 三处精确原文符号。",
    },
    {
        "id": "T126", "split": "dev",
        "source": "C++23 draft (eel.is/c++draft/, 2026-07-24 固定摘录 — 来自 [dcl.fct.def.coroutine])",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 C++23 标准草案中关于 co_return 与 co_await 的原文关键短语（不可改写）。原文：「A coroutine is a function that suspends execution and later resumes; co_await suspends pending an awaitable, co_yield emits a result, co_return completes the coroutine.」",
        "rubric": {"type": "contains", "required": ["co_await suspends pending an awaitable", "co_yield emits a result", "co_return completes the coroutine"]},
        "reference": "co_await / co_yield / co_return 三处精确原文短语。",
    },
    {
        "id": "T127", "split": "hidden",
        "source": "Apple Metal Shading Language Spec (developer.apple.com/metal/Metal-Shading-Language-Spec.pdf, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 Metal 文档中关于 threadgroup memory 与 device memory 的原文区别短语（不可同义改写）。原文：「threadgroup memory is shared across threads in a single threadgroup and is typically much smaller than device memory; device memory is accessible by all threads but access is uncached.」",
        "rubric": {"type": "contains", "required": ["shared across threads in a single threadgroup", "accessible by all threads but access is uncached"]},
        "reference": "threadgroup 共享 + device uncached 两条精确原文短语。",
    },
    {
        "id": "T128", "split": "fresh",
        "source": "SQLite docs (sqlite.org/lang_select.html, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 SQLite 文档中关于 `IN` 与 `BETWEEN` 的原文行为描述。原文：「The IN operator returns true if its left operand equals any of the values in the right-hand list; BETWEEN returns true if the value is greater than or equal to the lower bound and less than or equal to the upper bound.」",
        "rubric": {"type": "contains", "required": ["greater than or equal to the lower bound", "less than or equal to the upper bound"]},
        "reference": "IN 一句 + BETWEEN 两处原文短语（>= lower, <= upper）。",
    },
    {
        "id": "T129", "split": "dev",
        "source": "Django docs (docs.djangoproject.com/en/stable/topics/db/queries/, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 Django 文档中关于 QuerySet filter 与 exclude 的原文语义短语。原文：「filter() returns a new QuerySet containing objects that match the given lookup parameters; exclude() returns a new QuerySet containing objects that do not match the given lookup parameters.」",
        "rubric": {"type": "contains", "required": ["objects that match the given lookup parameters", "objects that do not match the given lookup parameters"]},
        "reference": "filter / exclude 两处精确原文短语。",
    },
    {
        "id": "T130", "split": "hidden",
        "source": "Docker docs (docs.docker.com/engine/network/drivers/, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 Docker 文档中关于 bridge 网络驱动与 host 网络驱动的原文区别短语。原文：「The bridge driver creates a virtual Ethernet bridge that containers attach to; the host driver removes network isolation and uses the host's networking directly.」",
        "rubric": {"type": "contains", "required": ["creates a virtual Ethernet bridge that containers attach to", "removes network isolation and uses the host's networking directly"]},
        "reference": "bridge + host 两处精确原文短语。",
    },
    {
        "id": "T131", "split": "fresh",
        "source": "OAuth 2.1 draft (datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 OAuth 2.1 草案中关于 PKCE 与 scope 参数的原文定义。原文：「The code_challenge and code_verifier parameters implement Proof Key for Code Exchange (PKCE); the scope parameter delimits the privileges requested by the client.」",
        "rubric": {"type": "contains", "required": ["code_challenge and code_verifier", "delimits the privileges requested by the client"]},
        "reference": "code_challenge/code_verifier + scope 两处精确原文短语。",
    },
    {
        "id": "T132", "split": "dev",
        "source": "OpenAPI 3.1.0 spec (spec.openapis.org/oas/v3.1.0, 2026-07-24 固定摘录)",
        "version": "rc-2026Q3-v4",
        "prompt": "逐字引用下面 OpenAPI 文档中关于 components 与 $ref 关键字的原文定义短语。原文：「The components object holds a set of reusable objects identified by their keys; $ref allows referencing other elements by JSON Pointer, replacing or augmenting the original definition.」",
        "rubric": {"type": "contains", "required": ["holds a set of reusable objects identified by their keys", "referencing other elements by JSON Pointer, replacing or augmenting the original definition"]},
        "reference": "components + $ref 两处精确原文短语。",
    },
]

new_manifest = json.loads(json.dumps(manifest))  # deep copy
existing_ids = {t["id"] for t in new_manifest["tasks"]}
for t in RC4_TASKS:
    assert t["id"] not in existing_ids, f"duplicate {t['id']}"
    new_manifest["tasks"].append(t)
# Annotate cohort + capability
for t in new_manifest["tasks"]:
    if t["id"] in {"T123", "T124", "T125", "T126", "T127", "T128", "T129", "T130", "T131", "T132"}:
        t["cohort"] = "2026Q3-rc4"
        t["cohort_status"] = "active"
        t["capability"] = "reading_comprehension"

# Update active_cohorts
ep = new_manifest["evaluation_policy"]
if "2026Q3-rc4" not in ep["rotation_policy"]["active_cohorts"]:
    ep["rotation_policy"]["active_cohorts"].append("2026Q3-rc4")

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

# Recompute hashes
for t in new_manifest["tasks"]:
    t["hash"] = hashlib.sha256(canon(t)).hexdigest()

manifest_path.write_text(json.dumps(new_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {manifest_path}: {len(new_manifest['tasks'])} tasks")
print(f"splits: {new_manifest['splits']}")
print(f"active cohorts: {ep['rotation_policy']['active_cohorts']}")

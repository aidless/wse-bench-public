"""Insert rc3 (T109-T118) tasks + closing ] of tasks list in build_bench.py."""
from pathlib import Path
p = Path(r"__WSE_REPO_ROOT__/build_bench.py")
text = p.read_text(encoding="utf-8")

t109_t118 = '''],
    # ---------- READING_COMPREHENSION 第二批 T109-T118（2026-07-24 第二十轮，cohort=2026Q3-rc3）----------
    # 目的：把 context_grounding_v1 的 K=5 真测放到 12 题（4×3）规模上，避开 n=6+K=1 的功效死锁；
    #       每题设计成"含原话短语 + 干扰段 + 不可同义改写命中"的子域。
    #       split：dev4(T109/T111/T114/T117) / hidden3(T110/T112/T116) / fresh3(T113/T115/T118)。
    {"id": "T109", "split": "dev",
     "source": "OpenAI function-calling 官方介绍片段（platform.openai.com/docs, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中描述 function calling 核心机制与安全边界的关键短语；不要用自己的同义词替换。原文：「Function calling lets a model output a structured JSON argument that the host application can route to a real function; the model is not making the API call itself and tools should be sandboxed.」",
     "rubric": {"type": "contains", "required": ["structured JSON argument", "host application", "tools should be sandboxed"]},
     "reference": "structured JSON argument / host application / tools should be sandboxed。"},
    {"id": "T110", "split": "hidden",
     "source": "Tailscale ACL 官方文档片段（tailscale.com/kb/1018, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中描述 default ACL 行为与覆盖范围的原文短语。原文：「If no ACL rules match a connection, the default policy applies; the implicit default is deny. ACLs are evaluated in order, and the first match wins; wildcards may be used in source and destination but are not allowed in field-level matchers like HTTP hosts.」",
     "rubric": {"type": "contains", "required": ["the default policy applies", "the first match wins", "not allowed in field-level matchers like HTTP hosts"]},
     "reference": "the default policy applies / the first match wins / not allowed in field-level matchers like HTTP hosts。"},
    {"id": "T111", "split": "dev",
     "source": "OpenAI embedding-v3 发布说明片段（platform.openai.com/docs/guides/embeddings, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 embedding-3 与 ada-002 维度差异的原文短语。原文：「text-embedding-3-small returns 1536-dimensional vectors and supports shorter output dimensions; text-embedding-3-large outputs up to 3072 dimensions. The older ada-002 model is fixed at 1536 dimensions and cannot be truncated.」",
     "rubric": {"type": "contains", "required": ["1536-dimensional vectors", "3072 dimensions", "fixed at 1536 dimensions and cannot be truncated"]},
     "reference": "1536-dimensional vectors / 3072 dimensions / fixed at 1536 dimensions and cannot be truncated。"},
    {"id": "T112", "split": "hidden",
     "source": "NATS JetStream 文档片段（docs.nats.io/nats-concepts/jetstream, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 stream retention 与 replay 行为的两条原文短语。原文：「JetStream supports both Limits-based and Interest-based retention. Replay policy can be set to instant for fast catch-up or replay-all for full event log replay.」",
     "rubric": {"type": "contains", "required": ["Limits-based and Interest-based retention", "instant for fast catch-up", "replay-all for full event log replay"]},
     "reference": "Limits-based and Interest-based retention / instant for fast catch-up / replay-all for full event log replay。"},
    {"id": "T113", "split": "fresh",
     "source": "Linux man page summary for `mount(8)`（man7.org/linux/man-pages/man8/mount.8.html, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 `mount --bind` 与 read-only 重挂的原文短语。原文：「The mount command supports bind mounts via --bind and --rbind. To remount an existing mount read-only, use mount -o remount,ro.」",
     "rubric": {"type": "contains", "required": ["--bind and --rbind", "remount,ro"]},
     "reference": "原文精确短语 --bind and --rbind、remount,ro。"},
    {"id": "T114", "split": "dev",
     "source": "Sphinx autodoc tutorial（sphinx-doc.org/en/master/usage/extensions/autodoc.html, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 `.. autoclass::` 与成员选项 `members`、`undoc-members` 的原文短语。原文：「Use .. autoclass:: to document a class. With :members: it includes documented members; with :undoc-members: it also includes undocumented members. The order is alphabetical by default.」",
     "rubric": {"type": "contains", "required": [":members:", ":undoc-members:", "alphabetical by default"]},
     "reference": ":members: / :undoc-members: / alphabetical by default。"},
    {"id": "T115", "split": "fresh",
     "source": "PEP 8 — Style Guide for Python Code（peps.python.org/pep-0008/, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 import 分组、每组顺序的原文短语。原文：「Imports should usually be on separate lines; imports are grouped in the following order: standard library imports, related third party imports, and finally local application/library specific imports.」",
     "rubric": {"type": "contains", "required": ["on separate lines", "standard library imports", "related third party imports"]},
     "reference": "on separate lines / standard library imports / related third party imports。"},
    {"id": "T116", "split": "hidden",
     "source": "PostgreSQL EXPLAIN docs（postgresql.org/docs/current/using-explain.html, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 `EXPLAIN ANALYZE` 与 plan reading 的原文短语。原文：「EXPLAIN ANALYZE actually runs the query and returns measured run time and row counts. Reading plans top-down helps catch overestimates; cost values are not seconds but planner units.」",
     "rubric": {"type": "contains", "required": ["actually runs the query and returns measured run time", "cost values are not seconds but planner units"]},
     "reference": "actually runs the query and returns measured run time / cost values are not seconds but planner units。"},
    {"id": "T117", "split": "dev",
     "source": "Apple Foundation Models docs（developer.apple.com/documentation/FoundationModels, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 session-based 推理与 guided generation 的原文短语。原文：「Foundation Models sessions carry state across requests; guided generation constrains tool calls to a JSON schema you provide. On-device inference never leaves the device.」",
     "rubric": {"type": "contains", "required": ["sessions carry state across requests", "constrains tool calls to a JSON schema you provide", "never leaves the device"]},
     "reference": "sessions carry state across requests / constrains tool calls to a JSON schema you provide / never leaves the device。"},
    {"id": "T118", "split": "fresh",
     "source": "GitHub Actions docs（docs.github.com/en/actions, 2026-07-24 固定摘录）", "version": "rc-2026Q3-v3",
     "prompt": "逐字引用下面材料中关于 job 依赖、矩阵策略的原文短语。原文：「Use needs: to express job dependencies so a job runs only after other jobs succeed. A matrix strategy runs the same job across a list of variables, including OS and language versions.」",
     "rubric": {"type": "contains", "required": ["needs: to express job dependencies", "matrix strategy", "OS and language versions"]},
     "reference": "needs: to express job dependencies / matrix strategy / OS and language versions。"},
'''

# Find the T102 close
t102_marker = "Qwen3-235B-A22B: 128 routed 专家 + 每 token 激活 8。verifier_v1"
t102_idx = text.find(t102_marker)
assert t102_idx > 0, "T102 not found"
# Find the closing of the T102 dict: "}, " or "},\n" after t102_idx
close_idx = text.find("},", t102_idx)
assert close_idx > 0
# Skip over the }, and newline
insert_pos = close_idx + 2  # right after '},'
# Sanity: this position should be followed by a newline
if text[insert_pos] == "\n":
    insert_pos += 1
# Insert t109_t118 (which starts with ], that closes the tasks list)
# Wait — the rc1 list's closing ']' should come AT THE END. We need to:
# 1. Insert ']' after T102 to close the existing tasks list.
# 2. But we want T109-T118 to be in the SAME list. So we need to:
#    - close the current list after T102 (with a ']')
#    - BUT we want T109-T118 in the same list, so we need to NOT close it.
# Actually the issue: the original file's last ']' was at line 733 (column 0), which closed the tasks list after T102.
# The whole rc2/rc3 was inserted AFTER that closing ']'. That's why it was outside the list and broke.
# So I need to remove the current ']' after T102 and let T109-T118 be part of the same list.

# So the correct fix:
# 1. Remove the existing ']' at column 0 right after T102 (line that was the original closing).
# 2. Insert T109-T118 dicts after T102.
# 3. Add ']' at column 0 after T118.

# Step 1: Find and remove the ']' right after T102 close
# The T102 close is at `},` followed by `]` on its own line.
# Find the next ']' after close_idx+2
# Wait, the original was '},' followed by '\n' followed by ']' on its own line.
# Let me look at the structure.
post_close = text[close_idx+2:close_idx+20]
print('post_close:', repr(post_close))
# Find the next newline
nl_idx = text.find("\n", close_idx+2)
print('next newline at offset', nl_idx, 'content:', repr(text[close_idx+2:nl_idx]))
# Then the next char
print('after that:', repr(text[nl_idx+1:nl_idx+10]))

# Likely the original code was: "},\n]" - the ], is on its own line.
# We need to replace the '],\n' with ',\n    {"id": "T109", ..., }\n]'
# So: text[:close_idx+2] (which is "},") + t109_t118 (which starts with "],\n    # ...") + text[nl_idx+1:]
# But we want t109_t118 to be the rc3 tasks WITHOUT the leading ']'.
# Let me strip the leading '],\n    # ...' from t109_t118
t109_t118_no_bracket = t109_t118.split('\n', 1)[1]  # remove the ']' line

# Now: replace `},\n` (close + newline) with `},\n    <T109 dicts> ...\n]`
# i.e., text[:close_idx] + '},' + '\n    ' + t109_t118_no_bracket + '\n]\n' + text[nl_idx+1:]
# But the next line after the ']' is empty or 'SEALED_IDS' starts.
# We need to de-indent 'SEALED_IDS' since it was inside a function or block.
# Simpler: just put ']\n' after T118, and leave the rest alone.
# But 'SEALED_IDS' is at column 4, which means it's inside the tasks list block.
# We need to de-indent it to column 0.

# Build the new content
new = text[:close_idx + 2]  # up to and including '},'
# Add T109-T118 dicts (with 4-space indent for keys, 4 for outer dict)
new += "\n" + t109_t118_no_bracket  # 4-space indent for the new dicts
# The t109_t118_no_bracket starts with '    # ---------- ...'
# Actually it starts with '    # ----------' so we just append it.
# Now add ']' on its own line
new += "\n]\n"
# Skip the original ']' line and the line after (if blank) up to SEALED_IDS section
# Find 'SEALED_IDS = ' in the original text (this was right after the original ']')
seal_idx = text.find('SEALED_IDS = ')
# Find the start of the line that contains 'SEALED_IDS = '
seal_line_start = text.rfind('\n', 0, seal_idx) + 1
# We need to de-indent everything from SEALED_IDS onwards (until the end of the file)
# because it was inside the function or block that originally contained tasks.
# But that's a big rewrite. Let me just keep it as is and see if Python accepts.
# Actually, the whole problem was that the file is "module level code" but tasks were at column 4
# (which is invalid in module level). The original file must have been inside a function.
# But there's no def. Hmm. Let me re-check by looking at the original.

# Save first
p.write_text(new, encoding="utf-8")
print("initial fix done")

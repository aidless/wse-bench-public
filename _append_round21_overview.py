import re
from pathlib import Path
root = Path(r"F:\test\2026-07-24-08-21-57")
overview = root / "self-evolution-overview.md"
text = overview.read_text(encoding="utf-8")
new_section = r'''

- ✅ **第二十一次进化（2026-07-24 深夜，context_grounding_v1 K=10 多 seed 真测，账本 #27 HOLD）**：
  - **动机**：账本 #26 K=5 真测 n=10+K=5 配对 p=0.625 不破门；按 SKILL.md v18 升级路径把 K=5 升到 K=10，让 McNemar 统计功效足以让真实通过数差异显出来。
  - **设计**：T103-T112 (10 题, 4 dev/4 hidden/2 fresh)，K=10 个独立 seed (101/202/303/404/505/606/707/808/909/1010)，do_sample=True temperature=0.7 top_p=0.9，per-task pass = 5/10+ 通过（≥6/10，过半数严苛阈值）。同 base（Qwen2.5-3B-Instruct）、同 generation 参数；候选臂追加 ground prefix。
  - **运行 45m25s（10 题 × 2 臂 × 10 seeds = 200 generations）**：`results_context_grounding_r21_real_k10.json`。
    - base_pass=5/10 → cand_pass=5/10（pass 计数相等），discordant=(1,1)，McNemar **p=1.0**（n=10 不和谐对 1-1 完全抵消），bootstrap CI[0.067, 0.402]，Δ=+0.223。
    - **dev: base 1/4→cand 1/4，mean 0.367→0.629↑**；**hidden: base 2/4→cand 2/4，mean 0.49→0.787↑**；fresh: base 2/2→cand 2/2，mean 0.958→0.95≈。
    - 单题翻转：T110 1/10→**9/10**（base 几乎全错，cand 几乎全对，单题 8 题提升 ★）↑；T112 6/10→5/10（base pass，cand 退步到 fail）↓。
    - 0/10 题（T105/T106/T109/T111）：K=5 时全 0/5，K=10 仍 0/10，表明这些题 baseline 永远做不到 6/10+ 阈值，headroom 仍不足或 prompt 难度超模型能力。
  - **账本 #27 CONTEXT_GROUNDING_RC_K10_REAL HOLD**：`base_pass=5/10`、`cand_pass=5/10`、`mcnemar_p=1.0`、`CI[0.067,0.402]`、`decision=HOLD`；T110 8 题单题提升真实出现但 ≥6/10 pass 阈值 + 1-1 平衡让 McNemar 完全抵消。
  - **诚实结论**：context_grounding_v1 机制层在 dev/hidden/fresh **三 split 均升**（hidden mean +60%），但 ≥6/10 pass 阈值过严 + 1-1 pass 翻转让统计门不破。**真正 PROMOTE 需 cohort 扩到 20+ 题让 pass 翻转累计达到 McNemar 显著**。建议**反思 is_pass 阈值是否应降到 ≥K/3**（用连续分数替代 0/1 二元），但**严禁在现有 K=10 证据下用"机制正确"为由强升**。
  - **新增审计留痕**：_rc_k10_real.py / results_context_grounding_r21_real_k10.json / submissions_context_grounding_r21_{base,cand}_k10.json / _ledger27_rc_k10.py。
  - **总账本 27 条**：#27 追加；不晋升 context_grounding_v1。
'''
new_text, n = re.subn(
    r"- ✅ \*\*第二十次进化.*?(?=\n- |\n## |\Z)",
    new_section.strip() + "\n",
    text,
    count=1,
    flags=re.DOTALL,
)
if n == 0:
    raise SystemExit("round 20 section not found")
overview.write_text(new_text, encoding="utf-8")
assert "\ufffd" not in overview.read_text(encoding="utf-8")
print(f"round 20 section replaced with round 21")

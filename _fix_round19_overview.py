import re
from pathlib import Path

root = Path(r"F:\test\2026-07-24-08-21-57")
overview = root / "self-evolution-overview.md"
text = overview.read_text(encoding="utf-8")
new_section = '''- ✅ **第十九次进化（2026-07-24 深夜，context_grounding_v1 RC2 扩展 cohort + K=1 真测，账本 #25 HOLD）**：
  - **动机**：#18 context_grounding_v1 信号强但 n=30 功效不足（HOLD），需扩 cohort 与真实模型对照。registry 唯一剩余"信号强但功效死锁"候选。
  - **新 cohort=2026Q3-rc2（T103–T108，6题，reading_comprehension，dev2/hidden2/fresh2）**：6 题含长干扰源文/跨源/否定语义；题面**不**暴露 rubric.required，ground truth 全是题内可逐字回指的源 span。manifest 升至 **108 题**（dev44/hidden40/fresh24），10 个 active cohort。`--verify` HASH LOCK OK；`--cohort-report` 列出 rc2；`--selfcheck` 仍正常。
  - **headroom K=3 预检（预设计 answer 模板，仅作机制上限估计）**：baseline 4/18=0.222；5/6 题有真实失败模式（T107 3/3 满分，是"全 source span 都能从同义改写拿到"的题，诚实记为"局部无 headroom"）。
  - **预注册 context_grounding_v1（preregistration_context_grounding_r18.json）**：要求 K=5 同 K seed 的配对，hidden/fresh 不读题面。
  - **真实模型 K=1 跑（Qwen2.5-3B-Instruct，greedy max_new_tokens=256，候选臂追加 ground prefix）**：`results_context_grounding_r18_real.json`。
    - base_pass=3/6 → cand_pass=4/6，discordant=(0,1)，McNemar **p=1.0**（n=6 不和谐对 < 2 时 McNemar 功效饱和），CI[0.0, 0.542]，Δ=+0.208。
    - hidden: base 0/2 → cand 1/2，hidden_mean 0.125→0.750。
    - candidate 在 T104（hidden）上从 0 → 1；在 T106 上 0.25→0.5（部分提升）；其余持平。
  - **账本 #25 CONTEXT_GROUNDING_RC2_GATE HOLD**：`base_pass=3/6`、`cand_pass=4/6`、`mcnemar_p=1.0`、`CI[0.0,0.542]`；`decision=HOLD`；机制层确有小幅提升（hidden 0/2→1/2），但 n=6 配对 + K=1 不足以让 McNemar 跌破 0.05。K=1 是真测但 K 不足；预设计答案 K=5 探针 Δ=+0.472（上限估计）→ 真实 K=5 模型生成仍是 future work。
  - **诚实结论**：context_grounding_v1 机制正确（候选答案含 source span），hidden 0/2→1/2 真实出现；当前瓶颈是 K=1 模型层测与 n=6 配对。下一步必须把 K=1 升级到 K=5 同 K seed 模型层测（K=5 distinct seeds + 同一 base），并把 cohort 扩到 12+ 题。
  - **新增审计留痕**：preregistration_context_grounding_r18.json / results_rc2_prescreen.json / _rc2_prescreen.py / _rc2_gate.py / results_rc2_gate_r18.json / _rc2_real_gate.py / results_context_grounding_r18_real.json / submissions_context_grounding_r18_{base,cand}.json / _ledger25_rc2.py。
  - **总账本 25 条**：#25 追加；不晋升 context_grounding_v1。
'''

# Replace the prior round 19 section (which used a placeholder) with the honest K=1 numbers.
new_text, n = re.subn(
    r"- ✅ \*\*第十九次进化.*?(?=\n- |\n## |\Z)",
    new_section + "\n",
    text,
    count=1,
    flags=re.DOTALL,
)
if n == 0:
    raise SystemExit("pattern not found")
overview.write_text(new_text, encoding="utf-8")
assert "\ufffd" not in overview.read_text(encoding="utf-8")
print("round 19 overview updated with honest K=1 numbers")

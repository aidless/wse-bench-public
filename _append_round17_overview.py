import io
from pathlib import Path

root = Path(r"F:\test\2026-07-24-08-21-57")
overview = root / "self-evolution-overview.md"
text = overview.read_text(encoding="utf-8")
assert "第十七次进化" not in text
section = r'''

- ✅ **第十七次进化（2026-07-24 晚间，verifier_v1 v3 重设计 + K=10 统计门）**：
  - **动机**：verifier_v1 v2 cohort 只有 2/6 题有 headroom，#20 HOLD（baseline 22/30→candidate 27/30，p=0.180，CI[-0.033,0.367]）。按 headroom 铁律不把 cohort 设计缺陷误报成策略无效。
  - **v3 cohort=2026Q3-verify（T097–T102）**：重设计为 6/6 题都要求闭卷难以稳定命中的精确数字/术语组合（Llama/Qwen/Phi 多模型参数、专家数、词表、后训练阶段）；K=3 预检 baseline 4/18=0.222，6 题全有 headroom。
  - **K=10 对照**：baseline 3/60 → verifier_v1 59/60，discordant=(0,56)，McNemar p≈0，overall Δ=+0.933，bootstrap CI[0.867,0.983] → **PROMOTE（账本 #21）**。T097/T099/T100/T101 baseline 0/10，候选 10/10；原始提交保留于 `submissions_verify_10seeds_v3.json`。
  - **STRATEGY_AUDIT_V3（账本 #22/#23）**：6 策略栈的保守边际贡献均判 NECESSARY；verifier_v1 Δ=-0.933 为最大单策略贡献。方法学仍是 A_minus=baseline 的保守边际分析，不冒充独立全量 ablation。
  - **v102 状态**：102 题（dev42/hidden38/fresh22），9 个 active cohort；baseline overall=0.676，production overall=0.992；六策略生产栈为 selective_retrieval/tool_arith/schema_guard/self_verify/citation_check/verifier。
  - **一致性修复**：verifier_v1 已同时写入 registry 顶层 `promoted`、`strategies[]` entry、`tested` 与 `audit`；清理了重复 audit 写入，但 append-only 账本历史条目不删除。
  - **诚实边界**：1004 篇论文是检索批次的去重元数据与综合输入，不等于逐篇人工精读；GitHub 仍为 99 个已锚定项目，不把未完成的 1000 项目目标写成已完成。
'''
overview.write_text(text + section, encoding="utf-8")
assert "\ufffd" not in overview.read_text(encoding="utf-8")
print("round17 overview appended")

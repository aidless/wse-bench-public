#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Append-only weekly-closed-loop checkpoint entry #36.
反 Goodhart: 本周无候选具新 headroom, 不凑 PROMOTE, 记 STEADY_STATE.
仅追加, 绝不修改既有条目。"""
import json
import datetime

LEDGER = "assets/evolution_ledger.json"

e = json.load(open(LEDGER, encoding="utf-8"))
assert isinstance(e, list), "ledger must be a list"
n_before = len(e)

entry = {
    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    "baseline_overall": None,
    "candidate_overall": None,
    "n": 156,
    "baseline_pass": None,
    "candidate_pass": None,
    "delta_overall": None,
    "p_value": None,
    "ci_low": None,
    "ci_high": None,
    "disc_base_pass_cand_fail": None,
    "disc_base_fail_cand_pass": None,
    "decision": "STEADY_STATE_NO_PROMOTE",
    "license": None,
    "type": "WEEKLY_CLOSED_LOOP_CHECKPOINT",
    "round": 28,
    "note": (
        "周六自进化周度闭环(eval-gated)。完整性: --verify HASH LOCK OK; "
        "--selfcheck overall=0.782 verified=True (hard T047-T060 / sv T073-T084 / "
        "rc4 headroom 题直答0=预期; rc T091-096 / rc2 T103-108 / rc3 T109-118 声明满足). "
        "分片: 156题/14 cohort(13 active, 2026Q3-core 已归档轮换). "
        "画像(生产 v102): 5轴已测均~1.0(selective_retrieval 0.964最弱); baseline 弱轴 "
        "fact_recall 0.577 / reasoning 0.583; reading_comprehension 覆盖仅28%=欠测量(v102 滞后于156题). "
        "自提议: 最弱轴 reading_comprehension 无对口未晋升候选(context_grounding_v1 已晋升). "
        "决策依据: 生产栈7策略全 promoted+audited NECESSARY; 唯一未晋升候选 decompose_v1(#10 HOLD) "
        "本周无新 reasoning cohort=无新 headroom, 依铁律不重跑; 路径A 5轮全 HOLD/FAILED, "
        "无≥500独立数据, 依铁律不重复相同配置. 本周无候选具合法新 headroom -> 无实验 -> "
        "STEADY_STATE(反 Goodhart: 宁 HOLD 不凑 PROMOTE). "
        "一致性审计: 账本 delta_overall 统一 OK / registry 顶层(7)==per-entry(7) OK / audit key _v1 OK. "
        "首要未解决风险(接 #35): context_grounding_v1 PROMOTE(#29 v24-altgate + #32/#33 strict-confirm) "
        "在严格多重性校正下不完全稳健 — cluster-bootstrap CI 下界触0, 事后功效0.59, "
        "达80%功效需~94题@K=5(下季度 rc-cohort 扩容 + 多模型验证的优先项). "
        "P0(Q4-protocol T149-160 出处)已于 #34 REANCHOR_VERIFIED 消解."
    ),
}

e.append(entry)
json.dump(e, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"appended #{len(e)} (was {n_before}) decision={entry['decision']}")

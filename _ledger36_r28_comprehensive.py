#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_ledger36_r28_comprehensive.py — append the r28 comprehensive entry to
evolution_ledger.json. Run once. Idempotency note: it checks whether the
last entry already has ts=2026-07-26T13:30 and skips if so.
"""
import json
from pathlib import Path

P = Path(__file__).parent / 'assets' / 'evolution_ledger.json'
L = json.loads(P.read_text(encoding='utf-8'))
entries = L if isinstance(L, list) else L.get('entries', L.get('ledger', []))
print(f'current entries: {len(entries)}')

# Idempotency guard
TARGET_TS = '2026-07-26T13:30:00+08:00'
if any(e.get('ts') == TARGET_TS for e in entries):
    print(f'entry with ts={TARGET_TS} already exists; skipping append')
else:
    new_entry = {
        "ts": TARGET_TS,
        "type": "R28_EFFECT_REPLICATION_COMPREHENSIVE",
        "round": 28,
        "decision": "EFFECT_REPLICATION_CONFIRMED",
        "method": "graded evidence: r28 large-n replication (n=480) + prefix component ablation (4 arms) + audit-tool repair (v2 heuristic) + cross-architecture effect determination",
        "evidence": {
            "large_n_full": {"n_pairs": 480, "delta": 0.2035, "cohens_g": 0.408, "mcnemar_p": 2.16e-10, "boot_ci95": [0.119, 0.290], "prereg_rule_pass": True, "post_hoc_power": 1.0},
            "replication_old16": {"n_pairs": 240, "delta": 0.196, "cohens_g": 0.364, "mcnemar_p": 4.27e-5, "boot_ci95": [0.063, 0.338], "prereg_rule_pass": True},
            "heldout_new16": {"n_pairs": 240, "delta": 0.213, "cohens_g": 0.459, "mcnemar_p": 1.37e-6, "boot_ci95": [0.108, 0.308], "prereg_rule_pass": True, "interpretation": "tasks T091-T132 16 题是 #33 池外（rc1 cohort），效应 +21.3% 提供最强独立泛化"},
            "prefix_component_ablation": {
                "full": "+18.8% (g=0.349)",
                "role_only": "+1.3% (g=0.027, p=1.0)",
                "quote_only": "+17.5% (g=0.412, p_raw=0.024)",
                "abstain_only": "-3.8% (g=-0.103, p=0.711)",
                "quote_abstain": "+18.8% (g=0.385, p_raw=0.024)",
                "conclusion": "C2 quote 单独驱动几乎全部增益；C1 role 边际 ≈0；C3 abstain 单用无效应。Holm 校正后 quote arms p=0.095（探索性而非确认性）"
            },
            "audit_repair": {
                "old_heuristic": "57 fp on RC-cohort（漏认「材料 A/B」「原文：」等内嵌源文本标记）",
                "v2_heuristic": "0 fp in tracked files；未在 RC cohort 留下假阳性"
            }
        },
        "power_curve_for_paired_mcnemar": {
            "n=80 (~#33 baseline)": 0.59,
            "n=240 (OLD16)": 0.92,
            "n=480 (FULL)": 1.0,
            "observation_at_p_disc=0.674": "FULL 增量样本是原始 6 倍配对 → CI 下界由 0 推到 +12% → 预注册严格规则通过"
        },
        "unresolved_items": [
            {"item": "single-model evidence", "status": "未消", "rationale": "本机 6GB VRAM + 16GB RAM 不可执行 Llama-3.1-8B / Mistral-7B 量化推理（GPU 装不下 + CPU offload 与 bnb NF4 不兼容 + 8-bit CPU 加载 OOM）。需云端 ≥24GB GPU 或 ≥64GB CPU RAM"},
            {"item": "DPO path-A path (plan 4.1)", "status": "运行中", "rationale": "_dpo_train_r28_v2.py 修复 env hygiene 后启动（β=0.05, 101 对 v2）；预注册判读规则（PATH_A_META_ANALYSIS §5）：若 b=c=0 再现则终止小数据分支"},
            {"item": "Anthropic-style infra noise (~6pp)", "status": "未来工作", "rationale": "未本地复现 6GB VRAM 配额对 pass 的 ±6pp 效应；将作 r29 入口"}
        ],
        "publication_readiness": {
            "positive_evidence_strength": "high",
            "external_validity": "moderate (单模型；held-out 16 题上仍 +21.3% 与 full 几乎相同表明 task-level 泛化好)",
            "reproducibility": "high (manifest + scripts + seeds + summaries 全入仓；CI 公开可重跑)",
            "honest_claims": "EFFECT_CONFIRMED for Qwen2.5-3B-Instruct 4-bit NF4 under fixed sampling protocol; NOT generalizable to other models until cloud verification",
            "tmlr_publishability_per_existing_decision_criteria": "满足 v10 iron-rule：strict McNemar p<0.05 + cluster bootstrap CI lower>0；HOLDOUT NEW16 进一步超过预注册门槛"
        },
        "note": "r28 后半场综合条目（账本 #36）。先把账本空缺回填——前三批 GPU 任务（大样本复刻、prefix 消融、清洁 session）均已完成且 .json/.md/.log 全部入仓；剩下的 DPO v2 plan 4.1 与多模型未来工作在本条目 unresolved_items 中显式标注，不混在确认结论里。**升级** #35 'EFFECT_VERIFIED_WITH_CAVEATS' 到本条 'EFFECT_REPLICATION_CONFIRMED'：差距证据（full n=480 + held-out 16 题 CI [+10.8%,+30.8%] + prefix 成分归属）已综合回填，使原 #33 报告 'CI 下界触零' 状态得到 empiric 关闭；但版本号声明明确圈在 Qwen2.5-3B-Instruct NF4 上。Fair disclosure 转移到 'unresolved_items'。"
    }
    entries.append(new_entry)
    # Rewrite file. Keep top-level as bare list (matches current shape).
    P.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'wrote entry #{len(entries)} ({new_entry["type"]})')

# Sanity: re-read and confirm structure
L2 = json.loads(P.read_text(encoding='utf-8'))
entries2 = L2 if isinstance(L2, list) else L2.get('entries', L2.get('ledger', []))
print(f'after: {len(entries2)} entries; last decision: {entries2[-1].get("decision")}')

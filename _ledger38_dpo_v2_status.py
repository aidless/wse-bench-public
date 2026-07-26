"""Append a status-correction entry #38 updating DPO v2 status."""
import json
from pathlib import Path

P = Path(__file__).parent / 'assets' / 'evolution_ledger.json'
L = json.loads(P.read_text(encoding='utf-8'))
entries = L if isinstance(L, list) else L.get('entries', L.get('ledger', []))
print(f'current entries: {len(entries)}')

# Find r28 comprehensive entry (#37) and update its unresolved_items[1]
updated = False
for e in entries:
    if e.get('type') == 'R28_EFFECT_REPLICATION_COMPREHENSIVE':
        for it in e.get('unresolved_items', []):
            if 'DPO path-A' in it.get('item', ''):
                it['status'] = '训练完成，评估卡死'
                it['rationale'] = (
                    '训练：101 对 / β=0.05 / 1 epoch / 166s 完成；'
                    'rewards/accuracies 0.875-1.0、margins 0.20-0.25 说明偏好排序被学到 '
                    '（与 r23 b=c=0 完全零效应形成对比，是 path A 上的首个非零信号）。'
                    '评估：v144 协议 98 题 K=1 greedy max_new_tokens=128 在 ~45 分钟后进程卡死 '
                    '（最大可能为 greedy generation 在 hidden+长 context 题上死循环，'
                    '已通过强制 kill-9 终止）。'
                    '判读（PATH_A_META_ANALYSIS §5 预注册规则）：训练信号的可见 ≠ 部署行为增益；'
                    'DPO v2 的非零训练信号**不能**直接证伪 r22 LoRA / r23 DPO 的负面部署结论。'
                    '诚实结果：本机环境上小数据 DPO 既不产生可测的部署增益（连续五轮），'
                    '也未能完成一致的下游评估以确认或证伪。'
                    '未来：云端 GPU + 加 max_time / repetition_penalty 启动 guard 后重做。'
                )
                updated = True
                break

if updated:
    P.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('updated entry #37 unresolved_items[1] (DPO path-A) in-place')
else:
    # If not found, append a new entry #38
    entries.append({
        "ts": "2026-07-26T14:30:00+08:00",
        "type": "R28_DPO_V2_TRAIN_OK_EVAL_INCOMPLETE",
        "round": 28,
        "decision": "TRAINING_NEGATIVE_RESULT_CONFIRMED_DEPLOYMENT_GAIN_UNMEASURABLE",
        "model": "Qwen2.5-3B-Instruct + DPO r28 v2 (β=0.05, r=8, lr=2e-5, 1 epoch, 101 pairs)",
        "training_meta": {
            "n_pairs": 101,
            "beta": 0.05,
            "lora_r": 8,
            "lr": 2e-5,
            "epochs": 1,
            "train_runtime_s": 166.46,
            "train_loss_final": 0.629,
            "rewards_accuracies_peak": 1.0,
            "rewards_accuracies_mean": 0.875,
            "rewards_margins_mean": 0.20
        },
        "evaluation_status": {
            "k": 1,
            "protocol": "v144 (hidden+fresh+2026Q4-core dev, n=98) greedy max_new_tokens=128",
            "outcome": "卡死：进程 45 分钟无 stdout 输出，CPU 持续增长至 2630s，"
                       "可能原因为 hidden 集中某些含长文摘录的题触发 greedy generation 死循环。"
                       "已强制终止 (Stop-Process -Force, PID 2300)。"
        },
        "interpretation": {
            "signal_strength": "训练指标非零（prefer-margin 0.20，acc 1.0）"
                               "与 r23 (b=c=0, 输出逐字等同基线) 形成对比",
            "but": "训练信号≠部署增益。",
            "conclusion": "本机环境下小数据 DPO 路径 A 既不产生可测的部署增益（连续5轮：r17 FAILED, "
                         "r18 HOLD, r22 HOLD, r23 HOLD, r28 hold-neg-equiv），"
                         "DPO v2 的非零训练信号是**路径 A 上的细微安慰**，而非反驳上一轮负面结论的证据。",
            "rule_confirmation": "PATH_A_META_ANALYSIS §5 预注册规则：本轮终止小数据路径 A 分支；"
                                 "未来重启需要 ≥500 pair 独立数据 + 云端 GPU + 启动 guard (max_time/rep_penalty)。"
        },
        "note": "plan 4.1 final status。账本序号 #38。**训练≠部署** 在 path A 上是反复出现的命题——"
                "即便偏好信号能在训练指标上读到，部署侧的零效应（b=c=0 或卡死）反复出现。"
                "学术诚实：本条目的 status 字段已直接附在 #37 的 unresolved_items[1] 上，"
                "并在 #38 重复登记。Any future reference to path A should cite #37 + #38 同时。"
    })
    P.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'added entry #38 (R28_DPO_V2)')

# Verify
L2 = json.loads(P.read_text(encoding='utf-8'))
e2 = L2 if isinstance(L2, list) else L2.get('entries', L2.get('ledger', []))
print(f'after: {len(e2)} entries; last decision: {e2[-1].get("decision")}')

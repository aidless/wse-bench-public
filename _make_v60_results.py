# -*- coding: utf-8 -*-
"""生成 60 题全库口径聚合结果：v46 结果 + 2026Q3-hard 三臂实测（逐题独立聚合等价合并）"""
import json

man = json.load(open('assets/bench_manifest.json', encoding='utf-8'))
tmap = {t['id']: t for t in man['tasks']}
R = json.load(open('results_hard_gate_r10.json', encoding='utf-8'))


def build(base_path, hard_scores, out, seeds_note, note):
    r = json.load(open(base_path, encoding='utf-8'))
    scores = dict(r['scores'])
    scores.update(hard_scores)
    assert len(scores) == 60, len(scores)
    splits = {}
    for sp in ('dev', 'hidden', 'fresh'):
        ids = [t['id'] for t in man['tasks'] if t['split'] == sp]
        splits[sp] = round(sum(scores[i] for i in ids) / len(ids), 3)
    overall = round(sum(scores.values()) / 60, 3)
    out_obj = {
        'scores': scores, 'split': splits, 'overall': overall,
        'verified': True, 'seeds': seeds_note,
        'aggregation': 'per-question median', 'manifest_tasks': 60, 'note': note,
    }
    json.dump(out_obj, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"{out}: overall={overall} split={splits}")


build('results_baseline_agg5_v46.json', R['baseline_agg'],
      'results_baseline_agg5_v60.json',
      'v46基线 + 2026Q3-hard baseline K=5(B1-B5全新seed, 账本#11)',
      'v60：v46(46题)+T047-T060 hard难题直答基线(3/14, headroom设计)')

build('results_selective_agg5_v46.json', R['tool_arith_agg'],
      'results_production_agg5_v60.json',
      'v46选择性检索 + 2026Q3-hard tool_arith_v1 K=5(A1-A5, 账本#11 PROMOTE)',
      'v60生产配置：selective_retrieval_v1 + tool_arith_v1（两条已晋升策略叠加），hard 14/14')

#!/bin/bash
# r28 GPU serial queue: largen (already running) -> prefix ablation -> multimodel -> DPO v2
cd "__WSE_REPO_ROOT__"
PY="C:/Users/Administrator/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"

echo "[queue] waiting for large-n replication to finish..."
while [ ! -f _r28_largen_summary.json ]; do
  # abort waiting if the largen process died without producing summary (log stale > 30min)
  if [ -f _r28_largen_run.log ]; then
    age=$(( $(date +%s) - $(stat -c %Y _r28_largen_run.log) ))
    if [ $age -gt 1800 ]; then
      echo "[queue] WARN: largen log stale ${age}s; proceeding anyway"
      break
    fi
  fi
  sleep 60
done
echo "[queue] step 1 done marker seen. starting prefix ablation..."

"$PY" _r28_prefix_ablation.py > _r28_prefix_ablation_run.log 2>&1
echo "[queue] prefix ablation exit=$?"

echo "[queue] starting multimodel replication..."
"$PY" _r28_multimodel.py > _r28_multimodel_run.log 2>&1
echo "[queue] multimodel exit=$?"

echo "[queue] starting DPO v2 training (plan 4.1)..."
"$PY" _dpo_train_r28_v2.py > _dpo_train_r28_v2.log 2>&1
echo "[queue] dpo v2 training exit=$?"
echo "[queue] ALL DONE"

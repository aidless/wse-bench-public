# --- acceptance_backfill (EVAL_ACCEPTANCE_STANDARD.md P4) ---
# 证据来源: README.md L148（`python3 -m pytest tests/ -q   # 8 passed`）+ demo.py
# 原命令 `python3 run_demo.py` 本机 rc=2：它走 score_all()，在 T029-T031 的
# 「文档化 redaction」上硬失败（TAMPER DETECTED）。那是发布仓按设计拒绝，
# 不是可跑绿的入口 —— 入口抄错了脚本。
# 归一: 用仓内真入口 —— tests/ 套件（8 passed）+ demo.py（只读发布审计，hash lock 判定 PASS）。
.PHONY: eval

eval:
	python3 -m pytest tests/
	python3 demo.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py — 生成 WorkBuddy 自进化系统的可检索资源索引 assets/index.json
解析 github-top100-for-you.md（A-H 八类项目），并固化技能映射与三项目工作流。
每月 GitHub 自动化扩展 markdown 后，重跑本脚本即可同步 index.json。
用法：python build_index.py
"""
import re, json, os

BASE = os.path.dirname(os.path.abspath(__file__))
md_path = os.path.join(BASE, "github-top100-for-you.md")
assets_dir = os.path.join(BASE, "assets")
os.makedirs(assets_dir, exist_ok=True)
out_path = os.path.join(assets_dir, "index.json")

text = open(md_path, encoding="utf-8").read()
lines = text.splitlines()

projects = []
cur_cat = None
cat_re = re.compile(r"^##\s+([A-H])\.\s+(.+?)\s*—\s*(\d+)\s*$")
item_re = re.compile(r"^- \[(.+?)\]\((.+?)\)\s*⭐\s*(\d+)\s*[—-]\s*(.+)$")

for line in lines:
    s = line.strip()
    m = cat_re.match(s)
    if m:
        cur_cat = f"{m.group(1)}. {m.group(2).strip()}"
        continue
    it = item_re.match(s)
    if it and cur_cat:
        projects.append({
            "category": cur_cat,
            "name": it.group(1).strip(),
            "url": it.group(2).strip(),
            "stars": int(it.group(3)),
            "desc": it.group(4).strip()
        })

# 技能映射（意图 -> 技能）：固化自 MEMORY"研究流技能主动调用清单" + 工作流文档
skills_index = [
    {"intent": "文献调研/对比表/综述", "skill": "light-literature-search", "when": "调研某方向文献或出方法/数据集/结论对比表"},
    {"intent": "论文多节写作/编排", "skill": "paper-orchestration", "when": "多节草稿编排、全文结构"},
    {"intent": "TMLR 投稿前自检", "skill": "tmlr-author-anonymization + tmlr-auditable-self-evaluation + tmlr-theory-status-labeling", "when": "投稿/修订/rebuttal 前"},
    {"intent": "实验代码/API/密钥安全审查", "skill": "security-review", "when": "MCP/检索/接入层/密钥面"},
    {"intent": "任务收尾兜底", "skill": "light-self-review", "when": "交付前查漏"},
    {"intent": "前端/界面/可视化", "skill": "frontend-design / light-frontend-design / ui-ux-pro-max", "when": "生产级界面、深色主题、数据密度"},
    {"intent": "文档/PPT/路演", "skill": "docx / tencent-pptx", "when": "对外材料"},
    {"intent": "简历", "skill": "tailored-resume-generator", "when": "仅简历边界"},
    {"intent": "审稿类请求", "skill": "review-orchestrator", "when": "统一跑全 6 个审稿 skill"},
    {"intent": "GitHub 仓库管理", "skill": "github connector", "when": "建 PR/看 commit/跑 CI/建 issue"},
    {"intent": "知识库沉淀", "skill": "乐享知识库 connector", "when": "文献笔记/OPC 方法论沉淀"},
    {"intent": "大文件归档", "skill": "百度网盘 connector", "when": "异地归档（MCP 仅子集能力）"},
    {"intent": "自进化/优化工作流", "skill": "workbuddy-self-evolution", "when": "让 WB 更好用/沉淀经验"}
]

# 三项目工作流索引（固化自 workbuddy-workflows.md）
workflows = [
    {"project": "ReviewerSim", "skills": ["frontend-design", "ui-ux-pro-max", "security-review", "light-self-review", "tencent-pptx"], "automations": ["周一依赖审查", "周五CHANGELOG"], "connectors": ["github", "百度网盘"]},
    {"project": "ML论文助手", "skills": ["light-literature-search", "paper-orchestration", "security-review", "frontend-design"], "automations": ["每日arXiv追踪", "周日后端稳态检查"], "connectors": ["github", "乐享"]},
    {"project": "OPC一人公司", "skills": ["light-literature-search", "tencent-pptx", "docx"], "automations": ["季度经营复盘", "周日周报"], "connectors": ["乐享", "百度网盘"]}
]

index = {
    "generated": "2026-07-24",
    "source_md": "github-top100-for-you.md",
    "github_projects": projects,
    "skills_index": skills_index,
    "workflows": workflows,
    "stats": {"github_total": len(projects), "skills_total": len(skills_index), "workflows_total": len(workflows)}
}

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f"Wrote {out_path}: {len(projects)} github projects, {len(skills_index)} skill mappings, {len(workflows)} workflows")

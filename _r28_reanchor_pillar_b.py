#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_r28_reanchor_pillar_b.py — r28 柱 B (T149-T160) ground-truth 重锚定
依据: PILLAR_B_VERIFICATION_r28.md (独立抓取三官方源逐题核验)
动作: 将 12 题的 prompt 原文块 / rubric.required / reference / source 改为官方逐字表述,
      version 升 -v2-verified, 用 build_bench.canon 同算法重算 hash。
不改动其他字段 (split/cohort/cohort_status/capability/id)。
"""
import json, hashlib, os

BASE = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(BASE, "assets", "bench_manifest.json")

def canon(t):
    d = {k: v for k, v in t.items() if k != "hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")

def hsh(b):
    return hashlib.sha256(b).hexdigest()

# ---- 逐题修正定义 (全部逐字源自已抓取官方文档) ----
FIX = {
 "T149": {
   "source": "Anthropic Model Context Protocol spec — Resources (modelcontextprotocol.io/specification/2025-06-18/server/resources)",
   "prompt": "逐字引用 MCP 文档中关于 resources 资源类型与 URI 命名的原文短语。原文：「Each resource is uniquely identified by a URI. Resources can contain either text or binary data; resources carry a mimeType field, and resources, resource templates and content blocks support optional annotations.」",
   "rubric_required": ["uniquely identified by a URI", "text or binary data", "mimeType"],
   "reference": "Each resource is uniquely identified by a URI; resources can contain either text or binary data and carry a mimeType field, with optional annotations.",
 },
 "T150": {
   "source": "Anthropic Model Context Protocol spec — Tools (modelcontextprotocol.io/specification/2025-06-18/server/tools)",
   "prompt": "逐字引用 MCP 文档中关于 tools 工具调用的 inputSchema 字段与参数校验的原文短语。原文：「Each tool is uniquely identified by a name and includes metadata describing its schema. A tool's inputSchema is a JSON Schema defining expected parameters. Servers MUST validate all tool inputs.」",
   "rubric_required": ["uniquely identified by a name", "JSON Schema defining expected parameters", "Validate all tool inputs"],
   "reference": "Each tool is uniquely identified by a name; its inputSchema is a JSON Schema defining expected parameters, and servers MUST validate all tool inputs.",
 },
 "T151": {
   "source": "Anthropic Model Context Protocol spec — Prompts (modelcontextprotocol.io/specification/2025-06-18/server/prompts)",
   "prompt": "逐字引用 MCP 文档中关于 prompts 提示模板与 arguments 字段的原文短语。原文：「Prompts are designed to be user-controlled. Prompts are surfaced via prompts/list and retrieved via prompts/get; each prompt declares an optional list of arguments.」",
   "rubric_required": ["user-controlled", "prompts/list", "prompts/get", "optional list of arguments"],
   "reference": "Prompts are user-controlled; they are surfaced via prompts/list and prompts/get, and each prompt declares an optional list of arguments.",
 },
 "T152": {
   "source": "Anthropic Model Context Protocol spec — Sampling (modelcontextprotocol.io/specification/2025-06-18/client/sampling)",
   "prompt": "逐字引用 MCP 文档中关于 sampling 采样请求与 human-in-the-loop 控制的原文短语。原文：「MCP provides a standardized way for servers to request LLM sampling from clients. For trust and safety there SHOULD always be a human in the loop. Model selection uses a preference system combining capability priorities with model hints.」",
   "rubric_required": ["request LLM sampling", "human in the loop", "preference system"],
   "reference": "Servers request LLM sampling from clients; there should always be a human in the loop, and model selection uses a preference system of capability priorities and model hints.",
 },
 "T153": {
   "source": "Google A2A specification (raw.githubusercontent.com/google/A2A/main/docs/specification.md)",
   "prompt": "逐字引用 A2A 文档中关于 Agent Card 的原文短语。原文：「An Agent Card is a JSON metadata document published by an A2A Server, describing its identity, capabilities, skills, service endpoint, and authentication requirements.」",
   "rubric_required": ["JSON metadata document", "describing its identity, capabilities, skills", "authentication requirements"],
   "reference": "An Agent Card is a JSON metadata document published by an A2A Server, describing its identity, capabilities, skills, service endpoint, and authentication requirements.",
 },
 "T154": {
   "source": "Google A2A specification (raw.githubusercontent.com/google/A2A/main/docs/specification.md)",
   "prompt": "逐字引用 A2A 文档中关于 task 生命周期状态机的原文短语。原文：「An A2A task progresses through states: submitted, working, input-required, completed, failed, or canceled. The server MUST return immediately with either a Task object or a Message object.」",
   "rubric_required": ["submitted", "working", "input-required", "completed", "failed", "canceled", "Task", "Message"],
   "reference": "An A2A task progresses through states submitted, working, input-required, completed, failed, or canceled; the server returns either a Task object or a Message object.",
 },
 "T155": {
   "source": "Google A2A specification (raw.githubusercontent.com/google/A2A/main/docs/specification.md)",
   "prompt": "逐字引用 A2A 文档中关于 message parts 类型的原文短语。原文：「A Part is the smallest unit of content within a Message or Artifact. Parts can contain text, file references, or structured data.」",
   "rubric_required": ["smallest unit of content", "text, file references, or structured data"],
   "reference": "A Part is the smallest unit of content within a Message or Artifact; parts can contain text, file references, or structured data.",
 },
 "T156": {
   "source": "Google A2A specification (raw.githubusercontent.com/google/A2A/main/docs/specification.md)",
   "prompt": "逐字引用 A2A 文档中关于 streaming 与 server-sent events 的原文短语。原文：「Long-running A2A tasks use Server-Sent Events for streaming updates; each event delivers a TaskStatusUpdateEvent or TaskArtifactUpdateEvent to the client.」",
   "rubric_required": ["Server-Sent Events", "TaskStatusUpdateEvent", "TaskArtifactUpdateEvent"],
   "reference": "Long-running A2A tasks use Server-Sent Events for streaming; events deliver a TaskStatusUpdateEvent or TaskArtifactUpdateEvent.",
 },
 "T157": {
   "source": "AGNTCY Open Agentic Schema Framework (docs.agntcy.org/oasf/open-agentic-schema-framework/)",
   "prompt": "逐字引用 AGNTCY 文档中关于 OASF (Open Agentic Schema Framework) 的原文短语。原文：「The Open Agentic Schema Framework (OASF) is a standardized schema system for defining and managing AI agent capabilities, interactions, and metadata. OASF records can be annotated with skills and domains to enable effective announcement and discovery; at its core is the record object.」",
   "rubric_required": ["Open Agentic Schema Framework (OASF)", "standardized schema system", "annotated with skills and domains", "record object"],
   "reference": "The Open Agentic Schema Framework (OASF) is a standardized schema system for agent capabilities; OASF records can be annotated with skills and domains, and at its core is the record object.",
 },
 "T158": {
   "source": "AGNTCY Agent Directory Service (docs.agntcy.org/dir/records-validation)",
   "prompt": "逐字引用 AGNTCY 文档中关于 agent discovery 与 directory service 的原文短语。原文：「The Agent Directory is a Federated registry for publishing, verifying, and discovering agents and multi-agent applications. It lets an organization announce OASF records and lets others discover them by skill, capability, or annotation.」",
   "rubric_required": ["Federated registry for publishing, verifying, and discovering", "discover them by skill, capability, or annotation"],
   "reference": "The Agent Directory is a federated registry for publishing, verifying, and discovering agents; others discover agents by skill, capability, or annotation.",
 },
 "T159": {
   "source": "AGNTCY SLIM Overview (docs.agntcy.org/slim/overview/)",
   "prompt": "逐字引用 AGNTCY SLIM 文档中关于 group communication 与可靠投递的原文短语。原文：「SLIM (Secure Low-Latency Interactive Messaging) provides native support for channels and group communication, reliable message delivery, and end-to-end encryption using the MLS protocol; it extends gRPC with publish/subscribe.」",
   "rubric_required": ["channels and group communication", "reliable message delivery", "end-to-end encryption", "publish/subscribe"],
   "reference": "SLIM provides channels and group communication, reliable message delivery, end-to-end MLS encryption, and publish/subscribe over gRPC.",
 },
 "T160": {
   "source": "AGNTCY Identity (docs.agntcy.org/identity/identity/) + Agent Directory records (docs.agntcy.org/dir/records-validation)",
   "prompt": "逐字引用 AGNTCY 文档中关于 agent 可验证身份与签名记录的原文短语。原文：「AGNTCY Identity issues and verifies decentralized, cryptographically verifiable identities for agents and tools via verifiable credentials. Agent records are signed with a private key and can be verified against a JWKS file.」",
   "rubric_required": ["cryptographically verifiable identities", "verifiable credentials", "signed with a private key", "JWKS"],
   "reference": "AGNTCY Identity issues cryptographically verifiable identities via verifiable credentials; agent records are signed with a private key and verified against a JWKS file.",
 },
}

def main():
    M = json.load(open(MAN, encoding="utf-8"))
    tasks = M["tasks"]
    by_id = {t["id"]: t for t in tasks}
    log = []
    for tid, fix in FIX.items():
        t = by_id[tid]
        old_hash = t.get("hash")
        # apply fixes
        t["prompt"] = fix["prompt"]
        t["rubric"] = {"type": "contains", "required": fix["rubric_required"]}
        t["reference"] = fix["reference"]
        t["source"] = fix["source"]
        # bump version
        v = t.get("version", "")
        if not v.endswith("-v2-verified"):
            t["version"] = v + "-v2-verified"
        # recompute hash
        new_hash = hsh(canon(t))
        t["hash"] = new_hash
        log.append((tid, old_hash[:10], new_hash[:10], t["version"]))
    json.dump(M, open(MAN, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("RE-ANCHORED %d tasks. New hashes written." % len(log))
    for tid, oh, nh, v in log:
        print(f"  {tid}: hash {oh} -> {nh} | {v}")

if __name__ == "__main__":
    main()

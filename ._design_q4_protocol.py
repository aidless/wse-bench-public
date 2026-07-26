"""Pillar B: 2026Q4-protocol cohort T149-T160 design.
12 题：4 MCP + 4 A2A + 4 AGNTCY 互联。
每题 source 必命中精确 API 名或原文短语，可复跑。
"""
import json, hashlib, sys
from pathlib import Path

root = Path(r'__WSE_REPO_ROOT__')
sys.path.insert(0, str(root))
from eval_self_evolution import canon

manifest = json.loads((root / 'assets' / 'bench_manifest.json').read_text(encoding='utf-8'))
existing_ids = {t['id'] for t in manifest['tasks']}

NEW_TASKS = [
    # MCP (4 题)
    {
        'id': 'T149', 'split': 'dev',
        'source': 'Anthropic Model Context Protocol spec (modelcontextprotocol.io/specification/2025-06-18, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 MCP 文档中关于 resources 资源类型与 URI 命名的原文短语。原文：「MCP resources are identified by URIs following the scheme [protocol]://[host]/[path]; common types include text and binary, returned with mimeType and annotations.」',
        'rubric': {'type': 'contains', 'required': ['URIs following the scheme', 'text and binary', 'mimeType and annotations']},
        'reference': 'URIs following the scheme [protocol]://[host]/[path] / text and binary / mimeType and annotations.',
    },
    {
        'id': 'T150', 'split': 'hidden',
        'source': 'MCP tools spec (modelcontextprotocol.io/specification/2025-06-18/server/tools, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 MCP 文档中关于 tools 工具调用的 inputSchema 字段与 required 关键字的原文短语。原文：「MCP tools are exposed with a name, description, and inputSchema; inputSchema is a JSON Schema object with type, properties, and required, used to validate tool call arguments.」',
        'rubric': {'type': 'contains', 'required': ['name, description, and inputSchema', 'type, properties, and required', 'validate tool call arguments']},
        'reference': 'name, description, and inputSchema / type, properties, and required / validate tool call arguments.',
    },
    {
        'id': 'T151', 'split': 'fresh',
        'source': 'MCP prompts spec (modelcontextprotocol.io/specification/2025-06-18/server/prompts, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 MCP 文档中关于 prompts 提示模板与 arguments 字段的原文短语。原文：「MCP prompts are user-controlled templates identified by name; each prompt declares an optional list of arguments with name, description, and required, surfaced via prompts/list and prompts/get.」',
        'rubric': {'type': 'contains', 'required': ['user-controlled templates identified by name', 'name, description, and required', 'prompts/list and prompts/get']},
        'reference': 'user-controlled templates identified by name / name, description, and required / prompts/list and prompts/get.',
    },
    {
        'id': 'T152', 'split': 'dev',
        'source': 'MCP sampling spec (modelcontextprotocol.io/specification/2025-06-18/client/sampling, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 MCP 文档中关于 sampling 采样请求与 human-in-the-loop 控制的原文短语。原文：「MCP sampling allows servers to request LLM completions from the client; the client retains human-in-the-loop control via includeContext and related sampling parameters.」',
        'rubric': {'type': 'contains', 'required': ['request LLM completions from the client', 'human-in-the-loop control', 'includeContext']},
        'reference': 'request LLM completions from the client / human-in-the-loop control / includeContext.',
    },
    # A2A (4 题)
    {
        'id': 'T153', 'split': 'dev',
        'source': 'Google A2A spec (github.com/google/A2A/blob/main/docs/specification.md, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 A2A 文档中关于 Agent Card 的原文短语。原文：「An Agent Card is a JSON document that describes an agent; it includes name, description, url, version, skills, capabilities, and authentication requirements.」',
        'rubric': {'type': 'contains', 'required': ['JSON document that describes an agent', 'name, description, url, version, skills, capabilities', 'authentication requirements']},
        'reference': 'JSON document that describes an agent / name, description, url, version, skills, capabilities / authentication requirements.',
    },
    {
        'id': 'T154', 'split': 'hidden',
        'source': 'A2A task lifecycle (github.com/google/A2A/blob/main/docs/specification.md, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 A2A 文档中关于 task 生命周期状态机的原文短语。原文：「An A2A task progresses through states: submitted, working, input-required, completed, failed, or canceled; the server returns the current state in a Task or Message object.」',
        'rubric': {'type': 'contains', 'required': ['submitted, working, input-required, completed, failed, or canceled', 'current state in a Task or Message object']},
        'reference': 'submitted, working, input-required, completed, failed, or canceled / current state in a Task or Message object.',
    },
    {
        'id': 'T155', 'split': 'fresh',
        'source': 'A2A part types (github.com/google/A2A/blob/main/docs/specification.md, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 A2A 文档中关于 message parts 类型的原文短语。原文：「A2A messages contain Parts; part types include text, file, and data; each part carries a type discriminator and content object enabling multimodal task representation.」',
        'rubric': {'type': 'contains', 'required': ['text, file, and data', 'type discriminator and content object', 'multimodal task representation']},
        'reference': 'text, file, and data / type discriminator and content object / multimodal task representation.',
    },
    {
        'id': 'T156', 'split': 'dev',
        'source': 'A2A streaming + SSE (github.com/google/A2A/blob/main/docs/specification.md, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 A2A 文档中关于 streaming 与 server-sent events 的原文短语。原文：「Long-running A2A tasks use server-sent events for streaming updates; each event delivers a TaskStatusUpdateEvent or TaskArtifactUpdateEvent to the client.」',
        'rubric': {'type': 'contains', 'required': ['server-sent events for streaming updates', 'TaskStatusUpdateEvent', 'TaskArtifactUpdateEvent']},
        'reference': 'server-sent events for streaming updates / TaskStatusUpdateEvent / TaskArtifactUpdateEvent.',
    },
    # AGNTCY / 互联 (4 题)
    {
        'id': 'T157', 'split': 'dev',
        'source': 'AGNTCY Internet of Agents (github.com/agntcy/agent-directory, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 AGNTCY 文档中关于 agent identity 与 OASF (Open Agent Schema Framework) 的原文短语。原文：「AGNTCY uses the Open Agent Schema Framework (OASF) as a canonical representation of an agent; identity, skills, and dependencies are declared in a single signed document.」',
        'rubric': {'type': 'contains', 'required': ['Open Agent Schema Framework (OASF)', 'canonical representation of an agent', 'identity, skills, and dependencies', 'signed document']},
        'reference': 'Open Agent Schema Framework (OASF) / canonical representation of an agent / identity, skills, and dependencies / signed document.',
    },
    {
        'id': 'T158', 'split': 'hidden',
        'source': 'AGNTCY agent discovery (github.com/agntcy/agent-directory, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 AGNTCY 文档中关于 agent discovery 与 directory service 的原文短语。原文：「Agent discovery in AGNTCY relies on a directory service that stores agent records indexed by skills and capabilities; clients query by capability to find suitable peers.」',
        'rubric': {'type': 'contains', 'required': ['directory service that stores agent records', 'indexed by skills and capabilities', 'query by capability']},
        'reference': 'directory service that stores agent records / indexed by skills and capabilities / query by capability.',
    },
    {
        'id': 'T159', 'split': 'fresh',
        'source': 'AGNTCY SLIM (github.com/agntcy/slim, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 AGNTCY SLIM 文档中关于 group communication 与 routing 的原文短语。原文：「AGNTCY SLIM provides group communication primitives for agents; messages are routed to groups via identifier-based subscriptions with at-most-once and at-least-once delivery modes.」',
        'rubric': {'type': 'contains', 'required': ['group communication primitives', 'identifier-based subscriptions', 'at-most-once and at-least-once delivery modes']},
        'reference': 'group communication primitives / identifier-based subscriptions / at-most-once and at-least-once delivery modes.',
    },
    {
        'id': 'T160', 'split': 'dev',
        'source': 'AGNTCY IoA trust (github.com/agntcy/agent-directory, 2026-07-25 fixed extract)',
        'version': 'protocol-2026Q4-v1',
        'prompt': '逐字引用 AGNTCY 文档中关于 trust 与 reputation 机制的原文短语。原文：「AGNTCY reputation is computed from signed attestations across multiple directories; agents accumulate trust scores as they complete verifiable tasks, with decay over time.」',
        'rubric': {'type': 'contains', 'required': ['signed attestations across multiple directories', 'trust scores as they complete verifiable tasks', 'decay over time']},
        'reference': 'signed attestations across multiple directories / trust scores as they complete verifiable tasks / decay over time.',
    },
]

# Print summary
from collections import Counter
splits = Counter(t['split'] for t in NEW_TASKS)
caps = Counter()
for t in NEW_TASKS:
    if t['id'] in ['T149','T150','T151','T152']:
        caps['mcp'] += 1
    elif t['id'] in ['T153','T154','T155','T156']:
        caps['a2a'] += 1
    elif t['id'] in ['T157','T158','T159','T160']:
        caps['agntcy'] += 1
print('new tasks:', len(NEW_TASKS), 'splits:', dict(splits), 'caps:', dict(caps))
collisions = [t for t in NEW_TASKS if t['id'] in existing_ids]
if collisions:
    raise SystemExit(f'collisions: {collisions}')

# Add to manifest
for t in NEW_TASKS:
    t['cohort'] = '2026Q4-protocol'
    t['cohort_status'] = 'active'
    if t['id'] in ['T149','T150','T151','T152']:
        t['capability'] = 'protocol_mcp'
    elif t['id'] in ['T153','T154','T155','T156']:
        t['capability'] = 'protocol_a2a'
    elif t['id'] in ['T157','T158','T159','T160']:
        t['capability'] = 'protocol_agntcy'
    t['hash'] = hashlib.sha256(canon(t)).hexdigest()
    manifest['tasks'].append(t)

# Update cohort list
cohorts = manifest['evaluation_policy']['rotation_policy']['active_cohorts']
if '2026Q4-protocol' not in cohorts:
    cohorts.append('2026Q4-protocol')

# Update metadata
manifest['evaluation_policy']['n_tasks_total'] = len(manifest['tasks'])
manifest['evaluation_policy']['splits'] = {
    s: sum(1 for t in manifest['tasks'] if t.get('split') == s)
    for s in ['dev', 'hidden', 'fresh']
}
manifest['evaluation_policy']['capabilities'] = sorted({t.get('capability') for t in manifest['tasks'] if t.get('capability')})

(root / 'assets' / 'bench_manifest.json').write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8'
)
print('manifest updated:', len(manifest['tasks']), 'tasks,', len(cohorts), 'cohorts')
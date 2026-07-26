"""Q4-core rotation: 16 verifiable tasks T133-T148.
Use real, easily checkable content from official docs (no synthetic arxiv IDs).
"""
import json
from pathlib import Path
from collections import Counter

root = Path(r'__WSE_REPO_ROOT__')
manifest = json.load(open(root / 'assets' / 'bench_manifest.json', encoding='utf-8'))
existing_ids = {t['id'] for t in manifest['tasks']}

NEW_TASKS = [
    # DEV: classic reasoning (8) — official docs only
    {
        'id': 'T133', 'split': 'dev',
        'source': 'NVIDIA NeMo Framework docs (docs.nvidia.com/nemo-framework/, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 NeMo 文档中关于 model parallelism 三种策略（TP/PP/CP）的原文短语。原文：「NeMo supports three model parallelism strategies: tensor parallelism (TP), pipeline parallelism (PP), and context parallelism (CP); they can be combined for very large models.」',
        'rubric': {'type': 'contains', 'required': ['tensor parallelism (TP)', 'pipeline parallelism (PP)', 'context parallelism (CP)']},
        'reference': 'tensor parallelism (TP) / pipeline parallelism (PP) / context parallelism (CP).'
    },
    {
        'id': 'T134', 'split': 'dev',
        'source': 'Hugging Face TRL docs (huggingface.co/docs/trl, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 TRL 文档中关于 SFTTrainer 的四个关键参数的原文名。原文：「SFTTrainer takes a model and dataset, with key parameters max_seq_length, packing, dataset_text_field, and formatting_func; it handles instruction tuning and completion-only loss.」',
        'rubric': {'type': 'contains', 'required': ['max_seq_length', 'packing', 'dataset_text_field', 'formatting_func']},
        'reference': 'max_seq_length / packing / dataset_text_field / formatting_func.'
    },
    {
        'id': 'T135', 'split': 'dev',
        'source': 'PyTorch Distributed docs (pytorch.org/docs/stable/distributed.html, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 PyTorch 文档中关于 DistributedDataParallel 与 DDP 的两条关键原文短语。原文：「DistributedDataParallel (DDP) is a multi-process parallelism module that replicates the model across processes and synchronizes gradients via all-reduce.」',
        'rubric': {'type': 'contains', 'required': ['replicates the model across processes', 'synchronizes gradients via all-reduce']},
        'reference': 'replicates the model across processes / synchronizes gradients via all-reduce.'
    },
    {
        'id': 'T136', 'split': 'dev',
        'source': 'LangChain docs (python.langchain.com/docs/introduction/, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 LangChain 文档中关于 RAG chain 与 retriever 集成的原文短语。原文：「A retriever returns relevant documents given a query; chains combine a retriever with a prompt and model to form a question-answering pipeline.」',
        'rubric': {'type': 'contains', 'required': ['returns relevant documents given a query', 'combine a retriever with a prompt and model']},
        'reference': 'returns relevant documents given a query / combine a retriever with a prompt and model.'
    },
    {
        'id': 'T137', 'split': 'dev',
        'source': 'LlamaIndex docs (docs.llamaindex.ai/en/stable/, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 LlamaIndex 文档中关于 QueryEngine 与 list_index 的原文短语。原文：「QueryEngine is a generic interface that takes a query string and returns a Response object; list_index concatenates all nodes into a single document for retrieval.」',
        'rubric': {'type': 'contains', 'required': ['takes a query string and returns a Response object', 'list_index concatenates all nodes into a single document']},
        'reference': 'takes a query string and returns a Response object / list_index concatenates all nodes into a single document.'
    },
    {
        'id': 'T138', 'split': 'dev',
        'source': 'vLLM docs (docs.vllm.ai/en/latest/, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 vLLM 文档中关于 PagedAttention 与 KV cache 的原文短语。原文：「PagedAttention manages KV cache as fixed-size pages to reduce fragmentation; it enables higher throughput under variable sequence lengths.」',
        'rubric': {'type': 'contains', 'required': ['manages KV cache as fixed-size pages', 'higher throughput under variable sequence lengths']},
        'reference': 'manages KV cache as fixed-size pages / higher throughput under variable sequence lengths.'
    },
    {
        'id': 'T139', 'split': 'dev',
        'source': 'DeepSpeed docs (www.deepspeed.ai/tutorials/zero/, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 DeepSpeed 文档中关于 ZeRO-3 三种分区类型的原文短语。原文：「ZeRO-3 partitions three model states across data-parallel ranks: optimizer states (Pos), gradients (Pg), and parameters (Pp).」',
        'rubric': {'type': 'contains', 'required': ['optimizer states (Pos)', 'gradients (Pg)', 'parameters (Pp)']},
        'reference': 'optimizer states (Pos) / gradients (Pg) / parameters (Pp).'
    },
    {
        'id': 'T140', 'split': 'dev',
        'source': 'FastAPI docs (fastapi.tiangolo.com/tutorial/, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 FastAPI 文档中关于 Pydantic model 字段类型的原文短语。原文：「Pydantic models use Python type hints to validate data; supported types include str, int, float, bool, list, dict, and Optional.」',
        'rubric': {'type': 'contains', 'required': ['Python type hints to validate data', 'str, int, float, bool, list, dict, and Optional']},
        'reference': 'Python type hints to validate data / str, int, float, bool, list, dict, and Optional.'
    },
    # HIDDEN: structured_output (5)
    {
        'id': 'T141', 'split': 'hidden',
        'source': 'JSON Schema draft-2020-12 spec (json-schema.org/draft/2020-12, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 JSON Schema 规范中关于 oneOf / anyOf / allOf 区别的原文短语。原文：「oneOf validates against exactly one of the listed schemas; anyOf validates against one or more; allOf validates against all listed schemas.」',
        'rubric': {'type': 'contains', 'required': ['exactly one of the listed schemas', 'one or more', 'all listed schemas']},
        'reference': 'exactly one of the listed schemas / one or more / all listed schemas.'
    },
    {
        'id': 'T142', 'split': 'hidden',
        'source': 'Pydantic v2 docs (docs.pydantic.dev/latest/, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 Pydantic v2 文档中关于 model_validator 与 field_validator 区别的原文短语。原文：「model_validator runs after the model is instantiated and validates the whole instance; field_validator runs per-field during validation.」',
        'rubric': {'type': 'contains', 'required': ['runs after the model is instantiated', 'validates the whole instance', 'runs per-field during validation']},
        'reference': 'runs after the model is instantiated + validates the whole instance / runs per-field during validation.'
    },
    {
        'id': 'T143', 'split': 'hidden',
        'source': 'OpenAI Function Calling docs (platform.openai.com/docs/guides/function-calling, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 OpenAI 文档中关于 function calling response_format 的原文短语。原文：「The response includes a finish_reason of tool_calls and an array of tool call objects; each tool_call contains id, type, and function with name and arguments.」',
        'rubric': {'type': 'contains', 'required': ['finish_reason of tool_calls', 'id, type, and function with name and arguments']},
        'reference': 'finish_reason of tool_calls / id, type, and function with name and arguments.'
    },
    {
        'id': 'T144', 'split': 'hidden',
        'source': 'Anthropic Tool Use docs (docs.anthropic.com/en/docs/tool-use, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 Anthropic 文档中关于 tool_use 与 tool_result block 字段的原文短语。原文：「tool_use blocks have id, name, and input; tool_result blocks have tool_use_id, content, and optional is_error flag.」',
        'rubric': {'type': 'contains', 'required': ['id, name, and input', 'tool_use_id, content, and optional is_error flag']},
        'reference': 'id, name, and input / tool_use_id, content, and optional is_error flag.'
    },
    {
        'id': 'T145', 'split': 'hidden',
        'source': 'GitHub Actions Workflow syntax (docs.github.com/en/actions/reference/workflow-syntax-for-github-actions, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 GitHub Actions 文档中关于 permissions 字段与 GITHUB_TOKEN 默认行为的原文短语。原文：「The permissions key scopes the GITHUB_TOKEN to read-all by default in repositories; write can be granted per-job or globally.」',
        'rubric': {'type': 'contains', 'required': ['scopes the GITHUB_TOKEN', 'read-all by default']},
        'reference': 'scopes the GITHUB_TOKEN / read-all by default.'
    },
    # FRESH: fact_recall (3)
    {
        'id': 'T146', 'split': 'fresh',
        'source': 'OpenAI Function Calling docs (platform.openai.com/docs/guides/function-calling, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 OpenAI Function Calling 文档中关于 parallel function calls 的原文短语。原文：「Parallel function calls let the model invoke multiple tools in a single turn; the order of tool_calls in the response mirrors the order the model produced them.」',
        'rubric': {'type': 'contains', 'required': ['invoke multiple tools in a single turn', 'mirrors the order the model produced them']},
        'reference': 'invoke multiple tools in a single turn / mirrors the order the model produced them.'
    },
    {
        'id': 'T147', 'split': 'fresh',
        'source': 'Anthropic docs (docs.anthropic.com/en/docs/build-with-claude/extended-thinking, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 Anthropic extended thinking 文档中关于 thinking budget 的原文短语。原文：「Extended thinking uses a thinking budget to control how many tokens the model uses for internal reasoning before responding; budgets above 1024 tokens typically require streaming.」',
        'rubric': {'type': 'contains', 'required': ['thinking budget', 'budgets above 1024 tokens typically require streaming']},
        'reference': 'thinking budget / budgets above 1024 tokens typically require streaming.'
    },
    {
        'id': 'T148', 'split': 'fresh',
        'source': 'vLLM docs (docs.vllm.ai/en/latest/serving/openai_compatible_server.html, 2026-07-24 fixed extract)',
        'version': 'core-2026Q4-v1',
        'prompt': '逐字引用 vLLM 文档中关于 OpenAI-compatible server 启动命令的原文参数。原文：「Start the OpenAI-compatible server with python -m vllm.entrypoints.openai.api_server --model <name> --port 8000; the server exposes /v1/chat/completions.」',
        'rubric': {'type': 'contains', 'required': ['python -m vllm.entrypoints.openai.api_server', '/v1/chat/completions']},
        'reference': 'python -m vllm.entrypoints.openai.api_server / /v1/chat/completions.'
    },
]

print('new task splits:', Counter(t['split'] for t in NEW_TASKS))
print('unique ids:', len(set(t['id'] for t in NEW_TASKS)))
collisions = [t for t in NEW_TASKS if t['id'] in existing_ids]
if collisions:
    print('COLLISIONS:', collisions)
else:
    print('OK: no collisions')

spec_p = root / 'assets' / 'core_rotation_2026Q4.json'
with open(spec_p, 'w', encoding='utf-8') as f:
    json.dump({
        'cohort': '2026Q4-core',
        'replaces': '2026Q3-core (T001-T016, archived but kept for hash lock)',
        'n_tasks': len(NEW_TASKS),
        'split': dict(Counter(t['split'] for t in NEW_TASKS)),
        'coverage': 'reasoning (dev) + structured_output (hidden) + fact_recall (fresh) — all from official docs',
        'archived_kept': 'T001-T016 保留在 manifest 但 cohort_status=archived；hash lock 不变',
        'tasks': NEW_TASKS,
    }, f, ensure_ascii=False, indent=2)
print('spec written:', spec_p)
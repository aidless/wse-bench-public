# 柱 B (T149–T160) Ground-Truth 核验报告 — r28

**日期**: 2026-07-25 | **核验人**: 新对话续作(易牧)
**方法**: 独立抓取三个官方 spec 页面,逐题比对 manifest 中 `rubric.required` 是否为官方文档**逐字原文**;非逐字者标注 PARAPHRASE / FABRICATED / UNVERIFIED。
**结论**: 12 题中 **0 题**的 required 串全部为逐字原文;MCP 4 题与 A2A 4 题为 PARAPHRASE(部分串 FABRICATED);AGNTCY 4 题中 3 题含官方文档不存在的断言(FABRICATED/UNVERIFIED)。**self-audit P0 #1 风险确认成立,严重性"高"。**

---

## 逐题核验

### MCP (source: modelcontextprotocol.io/specification/2025-06-18)

| ID | 当前 required | 官方事实 | 状态 | 修正为逐字串(官方) |
|---|---|---|---|---|
| T149 | `URIs following the scheme` / `text and binary` / `mimeType and annotations` | 官方:"Each resource is uniquely identified by a URI";"Resources can contain either text or binary data";字段 `mimeType` 与 `annotations` 分列。**[protocol]://[host]/[path] 句式官方无** | PARAPHRASE + 1 FABRICATED | `uniquely identified by a URI` / `text or binary data` / `mimeType` |
| T150 | `name, description, and inputSchema` / `type, properties, and required` / `validate tool call arguments` | 官方:"Each tool is uniquely identified by a name and includes metadata describing its schema";"inputSchema: JSON Schema defining expected parameters";"Servers MUST: Validate all tool inputs" | PARAPHRASE | `uniquely identified by a name` / `JSON Schema defining expected parameters` / `Validate all tool inputs` |
| T151 | `user-controlled templates identified by name` / `name, description, and required` / `prompts/list and prompts/get` | 官方:"Prompts are designed to be user-controlled";`prompts/list` `prompts/get` 为真实方法;arguments 例含 name/description/required | PARAPHRASE(末串正确) | `user-controlled` / `prompts/list` / `prompts/get` / `optional list of arguments` |
| T152 | `request LLM completions from the client` / `human-in-the-loop control` / `includeContext` | 官方:"servers to request LLM sampling";"human in the loop with the ability to deny";`includeContext` 为真实参数 | PARAPHRASE(末串正确) | `request LLM sampling` / `human in the loop` / `includeContext` |

### A2A (source: github.com/google/A2A raw specification.md)

| ID | 当前 required | 官方事实 | 状态 | 修正为逐字串(官方) |
|---|---|---|---|---|
| T153 | `JSON document that describes an agent` / `name, description, url, version, skills, capabilities` / `authentication requirements` | 官方定义:**"A JSON metadata document published by an A2A Server, describing its identity, capabilities, skills, service endpoint, and authentication requirements."** 末串正确;但"name/description/url/version"非该定义句内容 | PARAPHRASE(字段列错) | `JSON metadata document` / `describing its identity, capabilities, skills` / `authentication requirements` |
| T154 | `submitted, working, input-required, completed, failed, or canceled` / `current state in a Task or Message object` | 官方枚举:TASK_STATE_SUBMITTED/WORKING/INPUT_REQUIRED/COMPLETED/FAILED/CANCELED(另含 REJECTED/AUTH_REQUIRED);"MUST return... Task object OR Message object" | PARAPHRASE(实质对,枚举名大小写差异) | `submitted` / `working` / `input-required` / `completed` / `failed` / `canceled` / `Task` / `Message` |
| T155 | `text, file, and data` / `type discriminator and content object` / `multimodal task representation` | 官方:"The smallest unit of content within a Message or Artifact. Parts can contain text, file references, or structured data." 后两串官方无(proto 占位符未渲染) | PARAPHRASE + 2 FABRICATED | `smallest unit of content` / `text, file references, or structured data` |
| T156 | `server-sent events for streaming updates` / `TaskStatusUpdateEvent` / `TaskArtifactUpdateEvent` | 官方:"Server-Sent Events" 为复用标准;事件名 `TaskStatusUpdateEvent` `TaskArtifactUpdateEvent` 为真实类型 | PARAPHRASE(事件名正确) | `Server-Sent Events` / `TaskStatusUpdateEvent` / `TaskArtifactUpdateEvent` |

### AGNTCY (source: docs.agntcy.org — 原 github 仓库 404 / README 不含所声称内容)

| ID | 当前 required | 官方事实 | 状态 | 修正为逐字串(官方) |
|---|---|---|---|---|
| T157 | `Open Agent Schema Framework (OASF)` / `canonical representation of an agent` / `identity, skills, and dependencies` / `signed document` | 官方:"The Open Agentic Schema Framework (OASF) is a standardized schema system for defining and managing AI agent capabilities, interactions, and metadata." **名称漏"ic"**;"canonical representation of an agent" 官方无;OASF 核心是 `record object`,非"单签名文档" | FABRICATED(PARAPHRASE) | `Open Agentic Schema Framework (OASF)` / `standardized schema system` / `annotated with skills and domains` / `record object` |
| T158 | `directory service that stores agent records` / `indexed by skills and capabilities` / `query by capability` | 官方:"Federated registry for publishing, verifying, and discovering agents";"discover them by skill, capability, or annotation" | PARAPHRASE | `Federated registry for publishing, verifying, and discovering` / `discover them by skill, capability, or annotation` |
| T159 | `group communication primitives` / `identifier-based subscriptions` / `at-most-once and at-least-once delivery modes` | 官方 SLIM overview:"Native support for channels and group communication";"reliable message delivery";"end-to-end encryption (using the MLS protocol)";"publish/subscribe"。**"identifier-based subscriptions" 与 "at-most-once/at-least-once delivery modes" 官方 overview 无** | FABRICATED(2 串) | `channels and group communication` / `reliable message delivery` / `end-to-end encryption` / `publish/subscribe` |
| T160 | `signed attestations across multiple directories` / `trust scores as they complete verifiable tasks` / `decay over time` | 官方 Identity:"Decentralized identity for agents and tools—identifiers, verifiable credentials";"cryptographically verifiable identities";目录记录 "signed with a private key... verified via JWKS"。**"trust scores... decay over time" 官方无**(信任模型基于可验证凭证/JWKS,非数值衰减分) | FABRICATED("trust score decay") | `cryptographically verifiable identities` / `verifiable credentials` / `signed with a private key` / `JWKS` |

---

## 严重性汇总

- **MCP (T149–T152)**: PARAPHRASE 为主;T149 的 `[protocol]://[host]/[path]` 句式为 FABRICATED(官方仅列 https://,file://,git://,custom)。修正成本低,全部可锚定到真实逐字串。
- **A2A (T153–T156)**: 实质正确但表述为 paraphrase;T153 字段列错(name/description/url/version 非定义句内容);T155 后两串 FABRICATED(官方 proto 占位符未渲染)。修正成本低。
- **AGNTCY (T157–T160)**: **3/4 含官方文档不存在的断言**(T157 名称错漏+canonical 表述无;T159 两串无;T160 trust-score-decay 无)。这是最高风险——若保留原 required,正确引用官方文档的答案反而会判错。

## 推荐修正方案(待用户确认)

**方案 A(推荐):全 12 题 re-anchor 到上表"修正为逐字串"列**
- 同步更新每题 `prompt` 中的"原文："引用块为官方真实表述。
- 保留柱 B 12 题完整性,ground truth 全部可溯到官方 URL。
- 之后重跑 HASH LOCK(`build_bench.py` 或相应 hash 重锁),账本记 #34 PILLAR_B_REANCHOR。

**方案 B:AGNTCY 高风险 2 题(T159/T160)移除,其余 10 题 re-anchor**
- 理由:T159 的 delivery-mode 与 T160 的 trust-score-decay 在已抓取 overview 中无依据;若深读 session-layer / identity 深层文档仍找不到,则不应保留不可溯源 ground truth(TMLR 诚实边界:不Ship 无法溯源的 claim)。
- 柱 B 降为 10 题。

**方案 C:仅 re-anchor 已确认可溯源的 10 题,AGNTCY T159/T160 暂挂起待深读官方深层文档**
- 我先深挖 SLIM session-layer 与 AGNTCY Identity 深层页确认 delivery-mode / trust 机制是否存在,再决定 re-anchor 或移除。

## 影响评估

- 当前 33 条账本中**无任何条目依赖柱 B 12 题**(柱 B 属 r25 新增 cohort,未进入任何 PROMOTE/HOLD 统计;context_grounding 等结论基于 RC cohort,不受影响)。
- 故修正柱 B ground truth **不影响已发表的 7 策略结论与 r27 严格 ablation**,仅提升该 cohort 本身的有效性与可辩护性。
- 修正后必须重跑 HASH LOCK,否则 `--verify` 会因 manifest 变更失配 exit 2。

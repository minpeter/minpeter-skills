# Provider Matrix — Tool-Calling Schema Support (evidence table)

Verified 2026-08-04 against primary documentation. "Undocumented" means the
public docs were checked and no statement exists — it is not a guess in either
direction. Tool-input surface unless noted; structured *output* surfaces often
differ (e.g. Gemini allows top-level enums for `text/x.enum` responses).

## Composition / root / object policy

| Provider | Root object | anyOf | oneOf | allOf | required policy | additionalProperties |
|---|---|---|---|---|---|---|
| OpenAI strict | required (no root anyOf) | nested only | undocumented | **unsupported** | **all properties** | **false required** |
| Anthropic strict | required | yes | undocumented | yes (no `$ref` inside) | optional allowed | false in examples |
| Gemini (Schema, OpenAPI) | required via `parametersJsonSchema` | yes | undocumented | undocumented | optional | not listed |
| Gemini (`responseJsonSchema`) | output surface | yes | yes (= anyOf) | — | — | yes |
| Vertex | required | yes | not listed | not listed | optional | in proto |
| Bedrock | **required** | yes | — | yes (limited) | — | **false only** |
| Cohere | **required** | yes | **rejected** | **rejected** | ≥1 required per object | supported |
| Mistral | — | no public keyword matrix | | | | |
| GLM | examples-only | undocumented | undocumented | undocumented | selective | permissive transport |
| Kimi | **explicit** | undocumented | undocumented | undocumented | selective | undocumented |
| Qwen | **explicit** | undocumented | undocumented | undocumented | selective | undocumented |
| DeepSeek strict | required | yes | not listed | not listed | **all properties** | **false required** |
| xAI | required (object-branch root unions OK) | yes | yes (= anyOf) | single-subschema | omission = optional | default false |
| Fireworks | not stated | **yes** | **yes** | **yes** | yes | `unevaluatedProperties: false` semantics |
| FriendliAI | object examples | **yes (only)** | no | no | selective | ignored, always false |
| vLLM / SGLang | backend | via XGrammar | backend | backend | backend | backend |
| Together / GMI / Groq | OpenAI-compatible | undocumented | undocumented | undocumented | undocumented | undocumented |

## Formats, enums, limits

| Provider | format | enum | Notable limits |
|---|---|---|---|
| OpenAI strict | 9 enforced (date, date-time, time, duration, email, hostname, ipv4/6, uuid) | yes, ≤1,000 values (15k chars if >250) | depth 10, 5,000 properties, 120k schema chars |
| Anthropic strict | 10 supported | yes (numeric too); case-only differences leak | 20 strict tools, 24 optional + 16 union params |
| Gemini Schema | "most do not trigger any special functionality" | **string only** (typed Schema) | very large/deep schemas may be rejected |
| xAI | 8 enforced | yes | 128 tools (API ref) vs 200 (guide) — use 128 |
| DeepSeek strict | 5 (email, hostname, ipv4/6, uuid) | yes | 128 functions |
| Cohere | 4 (date-time, uuid, date, time) | yes | 200 fields aggregate; strict = API v2 only |
| Azure OpenAI | — | — | tool description ≤ 1,024 chars |
| Bedrock | Anthropic-like list | yes | Draft 2020-12 subset; 400s on unsupported |
| FriendliAI | — | — | `additionalProperties` always treated false |

## Sources

Primary docs (access 2026-08-04): developers.openai.com (structured-outputs,
function-calling, tools-tool-search) · docs.anthropic.com + platform.claude.com
(tool-use, strict-tool-use, structured-outputs) · anthropic.com/engineering/writing-tools-for-agents
· ai.google.dev (function-calling, structured-output, api/generate-content) ·
cloud.google.com Vertex Schema reference · firebase.google.com (function-calling,
generate-structured-output) · modelcontextprotocol.io spec 2025-11-25 +
SEP-1613 + issue #2806 · docs.aws.amazon.com/bedrock · docs.cohere.com ·
docs.mistral.ai · docs.z.ai · platform.kimi.ai · alibabacloud.com Model Studio ·
api-docs.deepseek.com · docs.x.ai · docs.fireworks.ai · friendli.ai/docs ·
docs.together.ai · docs.gmicloud.ai · console.groq.com · docs.vllm.ai ·
docs.sglang.io · openrouter.ai/docs.

Empirical: arXiv 2501.10868 (JSONSchemaBench) · arXiv 2509.18420 (IFEval-FC) ·
arXiv 2411.15100 (XGrammar) · EMNLP 2024 industry track (format restrictions
vs reasoning) · BFCL V4 format-sensitivity blog · arXiv 2504.19793
(ToolHijacker, NDSS 2026).

Aggregator/SDK failure evidence: github.com/BerriAI/litellm #23870 #27490
#34388 #28766 PR #31351 · github.com/vercel/ai #11041 #14342 #4662 #14678
#15730 #6572 #12183 PR #15283 · github.com/colinhacks/zod #5807 ·
github.com/langchain-ai/langchain-google #1076 · github.com/langchain4j #5947 ·
github.com/mlflow #24068 · github.com/aeewws/tool-schema-fixer
(normalization-rule inventory).

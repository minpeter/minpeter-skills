---
name: tool-schema-design
description: >-
  Designs JSON Schemas for LLM tool/function calling that survive across
  providers. Use when writing tool definitions, function-calling `parameters`,
  an MCP tool `inputSchema`, or zod/Pydantic tool schemas; when deciding
  between anyOf/oneOf/allOf; when choosing format/enum/description usage; or
  when one schema must run on several providers or strict modes (OpenAI,
  Anthropic, Gemini, Vertex, Bedrock, Cohere, xAI, DeepSeek, Fireworks,
  FriendliAI, vLLM/SGLang, and more). Covers the canonical-schema + adapter
  architecture, the hard rules (root object, no oneOf/allOf, nested anyOf
  allowed, no $ref/default/constraint keywords in the canonical schema),
  strict-mode transforms, the authoring guide for names, descriptions, and
  errors (what to write, what style, how long), and tool-design practices
  beyond the schema (naming, tool count, consolidation, output and error
  design, evals).
license: MIT
metadata:
  author: minpeter
---

# Tool Schema Design

House rules for writing LLM tool/function-calling schemas that work
everywhere. Verified against the primary docs of 12+ providers and inference
stacks — see [`references/provider-matrix.md`](references/provider-matrix.md)
for the per-provider evidence table.

## The architecture

No single JSON Schema is accepted unchanged by every provider. The decisive
contradiction: `additionalProperties: false` is **required** by OpenAI
strict, DeepSeek strict, and Bedrock, but stripped or rejected on
Gemini/Firebase paths. Nullability spelling also differs per provider. So:

**Keep one canonical schema (rich in meaning) → compile through thin
per-provider adapters → validate the post-transform wire schema.**

An adapter-free canonical schema is the best outcome; adapters exist only
for strict-mode transforms. Never ship a lowest-common-denominator schema as
the product — it is a non-strict fallback for discovery phases only.

## Hard rules (canonical schema)

Violating these cannot be repaired by an adapter.

| # | Rule | Why |
|---|------|-----|
| H1 | Root is a non-empty `type: "object"`. No root union/enum/const. | MCP, OpenAI strict, Bedrock, Cohere, Kimi, Qwen, xAI all force an object root. Top-level enums only exist in Gemini structured *output* — never tool input. |
| H2 | Concrete types only: `object`/`string`/`number`/`integer`/`boolean`/`array`; arrays carry one schema-valued `items`. | Universally supported; type errors are a graded failure class in tool-calling benchmarks. |
| H3 | `description` on the tool and on every non-obvious property (units, constraints, selection criteria). Skip tautologies. | Provider guidance calls descriptions the largest factor in tool performance. Descriptions cost tokens and are an attack surface on untrusted tools. |
| H4 | `oneOf`/`allOf`/`not` forbidden. **Nested `anyOf` is allowed.** | anyOf confirmed on OpenAI strict, Anthropic, xAI, DeepSeek strict, Cohere, current Gemini, Fireworks (full 2020-12), FriendliAI (anyOf *only*), vLLM/SGLang (XGrammar). oneOf/allOf are rejected or undocumented on several of these. Root anyOf stays banned via H1. Avoid even anyOf when targeting undocumented providers (Together, GMI, Groq, GLM/Kimi/Qwen) — split into separate tools or a string discriminator enum. |
| H5 | No `title`. | Absent from the Firebase vocabulary; costs nothing to skip. |
| H6 | Limits: nesting ≤ 10, total fields ≤ 200, tools ≤ 20 per request. | OpenAI depth cap 10; Cohere counts an aggregate 200-field budget; Anthropic strict allows 20 tools/request. Accuracy degrades as tool count grows. |
| H7 | No `$ref`/`$defs`/`default`/`const`/numeric-length constraints/`pattern` in the canonical schema. | An adapter-free schema beats a clever one. Inline repeated structures; put constraints in the description prose and validate server-side. |

## Soft rules (canonical holds the meaning; adapters transform)

| # | Rule | Adapter behavior |
|---|------|------------------|
| S1 | `required` reflects real optionality. Optional fields are fine. | OpenAI/DeepSeek strict: make every property required and encode optional as a nullable union. Everyone else: pass through. |
| S2 | Closed-object intent. | Inject `additionalProperties: false` recursively for OpenAI/DeepSeek/Bedrock; omit for Gemini/Firebase paths; omit for xAI (already default false). |
| S3 | Nullability is intent only. | OpenAI: null union / Anthropic: `["T","null"]` / Gemini: `nullable: true` / xAI & loose Anthropic: omit from `required`. Never conflate *missing* with *null*. Note: required+nullable has recorded runtime failures in production SDK paths — validate returned arguments. |
| S4 | Enums: string-valued on properties; use them for genuinely closed sets. | Legacy Gemini typed `Schema` only allows string enums (`repeated string`); numeric enums need the `parametersJsonSchema` path or string conversion. Under strict decoding enums are masked at token level — the strongest guarantee available. High-cardinality or evolving vocabularies belong in a string + lookup tool instead. |
| S5 | Use `format` (`date`, `date-time`, `email`, `uuid`, …). | Enforced by OpenAI strict, xAI, DeepSeek (5 formats); ignored but never rejected elsewhere. Never rely on it for validation — re-validate at the application boundary and repeat the semantics in the description ("ISO 8601 with UTC offset"). |
| S6 | ~~`$ref`/`default`/constraints tolerated~~ — superseded by H7: forbidden in the canonical schema. | Removing the keyword class removes the adapter logic for it entirely. |

## Adapter cheat sheet

- **OpenAI strict**: recursive `additionalProperties: false` + all properties required + optional → nullable union. Always set `strict: true`.
- **DeepSeek strict**: same as OpenAI; strip `minLength`/`maxLength`/`minItems`/`maxItems`; only email/hostname/ipv4/ipv6/uuid formats; beta base URL.
- **xAI**: strict is implicit — nothing to do. Omit explicit `additionalProperties: false`. Cap tools at 128 (docs contradict: 200 guide vs 128 API ref).
- **Anthropic**: pass through; `input_examples` available; ≤ 20 strict tools.
- **Gemini/Vertex/Firebase**: strip `additionalProperties`/strict wrappers, null union → `nullable: true`, inline `$defs`, drop `title`/`default`. `parameters` (OpenAPI subset) and `parametersJsonSchema` (JSON Schema) are different dialects — pick one and verify.
- **Bedrock**: object root + `additionalProperties: false`; Draft 2020-12 subset only.
- **Cohere**: ≥ 1 required property per object (disable `strict_tools` for no-arg tools); 200-field aggregate budget; remove oneOf/allOf.
- **GLM / Kimi / Qwen / Mistral**: no published keyword matrix — send the canonical schema as-is and validate returned arguments client-side. "OpenAI-compatible" describes the wire envelope, not strict behavior.
- **MCP**: keep the object root; flatten unions into separate tools or a string discriminator — hosts do not reliably consume `oneOf`.
- **Aggregators (OpenRouter/LiteLLM/Vercel AI SDK)**: pin provider+model+SDK version; validate the post-transform wire schema — these layers have stripped `parameters`, `required`, and `additionalProperties` in production. On OpenRouter set `require_parameters: true`.

## Beyond the schema (verified practices)

- **Naming**: `^[a-zA-Z0-9_-]{1,64}$` (the OpenAI∩Anthropic intersection; Gemini's wider charset is not portable). Namespace by service/resource (`asana_projects_search`); prefix vs suffix ordering measurably changes selection — choose by eval.
- **Consolidate**: one natural workflow = one tool with an `action` enum parameter, not one tool per endpoint.
- **Tool count**: ≤ 20 per turn; defer the long tail via tool search / dynamic loading (OpenAI namespaces, Kimi dynamic loading).
- **Enums for closed sets only**; OpenAI caps at 1,000 values.
- **Examples**: Anthropic `input_examples` (schema-validated, ~20–200 tokens); OpenAI warns examples can hurt reasoning models — put them in instructions instead.
- **Outputs**: return high-signal data + stable semantic IDs; add a `concise|detailed` detail parameter; paginate/truncate with defaults; on MCP emit `outputSchema` + `structuredContent` + a text mirror.
- **Errors**: separate protocol errors from execution errors; model-visible errors must say what to fix, never a raw traceback; validate inputs before executing.
- **Security**: remote tool metadata is untrusted input (MCP annotations, tool-search results) — allowlist, sanitize, show inputs to users. Crafted descriptions demonstrably hijack tool selection.
- **Maintenance**: generate schemas from Pydantic/Zod as the single source; CI-check type/schema drift; keep wire schemas byte-stable (providers cache compiled grammars); version semantic changes.
- **Evals**: iterate tool definitions against realistic multi-call tasks with held-out sets and operational metrics (calls, tokens, invalid-argument rate), not just tool-choice unit tests.

## Writing names, descriptions, and errors

Structure gets a schema *accepted*; authoring determines whether the model
calls it correctly. Full guide with templates:
[`references/authoring.md`](references/authoring.md). The short version:

- **Name**: self-describing `verb_noun` (`get_user_profile`, never
  `fetch(id)`); service-prefix when catalogs overlap.
- **Tool description = a short spec**, in order: what it does → when to use
  → when NOT to use + the alternative tool → what it returns → caveats.
  3–4 sentences; more only for complex tools. The
  "do NOT use for X, use Y" line is the highest-value sentence when tools
  overlap.
- **Write for the model, not humans**: no implementation details, no
  docstring-speak. Apply the intern test — a new engineer given only the
  schema should call the tool correctly.
- **Parameter descriptions**: one line = meaning + format/units + example
  (`"IANA time zone, e.g. America/Los_Angeles"`). Defaults go in prose
  ("default 500, max 2000"), never the `default` keyword (H7). Keep
  `required` minimal — models hallucinate values for required params the
  user never mentioned.
- **Errors**: never silent. `{success: false, error, retry_hint}` with a
  small canonical code set (`VALIDATION_ERROR`, `RATE_LIMITED`, …) and a
  retryable flag. The hint names the concrete fix.
- **Descriptions are eval-able artifacts**: wording changes change
  behavior — re-run tool evals after every edit.

## Operating principles

- Record capability in five distinct levels: `accepts` → `validates schema` → `constrains decoding` → `guarantees call` → `guarantees args`. A non-strict enum is a hint, not a guarantee.
- Pin every compatibility claim to provider + API version + model snapshot + strict flag + SDK version + date. Model-family drift is real (Kimi K3 vs K2.x tool_choice, Cohere strict = v2 only).
- Round-trip test adapter transforms for semantic changes; never inject dummy required sentinel fields to fake no-arg support.

## Not settled (do not guess)

Deeper production knowledge — failure taxonomy, strict-mode costs,
tool-count pressure, schema–model misalignment, schema
compilation — with verification labels:
[`references/deep-dive.md`](references/deep-dive.md).

GLM/Kimi/Qwen keyword-level acceptance (no public matrix) · xAI tool cap (200 vs 128 docs contradiction) · OpenAI/Anthropic `oneOf` status (undocumented) · schema-size↔accuracy curves (no controlled studies).

Nitpick: zod v4's `z.toJSONSchema()` always emits a root `$schema` key with no opt-out; no provider is known to reject it — ignore unless a rejection is observed.

# Provider Matrix: Versioned Tool-Input Targets

This matrix records tool-input behavior by API surface, not by provider brand.
It was re-verified against primary documentation on **2026-08-05**.

A row is still incomplete until a project pins its exact model and SDK version
and runs the conformance cases. Documentation acceptance is not the same as
schema validation, constrained decoding, guaranteed tool choice, or guaranteed
application-valid arguments.

## Evidence levels

Use these labels in adapter code and reviews:

| Label | Meaning |
|---|---|
| `documented` | The official provider documentation states the behavior. |
| `example-only` | An official example uses the shape, but no normative support statement was found. |
| `sdk-transform` | An official SDK rewrites the source schema before sending it. |
| `live-tested` | The exact model, surface, and SDK combination passed a recorded request test. |
| `unknown` | Do not infer support from wire compatibility or a neighboring surface. |

This file contains documented and example evidence. Add live-test records in the
project that owns the adapter, because credentials, models, and deployment
versions are environment-specific.

## Evidence ledger

The labels below attach an evidence level and primary source to each target ID
used by both matrix tables. A cell that says `unknown` still overrides the
row-level label; the ledger does not turn an example into a support guarantee.

| Target ID | Evidence | Primary source |
|---|---|---|
| `openai.responses.function.strict`, `openai.chat.function.strict` | `documented` | [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) |
| `anthropic.messages.tool.strict.raw` | `documented` | [Anthropic strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use) |
| `anthropic.sdk.tool.strict` | `sdk-transform` | [Anthropic structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) |
| `gemini.generateContent.function.parameters` | `documented` | [Gemini GenerateContent API](https://ai.google.dev/api/generate-content) |
| `gemini.generateContent.function.parametersJsonSchema` | `example-only` | [Gemini GenerateContent API](https://ai.google.dev/api/generate-content) |
| `vertex.v1.function.parameters` | `documented` | [Vertex FunctionDeclaration RPC](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rpc/google.cloud.aiplatform.v1) |
| `vertex.v1.function.parametersJsonSchema` | `example-only` | [Vertex FunctionDeclaration RPC](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rpc/google.cloud.aiplatform.v1) |
| `deepseek.beta.chat.function.strict` | `documented` | [DeepSeek tool calls](https://api-docs.deepseek.com/guides/tool_calls) |
| `cohere.v2.chat.strict_tools` | `documented` | [Cohere tool parameter types](https://docs.cohere.com/docs/tool-use-parameter-types) |
| `bedrock.converse.tool.strict`, `bedrock.invokeModel.claude.tool.strict` | `documented` | [Amazon Bedrock structured outputs](https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html) |
| `xai.tool.input` | `documented` | [xAI Structured Outputs](https://docs.x.ai/developers/model-capabilities/text/structured-outputs) |
| `fireworks.chat.function.parameters` | `documented` | [Fireworks tool calling](https://docs.fireworks.ai/guides/function-calling) and [JSON Schema support](https://docs.fireworks.ai/structured-responses/structured-response-formatting) |
| `mcp.2025-11-25.inputSchema` | `documented` | [MCP tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) |

## Target identity and core object rules

| Target ID | Surface and mode | Requiredness | Closed objects | Null and optional semantics | No-argument tool |
|---|---|---|---|---|---|
| `openai.responses.function.strict` | Responses API function tool with explicit `strict: true`; pin model | Every property must be in `required` | `additionalProperties: false` on every object | Optional non-nullable can use a null sentinel; optional nullable loses missing-vs-null distinction | Use an empty closed object only after target conformance; no dummy field |
| `openai.chat.function.strict` | Chat Completions function tool with `strict: true`; pin model | Same strict requirements | Same strict requirements | Same strict encoding issue | Use an empty closed object only after target conformance; no dummy field |
| `anthropic.messages.tool.strict.raw` | Messages API tool with `strict: true`, raw schema | Honest optional properties are supported within request-wide limits | Emit `additionalProperties: false` for source-closed objects; test open-map support | JSON Schema unions and optional properties are distinct | Empty object must be conformance-tested for the selected model/API |
| `anthropic.sdk.tool.strict` | Official SDK-generated strict tool schema | Source optionality is retained where the target supports it | SDK adds `additionalProperties: false`; open-map sources require a loss/unsupported diagnostic | SDK may transform the wire schema, then validates the original type | Pin SDK and test generated wire schema |
| `gemini.generateContent.function.parameters` | `FunctionDeclaration.parameters`, typed OpenAPI-style `Schema` | `required` is selective | No documented typed-Schema `additionalProperties` field in the API representation reviewed | Use typed-Schema `nullable: true`; do not use JSON Schema null syntax blindly | `parameters` is optional; verify omission or empty typed object in the selected client |
| `gemini.generateContent.function.parametersJsonSchema` | `FunctionDeclaration.parametersJsonSchema` | JSON Schema `required` | Official example uses `additionalProperties: false` | Never translate JSON Schema null syntax to `nullable`; emit null only after target evidence | Emit an empty JSON Schema object and test the selected model |
| `vertex.v1.function.parameters` | Vertex `FunctionDeclaration.parameters`, typed `Schema` | `required` is selective | Surface-specific; do not inherit the JSON-Schema-path rule | Use `nullable: true` on the typed path | Official RPC docs allow leaving parameters unset for a no-parameter function |
| `vertex.v1.function.parametersJsonSchema` | Vertex `parameters_json_schema` | JSON Schema `required` | Official example uses `additionalProperties: false` | Never translate JSON Schema null syntax to `nullable`; emit null only after target evidence | Empty object or omitted parameters; record a live test |
| `deepseek.beta.chat.function.strict` | Chat Completions beta base URL; every function `strict: true` | Every property of every object must be required | `additionalProperties: false` on every object | Current strict docs do not document a null type; optional-field encoding is unknown and must not be guessed | Unknown; block strict no-argument tools until live-tested |
| `cohere.v2.chat.strict_tools` | Chat API V2 with `strict_tools=True` | Each strict tool must declare at least one required top-level parameter | Supported subset; validate exact schema | Optional properties are allowed, but an all-optional tool is unsupported | Unsupported in strict mode because no required parameter exists |
| `bedrock.converse.tool.strict` | Bedrock Converse or ConverseStream tool with `strict: true`; pin model | Follow schema; no universal all-required statement | `additionalProperties` values other than `false` are unsupported; omission is example-only and must be tested | `null` is a supported basic type | Test by model and API surface |
| `bedrock.invokeModel.claude.tool.strict` | Bedrock InvokeModel Anthropic tool with `strict: true` | Follow schema and selected model limits | Official example closes the object; open-map sources need a loss/unsupported decision | `null` is in the Bedrock subset; model-specific limits still apply | Test by model and API surface |
| `xai.tool.input` | xAI tool parameters; strict input generation is implicit | Omission from `required` means optional | Defaults to false; set true explicitly to open an object | JSON Schema `null` is supported | Empty object should be live-tested |
| `fireworks.chat.function.parameters` | Fireworks Chat Completions tool `parameters`; pin model/deployment | JSON Schema `required` is selective | Schemas with `properties` are treated as closed by the structured grammar | `null` is supported | Empty object should be live-tested |
| `mcp.2025-11-25.inputSchema` | MCP tool `inputSchema`, default Draft 2020-12 | JSON Schema semantics | Explicitly controllable | JSON Schema semantics; host behavior still requires server validation | Recommended shape is `{ "type": "object", "additionalProperties": false }` |

## Composition, refs, constraints, and limits

| Target ID | Composition and refs | Formats and constraints | Notable request or schema limits |
|---|---|---|---|
| `openai.responses.function.strict` | Structured Outputs documents nested `anyOf`, `$defs`, `$ref`, and recursion; root `anyOf`, `allOf`, `not`, and conditionals are restricted | Support depends on model class; fine-tuned models lose several string, numeric, and array constraints | Structured Outputs docs list 5,000 object properties, nesting depth 10, and 120,000 total schema-name/enum/const characters |
| `openai.chat.function.strict` | Same Structured Outputs subset when strict is enabled | Same model-dependent subset | Chat Completions remains non-strict by default unless `strict: true` is set |
| `anthropic.messages.tool.strict.raw` | Use only the documented strict subset for the selected API revision; do not assume full JSON Schema | Raw unsupported constraints can fail compilation | 20 strict tools, 24 optional parameters, 16 union-typed parameters per request; additional grammar-size limits and 180-second compilation timeout |
| `anthropic.sdk.tool.strict` | SDK may simplify generated schemas | SDK removes unsupported constraints, adds them to descriptions where possible, filters formats, then validates the original source type | Same API limits as raw strict plus SDK-version-specific transforms |
| `gemini.generateContent.function.parameters` | Typed `Schema` exposes `anyOf`; it is not interchangeable with JSON Schema | Typed fields include nullable, enum, formats, length and numeric fields; `default` is accepted as documentation and ignored for validation | Large or deeply nested schemas can be rejected; pin model and client library |
| `gemini.generateContent.function.parametersJsonSchema` | The reviewed FunctionDeclaration reference identifies this as JSON Schema and shows an object example, but does not attach a tool-input keyword matrix | Treat keyword support beyond the official example as unknown until the selected model and API version are tested | The field is mutually exclusive with `parameters`; validate the post-transform payload |
| `vertex.v1.function.parameters` | The function-calling guide documents `anyOf`, typed `ref` and `defs`, and limited recursion for this OpenAPI-style surface | Supported fields include type, nullable, required, format, description, properties, items, enum, anyOf, ref, and defs; remaining attributes are unsupported | Up to 512 declarations are documented, nested-schema depth is capped at 32, and typed-def recursion is limited |
| `vertex.v1.function.parametersJsonSchema` | The RPC reference identifies a JSON Schema object and shows `additionalProperties: false`; no complete tool-input vocabulary was found in the reviewed page | Preserve source keywords only when documented or live-tested for the exact API version | Mutually exclusive with typed `parameters` |
| `deepseek.beta.chat.function.strict` | Documents `anyOf`, `$ref`, `$def`, and recursive refs | Supports `pattern`; formats: email, hostname, ipv4, ipv6, uuid; supports numeric const/default/bounds/multipleOf; rejects minLength, maxLength, minItems, maxItems | Unsupported schema types return an error; all tools in the request must set `strict: true` |
| `cohere.v2.chat.strict_tools` | Uses Cohere's Structured Outputs subset; verify keyword-by-keyword against the current V2 docs | The tool page delegates supported keyword details to the Structured Outputs vocabulary | Maximum 200 fields across all tools in one request |
| `bedrock.converse.tool.strict` | Draft 2020-12 subset: `anyOf`, limited `allOf`, internal `$ref`, `$def`, and `definitions`; no recursion or external refs | Formats include date/time/email/URI/IP/UUID; numerical and string constraints are unsupported; `minItems` only 0 or 1 | Unsupported features produce an immediate 400; first schema compilation can take minutes and successful grammars are cached 24 hours |
| `bedrock.invokeModel.claude.tool.strict` | Same Bedrock subset plus selected model behavior | Same subset; do not substitute Anthropic-direct limits | Anthropic Messages on the `bedrock-mantle` endpoint does not support Bedrock structured-output format, so surface selection matters |
| `xai.tool.input` | `anyOf`; `oneOf` behaves as `anyOf`; single-subschema `allOf`; non-circular `$ref` and `$defs` | Keywords have documented enforced, best-effort, and rejected classes; unknown formats should not be treated as guaranteed | Tool inputs are implicitly strict; pin model and API docs revision |
| `fireworks.chat.function.parameters` | Current docs support `anyOf`, `allOf`, `oneOf`, `$defs`, internal `$ref`, and recursive refs; external refs are unsupported | Supports length and array bounds, `pattern`, annotations, and defaults; unsupported regex constructs fall back to an unconstrained string | Support changed in mid-2026 for some deployment images, so pin deployment or model and retain live tests |
| `mcp.2025-11-25.inputSchema` | Valid JSON Schema object; defaults to Draft 2020-12 when `$schema` is absent | Protocol schema support does not guarantee every host/model enforces every keyword | Server must validate input, authorize execution, rate-limit, and sanitize output regardless of client behavior |

## Required adapter transforms

### OpenAI strict

- Set `strict: true`.
- Add `additionalProperties: false` recursively for source-closed objects.
- Reject or mark an intentional open map as lossy/unsupported if the selected
  strict target cannot preserve it.
- Put every property in `required`.
- Optional non-nullable source field: encode the complete constrained schema as
  nullable, then decode wire null to source missing. Mark `reversible`. If the
  field has an enum, const, or ref, ensure null is valid in the full branch, not
  only in the outer `type`.
- Optional nullable source field: mark distinction loss and reject by default.
- Validate the final schema against the exact model's Structured Outputs subset.

### Anthropic strict

- Add `additionalProperties: false` recursively.
- Preserve honest optional fields and nullability when the request-wide limits
  permit them.
- Raw API: reject unsupported keywords rather than silently passing them.
- SDK-assisted path: record every removed constraint and filtered format, then
  retain the original source validator. Pin the SDK version because the SDK is
  part of the compiler.

### Gemini and Vertex

- Split typed `parameters` from `parametersJsonSchema` before transforming.
- Typed path: JSON Schema null union becomes `nullable: true` only when that
  conversion preserves the source value set.
- JSON Schema path: never inject `nullable`. Keep source JSON Schema syntax,
  but emit each keyword only when the exact surface documents or passes it;
  otherwise return a diagnostic.
- Do not copy a keyword decision from Gemini to Vertex, or from output schemas
  to tool-input schemas, without matching the API surface.

### DeepSeek strict beta

- Use the beta base URL and set every function strict.
- Add `additionalProperties: false` and all-property `required` recursively.
- Retain only the documented formats.
- Drop unsupported min/max length and item-count keywords only with a lossy-wire
  diagnostic and source runtime validation.
- Do not synthesize optional-field nullability until a documented or live-tested
  null encoding exists for the target.

### Cohere V2 strict tools

- Count fields across the complete request.
- Verify each strict tool has at least one required top-level parameter.
- For a no-argument or all-optional tool, disable strict mode or omit the tool.
  Never inject a dummy parameter.

### Bedrock

- Select Converse, InvokeModel, or another documented surface explicitly.
- Compile source-closed objects with `additionalProperties: false` against
  Bedrock's supported Draft 2020-12 subset. The supported-feature section
  rejects `additionalProperties` values other than false, while the official
  Converse strict-tool example omits the keyword; record a live test for
  omission behavior instead of assuming parity. Reject or explicitly classify
  an intentional open map as lossy/unsupported.
- Reject recursion and unsupported numeric or string constraints at compile time,
  or mark them as runtime-enforced only under an explicit policy.

## Primary sources

Accessed 2026-08-05:

- OpenAI function calling:
  https://developers.openai.com/api/docs/guides/function-calling
- OpenAI Structured Outputs:
  https://developers.openai.com/api/docs/guides/structured-outputs
- Anthropic strict tool use:
  https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
- Anthropic structured outputs and SDK transforms:
  https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Gemini GenerateContent API, `Schema`, and `FunctionDeclaration`:
  https://ai.google.dev/api/generate-content
- Vertex AI FunctionDeclaration RPC reference:
  https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rpc/google.cloud.aiplatform.v1
- Vertex AI function calling guide:
  https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling
- DeepSeek tool calls and strict beta:
  https://api-docs.deepseek.com/guides/tool_calls
- Cohere tool parameter types, Chat API V2:
  https://docs.cohere.com/docs/tool-use-parameter-types
- Amazon Bedrock structured outputs and strict tool use:
  https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html
- xAI Structured Outputs and tool-input schema rules:
  https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- Fireworks tool calling:
  https://docs.fireworks.ai/guides/function-calling
- Fireworks JSON Schema support:
  https://docs.fireworks.ai/structured-responses/structured-response-formatting
- MCP tools specification, revision 2025-11-25:
  https://modelcontextprotocol.io/specification/2025-11-25/server/tools

## Not profiled yet

Mistral, GLM, Kimi, Qwen, Groq, Together, GMI, FriendliAI, OpenRouter,
LiteLLM, Vercel AI SDK, vLLM, and SGLang are deliberately omitted from the
normative matrix until each row is split by API surface and pinned to primary
evidence. An OpenAI-compatible request envelope does not establish OpenAI
strict-schema behavior.

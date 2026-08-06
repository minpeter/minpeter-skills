---
name: tool-schema-design
description: >-
  Designs portable JSON Schemas for LLM tool and function calling without
  silently changing meaning. Use when authoring OpenAI function parameters,
  Anthropic tool input_schema, Gemini or Vertex FunctionDeclaration schemas,
  Bedrock strict tools, MCP inputSchema, or Zod and Pydantic-generated schemas;
  when required, nullable, additionalProperties, anyOf, oneOf, refs, formats,
  defaults, or constraints behave differently across targets; or when building
  a schema adapter. Separates the semantic source contract, target profile,
  wire schema, and runtime validator; grades transforms as exact, reversible,
  lossy, or unsupported; and provides provider-surface rules, authoring guidance,
  diagnostics, and conformance cases.
license: MIT
metadata:
  author: minpeter
---

# Tool Schema Design

Design tool schemas as a compilation problem, not as a search for one JSON
object that every provider accepts.

## Rule zero: there is no universal wire schema

Providers expose different schema dialects, strict-mode rules, model limits,
and SDK transforms. A schema that is valid for one target can be rejected by
another, or worse, accepted with different meaning.

Use four layers:

1. **Semantic source contract**: the application's full meaning.
2. **Target profile**: provider, API surface, version, model, strict flag, SDK,
   and verification date.
3. **Wire schema compiler**: transforms the source for exactly that target and
   reports every semantic or enforcement change.
4. **Runtime validator**: validates returned arguments against the source
   contract before execution.

```text
semantic source contract
        ↓ compile(target profile)
wire schema + diagnostics + decoder
        ↓ provider/model
returned arguments
        ↓ decode + validate(source contract)
trusted application input
```

Never call a lowest-common-denominator wire schema the canonical schema. It has
already discarded meaning.

## Non-negotiable invariants

1. **Preserve the source contract.** Keep real requiredness, nullability,
   defaults, enums, formats, constraints, refs, recursion, and open or closed
   object intent in the source. A target adapter may lower a feature, but may
   not erase it silently.
2. **Tool arguments form an object.** The root is an object for portable tool
   input. A genuine no-argument tool uses an empty object. Never invent a dummy
   required field to satisfy a provider.
3. **Requiredness and nullability are independent.** Missing and explicit
   `null` are different states unless the application deliberately merges them.
4. **Arrays have one schema-valued `items`.** Do not encode arrays as strings or
   omit the item type.
5. **Pin the target surface.** `Gemini parameters` and
   `Gemini parametersJsonSchema` are different targets. So are raw provider
   APIs, cloud wrappers, and SDK-generated schemas.
6. **Validate twice.** Validate the compiled wire schema before sending it, then
   validate model arguments against the semantic source before execution.
7. **No silent loss.** Every dropped keyword, widened value set, merged state,
   or changed object policy produces a diagnostic.

## Requiredness and nullability

Model these four contracts explicitly:

| Source contract | Valid states |
|---|---|
| required `T` | value |
| required `T | null` | value, explicit null |
| optional `T` | missing, value |
| optional `T | null` | missing, explicit null, value |

An all-properties-required target can encode optional non-nullable `T` as
required `T | null`, then decode `null` back to missing. That transform is
reversible because the source never permits explicit null. When `T` carries an
`enum`, `const`, `$ref`, or other constraints, the nullable transform must wrap
or extend the complete constrained schema. Merely adding `null` to `type` while
an `enum` still excludes null is not a valid sentinel encoding.

The same target cannot faithfully encode optional nullable `T | null`. Both
missing and explicit null become `null`. This is an unrecoverable distinction
loss and must be rejected by default.

## Compiler contract

A compiler returns more than a JSON object:

```ts
type Fidelity = "exact" | "reversible" | "lossy" | "unsupported";
type Enforcement = "grammar" | "runtime" | "descriptive" | "none";

type Diagnostic = {
  path: string;
  code: string;
  fidelity: Fidelity;
  enforcement: Enforcement;
  distinction_lost: boolean;
  message: string;
  action: string;
};

type CompileResult = {
  targetId: string;
  wireSchema?: unknown;
  decoder?: "identity" | "null-sentinel-to-missing";
  diagnostics: Diagnostic[];
};
```

Default policy:

- `exact`: allow.
- `reversible`: allow only with the declared decoder and round-trip tests.
- `lossy`: block when a semantic distinction is lost. A widened wire grammar
  may be allowed only with an original-schema runtime validator, safe retry
  behavior, and an explicit policy decision.
- `unsupported`: do not send the request.

Two losses that look similar are operationally different:

- Removing `minimum: 1` from the wire schema widens generation, but the source
  validator can still detect an invalid value and request a retry.
- Collapsing missing and explicit null cannot be recovered after generation.
  Runtime validation cannot tell which state the model intended.

## Target profile

A target ID must identify the actual contract, not merely the company:

```json
{
  "id": "gemini.generateContent.function.parametersJsonSchema",
  "provider": "google",
  "api_surface": "generateContent.FunctionDeclaration.parametersJsonSchema",
  "api_version": "v1beta",
  "model": "<exact model snapshot>",
  "strict": false,
  "sdk": "<name or raw-http>",
  "sdk_version": "<pinned version>",
  "verified_at": "2026-08-05"
}
```

Compatibility claims without the surface, mode, and version are discovery
notes, not production evidence. See
[`references/provider-matrix.md`](references/provider-matrix.md).

## Portable authoring profile

Use this profile to reduce adapter work for new tools. It is not a universal
wire format and it does not justify deleting meaning from an existing source.

- Object root; empty object allowed for no-argument tools.
- Concrete JSON types and schema-valued array `items`.
- Honest `required` lists and explicit nullability.
- String enums for genuinely closed sets.
- Descriptions for the tool and every non-obvious field.
- Simple nesting and small active tool catalogs.
- Prefer `anyOf` over `oneOf` only when the selected targets document it.
- Treat refs, defaults, formats, patterns, and numeric or length constraints as
  source semantics to be lowered per target, not as globally forbidden syntax.
- Avoid root unions, conditionals, and complex composition unless every target
  profile has a conformance result for that shape.

## Adapter decisions by target

The full evidence table is in
[`references/provider-matrix.md`](references/provider-matrix.md). These are the
house decisions:

- **OpenAI strict function tools**: close every object, require every property,
  and use a nullable wire union only for an optional non-nullable source field.
  Decode null back to missing. Reject optional nullable fields unless the
  application explicitly accepts state collapse. Set `strict: true`.
- **Anthropic strict, raw API**: set `strict: true`, preserve honest optional
  fields and unions within Anthropic's request-wide complexity limits, and emit
  `additionalProperties: false` for source-closed objects. Do not silently
  close an intentional open map; reject it or mark it lossy when the selected
  target cannot preserve that object policy.
- **Anthropic SDK-assisted strict**: SDKs may strip unsupported constraints,
  copy them into descriptions, close objects, filter formats, and validate the
  original type after generation. Record this as lossy wire enforcement plus
  runtime enforcement, and pin the SDK version.
- **Gemini or Vertex typed `parameters`**: compile to the typed OpenAPI-style
  `Schema` dialect. Use `nullable: true` there, not in JSON Schema. If the typed
  surface cannot express closed-object intent or another source feature, emit a
  runtime-enforced diagnostic.
- **Gemini or Vertex `parametersJsonSchema`**: keep the source in JSON Schema
  syntax. Never rewrite a JSON Schema null union to typed-Schema `nullable`.
  Emit null unions, refs, and `additionalProperties` only where the exact target
  documents or passes those cases; otherwise report unsupported or runtime-only
  enforcement rather than switching dialects.
- **DeepSeek strict beta**: use the beta surface, set every function strict,
  close every object, require every property, filter formats to the documented
  allowlist, and remove unsupported length and array-size constraints only with
  diagnostics. The current docs do not establish a portable null encoding, so
  do not guess how to represent optional fields.
- **Cohere Chat API V2 `strict_tools`**: each strict tool needs at least one
  required top-level parameter and the request has a 200-field aggregate limit.
  A no-argument or all-optional tool is unsupported in strict mode; disable
  strict for that request or withhold the tool. Never add a sentinel parameter.
- **Bedrock strict tools**: select the exact API surface and model. Emit
  `additionalProperties: false` for source-closed objects, reject or explicitly
  mark open-map sources as lossy when the selected subset cannot preserve them,
  and reject unsupported recursion or constraints instead of assuming Anthropic
  parity.
- **xAI tool inputs**: strict input generation is implicit. Preserve optionality
  through omission from `required`, preserve nullability with JSON Schema null,
  and respect xAI's documented keyword enforcement levels.
- **Fireworks tool parameters**: use its current JSON Schema profile, including
  documented refs and composition, but pin the deployment or model because
  support has changed over time. Treat best-effort regex enforcement as such.
- **MCP**: emit a valid JSON Schema object. For a no-argument tool use
  `{ "type": "object", "additionalProperties": false }`. Validate arguments
  on the server regardless of host behavior.

Unprofiled providers are not "OpenAI strict" merely because their transport is
OpenAI-compatible. Add a target profile only after official-doc review and a
wire conformance test.

## Tool design beyond the schema

- **Names**: self-describing `verb_noun` or service-prefixed names. Keep names
  stable after deployment.
- **Descriptions**: state what the tool does, when to use it, when not to use it
  and the alternative, what it returns, and material caveats.
- **Catalog size**: expose the smallest relevant active set. Use tool search or
  dynamic loading rather than sending the long tail on every turn.
- **Outputs**: return compact high-signal data and stable semantic IDs. When
  using MCP, pair `outputSchema` and `structuredContent` where useful.
- **Errors**: separate protocol errors from execution errors. Model-visible
  execution errors say what must change and whether retry is safe.
- **Mutations**: make retries idempotent or provide idempotency keys.
- **Security**: treat remote tool metadata and descriptions as untrusted input.
  Allowlist tools, sanitize metadata, authorize at execution time, and never
  execute solely because a model produced schema-valid arguments.
- **Evals**: test tool selection, argument validity, multi-call recovery,
  latency, tokens, retries, and execution safety on held-out tasks.

Writing templates are in
[`references/authoring.md`](references/authoring.md). Failure modes and research
notes are in [`references/deep-dive.md`](references/deep-dive.md).

## Required workflow

1. Define or generate the semantic source contract.
2. Record missing versus null semantics explicitly.
3. Select a versioned target profile.
4. Compile and inspect diagnostics.
5. Reject unsupported or unapproved distinction-losing transforms.
6. Validate the wire schema against the target profile.
7. Run the conformance cases in
   [`references/conformance.md`](references/conformance.md).
8. Send the request.
9. Decode reversible transport encodings.
10. Validate arguments against the source contract.
11. Authorize and execute the tool.
12. Re-run tool evals after any name, description, schema, adapter, model, API,
    or SDK change.

# Conformance Cases for Tool-Schema Adapters

Run these cases for every target profile and after every provider, API, model,
SDK, schema-generator, or adapter change.

A documentation review is not a substitute for a request test. Store the exact
request, response or error, date, model, API version, SDK version, generated wire
schema, and adapter diagnostics.

## Result vocabulary

Record each case with these fields:

```json
{
  "case": "optional_nullable",
  "target_id": "openai.responses.function.strict",
  "model": "<exact model>",
  "api_version": "<version>",
  "sdk": "<name and version>",
  "verified_at": "<YYYY-MM-DD>",
  "schema_validation": "accepted | rejected | unknown",
  "generation_enforcement": "full | partial | best_effort | none | unknown",
  "wire_fidelity": "exact | reversible | lossy | unsupported",
  "decoder": "identity | null-sentinel-to-missing | none",
  "distinction_lost": true,
  "diagnostics": [],
  "evidence": "<official URL and stored test identifier>"
}
```

Do not use `accepted` to mean enforced. A server may accept a keyword and ignore
it, or an SDK may remove it before the request reaches the server.

## Core semantic cases

### C01: no argument

Source:

```json
{
  "type": "object",
  "properties": {},
  "required": [],
  "additionalProperties": false
}
```

Expected behavior:

- Target accepts a genuine empty argument object, omits the parameter schema, or
  reports unsupported.
- Adapter never invents a sentinel field.
- MCP wire target uses the empty closed object.
- Cohere V2 strict target reports unsupported because no required parameter
  exists.

### C02: required non-nullable

```json
{
  "type": "object",
  "properties": { "query": { "type": "string" } },
  "required": ["query"],
  "additionalProperties": false
}
```

Expected fidelity: `exact` on any target that supports the basic object shape.

### C03: required nullable

```json
{
  "type": "object",
  "properties": {
    "middle_name": { "type": ["string", "null"] }
  },
  "required": ["middle_name"],
  "additionalProperties": false
}
```

Expected behavior:

- Field remains required.
- Adapter must not remove it from `required` merely because it permits null.
- Typed OpenAPI-style targets may encode the same value set with
  `nullable: true`; classify as exact only after dialect validation.

### C04: optional non-nullable

```json
{
  "type": "object",
  "properties": { "language": { "type": "string" } },
  "required": [],
  "additionalProperties": false
}
```

For an all-properties-required target:

- wire: required `string | null`
- decoder: null sentinel to missing
- fidelity: `reversible`
- round trip: source missing -> wire null -> source missing

The source validator must still reject explicit source null. Repeat this case
with an enum and a `$ref`: the adapter must make the complete constrained branch
nullable. Changing only `type` while an enum still excludes null is invalid.

### C05: optional nullable

```json
{
  "type": "object",
  "properties": {
    "note": { "type": ["string", "null"] }
  },
  "required": [],
  "additionalProperties": false
}
```

For an all-properties-required target, expected result:

```json
{
  "wire_fidelity": "lossy",
  "distinction_lost": true,
  "diagnostic_code": "OPTIONAL_NULLABLE_STATE_COLLAPSE",
  "default_action": "reject"
}
```

Missing, explicit null, and value are three source states. Required nullable has
only null and value. No decoder can recover the missing-versus-null distinction.

## Object-policy cases

### C06: nested closed objects

Every nested object is closed in the source. Verify recursive injection for
strict targets and verify that an adapter does not accidentally open a nested
object while closing only the root.

### C07: intentionally open object

```json
{
  "type": "object",
  "properties": {
    "labels": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    }
  },
  "required": ["labels"],
  "additionalProperties": false
}
```

A target that permits only `additionalProperties: false` cannot preserve the
open string-map contract. Expected fidelity is `unsupported` or `lossy` with
semantic distinction loss. Do not silently close the map.

## Constraint cases

### C08: date-time format

Source contains `format: date-time`. Verify whether the target rejects, enforces,
accepts best-effort, or requires removal. Always validate the value at runtime.

### C09: provider-specific format gap

Use `format: date` against DeepSeek strict beta. Its current documented allowlist
does not include date. Expected adapter action: remove with a diagnostic and
runtime validation, or reject by policy. Never pass through with a claim of
universal safety.

### C10: numeric bounds

```json
{ "type": "integer", "minimum": 1, "maximum": 5 }
```

Verify exact enforcement, SDK removal, server rejection, or runtime-only
validation. Record enforcement separately from transport acceptance.

### C11: string pattern and length

Use both `pattern` and `minLength` so the test detects targets that support one
but reject or ignore the other.

### C12: array bounds

Use `minItems: 1` and `maxItems: 5`. Bedrock's documented `minItems` behavior and
DeepSeek's documented lack of item-count support must produce different target
results.

## Composition and reference cases

### C13: nested anyOf

Use a nested property with two distinct branches. Verify branch enforcement and
ensure the root remains an object.

### C14: root anyOf

Expected default portable decision: reject for tool input unless the target
profile explicitly supports and has live evidence for an object-root union.

### C15: oneOf

Use overlapping and non-overlapping branches. Detect providers that interpret
`oneOf` as `anyOf`, reject it, or enforce exclusive matching.

### C16: allOf

Use two subschemas. Detect targets that reject it, support only one subschema, or
implement limited merging.

### C17: internal refs

Use root `$defs` with an internal JSON Pointer `$ref`. Verify that the adapter
preserves or inlines it without changing requiredness or object policy.

### C18: recursive refs

Use a linked-list or tree schema. Expected results differ sharply: OpenAI and
current Fireworks document recursion, xAI documents non-circular refs only, and
Bedrock documents no recursive schemas.

### C19: external ref

Use an HTTP `$ref`. Default decision is unsupported unless the adapter resolves
and inlines it before compiling. Providers must never fetch arbitrary external
schemas at generation time.

## Enum and default cases

### C20: string enum

Verify exact value masking or best-effort behavior.

### C21: numeric enum

Detect typed surfaces that only expose string enums and JSON Schema surfaces
that preserve numeric enums.

### C22: default annotation

Verify whether `default` is retained, ignored, removed, or rejected. Do not
assume a provider inserts the value. Application defaulting occurs before or
after tool invocation under an explicit contract.

## Request-level cases

### C23: tool-count growth

Run the same held-out tasks with 5, 10, 20, and a larger active catalog. Measure
wrong-tool rate, no-tool rate, latency, tokens, and invalid arguments. This is a
quality curve, not merely a hard-limit test.

### C24: aggregate optional and union limits

Construct an Anthropic strict request near 24 optional fields and 16 union-typed
fields. Verify the current API behavior and compilation diagnostics.

### C25: aggregate field limit

Construct Cohere V2 strict requests below and above 200 fields across all tools.

### C26: schema cache identity

Send byte-identical and semantically equivalent but byte-different schemas.
Measure cold compilation latency and cache behavior where the provider documents
schema compilation.

## Runtime safety cases

### C27: wire-valid, source-invalid

Remove a source constraint from the wire grammar, then produce a value that the
wire accepts and source rejects. Verify that execution does not occur and the
model receives an actionable, bounded retry.

### C28: unauthorized but schema-valid

Produce a perfectly valid mutation call without sufficient authorization.
Verify independent policy denial.

### C29: timeout after possible mutation

Simulate an upstream timeout after the side effect may have occurred. Verify
idempotency key behavior and do not blindly retry.

### C30: malicious tool description

Inject instructions into untrusted remote tool metadata. Verify allowlisting,
sanitization, user-visible confirmation where required, and that metadata does
not override system or application policy.

## Minimum CI assertions

- Every target profile has a unique ID and verification date.
- Every compile result has diagnostics, even when empty.
- No `lossy` result with `distinction_lost: true` is emitted without failure.
- Every `reversible` result names and tests its decoder.
- Every removed keyword appears in diagnostics with its source path.
- Generated wire schemas are stable fixtures and diffed in review.
- Arguments are validated against the source contract before handler execution.
- No-argument tools never gain dummy fields.
- Typed `parameters` and `parametersJsonSchema` fixtures are never mixed.

# Deep Dive: Failure Modes and Production Reasoning

This file separates documented provider behavior, research claims, and house
practice. Do not turn a paper result or a single provider example into a
universal schema rule.

Labels:

- **[documented]**: supported by current primary provider or protocol docs.
- **[paper]**: a research result that may be model, dataset, or implementation
  specific.
- **[practice]**: an engineering policy derived from failure containment.

## 1. The deepest bug is semantic collapse [practice]

A provider rejection is visible. A schema accepted with changed meaning is more
dangerous.

Examples:

- An optional nullable field becomes required nullable, collapsing missing and
  explicit null.
- A closed source object becomes open because an adapter drops
  `additionalProperties: false`.
- A numeric range disappears from the wire grammar and no source validator runs.
- A JSON Schema null union is rewritten to an OpenAPI `nullable` keyword on a
  JSON Schema surface that may ignore it.
- A provider-level rule is copied to a different API surface owned by the same
  company.

The compiler must report these as semantic or enforcement changes, not as
successful normalization.

## 2. Schema support has multiple levels [practice]

Record capabilities separately:

1. **Transport accepts** the request field.
2. **Server validates** the schema vocabulary.
3. **Decoder constrains** generation to the schema.
4. **Tool choice is guaranteed** when requested.
5. **Arguments satisfy the wire schema**.
6. **Arguments satisfy the application source contract**.
7. **Execution is authorized and safe**.

An enum in a non-strict prompt is a hint. A constrained decoder may guarantee the
wire enum but cannot guarantee authorization, business invariants, freshness, or
safe side effects.

## 3. Strict mode has real costs [documented]

Strict generation usually compiles a schema into a grammar. Providers document
first-use latency, grammar caching, and complexity limits. The exact constraints
vary by surface:

- OpenAI strict requires closed objects and all properties required.
- Anthropic limits strict tools, optional fields, and union-typed fields across
  the entire request, then applies additional internal grammar limits.
- Bedrock validates a Draft 2020-12 subset, returns 400 for unsupported features,
  and caches successful grammar compilations.
- DeepSeek strict beta validates its documented subset and rejects unsupported
  schema types.

Consequences:

- Keep active schemas and tool catalogs focused.
- Keep wire schemas byte-stable when provider caches key on schema identity.
- Treat a new schema or adapter output as a deployment-affecting change.
- Put cross-field business logic in the source validator and handler rather than
  forcing every rule into the grammar.

## 4. SDKs can be schema compilers [documented]

An SDK helper is not neutral serialization. Anthropic documents SDK transforms
that remove unsupported constraints, move constraint information into
field descriptions, close objects, filter formats, and validate the original
source type after generation.

Therefore the target profile includes:

- SDK name and version
- source-schema generator version, such as Pydantic or Zod
- generated wire schema
- post-generation parser or validator

Upgrading an SDK can change behavior even when application source code and model
remain unchanged.

## 5. Tool-count pressure [documented + practice]

Providers publish different hard limits, and model quality can degrade before a
hard limit is reached. Do not turn a house budget such as 20 active tools into a
universal protocol cap.

Mitigations:

- select tools per turn or sub-agent
- use provider tool search or dynamic loading when available
- namespace only where it improves disambiguation
- consolidate one natural workflow rather than every backend endpoint
- evaluate wrong-tool rate as the active catalog grows

## 6. Description engineering [documented + practice]

Primary provider guidance consistently treats clear descriptions as important.
The highest-leverage information is usually the boundary against adjacent tools:
when not to use this tool and which tool to use instead.

Description changes can fix observed selection and argument mistakes, but they
must not replace structural validation. A sentence saying "positive integer"
does not enforce an integer or positivity.

## 7. Failure taxonomy [practice]

Classify a failure before changing the schema:

1. **Selection failure**: wrong tool or no tool.
   - Improve name, use and non-use boundaries, catalog selection, or examples.
2. **Wire-schema failure**: target rejects or miscompiles the schema.
   - Fix the target profile or adapter; do not weaken the source globally.
3. **Argument-shape failure**: missing field, wrong type, invented field.
   - Use strict decoding where appropriate, improve descriptions, and validate.
4. **Semantic argument failure**: wire-valid but application-invalid value.
   - Preserve source constraints, return actionable errors, and retry safely.
5. **Recovery failure**: model repeats the same invalid call.
   - Improve error codes and retry hints; cap retries and surface to the user.
6. **Execution-safety failure**: valid call lacks authorization or has unsafe
   side effects.
   - Enforce policy outside the model, use idempotency, and require confirmation
     where appropriate.
7. **Adapter drift**: provider, model, SDK, or aggregator changes behavior.
   - Pin versions, store generated wire schemas, and rerun conformance tests.

## 8. Research claims need scoped citations [paper]

Benchmarks such as JSONSchemaBench, BFCL, IFEval-FC, schema-compilation papers,
and tool-naming studies can reveal useful failure modes. Their numbers are not
portable unless the artifact records:

- paper version and table or figure
- model and decoding backend
- schema set and task distribution
- strict versus prompt-only mode
- whether the result measures acceptance, compilation, argument validity, or
  end-task success

Do not copy headline percentages into the house rules without that scope. Prefer
qualitative takeaways in the skill and keep exact results in a dated research
note.

## 9. Tool calls are RPCs [practice]

Treat every call as an untrusted remote procedure call:

- validate input before execution
- authenticate and authorize independently of schema validity
- make mutations idempotent or attach idempotency keys
- distinguish timeout from confirmed failure
- rate-limit by caller and operation
- redact secrets from prompts, schemas, logs, and errors
- sanitize outputs before returning them to the model
- log target profile, wire schema hash, model, diagnostics, tool choice, and
  validation result for incident analysis

## 10. Evaluation should measure consistency [practice]

A production evaluation suite includes:

- correct tool selection
- false-positive tool selection
- argument type and required-field validity
- source-contract validity after decoding
- missing versus null preservation
- multi-tool sequencing
- error recovery and retry count
- idempotency behavior
- latency and grammar-compilation cold start
- token cost and active catalog size
- variance across repeated runs

A high average pass rate can hide a costly tail. Track consistency and failure
classes, not only pass-at-one.

## Primary references

Provider and protocol links are maintained in
[`provider-matrix.md`](provider-matrix.md). Conformance cases and the expected
compiler diagnostics are in [`conformance.md`](conformance.md).

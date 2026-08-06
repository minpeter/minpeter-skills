# Authoring Guide: Names, Descriptions, Parameters, Outputs, and Errors

Schema compilation determines whether a provider accepts a tool. Authoring
determines whether the model selects it, fills it correctly, and recovers after
failure. Treat names and descriptions as behavior-affecting artifacts and test
them like code.

## Names

Use a self-describing action and resource:

- `get_user_profile`, not `fetch`
- `github_list_pull_requests`, not `process_data`
- `calendar_find_availability`, not `find`

House rules:

- Prefer `^[a-zA-Z0-9_-]{1,64}$` unless every target profile permits more.
- Prefer underscores when targeting providers that discourage punctuation.
- Namespace by service when catalogs overlap.
- Keep a deployed name stable. A semantic behavior change gets a new tool name
  or versioned contract.
- Evaluate prefix and suffix variants instead of assuming one naming order wins
  across models.

## Tool description as a selection contract

Write the description in this order:

1. **What it does**: one concrete sentence.
2. **When to use it**: user intents and triggering situations.
3. **When not to use it, plus the alternative**: the boundary against adjacent
   tools.
4. **What it returns**: the data and identifiers the model can use next.
5. **Material caveats**: scope, freshness, permissions, or side effects.

Example:

```text
Search saved contacts by name, email, company, or domain. Use this before
sending email or creating a calendar invitation when the recipient is not
already resolved to an address. Do not use it to search the public web; use the
web-search tool instead. Returns stable contact identifiers and available email
addresses. Results may be incomplete when directory access is restricted.
```

The highest-value sentence for overlapping tools is usually the explicit
"do not use for X; use Y" boundary.

### Length and style

- Simple tools usually need three or four information-dense sentences.
- Stay within the smallest description limit of the selected targets.
- Write for the model that must choose and call the tool, not for the engineer
  reading implementation details.
- Exclude backend trivia such as HTTP methods, library versions, or internal
  endpoint names unless that fact changes correct use.
- Use declarative prose. Avoid vague words such as "process", "handle", or
  "data" when a concrete verb and object exist.
- Include a micro-example only when it disambiguates format or intent.
- Re-run evaluations after punctuation and wording edits; description changes
  can change selection behavior.

## Parameter descriptions

One line should communicate meaning, representation, units, and one example when
useful:

```text
"symbol": "Exchange ticker symbol, for example AAPL."
"window_start": "Inclusive ISO 8601 timestamp with UTC offset, for example 2026-08-05T09:00:00+09:00."
"organizer_tz": "IANA time zone, for example Asia/Seoul."
"radius_m": "Search radius in metres, greater than 0."
```

Rules:

- Mirror exact schema field names in system instructions and examples.
- Keep `required` semantically honest. Do not require a value merely because a
  strict target requires all wire properties; that is an adapter concern.
- Record application defaults in the source contract. Whether `default` is sent
  on the wire is a target decision, and JSON Schema defaults are generally
  annotations rather than automatic value insertion.
- Put units and time-zone expectations in both the source validator and the
  description.
- Use enums only for genuinely closed and stable sets. High-cardinality or
  evolving vocabularies belong in a lookup tool or validated string.
- Do not describe tautological fields such as two mathematical operands named
  `a` and `b` unless additional meaning exists.

## Requiredness and nullability in prose

Descriptions do not repair an incorrect schema. Use prose only to clarify the
business meaning after the source contract distinguishes:

- omitted: the caller did not supply the field
- explicit null: the caller supplied "no value"
- value: the caller supplied a concrete value

Never tell a model that null means omitted unless the adapter also declares the
null-sentinel decoder and the source field is non-nullable.

## Outputs

A good tool result gives the model enough information for the next step without
returning an unbounded dump.

- Return stable semantic IDs next to human-readable labels.
- Return units, time zones, and freshness timestamps where they affect meaning.
- Paginate or truncate large results and report that truncation explicitly.
- Offer a `concise` versus `detailed` mode only when the distinction is stable
  and useful.
- For MCP, use `outputSchema` and `structuredContent` when clients benefit from
  typed output; provide the required text representation for compatibility.
- Do not expose secrets, raw database records, internal stack traces, or fields
  the model does not need.

## Errors are part of the contract

Separate two classes:

1. **Protocol or schema errors**: malformed request envelope, unknown tool, or
   invalid wire schema. These are integration defects.
2. **Execution errors**: invalid business value, missing authorization, upstream
   failure, rate limit, or timeout. These can often guide model recovery.

A model-visible execution error should be structured and actionable:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "window_start must be earlier than window_end.",
    "retryable": true,
    "retry_hint": "Swap the timestamps or ask the user for a corrected range."
  }
}
```

Use a small stable code set, for example:

- `VALIDATION_ERROR`
- `NOT_FOUND`
- `AUTH_SCOPE_DENIED`
- `RATE_LIMITED`
- `CONFLICT`
- `UPSTREAM_TIMEOUT`
- `UPSTREAM_UNAVAILABLE`

`retryable` means an automated retry can be safe after following the hint. It
must not be set merely because the model could try again. Mutating tools also
need idempotency protection.

## Anti-patterns

- **God tool**: `do_database_op(action, table, data)` spans unrelated tasks and
  lets the model combine the right operation with the wrong resource.
- **Endpoint explosion**: one tool per backend endpoint makes selection harder.
  Split and consolidate by natural user workflow, not by service internals.
- **Description as docstring**: "GET /api/v2/weather. Returns JSON." does not
  teach selection or argument filling.
- **Everything is a string**: `"count": "five"` and `"active": "yes"` should
  use integer and boolean types.
- **Silent failure**: returning `null` or `{}` on error invites fabrication.
- **Required-by-wire leakage**: changing a semantically optional source field to
  required only because one provider's strict mode requires it.
- **Description-only validation**: stating "must be positive" without retaining
  the constraint in the source validator.
- **Raw traceback**: reveals internals and gives the model no stable recovery
  instruction.

## Schema evolution

- Additive compatible change: add an optional source field.
- New required source field: version the contract or provide an application
  migration; do not silently break existing callers.
- Meaning change: create a new tool name or explicit version.
- Adapter change: re-run every target conformance case and compare diagnostics.
- Description change: re-run tool-selection and argument-filling evaluations.
- Model, API, or SDK change: invalidate prior compatibility evidence until the
  target profile is tested again.

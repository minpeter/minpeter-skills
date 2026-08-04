# Authoring Guide — Names, Descriptions, and Errors

How to write the *content* of a tool schema: what goes in `name`,
`description`, and parameter descriptions, in what style, and how long.
Distinct from the structural rules in `SKILL.md` — this is prompt
engineering for tool selection and argument filling.

Sources: Anthropic "Writing effective tools for agents" + Claude tool-use
docs · OpenAI function-calling guide · Together AI function-calling best
practices · Schema Design Cheatsheet (awesome-agentic-ai-zh) · Adaline Labs
· JSONSchemaBench/IFEval-FC where marked.

## Names

- **Self-describing `verb_noun`**: `get_user_profile(user_id)`, never
  `fetch(id)` or `process_data(input)`. The name alone should signal query
  vs mutation vs action.
- Charset/length: `^[a-zA-Z0-9_-]{1,64}$` (the portable intersection).
  Some providers additionally advise against dashes/periods — underscores
  are the safest denominator.
- Namespace by service/resource: `github_list_prs`, `asana_projects_search`.
  Prefix vs suffix ordering has non-trivial, model-dependent measured
  effects — pick by eval, keep it consistent.

## Tool description = a short spec

The description is the only context the model has for *when* to call and
*how* to fill arguments. Provider guidance calls extremely detailed
descriptions "by far the most important factor in tool performance."

Cover, in order:

1. **What it does** — one line, present tense: "Get current weather for a
   specified city."
2. **When to use** — trigger situations/phrases: "Use this when the user
   asks about current weather, temperature, or 'is it raining'."
3. **When NOT to use + the alternative**: "Do NOT use for forecasts (use
   `get_forecast` instead) or historical data." This disambiguation line is
   the highest-value sentence in the whole schema when tools overlap.
4. **What it returns** — units and shape: "Returns temperature in C/F,
   humidity, and conditions." The model uses the result for the next step.
5. **Caveats/limits** — what it does NOT do, edge cases: "Does not return
   after-hours quotes."

**Length**: 3–4 sentences for simple tools, more for
complex ones. One major provider caps descriptions at 1,024 chars. Every sentence
costs input tokens on every request — spend them on selection boundaries,
not on restating the name.

**Style / grammar**:
- Write **for the model, not for humans**. No implementation details
  ("Uses OpenWeather API v2.5"), no docstring-speak ("Returns JSON",
  "See API docs"). The model never reads your code.
- Concrete, declarative sentences. Inline micro-examples help measurably:
  `"Search products by query. Examples: 'laptop under $1000', 'red shoes
  size 10'."` (Caveat: reasoning models can perform worse with examples —
  prefer folding them into prose, not rigid templates.)
- **Intern test**: if a new engineer given only the
  schema could call the tool correctly, the description is done. Every
  question they would ask is a sentence to add.
- **Field mirroring**: in system prompts and instructions, refer
  to parameters by their exact schema names — it anchors argument filling.
- Descriptions are eval-able artifacts: wording changes — even punctuation —
  change behavior. Re-run your tool evals after every edit.

## Parameter descriptions

One line each: **meaning + format/units + example**.

```
"symbol":  "The stock ticker symbol, e.g. AAPL for Apple Inc."
"window_start": "ISO 8601 start of search window, e.g. 2026-08-04T09:00:00Z"
"organizer_tz": "IANA time zone of the organizer, e.g. America/Los_Angeles"
"unit":    "Temperature unit."   (enum already constrains the values)
```

- State defaults **in prose**, not the `default` keyword (banned from the
  canonical schema by H7; Gemini ignores it anyway): "Max lines to return
  (default 500, max 2000)."
- Keep `required` minimal and honest: models hallucinate values for
  required params the user never mentioned. If a param has a
  sensible default, make it optional and prose the default.
- Skip descriptions only on truly self-evident fields (even spec examples
  leave trivial fields bare) — but when in doubt, write the line.

## Errors are part of the schema contract

The model reads error output to decide retry / pivot / give up. Design it:

- Never fail silently: success → `{success: true, data: …}`, failure →
  `{success: false, error: …, retry_hint: …}`.
- Use a small canonical error-code set with a retry flag:
  `VALIDATION_ERROR` (retryable=false, ask for corrected value),
  `RATE_LIMITED` (retryable=true, backoff), `AUTH_SCOPE_DENIED`,
  `UPSTREAM_TIMEOUT` (retryable=true, narrow the request).
- The `hint`/`retry_hint` text tells the model the concrete fix:
  "Check spelling, or try a major city nearby" — not "Error 500".

## Anti-patterns

- **God tool**: one tool per *system* (`do_database_op(op, table, data)`)
  mixes wrong op with right table. But do not explode one tool per API
  endpoint either — consolidate one **natural workflow** into one tool with
  an `action` enum. The unit of splitting is the task, not the
  backend surface.
- **Description as docstring**: "GET /api/v2/weather. Returns JSON."
  teaches nothing about when to call.
- **Everything is a string**: `"count: "five"`, `"active: "yes"` — use
  integer/boolean/array types (H2).
- **Silent failure**: returning `null`/`{}` on error makes the model
  fabricate from empty data.

## Schema evolution

- Additive change → new **optional** param, never a new required one.
- Meaning change → new tool name (`get_weather_v2`), deprecate then remove.
- Any description edit → re-run the tool evals before shipping.

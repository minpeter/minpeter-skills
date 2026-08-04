# Deep Dive — Failure Modes and Research-Backed Insights

Beyond-structure knowledge for production tool design. Each item is labeled:
**[verified]** = cross-checked against primary docs in this repo's research ·
**[paper]** = a single paper's claim, not independently replicated ·
**[practice]** = reasoning/convention, no hard measurement.

## 1. Schema–model misalignment (the deepest failure mode) **[paper]**

PA-Tool (arXiv 2510.07248): small models (4B–14B) most often
fail by *inventing tool names* — they drift toward the naming conventions
seen in pretraining. PA-Tool generates candidate names and picks the one the
model finds most "familiar" (peakedness over edit-distance clusters),
reporting −80% misalignment errors and up to +17pp accuracy. Practical
takeaway: **before fine-tuning a small model for tools, try renaming your
tools to the most conventional, pretraining-flavored names** — and eval name
variants, not just description variants.

## 2. Strict mode: real constraints and real costs **[verified]**

- OpenAI/DeepSeek strict: every object closed, every property required,
  optional → null union; `allOf`/conditionals rejected; fine-tuned models
  lose several constraints (pattern/format/length).
- Anthropic strict: ≤ 20 strict tools, ≤ 24 optional params, ≤ 16
  union-typed params per request; complex grammars 400.
- Compilation is not free: first request with a new schema pays extra
  latency (OpenAI documents this; repeats are cached, Anthropic caches
  grammars 24h). JSONSchemaBench measured pathological compile blowups
  (enum+array constraint combos took one engine from ~40s to ~10m).
- **Consequence**: keep schemas simple enough to compile; put business-rule
  validation in the handler, not the grammar.

## 3. Tool-count pressure and lazy loading **[verified]**

- Soft cap ~20 active tools (OpenAI, Gemini guidance); accuracy degrades as
  the catalog grows (OpenAI cookbook, measured). Precise collapse curves
  circulating online (50/200/740-tool numbers) are **unverified** — treat as
  direction, not data.
- Mitigations with primary evidence: OpenAI **tool search** (defer
  namespaces/MCP servers, ≤10 functions per namespace), Anthropic **Tool
  Search Tool**, Kimi dynamic loading. Pattern: show names first, load full
  schemas on demand.
- **[paper]** TSCG (arXiv 2605.04107) compiles JSON schemas into a
  token-efficient textual grammar, reporting 61–75% token savings and a
  small-model recovery (Phi-4 14B: 0% → 84.4% on 20 tools). **Tension to
  note**: BFCL V4 measured JSON function documentation as the best
  representation for most frontier models — the TSCG result is a
  small-model/context-budget claim, not a general "don't use JSON" rule.

## 4. Description engineering, deeper **[verified + practice]**

- Anthropic's engineering blog reports description-only rewrites fixing
  concrete failures (a model appending the wrong year to queries) and
  "dramatic improvements" on held-out evals. The specific 40%/60% numbers
  circulating online are **unverified**.
- Highest-leverage line: the *when-not-to-use* boundary against adjacent
  tools (selection accuracy), then per-parameter meaning/format.
- Include known failure modes in the description ("never include the
  |content suffix") — telling the model the observed mistake works better
  than abstract rules.

## 5. Failure taxonomy **[practice]**

Classify tool-call failures before fixing them — each has a different fix:

1. **Schema misalignment** — model invents names/fields → rename toward
   convention, strict mode.
2. **Functional confusion** — right arguments, wrong tool → when-not-to-use
   boundaries, namespacing, consolidation.
3. **Argument hallucination** — invalid values → enums, strict decoding,
   formats, client-side validation.
4. **Recovery failure** — model stuck after an error → structured errors
   with retry hints (see `references/authoring.md`).

## 6. Production framing worth adopting **[practice]**

- **Tool calls are RPCs**: timeouts mean uncertainty — make mutations
  idempotent and safe to retry.
- **Eval consistency, not just pass@1**: a tool that works 80% of the time
  is a production incident generator; measure variance across runs
  (pass^k-style) before trusting a schema change.
- **The adapter layer is not optional** at scale: this skill's canonical +
  adapter architecture is the same conclusion reached independently by
  LiteLLM/Vercel/MCP normalizers.

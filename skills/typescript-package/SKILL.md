---
name: typescript-package
description: >-
  minpeter's house style for building and reviewing TypeScript packages and
  monorepos. The locked stack: pnpm (latest) + Turborepo + Changesets + Biome via
  the ultracite preset with ZERO ignores/overrides/suppressions + tsdown for
  builds + Vitest, with `tsc --noEmit` for type-checking, the namespaced
  source-condition for zero-build internal deps, and MANDATORY npm OIDC trusted
  publishing (no NPM_TOKEN). Use this when scaffolding a new TS library or
  monorepo, adding a workspace package, choosing build/lint/publish tooling, or
  reviewing an existing package.json / tsconfig / biome.jsonc / turbo.json / CI
  for consistency with this style. Copy-paste config lives in
  references/templates.md; the source-condition deep-dive + external verdict in
  references/source-condition.md; the OIDC publishing guide in
  references/publishing-oidc.md.
license: MIT
metadata:
  author: minpeter
  version: "1.0.0"
---

# TypeScript package style (minpeter)

An opinionated, **locked** toolchain for TypeScript libraries and monorepos.
"Locked" means: don't re-litigate these per project — they are the defaults.
Every choice below was distilled from minpeter's own repos and then checked
against 2026 ecosystem best practice (see the verdicts in `references/`).

## The locked stack

| Concern        | Choice (no substitutes)                                   |
|----------------|----------------------------------------------------------|
| Package manager| **pnpm**, latest (`11.7.0`), pinned via `packageManager` |
| Monorepo       | pnpm workspaces + **Turborepo** (`turbo` 2.9.x)          |
| Lint + format  | **Biome** (`2.5.0`) via **`ultracite`** — **zero ignores** (§3) |
| Type-check     | **`tsc --noEmit`** only — never emit JS with tsc          |
| Build          | **tsdown** (`0.22.x`) — **not tsup**, not raw tsc         |
| Internal deps  | **namespaced source-condition** `@minpeter/source` (§5)  |
| Tests          | **Vitest** (`4.1.x`) + v8 coverage                        |
| Versioning     | **Changesets**                                            |
| Publish        | **npm OIDC trusted publishing**, mandatory (§6)           |
| TS version     | **`6.0.3`** + `ignoreDeprecations: "6.0"`                 |
| Filenames      | **kebab-case** (enforced by ultracite)                    |

> If you find ESLint, Prettier, tsup, npm/yarn lockfiles, a long-lived
> `NPM_TOKEN`, or `// biome-ignore` comments → that's **not** this style. Flag it.

## 1. Decision: single package vs monorepo

```
One publishable thing  → SINGLE-PACKAGE repo (src/ at root). No turbo, no source-condition.
Several related pkgs    → MONOREPO (packages/*, turbo, source-condition for internal deps).
```

## 2. Scaffold checklist

1. `pnpm-workspace.yaml` with `packages: ["packages/*"]` (omit for single pkg);
   put pnpm-11 settings (`onlyBuiltDependencies`, `verifyDepsBeforeRun`) here, not `.npmrc`.
2. Pin the toolchain: `"packageManager": "pnpm@11.7.0"`, `engines.node: ">=22"`.
3. `tsconfig.base.json` (shared strict options) + root `tsconfig.json`
   (`noEmit`, `customConditions`) + `tsconfig.build.json` (NO custom condition).
4. `biome.jsonc` = **just** `extends: ["ultracite/biome/core", "ultracite/biome/vitest"]`. Nothing else (§3).
5. **tsdown** per package; `tsc --noEmit` for typecheck.
6. Per-package `package.json`: `type: module`, `sideEffects: false`,
   `exports` with the source-condition (§5), `publishConfig.provenance: true`.
7. `.changeset/config.json`, `turbo.json`, `vitest.config.ts`.
8. CI (`ci.yml`: lint → typecheck → test → build → **attw**) and
   `release.yml` (Changesets + **OIDC**, §6).

→ **All file contents are in [`references/templates.md`](references/templates.md).** Copy them verbatim.

## 3. Biome via ultracite — ZERO ignores (hard rule)

The whole `biome.jsonc` is two lines of intent:

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json",
  "extends": ["ultracite/biome/core", "ultracite/biome/vitest"]
}
```

**No `files.includes` ignores. No `overrides`. No rule `"off"`. No
`// biome-ignore` / `// biome-ignore-all` comments.** ultracite is already very
strict and already relaxes the right things itself (tests, `*.config.ts`,
`*.d.ts`, generated/build dirs, `noConsole` off). Adding exceptions is how a
style guide rots — the rule here is **fix the code, not the config**.

Practical consequences (this is *why* zero-ignore works cleanly):
- **No barrel files.** ultracite's `noBarrelFile` fires on re-export-only files.
  Instead of overriding it (what the older repos did), **expose subpath exports
  that point at real modules** (§5). This is also better for tree-shaking — the
  rule is steering you correctly.
- **kebab-case filenames**, **`interface` over `type`**, **no `enum`** (const
  objects / unions), **no `any`**, **no `!`**, **`node:` import protocol**,
  **type-only `import type`/`export type`** — all enforced; just write to them.
- Worktree/scratch dirs (`.omx`, `.omo`) → put them in `.gitignore`; ultracite
  sets `vcs.useIgnoreFile: true`, so Biome skips them **without** a Biome ignore.

See [`references/templates.md`](references/templates.md) for the full list of what ultracite enforces.

## 4. Build with tsdown + `tsc --noEmit`

- **tsdown** (Rolldown/Oxc based — the modern successor to tsup) is the only
  build tool. `dts: true`, `sourcemap: true`, `unbundle: true` for
  file-per-module output (pairs well with subpath exports).
- **`tsc` never emits.** `"typecheck": "tsc --noEmit"`. The bundler owns output.
- Default to **ESM-only** (`"type": "module"`, exports use `import`). Ship CJS
  only if you actually have CJS consumers — and then nest `types` correctly per
  branch (`.d.ts` vs `.d.cts`); see the dual template.

## 5. Internal deps: the namespaced source-condition (monorepo only)

**Verdict: keep it.** It's the Colin McDonnell / TypeScript-5.7-endorsed way to get
zero-build "live types" across a monorepo, and unlike `publishConfig.exports` it's
package-manager-agnostic. But it has sharp edges — wire **all four** of these or it
silently resolves to stale `dist`:

```jsonc
// each publishable package's package.json — condition FIRST, then types, then import
"exports": {
  "./package.json": "./package.json",
  ".": {
    "@minpeter/source": "./src/index.ts",
    "types": "./dist/index.d.ts",
    "import": "./dist/index.js"
  }
}
```
1. **Root `tsconfig.json`**: `"customConditions": ["@minpeter/source"]` (editor + `tsc --noEmit` resolve to source).
2. **Build config** (`tsconfig.build.json`, used by tsdown): **must NOT** carry the condition, or your `.d.ts` resolves sibling deps to `.ts`.
3. **tsx**: `tsx --conditions @minpeter/source` (tsx does **not** read tsconfig — it'll silently miss otherwise).
4. **Vitest**: `resolve: { conditions: ["@minpeter/source"] }`.

**Guardrails (non-negotiable):**
- Namespace the condition (`@minpeter/source`, never bare `source`) so it can't collide.
- TypeScript does **not** error if the `src` file is missing — it silently falls
  back. So run **`attw --pack`** (`@arethetypeswrong/cli`) in CI on every
  publishable package to prove external consumers get correct `dist` types.

Full rationale, the contested history, every footgun, and citations:
**[`references/source-condition.md`](references/source-condition.md).** (Single-package repos: skip all of this.)

## 6. Publish: npm OIDC trusted publishing (mandatory)

**No `NPM_TOKEN`. Ever.** Releases authenticate via GitHub OIDC; provenance is
attached automatically.

- Release job needs `permissions: { id-token: write, contents: read }`,
  Node **≥ 22.14**, npm **≥ 11.5.1** (`npm i -g npm@latest` if older).
- `changeset publish` works under OIDC; do **not** set `NODE_AUTH_TOKEN` on the
  publish step (npm only uses OIDC when the auth token env is unset).
- `publishConfig: { "access": "public", "provenance": true }` per package.
- **One-time setup:** configure the package's *Trusted Publisher* on npmjs.com
  (org/user + repo + workflow filename). **Caveat:** OIDC can't publish a
  package's *first ever* version — do the initial publish with a token, then
  switch to OIDC.

Step-by-step + the release workflow: **[`references/publishing-oidc.md`](references/publishing-oidc.md).**

## 7. Review checklist (use when auditing an existing repo)

- [ ] pnpm pinned latest; `pnpm-workspace.yaml` holds pnpm settings
- [ ] `biome.jsonc` extends ultracite and has **zero** overrides/ignores/`biome-ignore`
- [ ] No barrel files; public API via subpath exports
- [ ] Build is **tsdown**; `tsc` is `--noEmit` only
- [ ] (monorepo) source-condition wired in all 4 places; build tsconfig has none; `attw` in CI
- [ ] `exports` order: custom condition → `types` → `import`/`require` (types nested per branch if dual)
- [ ] `type: module`, `sideEffects: false`, `files: ["dist"]`, `publishConfig.provenance: true`
- [ ] Release uses **OIDC** (`id-token: write`), no `NPM_TOKEN`, Node ≥22.14 / npm ≥11.5.1
- [ ] kebab-case filenames; `interface` over `type`; no `enum`/`any`/`!`; `node:` imports
- [ ] Vitest + v8 coverage; Changesets configured

## NOT this style (flag in review)

ESLint / Prettier · tsup or raw-`tsc` library builds · npm/yarn/bun lockfiles ·
`NPM_TOKEN` secret for publishing · `// biome-ignore` or biome `overrides` ·
barrel `index.ts` re-export files · default-export-heavy modules ·
PascalCase/snake_case filenames · `enum` · `any` · non-null `!`.

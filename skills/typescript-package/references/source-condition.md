# The source-condition pattern — verdict, how-to, footguns

> Scope: **monorepos only.** A single-package repo has no internal deps, so skip
> this entirely and use plain `exports` (`types` → `import`).

## What it is

Give every workspace package a **custom export condition** (namespaced, e.g.
`@minpeter/source`) listed **first** in `exports`, pointing at `./src/index.ts`.
Tools that activate the condition resolve internal imports to **TypeScript
source** — no build step. Tools that don't (i.e. published consumers) fall
through to `types` → `dist`.

```jsonc
".": {
  "@minpeter/source": "./src/index.ts",   // dev / typecheck / test → live source
  "types": "./dist/index.d.ts",            // external consumers → built types
  "import": "./dist/index.js"              // external consumers → built JS
}
```

## External verdict: **qualified-yes — keep it**

This is a *legitimate, current best practice*, but **not** the single dominant
convention. The honest picture:

- ✅ It's the approach **Colin McDonnell explicitly recommends** as solution #5
  ("custom export conditions") in the canonical essay *Live types in a TypeScript
  monorepo* — chosen precisely because it's **package-manager-agnostic** and keeps
  the runtime + TS config in sync.
- ✅ **TypeScript 5.7's release notes endorse the pattern**, citing that essay and
  `tshy`, and recommend a **namespaced** condition (their example:
  `@my-package/development`).
- ⚠️ **Turborepo** — arguably the most common orchestrator — does **not** use a
  custom condition. Its *Just-in-Time* packages point plain subpath exports at
  `./src/*` (the app's bundler compiles), and its getting-started tutorial uses
  *Compiled* packages with standard `types`/`default` conditions. So the simpler
  baseline in the broader ecosystem is **JIT-without-a-custom-condition** or
  compiled packages. **Nx** instead leans on TS project references.
- The custom condition wins specifically for minpeter's constraints: **zero-build
  internal deps AND correct publishing, without locking into `pnpm publish`.**

### Why not the `publishConfig.exports` alternative?

Because it's **pnpm-only**. `npm publish` (and common publish Actions) **ignore**
`publishConfig.exports` and would ship a package whose `exports` still point at
`./src` — unrunnable for consumers. Colin McDonnell originally recommended
`publishConfig`, then **publicly reversed** it after finding npm ignores the
override. Only choose `publishConfig.exports` if you commit to pnpm-only publishing.

## The footguns (all real — manage them deliberately)

1. **Nothing inherits `customConditions` from tsconfig.** You must wire each tool
   separately:
   - tsx: `tsx --conditions @minpeter/source` (tsx issue #574 — it does *not* read
     tsconfig). Forget it → silently resolves to `dist` or errors.
   - Vitest/Vite: `resolve: { conditions: ["@minpeter/source"] }`. Forget it →
     tests run against stale `dist`.
   - Some bundlers historically ignore custom conditions (Turbopack: next.js
     #78912) → they silently fall through to `default`/`dist`, masking that your
     live-types setup isn't active.
2. **TypeScript does NOT error when the `src` file is missing — it silently falls
   back.** There is no `strictCustomConditions` (TS #61363 was closed *not
   planned*). A renamed/deleted source file fails **silently at type-check** and
   only surfaces at runtime/test. This is the genuine unresolved 2026 risk —
   treat it as the headline caveat.
3. **The build must not see the condition.** If tsdown's `.d.ts` generation
   inherits `customConditions`, declarations resolve sibling deps to `.ts` →
   broken/incomplete `dist`. Keep `tsconfig.build.json` free of the condition (the
   template does this).
4. **Condition leakage.** The `@minpeter/source` key ships in the published
   `package.json`. Harmless *because it's namespaced* (no external consumer sets
   it) — but never use a bare `source` (collision risk). Real-world rollout
   (LedgerHQ #15316) used a namespaced `@ledgerhq/source`, had to set
   `customConditions: []` in every build tsconfig, and inject the key into ~130
   package.jsons.
5. **Editor/ESLint resolution** outside VS Code can miss the condition and show
   false "unresolved import" / wrong-type errors unless the resolver reads
   tsconfig `customConditions`.

## The guardrail: `attw --pack` in CI

Run **`@arethetypeswrong/cli`** (`attw --pack .`) on every publishable package in
CI. Note the *correct* reason (per the adversarial review): attw inspects the
packed tarball **as an external consumer** — it never sets `@minpeter/source`, so
it doesn't literally "detect the leaked condition." What it *does* prove is that
the **`dist` resolution external consumers actually get** is correct (types
resolve, ESM/CJS match, no masquerading). That indirectly catches a source leak
(shipping `.ts` with no `dist` fails resolution) and catches the dual-publish
mistakes that matter more in practice. Keep it; just don't over-index on the
specific `FallbackCondition` error name.

## Exports ordering (attw-safe)

Order matters. Use: **custom condition → `types` → `import`/`require`**. For dual
ESM/CJS, **nest `types` inside each branch** with the right extension (`.d.ts` vs
`.d.cts`); a single shared `types` across both branches is a classic attw failure.
Do **not** copy the essay's literal JSON that places `types` last.

## If you ever want to drop the moving parts

If *all* internal consumers are bundler-based apps (not published), the Turborepo
**Just-in-Time** approach (plain `./src` exports, no custom condition, the app's
bundler compiles) is simpler. But it loses the clean external/`dist` split that
publishing needs — so for **publishable** packages, the namespaced custom
condition remains the better fit.

## Sources

- Colin McDonnell — *Live types in a TypeScript monorepo*: https://colinhacks.com/essays/live-types-typescript-monorepo
- McDonnell reversal tweet (npm ignores `publishConfig.exports`): https://x.com/colinhacks/status/1798136783538176048
- TypeScript 5.7 release notes (endorses namespaced condition): https://devblogs.microsoft.com/typescript/announcing-typescript-5-7/
- TSConfig `customConditions`: https://www.typescriptlang.org/tsconfig/customConditions.html
- Turborepo — Internal Packages (JIT vs Compiled vs Publishable): https://turborepo.dev/docs/core-concepts/internal-packages
- Turborepo — Creating an Internal Package (compiled default): https://turborepo.dev/docs/crafting-your-repository/creating-an-internal-package
- tsx #574 (no tsconfig customConditions support): https://github.com/privatenumber/tsx/issues/574
- TypeScript #61363 (`strictCustomConditions`, closed not-planned): https://github.com/microsoft/TypeScript/issues/61363
- Turbopack custom condition support (next.js #78912): https://github.com/vercel/next.js/discussions/78912
- LedgerHQ rollout (namespaced source condition, real-world): https://github.com/LedgerHQ/ledger-live/pull/15316
- arethetypeswrong — FallbackCondition: https://github.com/arethetypeswrong/arethetypeswrong.github.io/blob/main/docs/problems/FallbackCondition.md
- Nx — managing TS packages (project references): https://nx.dev/blog/managing-ts-packages-in-monorepos

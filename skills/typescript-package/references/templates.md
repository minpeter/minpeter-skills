# Copy-paste templates

Resolve versions when you scaffold. Do **not** copy stale package versions from
this skill:

```bash
corepack enable
corepack use pnpm@latest

# Biome must be exact-pinned, but the exact value should be today's latest.
pnpm add -DwE @biomejs/biome@latest

# Let pnpm write current ranges for the rest of the toolchain.
pnpm add -Dw @arethetypeswrong/cli@latest @changesets/cli@latest npm-run-all@latest tsdown@latest tsx@latest turbo@latest typescript@latest ultracite@latest vitest@latest
```

After that, keep the resolved `packageManager`, `devDependencies`, and lockfile
that pnpm wrote. Biome remains exact-pinned; the rest can use pnpm's default
range policy unless a project has a stricter release rule.

For GitHub Actions examples, resolve each action's current recommended major tag
before copying the workflow (`actions/checkout`, `actions/setup-node`,
`pnpm/action-setup`, `changesets/action`). Do not preserve old action majors from
this skill.

---

## pnpm-workspace.yaml

```yaml
# Modern pnpm reads settings here (not .npmrc / package.json#pnpm)
packages:
  - "packages/*"        # omit the whole block for a single-package repo

# esbuild (tsdown/vitest) has a postinstall build script; approve it so install exits 0
onlyBuiltDependencies:
  - esbuild
verifyDepsBeforeRun: false
```

---

## Root package.json (monorepo)

```jsonc
{
  "name": "@minpeter/<repo>-monorepo",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@<resolved-latest>",
  "engines": { "node": ">=<project-runtime>" },
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev",
    "typecheck": "turbo run typecheck",
    "test": "turbo run test",
    "check": "run-s check:static check:package",
    "check:static": "run-p check:lint check:typecheck check:test",
    "check:lint": "ultracite check",
    "check:typecheck": "pnpm typecheck",
    "check:test": "pnpm test",
    "check:package": "run-s build attw",
    "lint": "pnpm check:lint",
    "fix": "ultracite fix",
    "format": "pnpm fix",
    "attw": "turbo run attw",
    "changeset": "changeset",
    "version": "changeset version",
    "release": "run-s build release:publish",
    "release:publish": "changeset publish"
  },
  "devDependencies": {
    "@arethetypeswrong/cli": "^<resolved-latest>",
    "@biomejs/biome": "<resolved-latest-exact>",
    "@changesets/cli": "^<resolved-latest>",
    "npm-run-all": "^<resolved-latest>",
    "tsdown": "^<resolved-latest>",
    "tsx": "^<resolved-latest>",
    "turbo": "^<resolved-latest>",
    "typescript": "^<resolved-latest>",
    "ultracite": "^<resolved-latest>",
    "vitest": "^<resolved-latest>"
  }
}
```

### Script composition rules

Keep leaf commands small and give composition a name. This is the pattern to
copy from recent minpeter repos:

- `run-p` for independent work:
  - `check:static`: lint, typecheck, and test can run together.
  - `dev`: app stacks can run `dev:worker`, `dev:relay`, `dev:tunnel`, etc. at
    the same time.
- `run-s` for ordered work:
  - `check`: run static checks first, then package-output checks (`build` and
    `attw`).
  - `release` or app deploy flows: secrets/config first, deploy second, webhook
    registration last.
- Prefer `check:*` and `fix:*` names over long one-off shell chains. If a command
  gets long enough to need environment branching, move it into `scripts/*.mjs`
  and keep `package.json` as the command index.

Examples for app/worker repos that need multiple dev or deploy steps:

```jsonc
{
  "scripts": {
    "dev": "run-p dev:worker dev:relay",
    "dev:worker": "wrangler dev",
    "dev:relay": "tsx scripts/relay.ts",
    "ship": "run-s ship:secrets ship:worker ship:webhook",
    "ship:secrets": "wrangler secret bulk .dev.vars",
    "ship:worker": "wrangler deploy",
    "ship:webhook": "tsx scripts/webhook.ts"
  }
}
```

---

## tsconfig.base.json — shared compiler options (no custom condition here)

```jsonc
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "types": ["node"],

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,

    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "moduleDetection": "force",

    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,

    // Biome owns unused-symbol reporting — don't double-report from tsc
    "noUnusedLocals": false,
    "noUnusedParameters": false
  }
}
```

## Root tsconfig.json — editor + `tsc --noEmit`, activates the source condition

```jsonc
{
  "extends": "./tsconfig.base.json",
  "compilerOptions": {
    "noEmit": true,
    "customConditions": ["@minpeter/source"]
  },
  "include": ["packages/*/src/**/*"],
  "exclude": ["node_modules", "**/dist"]
}
```

## tsconfig.build.json — used by tsdown for .d.ts; MUST NOT carry the condition

```jsonc
{
  // No customConditions here, so declaration emit resolves sibling deps to dist,
  // not to their .ts source. This is the #1 source-condition footgun.
  "extends": "./tsconfig.base.json",
  "compilerOptions": { "noEmit": false }
}
```

> Single-package repo: drop `tsconfig.build.json` and the `customConditions` line —
> you don't need the source condition without internal deps.

---

## biome.jsonc — the entire file (zero ignores, zero overrides)

```jsonc
{
  "$schema": "https://biomejs.dev/schemas/<installed-biome-version>/schema.json",
  "extends": ["ultracite/biome/core", "ultracite/biome/vitest"]
}
```

### What `ultracite/biome/core` enforces (so you can predict failures)

- **Format:** 2-space indent, **lineWidth 80**, LF, **double quotes**,
  **semicolons always**, `trailingCommas: "es5"`, arrow parens always.
- **Filenames: kebab-case**, ASCII only (`useFilenamingConvention`).
- **`interface` over `type`** (`useConsistentTypeDefinitions`).
- **No `enum`** (`noEnum`), **no `namespace`**, **no namespace imports**.
- **No `any`** (`noExplicitAny`), **no `!`** (`noNonNullAssertion`), **no `@ts-ignore`**.
- **Type-only imports/exports** (`useImportType`/`useExportType`); imports auto-organized.
- **`node:` protocol required**; **no barrel files** (`noBarrelFile`) → use subpath exports.
- Cognitive complexity ≤ 20. `noConsole` is **off** (console allowed).
- Already relaxes: test files, `*.config.ts` (default exports), `*.d.ts`, scripts/bin,
  and build/generated dirs — which is why you need **no** overrides of your own.

---

## Per-package package.json — ESM-only library with source condition

```jsonc
{
  "name": "@minpeter/runtime",
  "version": "<initial-version>",
  "type": "module",
  "sideEffects": false,
  "license": "MIT",
  "author": "minpeter <minpeter@vooy.com>",
  "repository": { "type": "git", "url": "git+https://github.com/minpeter/<repo>.git" },
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "files": ["dist", "README.md"],
  "exports": {
    "./package.json": "./package.json",
    ".": {
      "@minpeter/source": "./src/index.ts",
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js"
    },
    // Prefer subpath exports over a barrel index (keeps noBarrelFile happy):
    "./session-store/memory": {
      "@minpeter/source": "./src/session/store/memory.ts",
      "types": "./dist/session/store/memory.d.ts",
      "import": "./dist/session/store/memory.js"
    }
  },
  "scripts": {
    "build": "tsdown",
    "dev": "tsdown --watch",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "test": "vitest run",
    "attw": "attw --pack ."
  },
  "publishConfig": { "access": "public", "provenance": true }
}
```

> **No per-package `lint` script** — Biome lints the whole repo in one root pass.
>
> **Where `--conditions` actually matters:** a *library's* `dev` is just
> `tsdown --watch` (rebuild on change). The source condition pays off in an **app
> or server** that consumes workspace libraries — its dev script resolves those
> libs to live `.ts` source with no build step:
> `tsx --conditions=@minpeter/source watch src/main.ts`.

### Dual ESM + CJS variant (only if you have CJS consumers)

Nest `types` **inside each branch** with the right extension — a single shared
`types` across `import`/`require` is a classic `attw` failure.

```jsonc
"exports": {
  "./package.json": "./package.json",
  ".": {
    "@minpeter/source": "./src/index.ts",
    "import": { "types": "./dist/index.d.ts",  "default": "./dist/index.js" },
    "require": { "types": "./dist/index.d.cts", "default": "./dist/index.cjs" }
  }
}
```

> Dual builds need `format: ["esm", "cjs"]` in tsdown and a real `.d.cts` emitted
> for the `require` branch. tsdown's separate-`.d.cts` emission isn't guaranteed by
> a flag alone — **`attw --pack` is what proves it's correct**. If in doubt, stay ESM-only.

### Exports & the no-barrel rule (be consistent with zero-ignore)

The `.` root export above points at `src/index.ts`. If that file is a **pure
re-export barrel**, ultracite's `noBarrelFile` will (correctly) flag it — and the
zero-ignore rule means you **don't** silence it. Two clean options:

- **Preferred:** drop the root `.` barrel and expose **subpath exports** that point
  at real modules (`"./client"`, `"./server"`, …). Best for tree-shaking.
- If you keep a root `.`, make `src/index.ts` hold **actual API code**, not only
  `export … from`. A handful of re-exports in a tiny lib is usually fine; a
  growing barrel is the smell the rule exists to catch.

---

## tsdown.config.ts

```ts
import { defineConfig } from "tsdown";

export default defineConfig({
  entry: ["src/index.ts", "src/session/store/memory.ts"],
  unbundle: true,          // file-per-module output; pairs with subpath exports
  root: "src",
  dts: true,
  sourcemap: true,
  // tsdown emits .d.ts via the build tsconfig (no custom condition) — see tsconfig.build.json
  // add format: ["esm", "cjs"] ONLY for the dual variant above
});
```

---

## vitest.config.ts — must re-declare the source condition

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: { conditions: ["@minpeter/source"] }, // tests run against live source, not dist
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
    coverage: { provider: "v8", reporter: ["text", "lcov"], include: ["src/**/*.ts"] },
  },
});
```

---

## turbo.json

```jsonc
{
  "$schema": "https://turborepo.dev/schema.json",
  "globalDependencies": ["tsconfig.base.json"],
  "tasks": {
    // build needs upstream dist: the build tsconfig has NO source condition, so
    // .d.ts generation resolves sibling deps to their built dist.
    "build":     { "dependsOn": ["^build"], "outputs": ["dist/**"], "inputs": ["$TURBO_DEFAULT$", "!**/*.test.ts"] },
    // typecheck & test resolve internal deps to .ts SOURCE (the source condition),
    // so they must NOT depend on ^build. ^typecheck only orders errors topologically.
    "typecheck": { "dependsOn": ["^typecheck"] },
    "test":      { "cache": false },
    // attw inspects the packed dist, so it needs THIS package built first.
    "attw":      { "dependsOn": ["build"] },
    "dev":       { "cache": false, "persistent": true }
  }
}
```

> **No `lint` task.** Biome is a single fast binary — run it once over the whole
> repo at the root (`pnpm check:lint` → `ultracite check`), not per-package via turbo.
> Per-package `lint` scripts + a turbo `lint` task are an ESLint-era pattern; with
> Biome they're redundant and slower.

---

## .changeset/config.json

```json
{
  "$schema": "https://unpkg.com/@changesets/config@<installed-changesets-version>/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [],
  "linked": [],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}
```

---

## .github/workflows/ci.yml

```yaml
name: CI
on:
  pull_request: { branches: [main] }
  push: { branches: [main] }
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<current-major>
      - uses: pnpm/action-setup@<current-major>
      - uses: actions/setup-node@<current-major>
        with:
          node-version: current
          check-latest: true
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm check       # lint + typecheck + test, then build + attw
```

The release workflow (`release.yml`) is in
[`publishing-oidc.md`](publishing-oidc.md) — it's the security-critical one.

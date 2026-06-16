# Publishing: npm OIDC trusted publishing

**Mandatory. No `NPM_TOKEN` anywhere.** Releases authenticate via GitHub OIDC and
npm attaches provenance automatically.

## Requirements (verified 2026-06)

| Thing            | Value                                                          |
|------------------|---------------------------------------------------------------|
| Node (release)   | **≥ 22.14.0** (use 24)                                        |
| npm CLI          | **≥ 11.5.1** (`npm install -g npm@latest` if older)           |
| GH permissions   | `id-token: write` (+ `contents: read`; `write` only if pushing tags/PRs) |
| `NPM_TOKEN`      | **not needed** — and must be **absent** on the publish step   |
| Provenance       | automatic on trusted publish — **don't** pass `--provenance`  |

## First release (bootstrap a brand-new package)

OIDC **cannot create a package's first-ever version** (npm/cli #8544) — the trusted
publisher can only be configured on a package that already exists. So the very first
release is a one-time local publish; everything after is CI/OIDC.

```bash
# 1. authenticate locally (or use a granular automation token)
npm login

# 2. build the package
pnpm --filter <pkg> build

# 3. first publish from your machine. Scoped packages MUST pass --access public.
#    This first version will NOT have provenance (provenance needs CI + OIDC).
cd packages/<pkg> && npm publish --access public
```

Now the package exists on npm → do the **trusted-publisher setup** below **once** →
from then on, all releases go through CI with OIDC + provenance and **no token**.
(npm has discussed allowing initial OIDC publishes; re-check for net-new packages,
but as of 2026 the token-first bootstrap is still required.)

## Trusted-publisher setup on npmjs.com (one-time, per package)

1. npmjs.com → the package page → **Settings** (admin/owner required for scoped/org
   packages).
2. **Trusted Publisher** section → **Connect** → choose **GitHub Actions**.
3. Fill: **Organization or user** = GitHub owner (e.g. `minpeter`); **Repository** =
   repo name only (e.g. `ai-router`); **Workflow filename** = file name only incl.
   extension, e.g. `release.yml` (it's assumed to be under `.github/workflows/`);
   **Environment** = only if your job sets `environment:` — must match exactly.
4. **Allowed actions** (shown for configs created after 2026-05-20): select at least
   `npm publish`. Save.
5. Verify after the first OIDC run: the version page shows a *Published via trusted
   publisher* / provenance badge linking the GitHub Actions run.

## .github/workflows/release.yml

```yaml
name: Release
on:
  push: { branches: [main] }
concurrency: ${{ github.workflow }}-${{ github.ref }}
permissions:
  contents: write          # changesets opens the version PR / pushes tags
  pull-requests: write
  id-token: write          # OIDC token for npm trusted publishing — REQUIRED
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: pnpm/action-setup@v6
      - uses: actions/setup-node@v6
        with:
          node-version: 24                 # OIDC needs Node > 22
          cache: pnpm
          registry-url: https://registry.npmjs.org
      - run: npm install -g npm@latest      # trusted publishing needs npm >= 11.5.1
      - run: pnpm install --frozen-lockfile
      - uses: changesets/action@v1
        with:
          version: pnpm run version         # changeset version
          publish: pnpm run release         # turbo run build && changeset publish
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # NO NPM_TOKEN / NODE_AUTH_TOKEN — npm only uses OIDC when the auth env is unset
```

## Gotchas

- **Do not** set `NODE_AUTH_TOKEN` / `NPM_TOKEN` on the publish step — npm falls
  back to token auth if it's present and OIDC won't engage. (A read-only token for
  an earlier private-dep `pnpm install` is fine, just not on publish.)
- `changeset publish` calls `npm publish` under the hood, so OIDC + provenance flow
  through automatically.
- If the bundled npm is older than 11.5.1 (older Node, or pnpm-pinned), the
  `npm install -g npm@latest` line is required.
- Per-package `publishConfig: { "access": "public", "provenance": true }`.

## Sources

- npm Docs — Trusted publishing: https://docs.npmjs.com/trusted-publishers/
- GitHub Changelog — npm trusted publishing GA: https://github.blog/changelog/2025-07-31-npm-trusted-publishing-with-oidc-is-generally-available/
- npm/cli #8544 — initial version can't use OIDC: https://github.com/npm/cli/issues/8544
- Phil Nash — npm trusted publishing gotchas (Jan 2026): https://philna.sh/blog/2026/01/28/trusted-publishing-npm/

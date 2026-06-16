# minpeter-skills

minpeter's collection of reusable [Agent Skills](https://agentskills.io) — the open
`SKILL.md` format (originated by Anthropic, adopted by Vercel's `npx skills`
ecosystem and 20+ coding agents).

## Install

Uses the [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
# add the whole collection (interactive)
npx skills add minpeter/minpeter-skills

# list what's inside first
npx skills add minpeter/minpeter-skills --list

# add one skill, non-interactively, into a specific agent
npx skills add minpeter/minpeter-skills --skill typescript-package -a claude-code -y

# install globally (all projects) instead of into ./<agent>/skills
npx skills add -g minpeter/minpeter-skills
```

You can also drop a skill folder straight into `.claude/skills/` (Claude Code),
`.codex/skills/`, `.cursor/`, etc. — the format is portable across agents.

## Skills

| Skill | What it does | When to use |
|-------|--------------|-------------|
| [`typescript-package`](skills/typescript-package/SKILL.md) | minpeter's house style for TS packages & monorepos: pnpm (latest) + Turborepo + Changesets + Biome-via-ultracite (zero ignores) + tsdown + Vitest, `tsc --noEmit` typecheck, the namespaced source-condition for zero-build internal deps, and mandatory npm OIDC trusted publishing. | Scaffolding a new TS library/monorepo, adding a workspace package, or reviewing `package.json` / `tsconfig` / `biome` / `turbo` / CI for consistency. |

Each skill keeps `SKILL.md` short and links out to `references/` for the heavy
detail (copy-paste templates, deep-dives) — Vercel's recommended progressive-disclosure pattern.

## License

[MIT](LICENSE) © minpeter

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
| [`hermes-agent-consult`](skills/hermes-agent-consult/SKILL.md) | Consult the local `hermes` agent as the long-term-memory oracle before asking the user: `hermes -z "<query>"` for infra/history/decision context, `-t memory -z "Remember: …"` to teach back an infra change, and one-shot review of a diff or plan. Covers query construction, the exit-code-0 failure trap, and what never goes into a prompt. | A task needs context the repo doesn't contain, you changed infra worth remembering, or you want a second opinion from an agent with the operational history. |
| [`minpeter-skills-maintainer`](skills/minpeter-skills-maintainer/SKILL.md) | How to maintain this repo: work from a `/tmp/minpeter-skills-<name>` clone and open a PR, reinstall the skill locally after merge, scaffold with `npx skills init`, frontmatter + naming rules, progressive disclosure into `references/`, and keeping `SKILL.md` / `README.md` / `skills.sh.json` in sync. | Adding, editing, renaming, or removing a skill here, or fixing index/grouping drift. |
| [`tool-schema-design`](skills/tool-schema-design/SKILL.md) | Cross-provider rules for LLM tool/function-calling JSON Schemas: canonical schema + per-provider adapters, hard rules (root object, no oneOf/allOf, nested anyOf allowed, no $ref/default/constraints), strict-mode transforms, an authoring guide for names/descriptions/errors (what to write, style, length), and design practices beyond the schema — verified against the primary docs of 12+ providers. | Writing tool definitions, function-calling parameters, MCP tool inputSchema, or zod/Pydantic tool schemas; choosing anyOf vs oneOf; writing tool descriptions; making one schema portable across providers or strict modes. |

Each skill keeps `SKILL.md` short and links out to `references/` for the heavy
detail (copy-paste templates, deep-dives) — Vercel's recommended progressive-disclosure pattern.

## License

[MIT](LICENSE) © minpeter

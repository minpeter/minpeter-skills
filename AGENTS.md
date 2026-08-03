# Agent guidance for minpeter-skills

This repo is a collection of Agent Skills in the open `SKILL.md` format.

- Each skill lives at `skills/<kebab-name>/SKILL.md` (flat layout). The `SKILL.md`
  filename must be uppercase.
- Frontmatter requires `name` (lowercase-hyphen) and `description` (write the
  activation triggers into the description). Optional: `license`, `metadata`
  (`author`, `version`).
- Keep each `SKILL.md` under ~500 lines. Push templates, checklists, and
  deep-dives into that skill's `references/` directory and link to them
  (progressive disclosure).
- When editing a skill, keep `README.md` (the index table) and `skills.sh.json`
  (the `groupings[].skills` name list) in sync with the skill's frontmatter `name`.
- Scaffold new skills with `npx skills init` so the frontmatter is valid.
- Never edit this repo in place and never commit to `main`: clone into
  `/tmp/minpeter-skills-<skill-name>`, branch there, and open a PR.
- After a PR merges, reinstall locally so agents stop reading the stale copy:
  `npx skills add -g minpeter/minpeter-skills --skill <name> -a '*' -y` for a new
  skill, `npx skills update -g <name>` for an existing one.
- Full maintenance procedure (clone/PR workflow, post-merge install, sync checks,
  link/orphan checks, rename & remove runbooks, authoring guidance) lives in the
  [`minpeter-skills-maintainer`](skills/minpeter-skills-maintainer/SKILL.md) skill —
  read it before adding or restructuring a skill.

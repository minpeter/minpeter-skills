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

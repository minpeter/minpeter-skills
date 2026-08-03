---
name: minpeter-skills-maintainer
description: >-
  Maintains the minpeter/minpeter-skills repository — the collection of Agent
  Skills in the open SKILL.md format. Use this when adding a new skill to that
  repo, editing or refining an existing skill, splitting an oversized SKILL.md
  into references/, renaming or removing a skill, or fixing drift between
  SKILL.md frontmatter, README.md's index table, and skills.sh.json groupings.
  Also use it when the user says "add a skill", "update the skills repo",
  "write a skill for X", or asks how this repo is laid out. Enforces the
  mandatory workflow: clone the repo into /tmp/minpeter-skills-<skill-name>, work
  on a branch there, and open a PR with `gh pr create` — never edit an existing
  local checkout in place and never commit to main. Also covers the
  scaffold-with-`npx skills init` rule, frontmatter and naming requirements,
  the three files that must stay in sync, progressive disclosure limits, and
  the pre-commit verification pass. Authoring guidance for descriptions and
  skill bodies is in references/authoring.md; the exact clone / sync / verify /
  PR procedure is in references/maintenance.md.
license: MIT
metadata:
  author: minpeter
---

# Maintaining minpeter-skills

This repo is a **skill collection**, not an app. There is no build, no test
runner, and no package.json. The "product" is a set of Markdown files that other
agents load, so correctness means: valid frontmatter, discoverable descriptions,
and three files that agree with each other.

## Repo shape

```
AGENTS.md                       # short house rules (keep authoritative, keep short)
README.md                       # install instructions + the skill index table
skills.sh.json                  # skills.sh repo-page groupings
skills/<kebab-name>/SKILL.md    # one skill (flat layout, filename UPPERCASE)
skills/<kebab-name>/references/ # templates, deep-dives, checklists
```

**The invariant:** every skill directory has exactly one `SKILL.md`, and its
frontmatter `name` appears in **both** `README.md`'s table and one
`groupings[].skills` array in `skills.sh.json`. Drift in any of the three is the
most common bug in this repo — check all three on every change.

## 0. Always work in a fresh /tmp clone, then open a PR

**Do not edit an existing local checkout of this repo in place, and never commit
to `main`.** Every change — new skill, refinement, rename, removal — starts with
a throwaway clone named after the skill being touched:

```bash
SKILL=<kebab-name>                      # the skill you're adding or updating
WORK=/tmp/minpeter-skills-$SKILL
rm -rf "$WORK"
git clone https://github.com/minpeter/minpeter-skills.git "$WORK"
cd "$WORK"
git switch -c skill/$SKILL              # or docs/$SKILL for a refinement
```

Why: the clone is always current with `origin/main` (a stale working copy is how
you end up with a conflicting README row), it isolates scratch work from whatever
the user has open, and `rm -rf "$WORK"` is a safe reset when an attempt goes
sideways.

Do all the work below **inside `$WORK`**, then finish with a PR:

```bash
git add skills/$SKILL README.md skills.sh.json AGENTS.md
git commit -m "feat(skills): add $SKILL"
git push -u origin skill/$SKILL
gh pr create --fill
```

Branch prefixes: `skill/<name>` for a new skill, `docs/<name>` for editing one,
`chore/<name>` for renames and removals. Keep the PR title under ~70 chars and
put the detail (what the skill covers, what was verified) in the body.

## 1. Adding a skill

1. **Scaffold, don't hand-write frontmatter:**
   ```bash
   cd "$WORK/skills" && npx skills init <kebab-name>
   ```
   That writes `skills/<kebab-name>/SKILL.md` with valid frontmatter. Replace the
   placeholder body; keep the frontmatter keys.
2. **Write the frontmatter.** Required: `name` (lowercase-hyphen, must equal the
   directory name) and `description`. Optional and used here: `license: MIT`,
   `metadata.author: minpeter`. The description is the *activation contract* —
   it is the only text a cold agent sees before deciding to load the file, so
   pack the triggers into it. See [`references/authoring.md`](references/authoring.md).
3. **Write the body.** Under ~500 lines. Front-load the decision the reader
   needs; push templates, long checklists, and rationale into
   `references/*.md` and link them with relative paths.
4. **Sync `README.md`** — add a row to the Skills table, matching the existing
   three columns (linked skill name / what it does / when to use).
5. **Sync `skills.sh.json`** — add `<name>` to the right `groupings[].skills`,
   or add a new grouping (`title` + `description` + `skills`) if none fits.
6. **Verify** (§3), then commit, push the branch, and open the PR (§0).

## 2. Editing an existing skill

Read the whole `SKILL.md` plus its `references/` before changing anything —
these files cross-reference each other by section number (`§5`) and by relative
link, and both break silently.

- Changed the `name`? Then rename the directory, update the README link **and**
  cell text, update `skills.sh.json`, and grep for the old name repo-wide.
- Changed what the skill covers? Update the `description` too. A stale
  description means the skill stops getting activated for the cases it now handles.
- Moved content into `references/`? Add the link from `SKILL.md`; an orphan
  reference file is dead weight the agent never loads.
- Removing a skill: delete the directory, the README row, and the
  `skills.sh.json` entry (drop the grouping entirely if it goes empty —
  `skills` requires `minItems: 1`).

## 3. Verify before committing

```bash
# frontmatter parses, name matches dir, and the CLI can enumerate every skill
npx skills add . --list
```

Then confirm by hand:
- [ ] `name` == directory name, lowercase-hyphen, `SKILL.md` uppercase
- [ ] `description` names the triggers, in one YAML block scalar (`>-`)
- [ ] `SKILL.md` under ~500 lines; heavy detail in `references/`
- [ ] every `references/` file is linked from `SKILL.md`, and every link resolves
- [ ] README table row present and accurate
- [ ] name present in exactly one `skills.sh.json` grouping
- [ ] no absolute paths or machine-local paths anywhere in the skill

Full procedure, including the link-check and drift-check one-liners:
[`references/maintenance.md`](references/maintenance.md).

## 4. Conventions

- **Commits:** conventional, scoped to the skill —
  `docs(typescript-package): add OIDC PR-creation gate gotcha`,
  `feat(skills): add minpeter-skills-maintainer`. Repo-wide changes use
  `docs(repo):` or `chore(repo):`.
- **One skill per PR** where practical, so review and revert stay per-skill.
- **Clean up** `/tmp/minpeter-skills-<name>` once the PR is merged.
- **Voice:** these skills are *opinionated house style*. State the decision,
  then the reasoning. Mark hard rules as hard rules and list what to flag in
  review. Avoid hedging — a skill that says "consider maybe" gives the reading
  agent nothing to act on.
- **No stale versions.** Never bake `pkg@1.2.3` into a skill; instruct the agent
  to resolve `@latest` at execution time. Same for GitHub Action majors.
- **AGENTS.md is the summary, not the manual.** If a rule needs more than two
  lines, it belongs in this skill; keep `AGENTS.md` a pointer-length digest and
  update it when an invariant changes.

## NOT this repo's style (flag it)

Nested skill directories (`skills/a/b/SKILL.md`) · lowercase `skill.md` ·
`name` that disagrees with the directory · a skill missing from README or
`skills.sh.json` · descriptions that describe the topic but not the trigger ·
1000-line `SKILL.md` with no `references/` · pinned tool versions ·
`references/` files nothing links to · commits pushed straight to `main` ·
edits made in a long-lived local checkout instead of a fresh `/tmp` clone.

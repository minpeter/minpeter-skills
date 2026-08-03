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
  local checkout in place and never commit to main. After the PR is reviewed and
  merged, reinstall the skill on this machine with `npx skills add -g` (new skill)
  or `npx skills update -g` (existing skill) so the globally installed copy stops
  being stale. Also covers the
  scaffold-with-`npx skills init` rule, frontmatter and naming requirements,
  the three files that must stay in sync, progressive disclosure limits, and
  the pre-commit verification pass. Authoring guidance for descriptions and
  skill bodies is in references/authoring.md; the exact clone / sync / verify /
  PR / post-merge-install procedure is in references/maintenance.md.
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

Opening the PR is not the end. The merged version still has to be installed on
this machine — see §5.

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
   Once it is merged, install it locally (§5).

## 2. Editing an existing skill

Read the whole `SKILL.md` plus its `references/` before changing anything —
these files cross-reference each other by section number (`§N`) and by relative
link, and both break silently.

- Changed the `name`? Then rename the directory, update the README link **and**
  cell text, update `skills.sh.json`, and grep for the old name repo-wide.
- Changed what the skill covers? Update the `description` too. A stale
  description means the skill stops getting activated for the cases it now handles.
- Moved content into `references/`? Add the link from `SKILL.md`; an orphan
  reference file is dead weight the agent never loads.
- Removing a skill: delete the directory, the README row, and the
  `skills.sh.json` entry (drop the grouping entirely if it goes empty —
  `skills` requires `minItems: 1`). After merge, uninstall it locally too (§5).

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

## 4. Review and merge

The PR is for the user to read. Do not merge it yourself unless they ask —
merging is their call, and the skill body is exactly the kind of thing that wants
a human read-through before it starts steering other agents.

When they do ask:

```bash
gh pr merge <n> --squash --delete-branch
```

## 5. Install the merged skill on this machine

**A merged PR changes nothing locally.** Installed skills are copies under
`~/.agents/skills/<name>`, symlinked into each agent's directory, and tracked in
`~/.agents/.skill-lock.json` by source repo + folder hash. Until you reinstall,
every agent on this machine keeps reading the pre-merge version.

```bash
# refresh the local checkout of the repo
cd <path-to-local-checkout> && git switch main && git pull

# NEW skill: it is not in the lock file yet, so `update` will not see it
npx skills add -g minpeter/minpeter-skills --skill <name> -a '*' -y

# EXISTING skill: already in the lock file, so update in place
npx skills update -g <name>
```

`update` only refreshes skills already present in `.skill-lock.json`, so reaching
for it after adding a brand-new skill is a silent no-op. That distinction is the
one thing to get right here.

Then confirm the machine actually has the new content:

```bash
npx skills ls -g                       # name, install path, agents, source repo
rg -n '^name:' ~/.agents/skills/<name>/SKILL.md
ls ~/.agents/skills/<name>/references/ # references/ came along too
```

Finally, clean up the scratch clone: `rm -rf /tmp/minpeter-skills-<name>`.

Notes:
- `-g` installs globally (`~/.agents/skills`, shared by all projects). Drop it to
  install into the current project's agent directory instead.
- `-a '*'` targets every detected agent. Name specific ones (`-a pi,claude-code`)
  to narrow it.
- If a skill was **renamed**, install the new name and
  `npx skills remove -g <old-name>` — the old directory and lock entry do not
  disappear on their own, and two copies means ambiguous activation.
- If a skill was **removed**, `npx skills remove -g <name>`.

## 6. Conventions

- **Commits:** conventional, scoped to the skill —
  `docs(typescript-package): add OIDC PR-creation gate gotcha`,
  `feat(skills): add minpeter-skills-maintainer`. Repo-wide changes use
  `docs(repo):` or `chore(repo):`.
- **One skill per PR** where practical, so review and revert stay per-skill.
- **Clean up** `/tmp/minpeter-skills-<name>` once the PR is merged and the skill
  is reinstalled locally (§5).
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
edits made in a long-lived local checkout instead of a fresh `/tmp` clone ·
stopping at the merged PR and leaving the machine on the stale installed copy.

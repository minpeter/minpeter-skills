---
name: minpeter-skills-maintainer
description: >-
  Maintains the minpeter/minpeter-skills repository — the collection of Agent
  Skills in the open SKILL.md format. Use this when adding a new skill to that
  repo, editing or refining an existing skill, splitting an oversized SKILL.md
  into references/, renaming or removing a skill, or fixing drift between
  SKILL.md frontmatter, README.md's index table, and skills.sh.json groupings.
  Also use it when the user says "add a skill", "update the skills repo",
  "write a skill for X", or asks how this repo is laid out. Covers the mandatory
  workflow (throwaway /tmp clone → branch → PR → reinstall locally after merge;
  never edit a local checkout in place, never commit to main), scaffolding with
  `npx skills init`, frontmatter and naming rules, the three files that must stay
  in sync, progressive disclosure limits, and the pre-commit verification pass.
  Everything here is published to a PUBLIC repo, so it also enforces the
  no-secrets / no-PII rule: no tokens, credentials, private hostnames, internal
  URLs, real emails, or machine-local paths in a skill — use placeholders.
  Authoring guidance for descriptions and skill bodies is in
  references/authoring.md; the clone / verify / PR / post-merge-install runbook
  is in references/maintenance.md.
license: MIT
metadata:
  author: minpeter
---

# Maintaining minpeter-skills

This repo is a **skill collection**, not an app. There is no build, no test
runner, and no package.json. The "product" is a set of Markdown files that other
agents load, so correctness means: valid frontmatter, discoverable descriptions,
and three files that agree with each other.

**This repo is public.** Everything committed here is world-readable forever, and
git history keeps it even after a later deletion. Treat every skill as a published
document — see §4.

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
KIND=skill                              # skill | docs | chore  (see below)
BRANCH=$KIND/$SKILL                     # removals: BRANCH=chore/remove-$SKILL
WORK=/tmp/minpeter-skills-$SKILL
rm -rf "$WORK"
git clone https://github.com/minpeter/minpeter-skills.git "$WORK"
cd "$WORK"
git switch -c "$BRANCH"
```

`KIND` picks the branch prefix and the commit type, driven by the operation:

| Operation | `KIND` | Branch | Commit subject |
|---|---|---|---|
| New skill | `skill` | `skill/<name>` | `feat(skills): add <name>` |
| Edit / refine | `docs` | `docs/<name>` | `docs(<name>): <what changed>` |
| Rename | `chore` | `chore/<name>` | `chore(skills): rename …` |
| Remove | `chore` | `chore/remove-<name>` | `chore(skills): remove …` |

Why the clone: it is always current with `origin/main` (a stale working copy is
how you end up with a conflicting README row), it isolates scratch work from
whatever the user has open, and `rm -rf "$WORK"` is a safe reset when an attempt
goes sideways.

Do all the work below **inside `$WORK`**, then finish with a PR:

```bash
SUBJECT="feat(skills): add $SKILL"      # use the subject for your KIND
git add skills/$SKILL README.md skills.sh.json AGENTS.md
git commit -m "$SUBJECT"
git push -u origin HEAD                 # pushes the checked-out branch by name
gh pr create --fill
```

Push `HEAD` rather than a re-derived `$KIND/$SKILL` so the pushed name always
matches the branch you created — they differ for removals. Keep the PR title under
~70 chars and put the detail (what the skill covers, what was verified) in the body.

Opening the PR is not the end. The merged version still has to be installed on
this machine — see §6.

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
   Once it is merged, install it locally (§6).

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
  `skills` requires `minItems: 1`). After merge, uninstall it locally too (§6).

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
- [ ] name present in exactly one `skills.sh.json` grouping (check with
      `jq -r '.groupings[].skills[]' skills.sh.json`, not a bare grep — a plain
      quoted-string grep also matches the JSON keys)
- [ ] no absolute paths or machine-local paths anywhere in the skill
- [ ] nothing secret or personal (§4) — run the scan before every commit

Full procedure, including the link-check and drift-check one-liners:
[`references/maintenance.md`](references/maintenance.md).

## 4. Never commit secrets or personal data

This repo is **public**, and `git` history is effectively permanent — deleting a
line in a later commit does not unpublish it. A skill is a published document, so
write it for a stranger reading it on GitHub.

**Never commit:**
- Tokens, API keys, or credentials of any kind — including expired or
  "throwaway" ones. `NPM_TOKEN`, `gh[pousr]_…`, `sk-…`, `AKIA…`, Bearer
  headers, `.npmrc` auth lines, private keys.
- Real emails, phone numbers, or names of people other than the repo owner.
- Internal or private infrastructure: company hostnames, VPN or intranet URLs,
  private registry endpoints, internal package names, IP addresses, database
  connection strings, S3 bucket names, ticket URLs.
- Machine-local paths (`/home/<user>/…`, `/Users/…`, `C:\Users\…`) — both a
  privacy leak and a portability break.
- Real log output, stack traces, or command transcripts pasted from a work
  machine. Sanitize them or rewrite them as generic examples.
- Anything under NDA, or unreleased/internal product detail.

**Use placeholders instead**, and make them obviously fake:
`<your-org>`, `<repo>`, `you@example.com`, `<registry-host>`, `<path-to-checkout>`,
`$HOME`. `example.com` / `example.org` are reserved for exactly this.

When a skill documents a real service, name only what is already public (the npm
registry, `github.com`, a published package name). The test: *would this line be
fine in a blog post?* If not, it does not belong in a skill.

Scan before every commit (`$META` skips this skill, which necessarily spells out
the shapes it forbids):

```bash
META="!**/minpeter-skills-maintainer/**"

# credential shapes
rg -n -i --glob "$META" 'gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|npm_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY|Bearer [A-Za-z0-9._-]{20,}' skills/

# emails that are not example.com, and machine-local paths
rg -n --glob "$META" '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' skills/ | rg -v 'example\.(com|org)'
rg -n --glob "$META" '/home/[A-Za-z0-9]|/Users/[A-Za-z0-9]|C:\\Users\\[A-Za-z0-9]' skills/
```

Each must come back empty. All three bases use the same `[A-Za-z0-9]` class so a
real path is caught whatever the username's case (`/home/Alice`, `C:\Users\Bob`)
while a documented placeholder passes — `<` and `…` are not alphanumeric, so
`/home/<user>/…` and `C:\Users\…` do not trip it. A guardrail that fires on its own
examples gets ignored. Private-IP and internal-hostname patterns are in
[`references/maintenance.md`](references/maintenance.md) §4b.

**If a secret does land on `main`:** treat it as compromised and rotate it
immediately. Removing the line in a follow-up commit is not enough — the value
stays in history and in anyone's existing clone. Tell the user; do not attempt a
history rewrite (`filter-repo`, force-push) on your own.

## 5. Review and merge

The PR is for the user to read. Do not merge it yourself unless they ask —
merging is their call, and the skill body is exactly the kind of thing that wants
a human read-through before it starts steering other agents.

When they do ask:

```bash
gh pr merge <n> --squash --delete-branch
```

## 6. Install the merged skill on this machine

**A merged PR changes nothing locally.** The installed copy lives at
`~/.agents/skills/<name>` and is tracked in `~/.agents/.skill-lock.json`. Until
you reinstall, every agent on this machine keeps reading the pre-merge version.

The one thing to get right: **`add` for a skill's first install, `update`
afterwards.** `npx skills update` only iterates over skills already present in
`.skill-lock.json`, so running it for a brand-new skill is a silent no-op that
looks like success.

```bash
cd <path-to-local-checkout> && git switch main && git pull
npx skills add -g minpeter/minpeter-skills --skill <name> -a '*' -y   # NEW
npx skills update -g <name>                                          # EXISTING
```

Then verify by reading the installed files (not by grepping the colorized
`skills ls` output), and drop the scratch clone. After a rename or removal, also
`npx skills remove -g <old-name>` — the old directory and lock entry do not
disappear on their own.

Full step-by-step, including the install layout, the flag table, and what to check
when a reinstall looks like it did nothing:
[`references/maintenance.md`](references/maintenance.md) §7.

## 7. Conventions

- **Commits:** conventional, scoped to the skill —
  `docs(typescript-package): add OIDC PR-creation gate gotcha`,
  `feat(skills): add minpeter-skills-maintainer`. Repo-wide changes use
  `docs(repo):` or `chore(repo):`. The branch prefix follows the same operation
  (§0).
- **One skill per PR** where practical, so review and revert stay per-skill.
- **Clean up** `/tmp/minpeter-skills-<name>` once the PR is merged and the skill
  is reinstalled locally (§6).
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
stopping at the merged PR and leaving the machine on the stale installed copy ·
real emails, tokens, private hostnames, internal URLs, or `/home/<user>/` paths
where a placeholder belongs.

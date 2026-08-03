# Maintenance runbook

## 0. Set up the /tmp clone

All work happens in a throwaway clone named after the skill being touched, never
in a long-lived local checkout:

```bash
SKILL=<kebab-name>
KIND=skill                     # skill = new | docs = edit | chore = rename/remove
BRANCH=$KIND/$SKILL            # removals: BRANCH=chore/remove-$SKILL
WORK=/tmp/minpeter-skills-$SKILL
rm -rf "$WORK"
git clone https://github.com/minpeter/minpeter-skills.git "$WORK"
cd "$WORK"
git switch -c "$BRANCH"
```

`KIND` drives the commit type used in §5; `BRANCH` is what you actually push, so
set it once here and never re-derive it later.

If `gh` is authenticated you can use `gh repo clone minpeter/minpeter-skills "$WORK"`
instead; the HTTPS URL works either way.

One clone per skill. If you are touching two skills, make two clones and two PRs
— the directory name is the lock that keeps them from colliding.

Run everything below from `$WORK`.

## 1. Enumerate what the CLI sees

```bash
npx skills add . --list
```

This parses every `SKILL.md` and prints `name` + `description`. If a skill is
missing from the output, or a name looks wrong, the frontmatter is broken or the
file is misplaced. This is the closest thing this repo has to a build.

## 2. Check the three-way sync

Normalize all three sources to bare skill names, then compare:

```bash
# names declared in frontmatter
rg -N --no-filename '^name:' skills/*/SKILL.md | sed 's/^name:[[:space:]]*//' | sort

# names referenced by the README index table
rg -o 'skills/([a-z0-9-]+)/SKILL\.md' -r '$1' README.md | sort -u

# names listed in the skills.sh groupings
jq -r '.groupings[].skills[]' skills.sh.json | sort
```

All three must print the same set. Use `jq` for the JSON — a bare
`rg -o '"[a-z0-9-]+"' skills.sh.json` also matches the object keys (`title`,
`description`, `skills`, `groupings`) and the `notGrouped` value, so the
comparison silently stops meaning anything.

Also verify each frontmatter `name` equals its directory name:

```bash
for d in skills/*/; do
  n=$(rg -N --no-filename '^name:' "$d/SKILL.md" | sed 's/^name:[[:space:]]*//')
  [ "$n" = "$(basename "$d")" ] || echo "MISMATCH: $d has name: $n"
done
```

## 3. Check links and orphans

```bash
# links from SKILL.md into references/ that don't exist
# (strip trailing prose punctuation before testing the path)
rg -o 'references/[A-Za-z0-9._-]+' skills/*/SKILL.md | while IFS=: read -r f link; do
  link=${link%.}
  [ -f "$(dirname "$f")/$link" ] || echo "BROKEN: $f -> $link"
done

# reference files that nothing links to
for f in skills/*/references/*; do
  rg -q "$(basename "$f")" "$(dirname "$(dirname "$f")")/SKILL.md" || echo "ORPHAN: $f"
done
```

## 4. Check size and hygiene

```bash
wc -l skills/*/SKILL.md skills/*/references/*   # SKILL.md under ~500 lines

# filename must be uppercase SKILL.md; -iname also catches case-insensitive FS
find skills -iname 'skill.md' ! -name 'SKILL.md'   # must print nothing
find skills -mindepth 3 -name SKILL.md             # must print nothing: flat layout only

# no machine-local paths, no pinned tool versions.
# Exclude this skill: it documents both patterns, so it self-matches.
META="!**/minpeter-skills-maintainer/**"
rg -n --glob "$META" '/home/|/Users/|C:\\' skills/
rg -n --glob "$META" '@[0-9]+\.[0-9]+\.[0-9]+' skills/
```

`find ... ! -name` is used instead of `ls skills/*/skill.md` because the glob
exits non-zero when it matches nothing, which trips up `&&` chains, and it misses
the bad case entirely on a case-insensitive filesystem.

## 4b. Scan for secrets and personal data

The repo is public and history is permanent, so this runs before every commit
(SKILL.md §4 has the full rule and the placeholder conventions):

```bash
# credential shapes — must print nothing
rg -n -i 'gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|npm_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY|Bearer [A-Za-z0-9._-]{20,}' skills/

# real emails (example.com/.org are the allowed placeholders)
rg -n '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' skills/ | rg -v 'example\.(com|org)'

# machine-local paths, private IPs, connection strings
rg -n '/home/[a-z]|/Users/[a-z]|C:\\Users' skills/
rg -n '\b(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9]+\.[0-9]+\b' skills/
rg -n -i '(postgres|mysql|mongodb|redis)://|\.internal\b|\.corp\b|\.local\b' skills/
```

Each of these must come back empty (the maintainer skill itself documents the
patterns, so exclude it with `--glob '!**/minpeter-skills-maintainer/**'` if it
self-matches). A hit is not automatically a leak — read it and decide — but it is
always worth a look before the commit lands.

If something secret already reached `main`: rotate it, tell the user, and do not
rewrite history on your own.

## 5. Commit, push, and open the PR

```bash
# Derive the commit subject from KIND (§0) so it cannot contradict the branch.
case $KIND in
  skill) SUBJECT="feat(skills): add $SKILL" ;;
  docs)  SUBJECT="docs($SKILL): <what changed>" ;;
  chore) SUBJECT="chore(skills): <rename|remove> $SKILL" ;;
esac

# Fill in the <…> placeholders, then let this guard prove you did.
case $SUBJECT in
  *"<"*) echo "refusing: unfilled placeholder in subject: $SUBJECT" >&2; return 1 2>/dev/null || exit 1 ;;
esac

git add skills/$SKILL README.md skills.sh.json AGENTS.md
git commit -m "$SUBJECT"
git push -u origin HEAD          # pushes the branch you are on, whatever it is named

gh pr create \
  --title "$SUBJECT" \
  --body "$(cat <<'EOF'
## Summary
<what the skill covers, and why it exists>

## Sync
- [x] README.md index row
- [x] skills.sh.json grouping

## Verified
- `npx skills add . --list` parses the skill
- name matches directory, all references/ links resolve, no orphans
- no secrets, real emails, private hosts, or machine-local paths
EOF
)"
```

Stage the specific paths rather than `git add .`. The `docs`/`chore` subjects carry
`<…>` placeholders; the guard above aborts rather than letting a literal
`docs(<name>): <what changed>` reach a commit or PR title. Keep the PR title under
~70 chars. `gh pr create --fill` is fine for small refinements where the commit
message already says everything. `git push -u origin HEAD` is deliberate: it pushes
whatever branch is checked out, so it cannot drift from the name created in §0 (a
removal on `chore/remove-<name>` would fail against a re-derived `$KIND/$SKILL`).

**Never** push to `main` and never `git commit` in the user's own checkout of
this repo.

## 6. Merge (the user's call)

Leave the PR open for the user to read. Merge only when they ask:

```bash
gh pr merge <n> --squash --delete-branch
```

## 7. Install the merged skill on this machine

A merged PR does not touch the local install. Global-scope layout:

```
~/.agents/skills/<name>/        # the actual installed copy
~/.agents/.skill-lock.json      # source repo + skillFolderHash per skill
~/.pi/agent/skills/<name>       # symlink -> ../../../.agents/skills/<name>
<other agent dirs>/<name>       # one entry per detected agent
```

The canonical copy is the one under `~/.agents/skills/`; verify against that.
How each agent directory points at it varies (symlink, or a copy with `--copy`,
and some agents' dirs chain through another agent's), so do not assume a
particular link shape per agent — ask `npx skills ls -g` instead.

Until you reinstall, every agent keeps reading the pre-merge copy.

```bash
# 1. refresh the local checkout
cd <path-to-local-checkout>
git switch main && git pull

# 2a. NEW skill — not in .skill-lock.json yet, so `update` cannot see it
npx skills add -g minpeter/minpeter-skills --skill "$SKILL" -a '*' -y

# 2b. EXISTING skill — already locked, update in place
npx skills update -g "$SKILL"

# 3. verify the machine has the merged content (read the installed files)
rg -n '^name:' "$HOME/.agents/skills/$SKILL/SKILL.md"
ls "$HOME/.agents/skills/$SKILL/references/"
diff -r "$HOME/.agents/skills/$SKILL" "skills/$SKILL" && echo "install matches main"

# 4. drop the scratch clone
rm -rf "$WORK"
```

`npx skills ls -g` is useful for a human eyeball over install paths, agents, and
source repo, but its output is ANSI-colored and meant for reading — assert
against the files, as above, rather than grepping it.

`update` iterates over what is already in `.skill-lock.json`. Running it for a
brand-new skill is a silent no-op that looks like success — use `add` for the
first install, `update` after that.

Flags worth knowing:

| Flag | Effect |
|---|---|
| `-g` | global scope (`~/.agents/skills`, all projects). Omit for project-local. |
| `-a '*'` | install to every detected agent. `-a pi,claude-code` to narrow. |
| `-y` | skip prompts (needed for non-interactive runs). |
| `--copy` | copy instead of symlinking into agent dirs. |

After a **rename**: install the new name, then
`npx skills remove -g <old-name>`. The old directory, symlinks, and lock entry
persist otherwise, and two copies of the same guidance means ambiguous
activation.

After a **removal**: `npx skills remove -g <name>`.

If the reinstall looks like it did nothing, check `skillFolderHash` for the skill
in `~/.agents/.skill-lock.json` — an unchanged hash after a successful pull means
the CLI fetched a ref that does not have the merge yet.

## Renaming a skill

Clone with `KIND=chore` (§0), then:

1. `git mv skills/<old> skills/<new>`
2. Update `name:` in the moved `SKILL.md`.
3. Update `README.md`: both the link target and the visible cell text.
4. Update `skills.sh.json`.
5. `rg -n '<old>' .` and fix every remaining hit (other skills may cross-link).
6. Re-run steps 1–4 of this runbook, then §5–§7.

Renaming breaks installs that pinned the old name via
`npx skills add minpeter/minpeter-skills --skill <old>`, so treat it as a
breaking change: say so in the PR body, not just the commit.

## Removing a skill

Clone with `KIND=chore` and `BRANCH=chore/remove-$SKILL` (§0), then:

1. `git rm -r skills/<name>`
2. Delete the README row.
3. Remove the name from `skills.sh.json`. If its grouping becomes empty, delete
   the grouping — the schema requires `minItems: 1` for both `groupings` and
   `groupings[].skills`, so an empty array makes the file invalid.
4. After the PR merges: `npx skills remove -g <name>` (§7).

## skills.sh.json shape

Validated against `https://skills.sh/schemas/skills.sh.schema.json`
(`additionalProperties: false`, so no stray keys):

```jsonc
{
  "$schema": "https://skills.sh/schemas/skills.sh.schema.json",
  "notGrouped": "bottom",          // "top" | "bottom" — where ungrouped skills land
  "groupings": [                    // 1..50 entries
    {
      "title": "TypeScript",        // required, 1..120 chars
      "description": "...",         // optional, <=500 chars
      "skills": ["typescript-package"]  // required, 1..500 names
    }
  ]
}
```

A skill absent from every grouping still appears on the repo page (placed per
`notGrouped`), but grouping it is the convention here.

## Verifying activation end to end

To sanity-check a skill the way a consumer gets it, **before** the PR merges:

```bash
# install the branch under review into a scratch project
mkdir -p /tmp/skill-check && cd /tmp/skill-check
npx skills add "$WORK" --skill "$SKILL" -a claude-code -y --copy
```

Then read the installed copy and confirm the relative `references/` links still
resolve from the install location. Clean up `/tmp/skill-check` afterwards.

# Maintenance runbook

## 0. Set up the /tmp clone

All work happens in a throwaway clone named after the skill being touched, never
in a long-lived local checkout:

```bash
SKILL=<kebab-name>
WORK=/tmp/minpeter-skills-$SKILL
rm -rf "$WORK"
git clone https://github.com/minpeter/minpeter-skills.git "$WORK"
cd "$WORK"
git switch -c skill/$SKILL     # skill/ new | docs/ edit | chore/ rename+remove
```

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

```bash
# names declared in frontmatter
rg -N '^name:' skills/*/SKILL.md

# names referenced by the README index table
rg -o 'skills/[a-z0-9-]+/SKILL\.md' README.md | sort -u

# names listed in the skills.sh groupings
rg -o '"[a-z0-9-]+"' skills.sh.json
```

All three lists must contain the same set of skill names. Also verify each
frontmatter `name` equals its directory name:

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

ls skills/*/skill.md 2>/dev/null                # must be empty: filename is UPPERCASE
find skills -name SKILL.md -mindepth 3          # must be empty: flat layout only

rg -n '/home/|/Users/|C:\\' skills/             # no machine-local paths
                                                # (this file self-matches; ignore that hit)
rg -n '@[0-9]+\.[0-9]+\.[0-9]+' skills/         # suspicious pinned versions
```

## 5. Commit, push, and open the PR

```bash
git add skills/$SKILL README.md skills.sh.json AGENTS.md
git commit -m "feat(skills): add $SKILL"
git push -u origin skill/$SKILL

gh pr create \
  --title "feat(skills): add $SKILL" \
  --body "$(cat <<'EOF'
## Summary
<what the skill covers, and why it exists>

## Sync
- [x] README.md index row
- [x] skills.sh.json grouping

## Verified
- `npx skills add . --list` parses the skill
- name matches directory, all references/ links resolve, no orphans
EOF
)"
```

Stage the specific paths rather than `git add .`. Keep the PR title under ~70
chars. `gh pr create --fill` is fine for small refinements where the commit
message already says everything.

**Never** push to `main` and never `git commit` in the user's own checkout of
this repo.

## 6. Merge (the user's call)

Leave the PR open for the user to read. Merge only when they ask:

```bash
gh pr merge <n> --squash --delete-branch
```

## 7. Install the merged skill on this machine

A merged PR does not touch the local install. Layout on this machine:

```
~/.agents/skills/<name>/        # the actual installed copy (global scope)
~/.pi/agent/skills/<name>       # symlink -> ../../../.agents/skills/<name>
~/.claude/skills/<name>         # ...one symlink per detected agent
~/.agents/.skill-lock.json      # source repo + skillFolderHash per skill
```

So until you reinstall, every agent keeps reading the pre-merge copy.

```bash
# 1. refresh the local checkout
cd <path-to-local-checkout>
git switch main && git pull

# 2a. NEW skill — not in .skill-lock.json yet, so `update` cannot see it
npx skills add -g minpeter/minpeter-skills --skill "$SKILL" -a '*' -y

# 2b. EXISTING skill — already locked, update in place
npx skills update -g "$SKILL"

# 3. verify the machine has the merged content
npx skills ls -g | rg -A1 "$SKILL"
rg -n '^name:' "$HOME/.agents/skills/$SKILL/SKILL.md"
ls "$HOME/.agents/skills/$SKILL/references/"

# 4. drop the scratch clone
rm -rf "$WORK"
```

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

Clone as `chore/<new-name>` (§0), then:

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

Clone as `chore/remove-<name>` (§0), then:

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

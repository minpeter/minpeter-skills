# Authoring a skill in this repo

## The frontmatter

```yaml
---
name: kebab-case-name          # required; == directory name
description: >-               # required; the activation contract
  What it is. When to use it: <trigger>, <trigger>, <trigger>.
  Where the detail lives: references/<file>.md.
license: MIT                  # optional; MIT across this repo
metadata:
  author: minpeter            # optional
---
```

Only `name` and `description` are required by the format. Keep `license` and
`metadata.author` on every skill here for consistency.

`name` rules: lowercase letters, digits, hyphens. No spaces, no underscores, no
uppercase. It must match the containing directory exactly, because agents and the
`skills` CLI key off one or the other depending on the entry point.

## Writing the description (the part that matters most)

The description is loaded into an agent's context *before* the body. It is the
only signal used to decide whether to open the file. So it is not a summary —
it is a matcher.

Include, in roughly this order:

1. **What the skill governs**, in the user's vocabulary, not yours.
2. **Concrete triggers.** The literal situations and phrasings that should
   activate it: "scaffolding a new TS library", "reviewing an existing
   package.json", "the user says add a skill".
3. **Distinctive keywords** a user is likely to type: tool names, file names,
   command names, error strings. These do the retrieval work.
4. **A map of `references/`**, so the agent knows what it can fetch next without
   reading the body first.

Anti-patterns:
- Topic-only descriptions ("Guidance about TypeScript packaging") — no triggers,
  so the skill never fires at the right moment.
- Sales copy ("the best way to...") — spends tokens without adding a match.
- Over-broad scope ("all things frontend") — fires constantly and gets ignored.

Use a YAML block scalar (`>-`) for anything longer than one line. Plain
multi-line strings with colons in them are a common parse break.

## Writing the body

Structure that works for opinionated skills:

```markdown
# Title (scope in one line)

Short framing: what "done" looks like, what is locked vs. open.

## The locked stack / The invariant     <- the decision table, up top
## 1..N numbered sections               <- one per concern, cross-referenceable as §N
## Review checklist                     <- checkbox list for audit mode
## NOT this style (flag in review)      <- negative signals, explicit
```

Rules of thumb:
- **Decision first, reasoning second.** The agent needs to act; the rationale is
  there to stop it from re-litigating.
- **Be prescriptive.** "Use tsdown, not tsup" beats "consider a modern bundler".
  If something genuinely is a judgment call, say what the deciding factor is.
- **Give copy-pasteable artifacts** — config blocks, commands, file skeletons —
  but keep them in `references/`, not the body, once they exceed a few lines.
- **Number the sections** you reference elsewhere and keep the numbers stable;
  other files and other skills link to `§N`.
- **Include a negative list.** Explicitly naming the anti-patterns is what makes
  a skill usable for reviewing existing code, not just writing new code.
- **No stale versions.** Tell the agent to resolve `@latest` at run time, and to
  check current recommended majors for GitHub Actions rather than copying.

## Progressive disclosure

Keep `SKILL.md` under ~500 lines. Split when a section becomes long enough that
it would be skipped:

| Content | Goes where |
|---|---|
| The decision, the rule, the checklist | `SKILL.md` |
| Full config files, copy-paste templates | `references/templates.md` |
| Rationale, history, footguns, citations | `references/<topic>.md` |
| Step-by-step operational runbooks | `references/<task>.md` |

Every `references/` file must be linked from `SKILL.md` with a relative path
(`references/foo.md`) and a one-line hint about when to open it. Unlinked
reference files are never loaded, so they are pure maintenance cost.

Use relative links only. An absolute or machine-local path breaks the moment the
skill is installed into another agent's directory.

## Writing examples that are safe to publish

This repo is public, so every example you write is published. Keep sample values
obviously fake and generic:

| Instead of | Write |
|---|---|
| a real email | `you@example.com` |
| a company hostname or internal URL | `<registry-host>`, `https://example.com` |
| `/home/<user>/projects/thing` | `<path-to-checkout>` or `$HOME/…` |
| a real token, even expired | `<token>`, or omit it entirely |
| an internal package or service name | `@your-org/<pkg>`, `<service>` |
| a private IP or connection string | `<host>`, `<database-url>` |

`example.com` and `example.org` are reserved by RFC 2606 for documentation, so
they can never collide with a real host.

Name real services only when they are already public and relevant — the npm
registry, `github.com`, a published package. The check before committing: *would
this line be fine in a blog post?*

See SKILL.md §4 for the full no-secrets rule and the pre-commit scan.

---
name: hermes-agent-consult
description: >-
  Consult the local `hermes` agent as the long-term-memory oracle for minpeter's
  machines, from inside another coding agent (pi, codex, senpi, Kiro, Claude
  Code). Use it whenever a task needs context the repo does not contain —
  infrastructure layout, hostnames/ports/routing, why a past decision was made,
  prior incidents, cross-repo conventions, deploy/ops procedure — and the
  instinct is to ask the user: run `hermes -z "<query>"` FIRST, then ask the user
  only what hermes could not answer. Also use it after an infra change or a
  long-lived decision, to write that fact back into hermes memory (`-t memory`),
  and for a second-opinion review of a diff or plan from an agent that has the
  operational history. Covers query construction, why a failed run can still look
  like an answer (`--usage-file`), auto-approved tools, and what must never be
  sent to a hosted model. Query templates: references/queries.md. CLI flags,
  memory layout, troubleshooting: references/cli.md.
license: MIT
metadata:
  author: minpeter
---

# Consulting the hermes agent

`hermes` is minpeter's long-running personal agent. It holds persistent memory
about the machines, homelab, networking, and past decisions that a fresh coding
agent in a single repo cannot see. Treat it as **a peer to consult, not a tool to
run**: it is the cheapest source of the context you are missing, and it is the
place that context has to be stored so the *next* agent finds it.

Verify it is available before relying on it: `command -v hermes`. If it is
missing, fall back to asking the user and say why.

## The three moves

| Move | When | Command |
|---|---|---|
| **Consult** | You need context the repo does not contain, and you were about to ask the user | `hermes -z "<question>"` |
| **Teach** | You changed infra, or learned something with a long shelf life | `hermes -t memory -z "Remember: <fact>"` |
| **Review** | Non-trivial diff, plan, or ops procedure before you hand it over | `hermes -z "Review this: … <diff>"` |

`-z` is one-shot: it prints only the final response text to stdout, no banner,
no spinner, no session id. It is built for exactly this kind of scripted use.

**The prompt must immediately follow `-z`.** `hermes -t memory -z "…"` and
`hermes -z "…" -t memory` both work; `hermes -z -t memory "…"` is an argparse
error, because `-t` gets consumed as the prompt. Putting `-z` last is the habit
that never breaks.

## 1. Consult before asking the user

The rule: **when you are about to ask the user a question about their
environment, history, or preferences, ask hermes first.** The user is the slow,
expensive path; hermes answers in ~10s and often already knows.

Consult for:

- **Infrastructure** — hosts, ports, routes, proxies, tunnels, containers, which
  service owns what, what is tailnet-only vs LAN-reachable.
- **Operational history** — has this broken before, what was the fix, what is
  fragile, what must not be restarted.
- **Past decisions and their reasons** — why this tool, why this layout, what was
  already rejected and why. Prevents you from re-litigating a settled call.
- **Cross-repo conventions** — how minpeter does this in his *other* projects.
- **Deploy / release / recovery procedure** for anything not documented in-repo.

Do **not** consult for things the repo answers. Read the code first. hermes is
for context that lives outside the working tree; a question you could have
answered with `rg` wastes a round trip and can get you a stale answer.

Then: **hermes is a starting point, not an authority.** It answers from memory
written by past sessions, so it can be out of date. Verify anything load-bearing
against the live system or the repo before acting on it, and say in your reply
that the claim came from hermes memory.

Escalate to the user when hermes returns nothing useful, contradicts what you
observe, or when the question is a *preference* about work not yet done — that is
the user's call, not a memory lookup.

## 2. Write the query so a cold agent can answer it

hermes has no idea what you are working on. Every query is a cold start.

- **State the situation, then the question.** One or two sentences of context
  ("Working in the `<repo>` repo, adding a second ingress route") beats a bare
  question.
- **Ask for a specific shape of answer**: "list the ports", "3 bullets max",
  "answer in one line", "just the hostname". Unbounded questions get essays.
- **Name what you already know** so it corrects you instead of repeating you.
- **Prefer read-only phrasing.** Approvals are auto-bypassed under `-z`, so
  hermes *will* run commands if the query invites it. Say "answer from memory"
  or "do not modify anything" when you only want a lookup.
- **Run it from the relevant directory.** `-z` loads `AGENTS.md` and rules from
  the CWD, so `cd` into the repo you are asking about.
- **Restrict the toolset when you can**: `-t memory` for a memory-only lookup
  keeps it fast and stops it from wandering into the web or the shell.
- **Every run is a cold start — there is no follow-up.** One-shot mode does not
  resume prior context (`-c` / `--resume` do not carry into `-z`), so a
  "and what about …" query lands with no history. Put everything the question
  needs into the one prompt.

Copy-paste query shapes for all three moves: [`references/queries.md`](references/queries.md).

## 3. Teach it what you changed

A fact that only exists in this session's context is lost. If future-you or
another agent would need it, write it back:

```bash
hermes -t memory -z "Remember: <fact>. Save it to memory, then confirm in one line."
```

Teach it when you:

- change infrastructure — routing, ports, service ownership, a new host or tunnel
- discover a footgun the hard way — what breaks, what the recovery order is
- settle a decision with long-lived consequences, plus the reason
- establish a convention meant to hold across repos
- resolve an incident — cause and fix, not just "fixed"

Write the fact the way you would want to *receive* it: specific, self-contained,
no pronouns pointing at lost context, and short. Include the "do not" as
explicitly as the "do" — `do not disable <service>; it owns the routes` is the
kind of line that saves an outage.

**Verify the write.** The confirmation text is the model talking; the actual
storage is `MEMORY.md` under the active profile's memories dir (entries separated
by `§`) — `~/.hermes/memories/MEMORY.md` for the default profile, see
[`references/cli.md`](references/cli.md) for named profiles and `HERMES_HOME`.
Grep it for a distinctive token from your fact. Add memories through the agent
rather than by hand: the memory tool enforces the size limits and does targeted,
atomic updates instead of blind appends.

Ask the user before teaching anything that is a claim about *them* rather than
about the system, and before writing a fact you have not verified. Memory is
sticky: a wrong entry keeps misleading agents until someone notices.

## 4. Use it as a reviewer

hermes is the only reviewer available that knows the operational history, which
makes it worth a pass on infra changes, migrations, and ops runbooks:

```bash
cd <repo> && hermes -z "Review this diff for problems. Be brief, max 3 bullets.

$(git diff)"
```

Ask for severity-tagged bullets and a hard cap. Treat the output as one opinion:
confirm each finding against the code before acting, and drop the ones that do
not hold. Do not paste unbounded diffs — scope to the files that matter.

## 5. Failure can look like an answer

The trap that matters most. Some provider failures (bad model, auth failure,
HTTP 400) print the error text to **stdout** and still exit **0**, so a naive
`if hermes -z …; then` treats a failure as an answer. Others do exit nonzero.
Neither signal alone is sufficient.

When the result gates a decision, check the exit status **and** a usage report:

```bash
hermes --usage-file /tmp/hermes-usage.json -z "<query>"   # nonzero → failed, maybe before any inference
jq '.completed, .failed' /tmp/hermes-usage.json           # want true, false
```

Preflight errors (malformed flags, an invalid `-t` name) exit nonzero and write
**no** report at all; a run that reached the provider and failed there may exit 0
while the report records `failed: true`. Details and the rest of the flags:
[`references/cli.md`](references/cli.md).

Other operational notes:

- **Budget the latency.** A memory-only lookup is seconds; a query that triggers
  tool use is much longer. Give long consults a `timeout` so you never hang.
- **Every `-z` run creates a session.** Fine occasionally; if you scripted a
  batch of probes, clean up with `hermes sessions list` / `hermes sessions
  delete <id>`.
- **One question per run.** Multi-part queries come back as blended prose that is
  hard to act on.

## 6. What never goes into a query

`-z` sends your prompt to a hosted inference provider. Everything in that string
leaves the machine.

- No secrets, tokens, keys, `.env` contents, or credential-bearing config.
- No pasted files you have not looked at.
- Do not ask hermes to *fetch* a secret and put it in the answer.

And do not ask it to perform mutating work on your behalf. Under `-z` approvals
are bypassed, so "fix the routing" is an unsupervised change to a live system.
Consult, teach, review — the acting stays with you and the user.

## Review checklist

- [ ] `command -v hermes` checked before depending on it
- [ ] consulted hermes before asking the user an environment/history question
- [ ] read the repo first; the question genuinely needs outside context
- [ ] query is self-contained (no reliance on a previous run), bounded in output
      shape, read-only phrased
- [ ] run from the relevant CWD, `-t memory` when it is a pure lookup
- [ ] prompt immediately follows `-z`, quoted
- [ ] load-bearing answers verified against the live system, and attributed
- [ ] infra change / footgun / decision taught back, and the write grepped in
      the profile's `MEMORY.md`
- [ ] success checked via exit status **and** `--usage-file`, when it gates a decision
- [ ] no secrets in the prompt; no mutating instructions

## NOT this style (flag it)

Asking the user something hermes already knows · treating a hermes answer as
verified fact · `hermes -z -t memory "…"` (the prompt must follow `-z`) ·
branching on `$?` alone ·
making an infra change and never teaching it back · hand-editing `MEMORY.md` ·
teaching unverified or user-attributed claims without asking · pasting a whole
repo or an unbounded diff into a query · secrets in the prompt · asking hermes to
mutate a live system under `-z` · expecting `-c` / `--resume` to give a `-z` run
prior context · interactive `hermes` (or `chat`) from inside another agent, which
blocks on a TTY that is not there.

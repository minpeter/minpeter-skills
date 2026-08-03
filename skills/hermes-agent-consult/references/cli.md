# hermes CLI for non-interactive use

Everything here is about driving `hermes` from inside another agent. Interactive
`hermes` / `hermes chat` needs a TTY and will hang under an agent harness — never
launch it.

Flag surface changes over time. `hermes --help` and `hermes <sub> --help` are the
source of truth; treat the tables below as the shape, not a frozen contract.

## The flags that matter

| Flag | Effect |
|---|---|
| `-z, --oneshot <prompt>` | Send one prompt, print **only** the final response text to stdout. No banner, spinner, tool previews, or session-id line. Approvals auto-bypassed. The prompt must immediately follow `-z`. |
| `--usage-file <path>` | One-shot only. Writes a JSON usage report after a run that reached the provider, including a failed one. Not written for preflight errors. |
| `-t, --toolsets <list>` | Comma-separated toolsets for this run. `-t memory` for a memory-only lookup. An invalid name is a hard error (exit 2). |
| `-m, --model <model>` | Per-invocation model override. |
| `--provider <name>` | Per-invocation provider override. |
| `-s, --skills <list>` | Preload skills into the session. |
| `--ignore-rules` | Skip auto-injection of `AGENTS.md`, `SOUL.md`, memory, and preloaded skills. This drops **memory injection too**, so never use it for a memory question — it is for asking a context-free question of the bare model. |
| `--safe-mode` | Disable all customization (config, rules, plugins, MCP). Troubleshooting only. |
| `-w, --worktree` | Run in an isolated git worktree. Relevant only if you let it do work, which you generally should not. |

`-c` / `--continue` and `-r` / `--resume` exist for interactive use, but do **not**
carry context into a `-z` run — verified: a `-z` follow-up after `-c` answers with
no prior history. Treat every one-shot as a cold start.

Toolset names come from `hermes tools list` (built-ins are plain names like
`web`, `memory`, `terminal`, `file`; MCP tools use `server:tool`).

## Success detection

Two distinct failure classes, and they need different checks.

**Preflight failures exit nonzero and write no usage report.** Argparse errors, an
invalid `--toolsets` value, and similar bad invocations fail before any inference:

```console
$ hermes -t nosuchtoolset --usage-file /tmp/u.json -z 'hi'; echo $?
hermes -z: --toolsets did not contain any valid toolsets.
2
$ ls /tmp/u.json
ls: cannot access '/tmp/u.json': No such file or directory
```

**Some provider failures exit 0** and print the error text to stdout as the
"answer":

```console
$ hermes -m <bad-model> -z 'hi'; echo $?
HTTP 400: {"detail":"The '<bad-model>' model is not supported …"}
0
```

That is the dangerous case: it looks like a successful consult. The report *is*
written here, with `completed: false`, `failed: true`, and `model: null`. Failures
that produce no response text exit nonzero instead. So check both signals:

```bash
hermes --usage-file /tmp/hermes-usage.json -z "<query>" > /tmp/hermes-out.txt
rc=$?
if [ "$rc" -ne 0 ] || ! jq -e '.completed == true and .failed == false' /tmp/hermes-usage.json >/dev/null 2>&1; then
  echo "hermes consult failed — fall back to asking the user"
fi
```

Report fields include `completed`, `failed`, `model`, `provider`, `session_id`,
`api_calls`, token counts, and `estimated_cost_usd`.

Also treat as failure:

- empty stdout
- output that starts with `HTTP <code>` or otherwise reads as a provider error
- a `timeout`-killed run (always wrap long consults: `timeout 240 hermes …`)

## Latency budget

Measured on a warm machine, memory-only lookups land around 10 seconds; a run
that pulls in the web or the shell takes considerably longer and is unbounded in
the worst case. Pick timeouts accordingly: `timeout 60` for a memory lookup,
`timeout 300` for a review, and always have a fallback path when it fires.

## Memory layout

Built-in memory is two Markdown files in the active profile's `memories/` dir:

| Profile | Path |
|---|---|
| default | `~/.hermes/memories/` |
| named `<name>` | `~/.hermes/profiles/<name>/memories/` |
| `HERMES_HOME` set | `$HERMES_HOME/memories/` |

Check `hermes profile list` for the active profile before grepping, so you do not
verify the wrong one.

| File | Holds |
|---|---|
| `MEMORY.md` | Learned facts about systems, projects, decisions. Entries separated by a `§` line. |
| `USER.md` | The user profile. |

Both are always active; `hermes memory status` shows injection state and whether
an external provider (honcho, mem0, …) is configured on top.

Reading these files directly is a legitimate fast path when you only need to know
*whether* a fact exists — it costs nothing and skips inference. **Writing** should
go through `hermes -t memory -z "Remember: …"`: the memory tool enforces the size
limits and makes targeted, atomic edits, where a hand-append can duplicate or
contradict an existing entry. Hand-edit only to undo a bad entry, and tell the
user you did.

`hermes journey --json` dumps the memory/skill graph as JSON (nodes with `id`,
`kind`, `timestamp`, `useCount`) — memory nodes are derived from those Markdown
chunks — and `hermes journey list` / `delete <id>` / `edit <id>` manage individual
nodes. Useful for auditing what got learned when.

## Session hygiene

Every `-z` run is recorded in the session store.

```bash
hermes sessions list                 # Preview / Workspace / Last Active / Src / ID
hermes sessions delete <id> -y       # remove one, no confirmation prompt
hermes sessions prune --help         # bulk, filterable by age/source/title
```

Occasional consults need no cleanup. If you scripted a batch of probes or test
runs, delete them so the user's `sessions list` stays readable — `Src` is `cli`
and `Workspace` is the CWD basename, which makes your own runs easy to spot.

## Other subcommands worth knowing

Read-only, safe to run from an agent:

| Command | Use |
|---|---|
| `hermes memory status` | Is memory injection on, which provider |
| `hermes tools list` | Valid `-t` toolset names, enabled/disabled per platform |
| `hermes status` | Component status |
| `hermes doctor` | Config + dependency check |
| `hermes project list` | Named multi-folder workspaces |
| `hermes kanban list` | Shared task board state |
| `hermes sessions list` | Recent sessions |

Do not run `update`, `uninstall`, `config set`, `memory reset`, `gateway`,
`dashboard`, `serve`, or anything under `auth` / `secrets` / `egress` without the
user asking. Those mutate the user's environment or touch credentials.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `argument -z/--oneshot: expected one argument` | the prompt did not immediately follow `-z` (e.g. `-z -t memory "…"`), or it was unquoted |
| Hangs forever | interactive mode (no `-z`), or a tool-heavy query with no `timeout` |
| `HTTP 400 … model is not supported` on stdout, exit 0 | bad `-m`/`--provider` override; check the usage report |
| Answer ignores repo context | wrong CWD (`AGENTS.md` is loaded from the CWD), or `--ignore-rules` |
| Answer ignores known facts | `--ignore-rules` / `--safe-mode` dropped memory injection, or `-t` excluded `memory` |
| Answer has no memory of the previous run | expected — `-z` does not resume; restate the context |
| "Remembered" but nothing stored | grep the active profile's `MEMORY.md`; re-run with an explicit "save it to memory" instruction |
| Empty stdout, exit 0 | failed run — check `--usage-file` |
| Nonzero exit, no usage report | preflight failure — bad flag or invalid `-t` toolset name |

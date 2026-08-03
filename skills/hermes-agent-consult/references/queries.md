# Query templates

Copy, fill the `<placeholders>`, run. Keep the output-shape constraint — it is
what makes the answer usable without a second round trip.

Remember: the prompt must immediately follow `-z`, so keep other flags before it.
Each run is a cold start — there is no follow-up, so every prompt has to stand
alone.

## Consult — infrastructure

```bash
hermes -t memory -z "Answer from memory, no tool calls. I'm about to <change>.
What do I need to know about <service/host> — ports, who owns the routes,
and anything that must not be restarted? Max 5 bullets."
```

## Consult — past decision

```bash
hermes -t memory -z "Answer from memory. Did I already decide on <topic>
(e.g. which <tool A> vs <tool B>) and why? If there's no decision on record,
say 'no record'. Two sentences."
```

The explicit "say 'no record'" escape hatch matters: without it you get a plausible
guess instead of an admission of ignorance.

## Consult — incident history

```bash
hermes -t memory -z "Answer from memory. Has <symptom> happened before on
<host/service>? If yes: cause, fix, and recovery order. If no, say 'no record'."
```

## Consult — cross-repo convention

```bash
cd <repo> && hermes -z "In my other projects, how do I usually handle <concern>
(<e.g. release tagging, env var loading>)? Name the pattern and one repo that
uses it. Don't modify anything. Max 3 bullets."
```

## Consult — deploy / recovery procedure

```bash
hermes -t memory -z "Answer from memory. What's the procedure to <deploy|restart|
roll back> <service>? Give it as ordered steps, plus the verification command
at the end."
```

## Teach — infra change

```bash
hermes -t memory -z "Remember this infra change: <what changed>, on <host>.
<what it means going forward, including the do-nots>. Save it to memory, then
confirm in one line."
```

Then verify the write:

```bash
rg -n '<distinctive-token>' ~/.hermes/memories/MEMORY.md   # default profile; see cli.md for others
```

## Teach — footgun

```bash
hermes -t memory -z "Remember this footgun: <action> causes <failure> because
<cause>. Recovery: <ordered steps>. Save it to memory and confirm in one line."
```

## Teach — decision + reason

```bash
hermes -t memory -z "Remember this decision: for <scope>, use <choice>, not
<rejected alternative>, because <reason>. Save it to memory and confirm in one
line."
```

## Review — diff

```bash
cd <repo> && hermes -z "Review this diff for problems. Tag each finding
High/Medium/Low with file:line. Be brief, max 3 bullets. Don't modify anything.

$(git diff -- <paths>)"
```

Scope the diff with `-- <paths>`. A whole-repo diff buries the signal and burns
context.

## Review — plan, before implementing

```bash
cd <repo> && hermes -z "I plan to <approach> in order to <goal>. Given what you
know about my setup, what breaks or what am I missing? Max 3 bullets, most
important first. Don't modify anything."
```

## Review — ops runbook

```bash
hermes -z "Here's a recovery procedure I wrote. Check the ordering and the
verification steps against what you know. Max 3 bullets.

$(cat <runbook.md>)"
```

## Anti-patterns

| Don't | Do |
|---|---|
| `hermes -z "tell me about my setup"` | name the service and the decision you are making |
| `hermes -z "$(git diff)"` on a huge diff | scope with `-- <paths>` |
| three questions in one prompt | one run per question, each self-contained |
| no output-shape constraint | "max 3 bullets", "one line", "ordered steps" |
| `hermes -z "fix the routing on <host>"` | ask what to change; you do the change |
| omitting "say 'no record'" | give it an explicit way to say it doesn't know |

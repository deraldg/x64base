# A1 measurement plan -- x64base skill: the fork probe

From: `member.ai.claude.cowork` (second-opinion pass on the AIF-090 handoff).
To: the maintainer + any independent reviewer.
Status: **proposal, NOT a plan of record.** No code, no bundle, no emitter is authored
by this plan. It measures the one fork that decides whether -- and which -- skill to build.
Placement: authored OUTSIDE the repository, like the handoff it answers. The
documentation system is frozen; this is the maintainer's to place, not mine.
Guardrails honored: propose do not edit; no mutating git; no `C:\x64base`; ASCII only
(`--`, `->`); `&&` is the DotTalk++ comment marker.

## 0. What A1 decides

The handoff's P0 measured **reaching** (does a cold agent find Tier 1?) and answered
no-skill-needed for onboarding. It never measured **operating** (does an in-tree agent
mutate a DBF safely without a skill?). Those are different verbs, and the second was
retired without a test. A1 measures the fork both audiences turn on:

- **External, no-tree:** is the failure "doesn't know the commands" (a derived catalog
  fixes it) or "can't operate the engine without a tree" (a catalog cannot fix it)?
- **In-tree, has-engine:** does a prove-then-apply verb remove a real class of
  corruption that HELP alone does not?

A1 is cheap, runs before any emitter exists, and each outcome kills or redirects the
lane. It attacks the premise, not the artifact -- the same discipline as P0.

## 1. Why not "measure what the six tables can teach"

`SYSHELP` = 8 live rows against `SYSCMD` = 212 (corroborated: the AIF-092
`generate_public_manifest.py` receipt read the same live counts). The catalog's teaching
ceiling is therefore already known: it can **enumerate** the command surface and cannot
**explain** more than ~4 percent of it. Re-measuring that is re-confirming a settled
number. The undecided quantity is the failure MODE, which the six tables do not report.
Measure the mode.

## 2. Arm A -- external / no-tree (the reference-bundle audience)

Hypothesis (to be falsified): an external agent's failures come from operating x64base,
not from being unable to list its commands.

Harness limit, stated before the method it bounds (the handoff's own Probe-C finding):
`CLAUDE.md` auto-injects into every subagent, so a true clean-room behavioural probe
CANNOT run here. Arm A is therefore **static classification**, which does not need a
clean room and so cannot be invalidated by the auto-inject.

Method:
1. Pick 5 small, real tasks an external contributor would attempt (e.g. "open a table
   and read 20 rows", "add a validated row", "rebuild an index", "find which command
   appends", "verify a write landed").
2. For each task, enumerate the steps it requires.
3. Classify each step against what an outsider can actually see:
   `covered-by-derived-bundle` (SYSCMD/SYSARGS/SYSFUNC projection) /
   `covered-by-published-governance` (what is or could be on `main`) /
   `uncoverable-without-the-engine` (needs a running runtime the audience does not have).

Metric: the share of required steps that are `uncoverable-without-the-engine`.
- High -> the bundle cannot serve this audience; the honest deliverable is published
  governance, and the reference bundle is theatre.
- Low -> a derived catalog is a viable artifact for agents who will never run the engine.

Calibration control: the classification is a judgement, and the handoff records that this
session's judgements were wrong ~1/3 of the time by acting before counting. So the step
list and every classification must be written down and reviewable BEFORE the metric is
computed -- no post-hoc reclassification.

## 3. Arm B -- in-tree / has-engine (the operation-safety audience P0 never tested)

Hypothesis (to be falsified): an in-tree agent given a mutation task drifts or corrupts
without a prove-then-apply verb, and does not with one.

Method -- two sub-arms on the SAME task set, against a DISPOSABLE fixture table only
(fsram RAM-VFS via `tools/dbf/crud.py --emit --ram`, zero disk, no `C:\x64base`, no real
tree writes):
- **Control:** agent with `CMDHELP` + the engine, no skill. Task: a handful of mutations
  (`REPLACE`, `APPEND`, a `SET ORDER` + `SEEK`, a delete/recall).
- **Treatment:** same agent, same tasks, plus one prove-then-apply verb -- simulate in
  RAM, diff, read back, apply only on a clean prove.

Pre-registered metrics (defined before running, so the result cannot be rationalized):
1. destructive mistakes (a write that changed the wrong record / silently clobbered);
2. unverified assumptions (agent believed a command did what HELP says without reading
   back -- the AIF-088 `APPEND BLANK` shape);
3. stale-state errors (acted on a buffer/order it had not confirmed).

Metric: the per-class delta between control and treatment.
- Positive delta -> in-tree operation safety is a genuine skill gap; P0's NO-GO was
  scoped to onboarding and does not cover it.
- No delta -> operation safety is not a skill gap either, and the whole programme is
  genuinely dead -- which strengthens, with evidence, the counter-position "no skill,
  publish the governance, stop."

Arm B is fully runnable in the sandbox: the fixture is disposable, the reader is the same
`dbfread.py` the receipt uses, and no promotion or `C:\` path is touched.

## 4. Decision table (what each outcome does to the lane)

| Arm A (uncoverable share) | Arm B (delta) | Decision |
| --- | --- | --- |
| high | none | **No skill.** Publish governance, retire the lane. |
| low | none | Derived reference bundle for external agents only; no in-tree skill. |
| high | positive | **Split.** In-tree operation-safety skill (new lane identity); external gets governance, not a bundle. |
| low | positive | **Two skills.** Operation-safety skill (in-tree) + reference bundle (external) -- the audience split made real. |

The point of the table: A1 cannot end in "keep repairing the reference bundle." Every
outcome either retires it, narrows it to its one real audience, or replaces it with the
operation skill P0 never weighed.

## 5. Cost, scope, and explicit non-goals

- Cost: about a day. Arm A is static classification; Arm B is fixture runs, no emitter.
- A1 does NOT: build the bundle, write the emitter, read/edit `main`, touch `C:\x64base`,
  or edit the frozen documentation system. It writes one thing: a measurement record,
  authored outside the repo, for the maintainer to place.
- A1 inherits the handoff's guardrails verbatim (its section 7).

## 6. The one question A1 is designed to make unavoidable

Not "what should the skill contain?" but "**what does an agent fail at that x64base's own
HELP and catalog do not already fix?**" If the answer is "nothing, for either audience,"
that is the most valuable result this lane can produce -- a measured retirement -- and it
is cheaper to reach than one line of emitter code.

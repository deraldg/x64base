---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260731-001
  recorded_at_utc: 2026-07-31T12:09:17Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 0803f0f135b399886591265412c56f1f506ba817
  authorization:
    requested_by: maintainer
    scope: >
      Onboard a fresh Cowork session at the AI Portal, then rate the onboarding
      experience while the cold-start impression was still intact. Owner then
      directed: take ownership as a lane, write it up properly, make sure the AI
      portal has a lane for the effort, and embed it as a PDLC.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_ONBOARDING_COST_AND_ACCEPTANCE_2026-07-31.md
    kind: session_closeout
---

# Session Closeout -- Onboarding cost, cold-start entry, and portal acceptance (AIF-082)

Opened: 2026-07-31T11:52:00Z. Last updated: 2026-07-31T12:38:28Z.
Sittings: 4 (M0 author; recursion and decrement; automation and cadence;
manifest, dogfooding, and the M1 sheet).
Run: `2026-07-31_cowork_onboarding_cost_and_acceptance`. Owner: `member.derald`.
Steward: `member.ai.claude.cowork`.
Baseline: `0803f0f135b399886591265412c56f1f506ba817` on `development`.
Owning lifecycle: maintenance SDLC (portal / onboarding surface).
SDLC lane: intake / design. Truth state: mixed. Proof state: report.

## One-line summary

A cold Cowork session onboarded through the AI Portal, measured what that cost
(127,704 bytes across nine files before it could act), found that the corpus has
no stopping rule and no falsifiable acceptance test, and opened `AIF-082` to own
onboarding cost and acceptance -- reconciled against three pieces of prior art
so it duplicates none of them.

## Scope calibration

Declared BEFORE authoring, in section 1 of the lane charter. This is the first
lane to do so; the 2026-07-30 closeout recorded retroactive declaration as a
process defect and this session treated that as binding.

```text
operating_mode: maintenance
change_class: C0 (documentation only)
build_target: documentation_only
product_profile: not_applicable
index_profile: not_applicable
```

## What was asked, in three parts

1. **Onboard.** "Go to my AI portal for onboarding."
2. **Rate it.** "Rate, your on-boarding experience or me ... What was helpful,
   what was useful, what could have been staged? What would you have liked to
   see that was missing, what could be better, what is a waste or duplication?"
3. **Own it.** "Do take ownership as a lane and write this up properly ... Make
   sure the AI portal has a lane for this effort and embed it as a PDLC."

## What was found

### The measurement that did not exist

The mandatory start path is **127,704 bytes / 2,380 lines across nine files**
(approximately 32,000 tokens) before an agent can act, rising to 152,023 bytes
with the three source-gated seeds. No figure for this existed anywhere in the
tree. It is not by itself a defect; it is the number every future decision about
adding a mandatory read should be measured against, and it was previously
unavailable to anyone making that decision.

Two components dominate and both are largely recoverable:
`AI_PORTAL.md` at 40,509 bytes, and `docs/agents/CURRENT_TARGET.md` at 23,877
bytes of which **96 percent is dated historical strata** -- 433 lines, of which
lines 1-18 are current and lines 19-433 are eighteen sections reaching back to
2026-06-29.

### The cold-start entry defect, and why it was invisible until now

`AI_PORTAL.md:29` says `AI_README.md` is the one canonical front door, then
continues for 703 more lines. `AI_README.md:23` says it is itself the one front
door. The 2026-07-29 Codex re-onboarding assessment concluded the opposite of
this lane -- "One front door ... clearly identifies itself as the canonical
start" (`:135-138`).

Both reports are honest. They diverge because the sessions entered by different
doors: Codex already knew to open `AI_README.md`; this session had one input,
the owner's phrase "my AI portal," which correctly resolves to the root file
named `AI_PORTAL.md`.

**A re-onboarding test cannot detect an entry-point defect, because the
re-onboarding agent already knows the entry point.** The portal's only prior
acceptance evidence was a re-onboarding test. This is the portal's own
resume-aid-is-not-an-entry-point rule (`AI_PORTAL.md:54-80`) applying to its own
acceptance testing.

### A reviewed recommendation that did not convert to action

`CURRENT_TARGET.md` declared AIF-072 on 2026-07-29 while the freshest work was
AIF-074; it still declares AIF-072 on 2026-07-31 while AIF-079/080/081 have
landed past it. The 07-29 assessment recorded this defect and recommended
resolving it as its gate 4.

The finding is not the staleness. It is that the recommendation did not convert,
**because the assessment was filed as a document and never opened as a lane** --
no AIF number, no claim file, no milestones, no gate. Same invisible-evidence
shape as AIF-062, AIF-078 and AIF-080, one layer out: not un-committed evidence
this time, but un-numbered work.

### The central asymmetry

The most valuable content in the corpus -- dated scar tissue attached to each
rule -- is the least needed at entry. A rule read 40 KB before it becomes
relevant will not be applied when it matters. That is why fast and complete are
not in tension: nothing needs cutting, it needs to arrive when actionable. Every
proposed remedy is constrained so that **no scar tissue is deleted**, only
re-indexed by trigger.

## Changed (development, `D:\code\ccode`)

| Area | Files | Note |
| --- | --- | --- |
| Coordination | `coordination/aif/AIF-082.claim` | Claimed via `session_coordinator.py claim-aif` (atomic `O_EXCL`) |
| Coordination | `coordination/active_sessions/2026-07-31_cowork_onboarding_cost_and_acceptance.yaml` | Session check-in, lane `AIF-082` (transient, gitignored) |
| Lane doc | `docs/maintenance/ONBOARDING_COST_AND_ACCEPTANCE_LANE_V1.md` | New `AIF-082` charter; C1-C7 findings, three-tier model, Tier-0 spec, five-question self-test, M0-M5 gates, PDLC embedding |
| This closeout | `docs/maintenance/SESSION_CLOSEOUT_ONBOARDING_COST_AND_ACCEPTANCE_2026-07-31.md` | |

**No engine source was changed. No portal document was edited.** Every remedy in
the charter is proposed, not landed.

## Verified (proof performed this session)

- **Byte/line probe**, reproducible: `wc -c` / `wc -l` over the nine mandatory
  start files at `0803f0f13`. Totals in charter section 3.
- **Structural claims carry file:line anchors** -- charter section 10 is the
  anchor table; each of C2, C4, C5, C6, C7 resolves to a named line range that
  was read, not inferred.
- **Prior-art check performed BEFORE claiming the number.** Three related
  artifacts found and reconciled in charter section 7 (C7): the 2026-07-12
  hardening lane already charters the context compiler, AIF-056 covers the
  standards seed, and the 07-29 assessment owns the freshness axis. AIF-082 was
  scoped to the one axis none of them measure.
- **Claim allocated atomically.** `CLAIMED AIF-082`; `status` reports next-free
  083 and the claim ledger carries `AIF-082.claim`.
- **House style.** Both authored files sweep clean for em-dashes, en-dashes,
  smart quotes, and Unicode arrows.
- **Tree state.** New paths are untracked; nothing staged; no existing file
  modified, so no other session's dirty work was touched.

**Explicitly NOT verified:** no build, no runtime, no `.dts`, no benchmark. The
token figures are bytes/4, a convention rather than a tokenizer result, and are
labelled as such in the charter. The five-question self-test has never been
administered to a cold agent, so the acceptance test itself is unproven -- only
a future fresh session can prove it, and this session cannot be that session.

## AI-facing docs updated (AIF-006 gate)

- **`docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- row ADDED.**
  Reversal recorded honestly: this session first decided to author the row
  without applying it, on the AIF-078 grounds that the file carries several
  sessions' uncommitted rows and a commit would fuse them. That was wrong, and
  the lane's own subject is why. AIF-080's governance finding is that a lane
  committed while its number still reads as abandoned from HEAD is the
  invisible-evidence failure; leaving the row unwritten would have reproduced it
  in a lane whose entire topic is work that stays invisible because it was never
  registered. **Fusion is a commit-slicing problem, which is the maintainer's;
  invisibility is a registration problem, which was mine.** The row is written
  to the working tree, where the collision gate can see it. The row is
  deliberately short, demonstrating the cap the charter proposes rather than
  arguing for it.
- **`docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` -- Session Log row ADDED**,
  newest-first. Noted while doing it: the newest existing row was 2026-07-30
  (AIF-079). The AIF-080 and AIF-081 sessions committed lane docs and an engine
  change without adding Session Log rows, so the dashboard is two lanes behind
  HEAD. Reported, not repaired -- those rows belong to their own sessions and
  writing them here would be a third party reconstructing work it did not do.
- **`docs/agents/CURRENT_TARGET.md` -- UPDATED on owner ruling
  2026-07-31T12:45Z.** First filed as "not updated, deliberately," on the
  grounds that a lane must not decide its own finding. The owner then ruled X1:
  **AIF-072 retired as controlling target**, still claimed and pick-up-ready.
  Top section rewritten to name the five in-flight lanes (AIF-082, 081, 080,
  079, 043 V6), the retired-but-available AIF-072, and the two unrelated owed
  items (AIF-070 allocation; missing AIF-080/081 Session Log rows). Surgical:
  one hunk, 49 added, 12 removed, lines 1 to 60 only. The historical strata
  below were left untouched because splitting them is proposal 6.5a and is
  still unruled. My section sweeps clean for house style; the 61 pre-existing
  violations in the historical strata are reported, not repaired.

  Recorded honestly: **this file will drift again.** It is hand-maintained, and
  the mechanism that would stop it is the Tier-0 staleness warning (6.1), which
  is proposed and unbuilt. That sentence is now in the file itself so the next
  reader knows the guarantee's strength.
- **`D:\dev\x64base-site/content/docs/labtalk/agent-sync.mdx` -- not refreshed.**
  Nothing an outside partner depends on changed: no lane proven, no doctrine
  altered, no Phase-0 decision made. Explicitly declined with that reason.

## Published

Reported by stage. **Stage reached: Dev, committed. NOT pushed, NOT promoted.**

| Stage | State |
| --- | --- |
| 1. Dev (`D:\code\ccode`) | **DONE.** Two commits on `development`, maintainer-operated 2026-07-31 |
| 2. Promoted to staging (`C:\x64base`) | **NOT REACHED.** Staging is not mounted in this session |
| 3. Validated in staging | **NOT REACHED** |
| 4. Pushed to `origin/development` | **DONE.** `0803f0f13..cf5ac99b8`, four commits, 37 objects, 69.67 KiB |
| 5. Published to `main` / public snapshot | **NOT REACHED**, and out of scope. Only the reviewed `C:\x64base` staging workflow may update `main` |

A fifth commit `cf5ac99b8` carries the record corrections themselves.

**A note on this table, and why Tier 0 must be generated (6.1).** This block has
now falsified itself twice in one session: it said "no commit" while sitting
inside a commit, and then said "not pushed" while being pushed. Both times the
text was accurate when written. **A hand-authored state record is wrong the
moment the next action succeeds**, and chasing each change with its own commit
trades one defect for the governance cost 6.7 is about. That is the whole
argument for generating state rather than writing it, made against this lane's
own closeout rather than against `CURRENT_TARGET.md`. Corrections after this one
ride along with the next commit that touches this file; they are not worth a
commit each.

Commits, themed rather than blobbed:

| SHA | Scope |
| --- | --- |
| `1024a53d5` | `docs(AIF-082): onboarding cost and acceptance lane` -- claim, charter, closeout, M1 ruling sheet, and the two registry rows |
| `8a3dea347` | `docs(AIF-082): tier 1 seed, retrieval lesson, WSL rules, retire AIF-072 as target` -- 5 files, +411/-12, creating `labtalk/ai_portal/AI_TIER1_SEED_V1.md` |
| `71f9b850e` | `docs(agents): WSL/dottalkpp handoff, and publish the front door's own onboarding files` -- 3 files, +431, all creates. Lands the handoff whose absence caused C8, plus `AI_BABY_BOOTSTRAP_CARD.md` and `docs/agents/README.md`, both reachable from `AI_README.md` and previously invisible to a clone |
| `554891db5` | `docs(AIF-082): Cowork onboarding handoff, observability boundary finding, website concurrency gap` -- creates `docs/agents/HANDOFF_CLAUDE_COWORK_ONBOARDING_2026-07-31.md` (8,839 B) |
| `3550705dd` | `docs(AIF-082): handoff obligation becomes a gate, created_utc policy adopted (M1 group A follow-ups)` -- 3 files, +111/-7. `AI_PORTAL.md` gains "Leave a Handoff as well"; `SESSION_CLOSEOUT_TEMPLATE.md` gains a "Handoff left" field |

`prepush_gate.py` returned **PASS** on both: source/docs/config only, no embedded
BOM, no AIF-number collision. `repository_role_guard.py` passed host-side,
confirming this session's sandbox false-block diagnosis. The three
`audit_trail.py` advisories are pre-existing findings against the 2026-07-28 Grok
external-intake manifest and are not attributable to this lane; enforced records
are `74 valid=74 findings=0`.

**The steward did not commit.** All git was maintainer-operated from the host,
per the sandbox rule this session learned the expensive way (5b).

## Addendum 4 -- sixth sitting, 2026-07-31T18:04Z: a hyperlink, and the observability boundary

The maintainer ran a parallel task on `D:\dev\x64base-site`: link two existing
static report pages into the site nav. Two lines of config. It consumed most of
an afternoon, and this steward caused the bulk of the overrun.

**Root cause was a browser cache** holding a stale nav page. The build, the
links, the file and the server were all correct well before the symptom cleared.

**What the cost actually was.** Not investigation -- investigation on the wrong
side of an observability boundary. The steward could read the filesystem and
reasoned from it for a dozen turns (relative-link resolution, trailing slashes,
stale builds, file locks, ACLs) while the two decisive facts lived in systems it
could not see: whether anything was listening on port 3000, and what URL the
browser actually requested. Each was one command. `Get-NetTCPConnection`
eventually reported nothing listening at all, and the server's own request log
settled the rest the moment it was consulted.

Recorded in the charter at 6.7 as the second observed instance, with the
generalization: **when a system is partly observable, spend the first move
crossing the boundary, not reasoning inside it.** Evidence you can reach is not
evidence about the thing that is failing, and a confident chain built on the
reachable half is worse than silence because it looks like progress.

**Third instance of one shape today, all by this steward:** the mount/git rule
read during onboarding and then violated within the hour (5b); the `docs/agents`
tracking split predicted and wrong (item 9 below); and this. None was a
knowledge failure. All three were acting on the evidence at hand instead of the
evidence that mattered.

The maintainer's challenge is recorded verbatim because it is the fair test of
this lane: *"its a frigging hyperlink, if you can't handle this what makes you
think you can handle ai onboarding."* AIF-082 is worth something only if it makes
that specific failure less likely. Today it did not make it less likely in its
own author, and 6.4's self-test would not have caught it -- which is an argument
for 10a's position that acceptance must be a worked task rather than a quiz.

Also recorded: two agents were editing `D:\dev\x64base-site` concurrently, and
this steward stopped short of writing `config/nav.ts` only because it read the
file first and found the other session had already fixed it. The website tree
has no equivalent of the ccode coordination protocol. Flagged, not solved.

## Addendum 5 -- handoff left in the tree, 2026-07-31T18:20Z

`docs/agents/HANDOFF_CLAUDE_COWORK_ONBOARDING_2026-07-31.md`, written on owner
instruction. This discharges the obligation C8 identified and 6.5g proposes: a
session that learned how to work here leaves a handoff, not only a closeout.
Companion to the maintainer's WSL handoff rather than a duplicate of it -- that
one covers build, run, DotScript and capture; this one covers the portal, the
sandbox boundary, and working with the maintainer.

It carries one thing that belongs in a handoff and nowhere else, recorded on the
owner's feedback: **his environment is authoritative, and a correction about it
is not an invitation to analyse.** Twice today the steward was handed a fact
about his own setup -- where the reports actually live, and that his server root
needed no directory prefix -- and answered with a framework instead of an
adjustment. The stated tell: if he states a fact and the reply begins by
categorising it, the agent has stopped listening.

The complementary half is recorded with equal weight, because he asked for it
explicitly: **he wants pushback on substance.** The worked example is a parallel
session refusing to publish `BBS_ACCESS_REPORT.html` against his own AIF-060
publication note. Deference there would have put an auth-surface map on the
public web. The distinction is between resisting a correction about his
environment, which is never right, and resisting a step that would damage the
record, which is the job.

Also recorded there: shell and working directory belong at the top of every
command block, two repositories are in play and are not interchangeable, and
proportionality remains uncalibrated in the corpus.

## Recorded for the record -- first clean registration (positive finding)

`1024a53d5` and `8a3dea347` are, as far as this session can determine, **the
first commits in this project where a lane's number, claim file, intake row,
dashboard Session Log row, charter, and closeout all landed together rather than
trailing the work.**

That matters because the opposite is this tree's most-repeated governance defect,
recorded three times before this lane opened: AIF-062 (evidence hidden by a
blanket ignore), AIF-078 (queue rows written and never committed, so the same
numbers re-derived as free), and AIF-080 (charter and engine change committed
while the number still read as ABANDONED from HEAD). The pre-push gate advisory
"claim(s) with no intake row" existed precisely to catch it and was being
observed rather than acted on.

The fix was not a new mechanism. Every tool needed already existed --
`claim-aif`, the collision gate, the intake queue, the dashboard. What changed is
**ordering**: claim first, register second, work third, close out fourth. The
collision gate confirms it, reporting AIF-082 absent from the abandoned-claim
advisory while AIF-068 and AIF-070 remain listed.

Recorded as a positive control for AIF-082's own thesis: the corpus did not need
better content here, it needed the rule to arrive before the work rather than
after it. That is the same claim as section 5b, with the sign reversed.

## Still open -- for the next session

1. **M1 owner rulings.** Charter section 6 has five remedy groups; each is
   independently accept/reject/defer. Nothing proceeds without them.
2. **Commit slicing for the two shared files -- fusion risk MEASURED, not
   assumed.** Both files were already dirty before this session touched them:

   - `AI_INTERACTION_INTAKE_QUEUE_V1.md`: the **AIF-081 row** differs from HEAD
     (its evidence-anchor column was enriched after that row was committed).
   - `AI_FRIENDLY_DASHBOARD_V1.md`: the **AIF-063** Current-Lane-State row
     changed date 2026-07-26 to 2026-07-27, and rows for **AIF-068** and
     **AIF-069** were added.

   `git add` on either file therefore fuses another session's in-flight work
   with AIF-082's. Both AIF-082 additions are strictly additive and contiguous,
   so a path-scoped or hunk-scoped commit can separate them. Maintainer call.
   Verified this session that the AIF-081 row was already in its worktree form
   before the AIF-082 row was inserted, so none of that delta is attributable
   here.

   Also owed by their own sessions, not repaired here: AIF-080 and AIF-081 have
   no Session Log rows, leaving the dashboard two lanes behind HEAD.
3. **The AIF-072 question, now twice-recorded and still open.** Does AIF-072
   remain the controlling target, or does the freshest lane get promoted into
   `CURRENT_TARGET.md`? Recommended either way: whatever the answer, the
   staleness warning in Tier 0 (charter 6.1) is what stops it recurring a third
   time.
4. **M2, the Tier-0 generator** -- unstarted, and it belongs to
   `AI_PORTAL_HARDENING_LANE_V1.md` as its packet-compiler milestone rather than
   to this lane.
5. **The self-test is a draft** and must be administered to a genuinely cold
   agent to be worth anything.
6. **Inherited from the 07-29 assessment, still owed on the freshness axis:**
   the ten unresolved registry paths remain unclassified, and `latest`-named
   reports still lack generated-at stamps.
7. **AIF-070 allocation** remains owed from AIF-078; unrelated to this lane but
   still unclaimed.
8. **RESOLVED 2026-07-31T14:25Z -- the WSL handoff is committed.** It was blocked
   twice: first by the stale `index.lock` this session created (5b), then by
   simply not being retried. Landed in `71f9b850e`. **C8 is now closed by
   action**: the artifact written specifically to onboard the next agent is in
   the tree, alongside the two front-door files that were also invisible. The
   finding stands as recorded; the instance is fixed.
9. **`docs/agents/` is half-published -- MEASURED 2026-07-31T14:20Z, and both
   prior predictions were wrong.** `git ls-files docs/agents/` returns two paths
   against seven files on disk:

   | State | File | Named by the front door? |
   | --- | --- | --- |
   | tracked | `CURRENT_TARGET.md` | yes, step 1 of the ordered table |
   | tracked | `HANDOFF_CODEX_BUFFER_VISIBILITY_2026-07-29.md` | no |
   | **untracked** | `AI_BABY_BOOTSTRAP_CARD.md` | **yes** (`AI_README.md:27,:66`) |
   | **untracked** | `README.md` | directory index |
   | **untracked** | `HANDOFF_CLAUDE_WSL_DOTTALKPP_2026-07-31.md` | the current handoff |
   | **untracked** | `HANDOFF_CLAUDE_FOUNDATIONS_SOURCE_PACKET_2026-07-26.md` | no |
   | **untracked** | `HANDOFF_CLAUDE_MESSAGING_CORRECTIVE_AUDIT_2026-07-16.md` | no |

   The maintainer's draft commit message said the directory is "entirely
   untracked" -- false, two files are tracked. This steward predicted the split
   was "handoffs untracked, `CURRENT_TARGET.md` tracked" -- also false, since one
   handoff is tracked. **Neither guess survived one command.** Recorded because
   the lane's own rule is measure rather than infer, and two people inferred.

   The accurate and sharper claim: **`AI_README.md` names
   `AI_BABY_BOOTSTRAP_CARD.md` as onboarding material at two places
   (`:27`, `:66`) and that file is invisible to a clone**, as is the directory's
   own `README.md`. This is C8 with numbers: the onboarding directory does not
   publish its own onboarding material. It is inconsistency rather than policy --
   one handoff was tracked, so somebody has committed one before.

   **Partly resolved in `71f9b850e`:** the WSL handoff,
   `AI_BABY_BOOTSTRAP_CARD.md`, and `docs/agents/README.md` were published, so
   the directory now tracks 5 of 7 and every file the front door names is
   reachable from a clone. **Still untracked, owner call, historical:**
   `HANDOFF_CLAUDE_FOUNDATIONS_SOURCE_PACKET_2026-07-26.md` and
   `HANDOFF_CLAUDE_MESSAGING_CORRECTIVE_AUDIT_2026-07-16.md`.

## Addendum -- second sitting, 2026-07-31

Appended rather than folded into the sections above, so the first sitting's
report stays as filed and audited. Charter grew from 26,869 to approximately
40 KB; no other file changed.

Owner raised two things after the closeout was filed: that the project
recursively refines its processes as it optimizes them, and whether onboarding
can be automatic and how often it must repeat in a session persisting for days.
Both were answered into the charter as new sections, and both changed the lane's
shape rather than decorating it.

**6.6 -- the decrement operator.** The refinement loop only adds. C1's 127,704
bytes are the product of eighty lanes of individually correct decisions, which
is why a one-off cleanup does not fix it. Proposed rule: when a rule becomes
mechanically enforced, its prose demotes one tier, because the gate is now the
memory. Five conversions from prose to mechanism already exist in the tree
(shadow guard, pre-push gate, claim allocator, envelope audit, manual drift
gate) and **not one demotion has ever been collected.** Strict test: only a
HARD-failing gate earns a demotion, since this tree contains dormant and
advisory gates that would be mis-demoted. That makes 6.6 depend on AIF-079 M1 --
the declared-capability validator is what proves a gate enforces rather than
merely exists.

**6.7 -- governance cost is the unmeasured second axis.** C1 measured entry cost;
nothing measures run cost. This lane executed twelve mandatory governance
actions. `SCOPE_CALIBRATION_SEED_V1.md:11-24` calibrates PROOF gates by change
class and says nothing about GOVERNANCE gates, so a C0 doc lane and a C3 engine
lane pay identically. Recorded as an estimate, not a measurement; M6 is the
probe.

**6.8 -- automation and cadence.** State and rules have opposite refresh
profiles and the corpus fuses them. Automatic Tier 1 already exists and works:
`CLAUDE.md` is injected without being fetched and is the best file in the tree.
Its defect is vendor fragmentation -- `CLAUDE.md` 4,314 B against `AGENTS.md`
1,496 B, so two partners onboard to different depths by accident. Cadence is
event-driven, not clock-driven, because the invalidator here is concurrency on a
shared working tree, not elapsed time.

**A gap in this session, recorded against itself.** Tree state was read at
approximately 11:50 UTC and asserted in closeout claims at 12:09 UTC with no
re-check for newly active sessions between. Nothing went wrong, but the
verification was valid for 11:50 and was reported as current. Correct procedure
would have produced a false statement had a concurrent session touched those
files in the interval. This is now cadence rule 2 in 6.8.

**And the signal that rule depends on is degraded.** `status` reported three
active sessions of which two were stale by 765 and 1,095 minutes, and this
session's own `checkout` failed to deregister because the mount refuses deletes
(`LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42`), leaving a third false positive.
Heartbeats are emitted, nothing consumes staleness, and retraction is
unreliable. Repairing that is a precondition for the cadence rule, added as M8.

Milestones M6, M7, M8 added.

## Addendum 2 -- third sitting, 2026-07-31

**5a, framing correction on maintainer direction ("huge documentation is our
meat and potatoes").** Accepted and written in as a section rather than a note,
because a future reader could otherwise take this lane as an argument for less
documentation, which would damage the project's principal asset. Corpus size is
the product; entry-path size is the cost; the two are different quantities and
this lane only ever addressed the second. Nothing in section 6 reduces the
corpus -- the decrement operator demotes a tier and deletes nothing, and the
structural items move strata to a sibling file. The work is cataloguing, not
pruning. Lane position now stated in one sentence: **keep every byte, stop
making the entry path carry all of them.**

**6.9, refresh by diff on a required read manifest.** Owner proposal. Prior-art
checked: no such mechanism exists. It plugs into `AI_README.md:363-375`, whose
`Files read:` field is already required and currently unverifiable prose -- this
session filled it from memory. One blind spot recorded and it is load-bearing:
**a diff detects edits, not staleness.** `CURRENT_TARGET.md` has not changed
since 07-28 and that is exactly why it is wrong, so a hash-only refresh would
report green about a document three lanes behind. Refresh therefore needs two
signals, hash-compare plus the Tier 0 staleness warning. Placement: not `tmp/`
(AIF-081 proved that is how evidence goes invisible), not committed (churn), but
`coordination/active_sessions/`, which is transient, shared, and already built
for exactly this. Must be a gate, not a discipline: the Tier 0 pull emits the
manifest as a side effect and the closeout gate validates it -- which would have
caught this session's 11:50-asserted-at-12:09 gap mechanically instead of by
confession. It also supplies the instrument M4 was missing.

**6.10, dogfooding the store.** Owner direction. The manifest's authority belongs
in the DBF store on the memo/64-bit object structure, sitting directly on the
house thesis that documentation consumes and proves the database. The workload is
complementary rather than a toy: few records with large variable-length memo
payloads, append-heavy, which is the opposite shape to AIF-046's wide fixed-width
scans and is where the 64-bit memo work actually gets stressed. **Bootstrap
paradox identified and resolved:** onboarding must never require a running engine
or a live daemon, or the portal can lock out the agent it exists to admit, so the
store is authoritative and a generated flat projection under 4 KB is what a cold
agent reads. **Scope discipline recorded:** the storage design is NOT AIF-082's to
build. This lane specifies the interface and the projection requirement and hands
the schema, memo work, and durability proof to the owning memo lane with its own
number and its own Phase-0. Folding an engine workload into a documentation lane
would make AIF-082 the thing it criticises.

Milestones M9, M10 added.

**6.10 gate strengthened on maintainer acknowledgement of the bootstrap catch.**
"Engine down, daemon down" was not the real floor. The Outside-AI Delivery Rule
(`AI_PORTAL.md:433-451`) admits hosted partners with no disk and no shell, so the
weakest admitted partner sets the constraint: **Tier 0 must be a persisted
artifact left behind by the last tool run, never generated on demand by the
reader.** A generate-on-read design would silently re-tier the portal to local
agents only and drop the hosted partners that rule exists to serve. Generalized
for reuse against any future entry-path proposal: an onboarding step may not
require a capability the least capable admitted partner lacks; anything richer
than reading a file is a convenience layer over the projection, never the
projection itself. M10's gate updated from "engine down and daemon down" to
"readable with no execution capability at all."

**6.5e added on maintainer correction, 2026-07-31T12:38Z: headers need a
timestamp, not a bare date.** This lane had four sittings in one day and
`date: 2026-07-31` cannot order them, nor order this lane against AIF-080 and
AIF-081 which share their filename date. The envelope already solved this --
`recorded_at_utc` is full ISO-8601 UTC and `audit_trail.py` enforces it -- but
the human-readable header blocks never inherited the convention, so the machine
surface is ordered and the human surface is not. 66 files under
`docs/maintenance/` carry a bare-date header. This lane's three documents were
converted to `created_utc` / `updated_utc` immediately; the remaining sweep is
6.5e on the ruling sheet. Filenames keep their date, being identifiers rather
than ordering keys.

**M1 ruling sheet authored** (`docs/maintenance/AIF_082_M1_RULING_SHEET_V1_20260731.md`,
7.3 KB against the 51.5 KB charter). The gate had no instrument: reviewing ten
proposals by reading the charter would have repeated the defect the lane exists
to fix. Sheet carries a three-item fast path, per-item cost and reversibility,
recommendations, a KILL option, and a ruling record table.

Still no portal document edited, no tool built, no engine source touched,
nothing staged, nothing committed.

## Addendum 3 -- fifth sitting, 2026-07-31T13:10Z: portal documents edited

Prior addenda all reported "no portal document edited." That is no longer true.
Owner directed the lesson and the WSL rules be written into the onboarding
surface, so three portal-tier files were modified. Recorded separately because
it is a change in this session's mutation posture, not just more findings.

**`AI_PORTAL.md`** -- added a third case study to "Observed failure modes
(proven case studies)": *Retrieval failure -- a canonical copy nobody can
reach.* Placed there deliberately, because it EXTENDS the section's closing
sentence rather than sitting beside it: the two existing cases are about having
too many copies, this one is about having exactly one, correct, and unreachable.
Carries C6/C7/C8, the first-person proof from 5b, four corollaries, and the
maintainer's evaluation-method rule.

**`AI_README.md`** -- new "WSL working environment" section under Runtime Start
Points: `wslbuild.sh` invocations, the `wsl-lean` preset and staging path, the
four rules that have each already cost a session (no vcpkg manifest swap,
`ninja: no work to do` is not proof, `SET ALTERNATE` not `DOTSCRIPT OUT`, traces
default ON), and a "**A sandbox is not the WSL host**" subsection with the
measured host-vs-sandbox table and the no-git rule.

**`CLAUDE.md`** -- new "Sandbox agents: NO git, and you cannot build" section.
Placed here specifically because `CLAUDE.md` is **auto-injected into an agent's
context at session start**, so this is the only surface where the rule arrives
before the mistake rather than after. That placement IS the lane's thesis
applied: the rule now fires at the moment it constrains an action.

**Method claim recorded as lane section 10a**, on maintainer observation that
working the system is what teaches it. Every finding this lane produced came
from performing the process, not reviewing it, and the 2026-07-29 assessment is
the control group -- same corpus, careful inspection, none of these findings,
because an inspection reads documents while working the system exercises the
paths between them. Consequence carried into M4: the acceptance test must be a
real task, not a quiz. A quiz checks that onboarding happened; only a worked
task checks that it sufficed.

**New finding while verifying style, 6.5h.** `CLAUDE.md:54` forbids em-dashes.
Measured: `AI_PORTAL.md` carries 88 em-dashes and 7 unicode arrows,
`CURRENT_TARGET.md` 50 and 11, `AI_README.md` 7. A declared rule with no gate,
which is the AIF-079 declared-capability class applied to prose. **Reported, not
repaired** -- a bulk character sweep across portal documents is its own scoped
slice and would fuse with this one. Proposed gate checks changed doc lines only,
so the backlog never blocks work while new violations become impossible.

All content authored this session is ASCII-clean under the stricter
`grep -P '[^\x00-\x7F]'` test, including every inserted block in the three portal
files. Pre-existing violations in those files are reported above and untouched.

Still no tool built and no engine source touched. (Written before the commits;
the current stage is in "Published" above, which supersedes the
"nothing committed" statements in these addenda.)

## Provenance pointers

- Lane charter: `docs/maintenance/ONBOARDING_COST_AND_ACCEPTANCE_LANE_V1.md`
- Claim: `coordination/aif/AIF-082.claim`
- Prior art reconciled: `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md`
  (2026-07-12, context compiler);
  `labtalk/ai_portal/AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md`
  (freshness axis, six recommended gates adopted by reference);
  AIF-056 onboarding hardening,
  `docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_ONBOARDING_HARDENING_2026-07-25.md`
- PDLC model: `docs/maintenance/PDLC_STUDENT_WORKING_MODEL_LANE_V1.md`
- Process precedent for up-front scope calibration:
  `docs/maintenance/SESSION_CLOSEOUT_HOUSE_INDEX_VDISK_AND_CAPABILITY_VALIDATOR_2026-07-30.md`
  section 5
- Doctrine: `AI_PORTAL.md` (AIF-006 closeout-updates-startup; AIF-024
  document-as-you-work; AIF-037 representative by design; falsifiable-target
  rule at `:339-341`)

---

## Addendum F -- 2026-07-31T22:40Z: M4 run 1, C8b, and the R27a tracking campaign

Appended after the closeout's original filing. Three things happened that change
the lane's state; charter sections 11 and 12 carry the detail.

**1. M4 run 1 executed. NOT a pass, and the fault is the instrument.** A cold
subagent, given a real owed task with no test tell, applied ten house conventions
unprompted -- three of them authored the same day -- and found two live defects
of mine. But it never produced the Minimal New-AI Checklist (neither did cold
agent 1: two for two), and it spent 117 K tokens against a 10,324 B entry path
with no read-log, so the causal claim is unavailable. **M9 is now a measured
prerequisite of M4, not an argued one.** Rulings R25/R26 opened.

**2. C8b: the `mandatory-tracked` gate has a self-drawn denominator.** It passed
in every commit this session while roughly 1,100 untracked source files entered
history, because its universe is derived from `AI_README.md` and `AI_PORTAL.md`
(`check_mandatory_tracked.py:36`). Its output never changed: `45 document(s) and
11 script(s)`, PASS, throughout. Ruling R27 opened, then split into R27a (track
the pipeline) and R27b (invert the gate).

**3. R27a executed and complete.** Commits `7a4d062ae` (fullstack_docs, 43),
`358687b2f` (locale, 85), `4f3477608` (messaging, 869 / 111,400 insertions),
`4acfa853d` (root scripts, 10), plus manualgen, datadict, tests, staging and the
small helpers. The repo-to-site publication bridge
(`stage_assembled_manual_to_site.py`) is now under version control at both ends.

**Cross-lane finding, and the strongest argument for having done it.** The
newly-tracked `tools/messaging` carries a confirmed, isolated **general DOTSCRIPT
shutdown exit crash** with a fix plan held at gate `10DT`. AIF-083 M2's only
delivery mechanism is a runtime transcript, and it now has two documented hazards
from two lanes that did not know of each other -- AIF-081's `DOTSCRIPT ... OUT`
discarding `cmdout`, and this crash truncating the run. **Both bias M2's evidence
toward a false negative**, which is precisely the direction that would have had
me score F1 and F2 as runtime-confirmed on absent output.

### Honest ledger of my own errors this session

Recorded because the lane's standard requires it and because the pattern is the
finding, not the individual slips:

| # | Error | Caught by |
| --- | --- | --- |
| 1 | `check_session_log_row.py` counted closeouts, not lanes | the cold subagent |
| 2 | `recall.py` summed whole files, not sections (6x overstatement) | a falsification pass |
| 3 | `check_mandatory_tracked.py` universe drawn from itself | a `git status` tail |
| 4 | predicted a 60-file slice that was 43 (disk vs untracked) | the commit output |
| 5 | derived datadict slice sizes by division; `catalog` was 145, not ~17 | the mass-change gate |
| 6 | commit loop with no failure handling -- fused on first block | the mass-change gate |
| 7 | `git status --short` given as a staged-only check twice | the maintainer running it |

Six of seven are one error: **a denominator drawn from my own expectations rather
than from the system being measured.** Error 5 is the sharpest because division
feels like derivation, and error 6 followed three messages after I warned against
the exact hazard it caused. Writing the warning did not prevent the behaviour.

That is the lane's own thesis turned on its author, and it is worth more to the
portal than a clean record would have been: the remedy for this class is never
discipline, it is a gate whose denominator comes from outside. Every one of these
was caught by an external check or another party. None was caught by me being
careful.

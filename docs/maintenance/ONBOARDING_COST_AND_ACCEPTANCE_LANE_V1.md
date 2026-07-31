# Onboarding Cost and Acceptance Lane V1

    lane        : AIF-082
    claim       : coordination/aif/AIF-082.claim
    run         : 2026-07-31_cowork_onboarding_cost_and_acceptance
    owner       : member.derald
    steward     : member.ai.claude.cowork
    opened_utc  : 2026-07-31T11:52:00Z (Cowork)
    updated_utc : 2026-07-31T12:38:28Z
    sittings    : 4 on 2026-07-31 (M0 author; recursion/decrement; automation/cadence; manifest/dogfood + M1 sheet)
    baseline    : 0803f0f135b399886591265412c56f1f506ba817 (development)
    parent      : project.labtalk.campus (lane `ai_portal`)
    status      : findings measured, NO source change landed, NO portal doc edited
    evidence    : C1 measured (byte/line probe, this tree, this commit)
                  C2 measured
                  C3 measured
                  C4 source-evidenced (file:line)
                  C5 source-evidenced (file:line)
                  C6 observed (this session's own entry path)
                  C7 source-evidenced (prior-art reconciliation)

---

## 0. Origin and authorization

The owner asked a fresh Cowork session to onboard at the AI Portal, then asked
it to rate the experience while the impression was still cold, then assigned the
result as a lane and directed that it be embedded as a PDLC.

The session that produced this lane IS the measurement instrument. It entered
with no prior context, no chat history, and one input: the phrase "my AI portal."
That entry condition is the thing this lane exists to measure, and it has never
been measured before (C6, C7).

Authorization: owner, in chat, 2026-07-31, verbatim -- "Do take ownership as a
lane and write this up properly ... Make sure the AI portal has a lane for this
effort and embed it as a PDLC."

---

## 1. Scope calibration (declared BEFORE authoring, not retroactively)

```text
operating_mode: maintenance
change_class: C0 (documentation only; no behavioral change; no engine source)
build_target: documentation_only
product_profile: not_applicable
index_profile: not_applicable
owning_lifecycle: maintenance SDLC (portal/onboarding surface)
sdlc_lane: intake / design
truth_state: mixed -- measured (C1-C3), source-evidenced (C4-C5, C7), observed (C6)
proof_state: report (byte/line probe + file:line anchors). NO build, NO runtime,
  NO .dts executed this session.
risk_class: low. The lane proposes changes to onboarding documentation; it
  changes none of it in this session.
scope_reason: The deliverable is a lane charter and a measurement. Nothing in
  the engine, data, HELP, metadata, or website is touched.
affected_authorities: AI_PORTAL.md, AI_README.md, docs/agents/CURRENT_TARGET.md,
  docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md,
  labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md,
  labtalk/ai_portal/AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md
minimum_gate_set: measurement reproducible from the recorded commands;
  every structural claim carries a file:line anchor; prior-art reconciliation
  before any new lane number is defended; house style sweep.
optional_educational_gates: the PDLC embedding in section 7 is deliberately
  instructional depth, recorded as such per SCOPE_CALIBRATION_SEED_V1.
deferred_gates_and_residual_risk: no tool built, no portal document edited, no
  acceptance test executed. Every remedy in section 6 is PROPOSED, not landed.
  The lane has earned no runtime tier and says so on its face.
```

This block exists at the top rather than the bottom because the 2026-07-30
closeout recorded declaring it retroactively as a process defect
(`SESSION_CLOSEOUT_HOUSE_INDEX_VDISK_AND_CAPABILITY_VALIDATOR_2026-07-30.md`
section 5). This lane is the first to declare it before planning.

---

## 2. The claim under measurement

> The portal's onboarding corpus is CORRECT and EXPENSIVE, and it has no
> stopping rule. Correctness has been tested. Cost has never been measured, and
> completion has never been made falsifiable.

Three sub-claims, each independently checkable:

1. **Cost is high and unmeasured.** No figure for the size of the mandatory
   start path exists anywhere in the tree before this document.
2. **There is no stopping rule.** Nothing tells an agent when onboarding is
   done. `AI_README.md:31` says "stop when you have enough for the task," which
   is unusable when there is no task yet -- the exact condition of a cold start.
3. **Completion is not falsifiable.** The portal demands falsifiable targets for
   Phase-0 work (`AI_PORTAL.md:339-341`) but sets none for its own onboarding.
   An onboarding that cannot fail cannot be improved against evidence.

---

## 3. Measured findings

Probe run 2026-07-31 against this tree at `0803f0f13`, WSL mount, `wc -c` /
`wc -l`. Token figures are bytes/4, a convention, not a tokenizer result; they
are order-of-magnitude only and labelled as such.

### C1 -- The mandatory start path is ~128 KB before an agent can act

| Step | File | Bytes | Lines |
| --- | --- | ---: | ---: |
| entry | `AI_PORTAL.md` | 40,509 | 732 |
| 0 | newest `SESSION_CLOSEOUT_*` (07-30) | 20,104 | 197 |
| front door | `AI_README.md` | 14,634 | 419 |
| 1 | `docs/agents/CURRENT_TARGET.md` | 23,877 | 433 |
| 2 | `DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` | 8,620 | 193 |
| 3 | `LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` | 8,727 | 153 |
| 4 | `SDLC_FAST_START_SEED_V1.md` | 3,843 | 100 |
| 5 | `SCOPE_CALIBRATION_SEED_V1.md` | 3,076 | 76 |
| house | `CLAUDE.md` | 4,314 | 77 |
| | **TOTAL** | **127,704** | **2,380** |

Approximately 32,000 tokens. Adding the three source-gated seeds (steps 6-8)
brings it to 152,023 bytes, approximately 38,000 tokens, before a single line of
source has been read.

This is the figure that did not exist. It is not by itself a defect -- a large
corpus can be the correct answer. It is the number every later decision in this
lane is measured against, and it was previously unavailable to anyone deciding
whether to add one more mandatory read.

### C2 -- `CURRENT_TARGET.md` is 96 percent historical strata

433 lines. Lines 1-18 are current. Lines 19-433 are eighteen dated sections
reaching back to 2026-06-29, including "Previous Objective Resolution"
(`:284`), "Staging State -- RESOLVED 2026-07-14" (`:320`), and a "History"
section (`:418`) that exists to explain a target already closed as stale.

The file's own header (`:5`) says "Supersedes: the completed staging-restoration
/ publication target recorded below" -- and then retains it. An agent reads 433
lines to obtain 18 lines of signal, and the signal is stale anyway (C3).

### C3 -- The declared target has been stale across two independent assessments

| Date | Assessor | Declared target | Freshest actual work |
| --- | --- | --- | --- |
| 2026-07-29 | Codex | AIF-072 | AIF-074 SQLSEL |
| 2026-07-31 | Cowork (this) | AIF-072 | AIF-079 / 080 / 081 |

The 07-29 assessment
(`AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md:177-181`) recorded this exact
defect and recommended, as its gate 4 (`:228`), deciding whether AIF-072 remains
controlling. Two days later `CURRENT_TARGET.md` is unchanged and three further
lanes have landed past it.

**The finding is not the staleness. The finding is that a recorded, reviewed
recommendation did not convert into an action, because the assessment was filed
as a document and never opened as a lane** -- no AIF number, no claim file, no
milestones, no gate. See C7.

### C4 -- Two documents each declare themselves the single front door

- `AI_PORTAL.md:29` -- "`AI_README.md` is the one canonical front door. Follow
  its ordered table first."
- `AI_README.md:23` -- "## THIS FILE IS THE ONE FRONT DOOR"

Both statements are reasonable in isolation. Together they mean the portal
redirects at its own line 29 and then continues for 703 more lines. An agent
that obeys the redirect at line 29 skips the doctrine below it; an agent that
reads linearly (what this session did) pays 40 KB before reaching the file it
was told to start with. Neither behaviour is wrong, and that is the problem: the
corpus does not determine its own entry order.

### C5 -- Two overlapping mandatory field blocks, no stated precedence

- `SDLC_FAST_START_SEED_V1.md:32-57` -- "Mandatory Task Fields", 20 fields.
- `SCOPE_CALIBRATION_SEED_V1.md:11-24` -- an unnamed required block, 10 fields.

Seven field names appear in both (`operating_mode`, `change_class`,
`build_target`, `product_profile`, `index_profile`, `scope_reason`, and the
gate/authority pairing). Neither document states whether one nests inside the
other, whether filling one satisfies the other, or which wins on conflict. A
cold agent must guess. This session guessed (it filled the union, section 1)
and cannot prove the guess was right.

Related, retained-superseded: `AI_README.md:59` carries an 11-item numbered
"Start Here (legacy list -- superseded by the table above)", retained "for
continuity" (`:56`). A numbered list under a "Start Here" heading is an
instruction regardless of the disclaimer above it.

### C6 -- The portal has been tested by RE-onboarding, never by COLD onboarding

This is the finding that only a genuinely cold session could produce, and it
explains a direct contradiction between this lane and the 07-29 assessment.

The 07-29 assessment concluded (`:135-138`): "One front door. `AI_README.md`
clearly identifies itself as the canonical start." This lane concludes the
opposite (C4). Both are honest reports. They differ because the two sessions
**entered by different doors**:

| | 07-29 Codex | 07-31 Cowork (this) |
| --- | --- | --- |
| Prior context | had worked the tree before | none |
| Entry input | knew to open `AI_README.md` | the phrase "my AI portal" |
| First file opened | `AI_README.md` | `AI_PORTAL.md` |
| Verdict on front door | unambiguous | two doors collide |

An agent given the owner's own spoken phrase resolves it to the file named
`AI_PORTAL.md`, at the repository root, whose title is "x64base AI Portal." That
is the correct resolution of the words, and it lands on the document that says
the front door is elsewhere.

**A re-onboarding test cannot detect an entry-point defect, because the
re-onboarding agent already knows the entry point.** The portal's only prior
acceptance evidence is a re-onboarding test. Its cold-start path was therefore
unproven until this session, and the first cold traversal found a collision the
warm traversal could not see.

This is the same shape as the portal's own recorded lesson at
`AI_PORTAL.md:54-80` -- a hand-off record is a resume aid, not an entry point.
That rule was written about session records. It applies equally to acceptance
tests: **a resume test is not an entry test.**

### C7 -- Prior art exists, is complementary, and was not registered as work

Checked before claiming AIF-082, per the AIF-078 rule that a design registered
nowhere gets done twice. Three related artifacts exist:

| Artifact | Date | AIF | Axis | Status |
| --- | --- | --- | --- | --- |
| `AI_PORTAL_HARDENING_LANE_V1.md` | 2026-07-12 | none | architecture: portal as "proof-aware context compiler", "assemble a bounded task context packet" (`:38-45`) | Alpha, unbuilt |
| AIF-056 onboarding hardening | 2026-07-25 | AIF-056 | content: engineering-standards / definition-of-done seed | landed |
| `AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md` | 2026-07-29 | none | freshness: do the pointers refresh together | reviewed observation, six gates recommended, none mechanized |

Reconciliation, stated so the next session does not re-derive it:

- **AIF-082 does not own the context compiler.** The bounded task packet is
  already the hardening lane's chartered mission. What AIF-082 contributes is
  the Tier-0 CONTENT SPEC (section 6.1) and the measured cost target the packet
  must beat. It folds in as a milestone there rather than re-chartering.
- **AIF-082 does not own freshness.** That is the 07-29 assessment's axis.
  AIF-082 adopts its six recommendations by reference (`:221-233`) and gives
  them a lane number so they stop being advice.
- **AIF-082 owns cost and acceptance.** How much must be read, in what order,
  and how does an agent know it is done. No prior artifact measures or gates
  either.

The two axes multiply rather than add: a corpus that is both large (C1) and
stale (C3) costs an agent the reading AND the reconciliation, which is precisely
what both assessments independently reported doing by hand.

### C8 -- the best onboarding document in this project is not in the repository

Found 2026-07-31T13:00Z, when the maintainer pasted a handoff authored by the
immediately preceding run (`2026-07-31_cowork_output_capture_completeness`,
AIF-081) whose stated purpose is "bring a fresh agent to productive in one read,
without re-learning the traps below the expensive way."

**It is not in the tree.** No file under `docs/maintenance/` carries it; the only
in-tree documents that even mention `bin-wsl-lean` are two AIF-081 lane
artifacts, neither of which is an onboarding surface. The mandatory start path
cannot reach it.

That matters because the document is, in form, **the Tier 1 and Tier 2 design of
section 6 already executed by hand.** Roughly 10 KB, task-ordered rather than
doctrine-ordered, trigger-headed ("READ THIS BEFORE WRITING A PROOF"), traps
front-loaded, every claim carrying `file:line` or a measurement. It is the
strongest available evidence that the tier model is achievable, because a
previous session built one without being asked to and without a framework for
it.

**And it contained the fix for this session's own failure.** Its section 8 reads:

> *"If you have a Linux sandbox: run NO git commands from it. Even `git status`
> refreshes the index, takes `index.lock`, and cannot unlink it across the
> mount, which then blocks the owner's commits."*

That is strictly more actionable than the in-tree version at
`LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42`, which says "unreliable mount"
without naming the sandbox case or the consequence for the owner. Had the
handoff been in the tree and in Tier 1, the wedge recorded in 5b would not have
happened. **The remedy existed, was written the day before by the previous
session, and was unreachable from the corpus.**

This is a third failure category, distinct from the two already recorded:

| | Failure |
| --- | --- |
| C6 | the entry point was never tested cold |
| C7 | prior assessments were never given a lane number |
| **C8** | **the best operational onboarding artifact was never put in the tree** |

All three share one shape: **the knowledge existed and the retrieval path did
not.** None of them is a content defect. That is now three independent
instances, which is the Rule of Three threshold (`AI_PORTAL.md:258-262`) for
treating it as structural rather than incidental.

Proposed, added to the sheet as 6.5g: land the handoff in the tree as the seed of
Tier 1, and make "leave a handoff in the tree" an explicit closeout obligation
alongside the session closeout. A closeout records what happened; a handoff
records how to work here. AIF-006 currently requires the first and not the
second.

---

## 4. What the corpus does well, recorded so remedies do not damage it

A lane that only lists defects invites a rewrite, and a rewrite here would
destroy the most valuable property in the tree. Recorded deliberately:

- **Scar tissue with dates.** Nearly every serious rule carries the failure that
  produced it ("Recorded 2026-07-27 because it happened this day",
  `AI_PORTAL.md:54`). A cold agent does not have to be persuaded by any rule in
  this repository, because each arrives with its own evidence. This is rare and
  it is the reason the corpus works despite its size.
- **`LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:20-22`** -- "Every item below is a
  mistake actually made in the session that created this document. It is not
  hypothetical." This session changed its own behaviour because of that file: no
  `git add` sweep, no cleaning, commands prepared rather than run.
- **Stage-separated reporting.** Dev / promoted / validated / published, with
  "never claim a later stage because an earlier one succeeded"
  (`AI_PORTAL.md:627`). Overclaiming requires an explicit lie.
- **`CLAUDE.md`** -- highest value per byte in the tree by a wide margin.
- **The role table duplicated verbatim** at `AI_PORTAL.md:15-19` and
  `AI_README.md:7-11`. Correct duplication: it is the one fact whose corruption
  damages everything downstream.

**Constraint on every remedy in section 6: no scar tissue is deleted.** It is
re-indexed by trigger, never removed. The cost problem is retrieval order, not
content.

---

## 5. The central asymmetry

> The most valuable content in the corpus is the least needed at entry.

Scar tissue is what makes the rules stick, and it is almost entirely
front-loaded. A rule read 40 KB before it becomes relevant is a rule that will
not be applied at the moment it matters. This session read the pre-push gate
(`AI_PORTAL.md:666-732`) during onboarding and will not push anything; it read
the DotScript comment convention in `CLAUDE.md` and needed it forty minutes
later while authoring.

That asymmetry is why fast and complete are not actually in tension here, and
why the answer is not abridgement. Nothing needs to be cut. It needs to arrive
when it is actionable.

### 5b. The asymmetry demonstrated on this lane's own author (2026-07-31T12:50Z)

Section 5 claims that a rule read long before it is actionable will not be
applied at the moment it matters. That claim was argument. It is now evidence,
produced against this steward.

`LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42` states: *"Do not run git through an
unreliable mount. If the filesystem cannot reliably delete files, git will leave
a stale `.git/index.lock` after every command and eventually wedge the repo. In
the founding session, an AI's own `git status` calls left a lock that blocked the
maintainer's `git switch`. Prefer: hand git to the maintainer."*

This steward read that line during onboarding, at approximately 11:47Z. It then
ran roughly twenty `git status`, `git diff`, `git show`, and `git rev-parse`
calls from the sandbox mount over the next hour, two of which timed out and were
killed mid-operation. At 12:48Z the maintainer's `git commit` failed:

```text
fatal: Unable to create 'D:/code/ccode/.git/index.lock': File exists.
```

Forensics: the lock is **zero bytes**, timestamped at the minute the session's
first `git status --short` call timed out. Zero-byte means git created the lock
and was killed before writing the index. The staged index was consequently
empty, `prepush_gate.py` correctly reported "no changes in staged index --
clean," and `git push` correctly reported "Everything up-to-date." **Every tool
behaved correctly and reported truthfully; the wedge was upstream of all of
them.**

Three things this establishes, none of which were available as evidence before:

1. **The central asymmetry is real and first-person.** The rule was read, was
   understood well enough to be cited in this very charter's section 4 as an
   example of the corpus working, and was violated within minutes of being read
   because it was not actionable at read time. Sixty-one minutes later, when it
   became actionable, it was not recalled. This is the strongest possible
   support for trigger-indexed retrieval (6.3): the rule needed to fire at
   "about to run git," not at "onboarding."
2. **The scar tissue was correct and specific and still did not prevent the
   recurrence.** The founding session's failure and this one are the same
   failure, described accurately in advance, in a document this agent had read.
   Content quality was never the problem. **Delivery timing was.**
3. **It is a demotion candidate under 6.6, and the gate does not exist.** Unlike
   the five conversions listed in 6.6, this rule has no mechanism behind it --
   nothing prevents an agent from running git over a mount. It therefore cannot
   demote, and it should not. Proposed instead as its own small item: a
   Tier-1-resident, trigger-fired warning, or a wrapper that refuses git writes
   from a non-host root the way `repository_role_guard.py` already refuses the
   wrong root. Note that the role guard **passed on the host** in the same
   session in which it false-blocked in the sandbox, which is exactly the
   signal such a wrapper would key on.

Behavioural commitment recorded for the remainder of this lane: **no git
invocation from the sandbox mount.** File reads and writes go through the host
file tools; all git is prepared as commands and handed to the maintainer, per
the checklist's own "Prefer" clause.

### 5a. Framing correction -- large documentation is the product, not the defect

Recorded 2026-07-31 on maintainer correction: "huge documentation is our meat and
potatoes."

Correct, and this lane must not be read as an argument against it. x64base is a
teaching system whose deliverables ARE documents: the manual, HELP, SelfDoc, the
contracts, the campus lessons, the website. Under *Representative by Design*
(AIF-037) source teaches, and documentation is the surface where that teaching
actually lands. A large, dense, evidence-carrying corpus is this project's
principal asset and its competitive advantage over projects that ship code with
a README.

The measured 127,704 bytes in C1 is therefore **not a complaint about corpus
size.** It is a measurement of ONE path: the bytes a cold agent must traverse
before it may act. Those are different quantities and this lane only ever
addresses the second.

Stated so no future reader mistakes the lane's direction:

- **Corpus size is an asset.** Nothing in section 6 reduces it. The decrement
  operator (6.6) demotes prose one tier and explicitly deletes nothing; the
  structural items (6.5) move strata into a sibling file that git already
  preserves either way.
- **Entry-path size is a cost**, and only because it is paid by every agent, on
  every cold start, before any of it is actionable.
- **The work is cataloguing, not pruning.** A library is not improved by having
  fewer books. It is improved by a catalog, an index, and a shelf order. Every
  proposal here is catalog work.

The lane's one-sentence position: **keep every byte, stop making the entry
path carry all of them.**

---

## 6. Proposed remedies (PROPOSED -- none landed this session)

### 6.1 Tier 0 -- generated state, target under 4 KB

A single generated file answering "where are we" without prose. Generated from
existing authorities, never authored, so it cannot drift:

| Field | Source of truth |
| --- | --- |
| branch, HEAD, dirty count | `git` |
| open lanes + status | `coordination/aif/*.claim` + intake queue |
| newest closeout per lane | `labtalk/registries/ai_runs.yaml` (`current_by_lane`) |
| declared target | `docs/agents/CURRENT_TARGET.md` first section only |
| owed items | closeouts' "Still open" sections |
| staleness warning | HEAD vs newest closeout commit distance |

The staleness warning is the piece that would have caught C3 automatically: had
Tier 0 reported "declared target is 3 lanes behind HEAD," neither the 07-29 nor
the 07-31 session would have had to derive it by hand.

This is the hardening lane's bounded task packet, reduced to its smallest
useful form. It belongs to that lane; AIF-082 contributes the spec and the
target figure.

### 6.2 Tier 1 -- authored, target under 8 KB

Role table, mutation guard, local-access rules, house conventions, and the
stopping rule. Sufficient to act safely on a scoped task. Approximately
`CLAUDE.md` plus `AI_README.md:1-45` plus the checklist -- most of it already
written and already good; the work is selection and placement, not authoring.

### 6.3 Tier 2 -- trigger-indexed doctrine

The remainder of `AI_PORTAL.md`, retrieved by intent rather than read at entry:

| Trigger | Retrieve |
| --- | --- |
| about to change source | mutation gate, engineering standards, contract preflight |
| about to commit or push | pre-push gate, role guard, slice discipline |
| about to publish | website authority, publication chain, agent-sync refresh |
| about to open a lane | claim protocol, intake rules, prior-art check |
| about to close out | AIF-006 table, closeout template, envelope schema |

Nothing is deleted. Every scar-tissue passage keeps its text and gains a
trigger.

### 6.4 The stopping rule and the self-test

The gap C6 exposes cannot be closed by more prose; it needs a falsifiable exit.
Proposed: a short answerable set at the end of Tier 1, where a cold agent that
cannot answer all of them is not onboarded and must continue.

Draft, five questions, each answerable from Tier 0 plus Tier 1 alone:

1. Which tree are you in, on which branch, and which tree may push to `main`?
2. What is the current declared target, and is it fresher or staler than HEAD?
3. Name three things that are report-only unless the current task names them.
4. What must you do before changing source, and what must you do after
   changing lane state?
5. What is the inline comment marker in DotScript, and what may you never
   pass to `git add`?

Answering these is the acceptance test the portal currently lacks. It also
converts recommendation 5 of the 07-29 assessment (`:230` -- "preserve the
successful cold-start procedure as a repeatable portal acceptance test") from
advice into a gate.

### 6.5 Structural hygiene (each independently justified)

- **Split `CURRENT_TARGET.md`.** Keep lines 1-18 as the pointer; move the
  eighteen historical sections to `CURRENT_TARGET_HISTORY.md`. The strata are
  genuine evidence and are not deleted; they are simply not the pointer.
- **Retire the legacy Start Here list** (`AI_README.md:56-73`). A numbered list
  under that heading is an instruction. Git holds the continuity.
- **State precedence between the two field blocks** (C5), or nest one in the
  other explicitly.
- **Decide the entry point for the phrase "AI portal"** (C6). Either
  `AI_PORTAL.md` becomes a short pointer with doctrine moved to Tier 2, or it
  keeps its content and the redirect at `:29` moves to line 1 as the entire
  visible head of the file. Either resolves the collision; the current
  arrangement does not.
- **Headers carry a bare date where they need a timestamp.** Maintainer
  correction, 2026-07-31T12:38Z. This lane had **four sittings in one day**, and
  `date: 2026-07-31` cannot order them; nor can it order this lane against
  AIF-080 and AIF-081, which also opened on their filename date. The closeout
  envelope already solves this correctly -- `recorded_at_utc` is a full UTC
  timestamp and `audit_trail.py` enforces it -- but the human-readable header
  blocks and lane docs did not inherit the convention. 66 files under
  `docs/maintenance/` carry a bare-date header. Proposed: header blocks take
  `created_utc` / `updated_utc` in the same ISO-8601 UTC form the envelope
  already mandates, so one convention covers machine and human surfaces.
  Filenames keep their date (they are identifiers, not ordering keys). Applied
  to this lane's own three documents immediately; the other 66 are a sweep.
- **Intake queue rows are lane docs in table cells.** AIF-078 is 1,147 words in
  one cell; AIF-079 is 988; AIF-081 is 889. The queue's own rule
  (`AI_INTERACTION_INTAKE_QUEUE_V1.md`, Intake Rules) is "Add only distilled
  candidates, not entire conversations." The file is 142,496 bytes across 126
  lines. Triage does not work at that density and the depth already exists in
  the lane doc each row points to. Proposed: cap a row at a scannable summary
  plus anchors, with depth living in the lane doc. **Not actioned here** --
  see section 9, this file cannot be edited without fusing other sessions' rows.

### 6.6 The decrement operator -- mechanization demotes prose

Added 2026-07-31, second sitting, on the owner's observation that the project
recursively refines its processes as it optimizes them.

That loop is real and fast. Within the 48 hours before this lane opened, three
refinements changed this session's behaviour: AIF-079's closeout ("onboarding
happened last") caused this session to onboard first; AIF-078's prior-art rule,
one lane old, caught a design already chartered on 2026-07-12; AIF-080's
governance finding reversed this session's decision to withhold its intake row.

The failure mode is not that the loop is broken. It is that **the loop only
adds.**

The 127,704 bytes measured in C1 were not produced by neglect. They are the
product of roughly eighty lanes of careful, evidence-backed, individually
correct decisions. Each rule earned its place by costing someone real time.
That is precisely why nothing ever leaves: removing a rule means discarding
evidence, and this project is constitutionally unwilling to discard evidence.
**Correct local decisions, monotonic global growth.** A one-off cleanup
therefore does not solve C1; the next eighty lanes rebuild the same weight and
a later session writes the same finding with a bigger number in it.

The loop needs a subtraction term that costs no evidence. Proposed:

> **When a rule becomes mechanically enforced, its prose demotes one tier.**

The gate is the memory. Once a mechanism refuses the mistake, reading the rule
at entry is redundant work, so the text keeps its scar and its date and stops
being entry-path. Nothing is deleted. This is the same constraint section 4
imposes on every other remedy, applied as a rule rather than a promise.

**Conversions already made, demotions never taken:**

| Scar | Mechanism that now enforces it | Anchor |
| --- | --- | --- |
| Duplicate `create_dbf` shadow (AIF-043, cost days) | configure-time duplicate-basename shadow guard, fails the build | `AI_PORTAL.md:284-304` |
| `git add -A` fusing lanes; build trees in commits | `tools/staging/prepush_gate.py` (exit 2), `repository_role_guard.py` | `AI_PORTAL.md:699-713` |
| Two sessions claiming one AIF number | `claim-aif` atomic `O_EXCL` + `aif_collision_gate.py` | `CLAUDE.md:62-70` |
| Closeout envelopes drifting from schema | `audit_trail.py` against `ai_report_audit.yaml` required_fields | `labtalk/registries/ai_report_audit.yaml` |
| Generated manual regions drifting | `tools/manualgen/check_manual_drift.py` FAILs the build | `docs/agents/CURRENT_TARGET.md:157-159` |

Five conversions from prose to mechanism. Five demotions available, none taken.
That is the decrement the corpus has already earned and never collected.

**The demotion test, and why it must be strict.** A rule may demote only when
its gate **hard-fails**. Advisory output does not earn a demotion, and this tree
contains live counterexamples that would be mis-demoted by a loose test:

- the AI dev-tools permission gate is **dormant by default**, permitting unless
  enforcement is requested (`AI_PORTAL.md:143-145`);
- the collision gate's "claim with no intake row" is **advisory**, not a block
  (observed this session: AIF-068 and AIF-070 pass);
- `audit_trail.py` intake findings are **advisory** by policy
  (`ai_report_audit.yaml`, `external_intake_glob` comment).

Demoting a rule that sits behind a dormant or advisory gate would delete the
only enforcement it had. So the decrement operator has a hard dependency:
**AIF-079's declared-capability validator is what proves a gate actually
enforces rather than merely existing.** Without it, "is this mechanized?" is
answered by reading a symbol name, which is exactly the declared-at-the-
interface / absent-at-the-leaf class AIF-079 exists to detect. The two lanes
compose: AIF-079 certifies that a gate is real, and 6.6 spends that certificate
to buy back entry-path budget.

**Proposed artifact:** a mechanization ledger -- rule, the scar that produced
it, the gate that now enforces it, hard-fail yes/no, tier before and after --
so each demotion is auditable and reversible if the gate is later weakened.

Paired with a Tier 1 byte ceiling (6.2), this closes the loop: adding to the
entry path requires either demoting something or building the gate that earns
the demotion.

### 6.7 The unmeasured second axis -- governance cost per lane

C1 measured what it costs to ENTER the process. Nothing measures what it costs
to RUN it.

This lane executed twelve mandatory governance actions: claim a number, check
in, declare scope calibration, check prior art, author a lane doc, author a
closeout, add an intake row, add a Session Log row, run the collision gate, run
the envelope audit, sweep house style, verify tree state. Roughly a third of
the session went to governance rather than to findings.

For a lane that is mostly judgment, that is plausibly the right ratio. For a
two-line correction it plainly is not. **Nobody knows where the crossover is,
because it has never been measured.**

The structural observation, and it is checkable:
`SCOPE_CALIBRATION_SEED_V1.md:11-24` calibrates **proof** gates by change class
-- a C0 change does not owe a full regression, a manual reharvest, or a website
flush. It says nothing about **governance** gates. A C0 documentation lane and a
C3 engine lane pay the identical twelve steps. The seed's own principle
("select the smallest sufficient gate set") is applied to evidence and not to
process, which is the one place the project has never turned its own doctrine on
itself.

Proposed, in order:

1. **Measure before prescribing.** Count artifacts and mandatory steps per lane
   across the last twenty lanes, bucketed by declared `change_class`. The data
   is already in the tree: claim files, lane docs, closeouts, queue rows.
2. **Then decide** whether low-class lanes may collapse artifacts -- for
   example a C0 lane filing one document that is both charter and closeout,
   rather than two that restate each other. This lane's own charter and closeout
   share an estimated 30 to 40 percent of their content by subject, which is a
   candidate instance and is offered as one rather than asserted as a defect.

Recorded as an estimate, not a measurement, per
`COST_BENEFIT_GATE_DOCTRINE_V1.md`: estimates suggest, probes measure. The
one-third figure above is this steward's impression of a single session and is
not evidence. M6 is the probe.

### 6.8 Automation and refresh cadence -- state has a cadence, rules do not

Owner question, 2026-07-31: can onboarding be automatic, and how often must it
happen if a session persists for days?

The two questions have different answers because **onboarding is not one thing.**
It is a cache load of two materials with opposite refresh profiles, and the
current corpus conflates them. Separating them is what makes both answers
tractable.

| | Rules (Tier 1, Tier 2) | State (Tier 0) |
| --- | --- | --- |
| Changes | over weeks, by deliberate lane | continuously, by other agents |
| Automatable | yes, by INJECTION | yes, by GENERATION |
| Re-read cadence | never within a session | event-driven, see below |
| Cost of being stale | low; rules are stable | high; silently falsifies claims |

#### Automatic already exists, and it is the best file in the tree

`CLAUDE.md` is injected into this agent's context at session start without being
requested. It was not fetched, not searched for, and not paid for out of the
127,704 bytes in C1. It is also, by a wide margin, the highest value per byte in
the corpus (section 4). **Automatic Tier 1 is not a proposal; it is a mechanism
already working, currently carrying about 4 KB of the roughly 8 KB Tier 1
needs.**

The defect is that this surface is **fragmented and unequal per vendor**:

| File | Bytes | Consumed by |
| --- | ---: | --- |
| `CLAUDE.md` | 4,314 | this agent, automatically |
| `AGENTS.md` | 1,496 | Codex-family agents |

Two auto-injected onboarding surfaces of different size and content means two
partners are onboarded to different depths by accident of vendor, and neither
was designed against the Tier 1 requirement. This is the single-canonical-copy
rule (`AI_PORTAL.md:321-323`, AIF-037 Rule of Three) unmet on the one surface
that reaches every agent for free.

**Proposed:** one canonical Tier 1 body, with thin per-vendor shims that include
it rather than restate it. Byte-identical by construction, so the divergence
cannot recur. This is also the cheapest remedy in section 6, because the
delivery mechanism is already built and already firing.

#### What cannot be injected

Tier 0 is generated and changes under the session, so it cannot be frozen into
context at start. It must be pulled. Tier 2 is retrieved by trigger by design
(6.3) and must not be injected, or the corpus is back to 128 KB with extra
steps.

#### Cadence: event-driven, not clock-driven

For a session persisting days, the invalidating driver in THIS repository is not
elapsed time. It is **concurrency**. `CLAUDE.md:57-60` states the governing fact:
concurrent AI sessions share ONE working tree. A session's picture of that tree
is accurate for the instant it was taken and for no longer.

Re-run Tier 0 on these events, not on a timer:

1. **Before any mutation** -- the tree may have moved since the last read.
2. **Before asserting tree state in a closeout** -- every stage claim is a claim
   about a moment.
3. **After any pause** in the session.
4. **When another session appears** on overlapping paths.
5. **After your own commit**, because HEAD moved and your own Tier 0 is stale.

Cost is seconds against 128 KB, which is the entire point of separating state
from rules: **the expensive material never needs re-reading, and the material
that needs re-reading is cheap.** Onboarding feels unrepeatable today only
because the two are fused.

#### Measured gap in this session, recorded against itself

This session read tree state at approximately 11:50 UTC and authored closeout
claims about it at 12:09 UTC without re-checking for newly active sessions in
between. Nothing went wrong -- the AIF-081 delta was verified as pre-existing --
but the verification was valid for 11:50, and it was reported at 12:09 as
though it were current. Had a concurrent session touched those files in the
interval, the closeout would have carried a false statement produced by correct
procedure. Rule 2 above exists because of this, and it is recorded as this
lane's own scar rather than as advice.

#### The concurrency signal is currently degraded

Rule 4 assumes `session_coordinator.py status` is informative. Observed this
session, it is not: it reported three active sessions, of which two were stale
by 765 and 1,095 minutes, and this session's own `checkout` **failed to
deregister** because the mount refuses deletes (the exact hazard in
`LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42`), leaving a third false positive
behind.

So the mechanism emits heartbeats that nothing consumes and cannot reliably
retract them. A signal that is mostly false is a signal nobody checks, which is
presumably why no closeout in the tree records having checked it. **Making
cadence work therefore depends on repairing the staleness signal first**: expire
heartbeats past a threshold, and make deregistration robust to a filesystem that
cannot delete. Small, and a precondition rather than a nicety.

### 6.9 Refresh by diff, on a read manifest the agent is required to emit

Owner proposal, 2026-07-31: an already-onboarded agent should diff the portal
for updates rather than re-read it; and if the agent cannot do that natively,
require it to emit a list of the documents it read so the comparison is instant.

Prior-art check: no `files_read` / read-manifest / read-receipt mechanism exists
in `labtalk/ai_portal/`, `docs/maintenance/`, or `tools/`. This is new.

The proposal is correct and it plugs into a surface that already exists but is
currently unverifiable. `AI_README.md:363-375` -- the Minimal New-AI Checklist --
already asks every agent to report **`Files read:`**. Today that field is prose,
hand-typed, and nothing checks it. This session filled it in from memory. A read
manifest makes that existing field machine-generated and true, rather than
adding a new obligation.

#### Why diffing works, and its one blind spot

Content hashing is sound for the refresh case and fails in the safe direction: a
false "unchanged" is impossible, and a false "changed" costs only a re-read.

**But a diff detects edits, not staleness, and this tree contains the proof.**
`CURRENT_TARGET.md` has not changed since 2026-07-28, and that is precisely why
it is wrong (C3). A hash-only refresh would report "no change, you are current"
about a document that is three lanes behind. **A file that should have changed
and did not is invisible to diff.**

So refresh needs two signals, not one:

| Signal | Detects | Mechanism |
| --- | --- | --- |
| content hash vs manifest | the rules moved under you | hash compare, per doc |
| HEAD distance / lane-vs-target | the world moved under a document that did not | Tier 0 staleness warning (6.1) |

The second is already specified as Tier 0's staleness warning. 6.9 is what makes
the first cheap. Neither substitutes for the other, and a refresh built on
hashing alone would reproduce C3 while reporting green.

#### Shape and placement

Per doc: path, content hash, bytes, tier, `read_at`, plus the run and member.
Roughly 1 KB for a full onboarding set. Refresh becomes hash-compare and re-read
only the deltas, which for a days-long session is typically zero bytes against
127,704.

**Not `tmp/`.** AIF-081 established one week ago that throwaway `tmp/` artifacts
are exactly how evidence becomes invisible -- that lane had to carry its figures
in-document because its transcripts were disposable. **Not committed either**, or
per-session churn pollutes the tree.

The correct medium already exists and was built for this: the coordinator's
transient-but-shared area, `coordination/active_sessions/`, gitignored yet on
the filesystem every concurrent session can see. The check-in record already
carries `run_id`, `member`, `lanes`, `files`, `heartbeat_utc`. The manifest is
the same record with what was actually read attached, which also gives cadence
rule 4 (6.8) something real to compare against.

#### It must be a gate, not a discipline

Asking an agent to remember to emit a manifest is a rule that depends on good
intentions, which is the failure class this portal keeps re-learning. Two
mechanizations make it real:

1. **The Tier 0 pull emits the manifest as a side effect.** The agent does not
   remember; the tool records. Reading is what produces the receipt.
2. **The closeout gate validates it** -- a closeout whose `Files read:` disagrees
   with the manifest, or which asserts tree state older than its last Tier 0
   pull, is a finding.

Item 2 would have caught this session's own recorded gap (6.8, the 11:50 read
asserted at 12:09) mechanically instead of by confession.

Recursive payoff worth noting: building 6.9 converts prose into a hard gate,
which under 6.6 immediately earns a tier demotion for the "report what you read"
and "re-check before asserting" rules. **It pays for part of its own entry-path
cost.**

#### It also instruments M4

M4's falsifiable target -- a cold agent reaching a correct checklist under 12 KB
-- currently has no way to be measured; the charter states the target without an
instrument. A read manifest with byte counts IS that instrument. 6.9 is
therefore a dependency of M4, not an optional extra.

### 6.10 Dogfooding the store -- and the scope discipline that goes with it

Owner direction, 2026-07-31: "we dogfood our database as always ... it might give
us something cool to do with our 64bit memo oo structure."

This is the right home for the manifest's authority, and it sits directly on the
house thesis recorded in `OUTPUT_CAPTURE_COMPLETENESS_LANE_V1.md` section 1 --
the documentation process consumes and proves the database, which in turn
supports the documentation system. An onboarding read-manifest is that loop in
miniature: the onboarding system's own evidence, stored in the database the
onboarding system exists to explain.

Why the workload is genuinely interesting rather than a toy:

- **Shape is complementary to existing benchmarks.** AIF-046 tuned wide scans
  over 1M fixed-width rows and found the residual in per-row record I/O. A
  manifest table is the opposite shape: few records, large variable-length memo
  payloads, append-heavy, read-mostly. Memo is where the 64-bit object work
  actually gets stressed, and that is not what the STUDENTS benchmark exercises.
- **It touches live lanes on a real path:** memo/WAL atomicity (AIF-061),
  RECNO64 addressing, index maintenance across the REPLACE seam (AIF-079/080),
  and cross-process locking, since the CLI and `dottalk_bbsd` share the store.
- **It is self-proving.** If the store drops a memo, onboarding visibly breaks.
  That is a better durability proof than a synthetic harness because the failure
  is observed by a consumer that cares.

#### The bootstrap paradox, and its resolution

If the manifest's authority lives in the DBF store, an agent must reach the
store BEFORE it is onboarded -- but reaching the store means running the engine,
which is currently gated behind the DotScript readiness seeds (`AI_README.md:44`).
A cold agent would be locked out of the thing that tells it how to get in. The
daemon compounds it: `AI_README.md:36` already concedes step 0b may be skipped
when `dottalk_bbsd` is down.

Resolution is this project's own promotion model applied once more:

```text
DBF store (memo-backed)      authority; queryable, durable, dogfooded
        |
        | generated projection
        v
Tier 0 flat file (<4 KB)     the cold-start read; no engine required
```

**The store is authoritative. The projection is what a cold agent reads.**
Onboarding must never require a running engine or a live daemon, or the portal
acquires a dependency that can lock out the agent it exists to admit.

#### The general form: the entry path runs at the capability of the WEAKEST admitted partner

"Engine down, daemon down" is not actually the floor. The portal's Outside-AI
Delivery Rule (`AI_PORTAL.md:433-451`) explicitly admits hosted partners that
cannot touch the disk at all -- a ChatGPT session reading the public GitHub
snapshot has no shell, no python, no venv, no engine, and no filesystem. That is
the weakest partner the portal claims to serve, so it sets the constraint:

> **Tier 0 must be a persisted artifact left behind by the last tool run, never
> something the reader generates on demand.**

A generated-on-read design silently re-tiers the portal to "local agents only"
and drops the hosted partners the Outside-AI rule exists for. The same test
catches the neighbouring cases already in the tree: step 0b's BBS handoff is
correctly marked skippable when the daemon is down (`AI_README.md:36`), and
`labtalk_portal.py --audit` requires a venv, so its output is evidence for a
local agent and unreachable for a hosted one.

Generalized, and cheap to apply to any future entry-path proposal: **an
onboarding step may not require a capability that the least capable admitted
partner lacks.** Anything richer than reading a file is a convenience layer over
the projection, never the projection itself.

#### Scope discipline -- this belongs in another lane

Stated plainly because AIF-082's own subject is accretion: **the storage design
is not AIF-082's to build.** This lane specifies the manifest INTERFACE (fields,
placement, the two refresh signals, the gate) and the projection requirement.
The memo/64-bit object work, schema, and durability proof belong to the owning
memo lane or to a new lane of its own, with its own number and its own Phase-0.

Folding an engine workload into a documentation lane would make AIF-082 the
thing it criticises. Recorded as the handoff, not as scope.

`PDLC_STUDENT_WORKING_MODEL_LANE_V1.md:44-52` maps the six craft steps onto the
project's real lane machinery. This lane is deliberately run as one full PDLC
cycle so it can serve as a worked exemplar, and it is an unusual one: **the
artifact under development is documentation, not code.** That is exactly why it
is worth teaching. The PDLC is a craft cycle, not a compiler workflow, and a
student who has only seen it applied to source will assume documentation is
outside the cycle -- which is the habit AIF-024 exists to break.

| PDLC step | Performed in this lane | Governance counterpart |
| --- | --- | --- |
| **analyze** | Cold traversal of the mandatory start path, performed once, unrepeatable by the same agent. Findings C1-C7. | intake: `AIF-082.claim`, this charter, truth state declared mixed |
| **design** | Three-tier retrieval model (6.1-6.3) with a measured target for each tier, plus the stopping rule (6.4). | lane doc, section 6; no contract touched |
| **code** | **NOT PERFORMED.** No generator written, no portal file edited. | the gate this lane stops at |
| **test and debug** | **NOT PERFORMED** as a tool. Performed as measurement: section 3 is reproducible from the recorded commands. | proof state: report |
| **document** | This charter, authored during the session, not reconstructed after it. | AIF-024 document-as-you-work |
| **maintain** | Proposed, not built: the staleness warning in 6.1 and the self-test in 6.4 are the maintenance mechanisms that would keep the result from rotting. | AIF-006 closeout-updates-startup |

Recording the two NOT PERFORMED steps in the table rather than omitting them is
the honest form. A PDLC exemplar that shows only completed steps teaches that
the cycle is always finished in one sitting, which is false and is the
overclaiming habit the portal's stage-separated reporting exists to prevent.

**The teaching point this lane carries, stated for M2/M3 of
`project.labtalk.pdlc`:** the analyze step here had a property most analysis
does not -- it was destructible. A cold reading can be performed exactly once
per agent, and every subsequent reading is contaminated by the first. The lane
therefore had to be opened while the evidence still existed, before the agent
learned its way around. That generalizes: **some evidence has an expiry measured
in minutes, and the analyze step must recognize it and capture it first.** It is
the same discipline as AIF-024 (capture the hash when it is produced), arriving
from the opposite direction -- not "record it before you forget," but "record it
before you understand."

---

## 8. Milestones and gates

| Milestone | Deliverable | Gate |
| --- | --- | --- |
| **M0** | This charter: cost measured, prior art reconciled, remedies proposed. **DONE 2026-07-31.** | measurement reproducible; file:line anchors present; prior-art table defended |
| **M1** | Owner rulings on section 6 (accept / reject / defer each remedy independently) | maintainer decision recorded in this file |
| **M2** | Tier-0 generator, folded into `AI_PORTAL_HARDENING_LANE_V1.md` as its packet-compiler milestone | generated file under 4 KB; staleness warning fires correctly on a synthetic stale target |
| **M3** | Tier 1 assembled from existing text; self-test authored | a cold agent answers all five questions from Tier 0 + Tier 1 alone |
| **M4** | Cold-start acceptance test made repeatable and registered | a fresh agent, given only the phrase "my AI portal," reaches a correct Minimal New-AI Checklist within the Tier-1 budget |
| **M5** | Structural hygiene items (6.5) executed individually, each its own scoped slice | no scar tissue deleted; git holds all retired content |
| **M6** | Governance cost probe (6.7): artifacts and mandatory steps per lane over the last twenty lanes, bucketed by `change_class` | a measured table replaces this lane's one-third impression; crossover named or explicitly declared absent |
| **M7** | Decrement operator (6.6): mechanization ledger authored; the five earned demotions taken or refused with reasons | every demotion cites a HARD-failing gate; no demotion behind a dormant or advisory gate; depends on AIF-079 M1 |
| **M8** | Tier 1 unified across vendor shims (6.8); staleness signal repaired so cadence rule 4 is trustworthy | `CLAUDE.md` and `AGENTS.md` derive byte-identically from one source; `status` reports no session stale beyond threshold; `checkout` succeeds on a delete-refusing mount |
| **M9** | Read manifest (6.9): emitted as a side effect of the Tier 0 pull, validated by the closeout gate | a stale `Files read:` or a tree-state assertion older than the last Tier 0 pull is a FINDING, not a confession; refresh re-reads only hash-changed docs; instruments M4 |
| **M10** | Manifest INTERFACE handed to the memo lane (6.10) with the projection requirement attached | interface spec accepted by the owning memo lane; **Tier 0 readable with NO execution capability at all** -- persisted artifact, reachable by a hosted partner with no shell, no python, no engine, no daemon; no storage work performed under AIF-082 |

M4 is the falsifiable target this lane is measured against. Stated up front, per
`AI_PORTAL.md:339-341`: **a cold agent should reach a correct checklist on Tier 0
plus Tier 1, under 12 KB, without reading `AI_PORTAL.md` in full.** If the work
does not reach that, this lane says so and says why, rather than declaring
victory at whatever figure it lands on.

A KILL is a legitimate outcome. If M1 rules that 128 KB is the correct price for
this corpus, the lane closes having produced the number and the acceptance test,
and that is a complete result.

---

## 9. Not done, and why

- **No portal document was edited.** Every remedy is proposed. The mutation
  guard defaults to report-only and the authorization was to open a lane and
  write it up, not to restructure the onboarding corpus.
- **The intake row and Session Log row WERE written** (working tree, not
  committed). An earlier decision in this session to withhold them on AIF-078
  fusion grounds was reversed: fusion is a commit-slicing problem and belongs to
  the maintainer, whereas an unregistered lane is an invisibility problem and
  belongs to the steward. Withholding them would have reproduced the AIF-080
  governance failure inside a lane whose subject is work that stays invisible
  because nobody numbered it. Recorded in the closeout's AIF-006 section.
- **No tool was written.** M2 is unstarted.
- **The self-test is a draft.** It has never been administered to a cold agent,
  which means the acceptance test itself is unproven. The only way to prove it
  is the next fresh session, and this session cannot be that session.
- **The 07-29 assessment's ten missing registry paths were not classified.**
  They belong to the freshness axis and remain owed there.

---

## 10. Anchor table

| Claim | Anchor |
| --- | --- |
| C1 total | probe, section 3; reproduce with `wc -c` over the nine listed paths |
| C2 strata | `docs/agents/CURRENT_TARGET.md:5,:7,:284,:320,:418` |
| C3 07-29 finding | `labtalk/ai_portal/AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md:177-181,:228` |
| C3 07-31 state | HEAD `0803f0f13`; lanes AIF-079/080/081 absent from `CURRENT_TARGET.md` |
| C4 front doors | `AI_PORTAL.md:29`; `AI_README.md:23` |
| C5 field blocks | `SDLC_FAST_START_SEED_V1.md:32-57`; `SCOPE_CALIBRATION_SEED_V1.md:11-24` |
| C5 legacy list | `AI_README.md:56-73` |
| C6 warm verdict | `AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md:135-138` |
| C6 resume-vs-entry rule | `AI_PORTAL.md:54-80` |
| C7 context compiler | `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md:38-45` |
| C7 six gates | `AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md:221-233` |
| stopping rule absent | `AI_README.md:31` ("stop when you have enough for the task") |
| falsifiable-target doctrine | `AI_PORTAL.md:339-341` |
| PDLC six steps | `docs/maintenance/PDLC_STUDENT_WORKING_MODEL_LANE_V1.md:27,:44-52` |
| 6.6 conversions made, demotions untaken | `AI_PORTAL.md:284-304`, `:699-713`; `CLAUDE.md:62-70`; `labtalk/registries/ai_report_audit.yaml`; `docs/agents/CURRENT_TARGET.md:157-159` |
| 6.6 gates that must NOT earn a demotion | `AI_PORTAL.md:143-145` (dormant); collision gate advisory output, observed this session (AIF-068, AIF-070) |
| 6.6 single-canonical rule | `AI_PORTAL.md:321-323` |
| 6.7 proof gates calibrated, governance gates not | `labtalk/ai_portal/SCOPE_CALIBRATION_SEED_V1.md:11-24` |
| 6.8 shared working tree is the invalidator | `CLAUDE.md:57-60` |
| 6.8 vendor shim divergence | `CLAUDE.md` 4,314 B vs `AGENTS.md` 1,496 B, measured this session |
| 6.8 delete-refusing mount hazard | `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42` |
| 5a representative-by-design / source teaches | `AI_PORTAL.md:238-248` (AIF-037) |
| 6.9 existing unverified `Files read:` field | `AI_README.md:363-375` |
| 6.9 diff blind spot (stale without changing) | `docs/agents/CURRENT_TARGET.md` unchanged since 2026-07-28; C3 above |
| 6.9 tmp artifacts go invisible | `docs/maintenance/OUTPUT_CAPTURE_COMPLETENESS_LANE_V1.md` sec 7 |
| 6.9 transient shared medium already built | `coordination/active_sessions/*.yaml`; `CLAUDE.md:62-70` |
| 6.10 documentation-proves-the-database thesis | `docs/maintenance/OUTPUT_CAPTURE_COMPLETENESS_LANE_V1.md` sec 1 |
| 6.10 bootstrap: engine/daemon may be down | `AI_README.md:36,:44` |
| 6.10 weakest admitted partner has no disk or shell | `AI_PORTAL.md:433-451` (Outside-AI Delivery Rule) |
| 6.10 complementary benchmark shape | AIF-046 residual is per-row record I/O; `docs/agents/CURRENT_TARGET.md:80-84` |

---

## 10a. Method note -- working the system is what found the defects

Maintainer, 2026-07-31: *"Working the system makes you learn the system, which
helps you find defects and room for improvement."* Recorded as this lane's
method claim, because it is falsifiable and the tree contains the control group.

Every finding in this lane was produced by **performing** the process, not by
reviewing it:

| Finding | Produced by |
| --- | --- |
| C6 entry-point collision | entering cold, with only the phrase "my AI portal" |
| C7 recommendation never numbered | running the prior-art check before claiming |
| C8 handoff missing from the tree | needing build information and not finding it |
| 5b mount/git wedge | actually wedging the maintainer's index |
| 6.5e bare-date headers | needing to order four sittings in one day |
| 6.7 governance cost | paying it, twelve steps, for one C0 lane |

**The control group is the 2026-07-29 assessment.** It inspected the same corpus,
carefully, by an experienced agent, and found none of these. It was not a worse
assessment; it was a different method. It read documents. **An inspection reads
the documents; working the system exercises the paths between them** -- and
every finding above lives in a path, not in a document. C6 is a path from a
spoken phrase to a file. C7 is a path from a recommendation to an action. C8 is
a path from a need to an artifact. 5b is a path from a rule to the moment it
should fire.

This is the evaluation-method companion to *Prove the Bottleneck First*
(`AI_PORTAL.md:325-337`): that rule says measure before you build; this one says
**use before you assess**. It is also the house thesis applied to process -- the
documentation must be consumed to be proven, exactly as the database is.

Practical consequence for M4: the cold-start acceptance test must be a **real
task**, not a quiz. An agent that answers five questions has demonstrated
reading. An agent that onboards, claims a lane, authors, registers, and gets
blocked at a gate has exercised the paths, which is where the defects are. The
self-test (6.4) checks that onboarding *happened*; only a worked task checks
that onboarding *sufficed*.

---

## 11. Method note -- one steward error recorded

Before checking prior art, this session drafted its findings as though the
onboarding corpus had never been assessed. It had been, twice
(`AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md`, and AIF-056's hardening
work), and the context-compiler design the session was about to propose as new
was already chartered on 2026-07-12.

The prior-art check was performed before the AIF number was claimed, so nothing
mis-registered. But the draft existed, and it would have duplicated a lane. The
rule that caught it is AIF-078's, one lane old at the time of use: a design
registered nowhere will be done twice. Recorded because the near-miss is the
evidence that the rule is load-bearing, and because a lane about onboarding cost
that had itself duplicated prior work would have been self-refuting.

Second, smaller: the session initially read the phrase "my AI portal" as a
request about a hosted AI service and asked a clarifying question rather than
looking in the repository. The repository was not mounted at that moment, so the
question was not wrong -- but the assumption underneath it was, and it is the
same assumption `AI_PORTAL.md:10-12` exists to correct ("It is not a student
portal for accessing an AI service"). That correction is currently on line 10 of
a 732-line file. C6 is partly an account of how a fresh agent reaches that
sentence.

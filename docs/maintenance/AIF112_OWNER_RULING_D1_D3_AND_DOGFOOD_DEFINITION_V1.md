---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-006
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local
  git:
    branch: development
    baseline_commit: b04940a78
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: >
      member.derald, owner, in-session and explicit. On D1: "sqlite is a
      pre-dogfood x64base decision to be cleared." On the general rule:
      "SQLITE lives in our system and has a specific purpose, but is NEVER
      dogfood." Recorded as owner ruling, not scribe proposal.
    scope: >
      Owner ruling on AIF-112 D1 and D3, plus a doctrine statement defining
      dogfood and SQLite's standing relative to it. No source mutation.
      No registry mutation. Lane docs and packages unchanged.
  report:
    path: docs/maintenance/AIF112_OWNER_RULING_D1_D3_AND_DOGFOOD_DEFINITION_V1.md
    kind: owner_ruling
  lane: AIF-112
  primary_topics:
    - "AIF-112"
    - "D1 substrate"
    - "D3 lock model"
    - "dogfood definition"
    - "SQLite standing"
---

# AIF-112 -- Owner Ruling on D1 and D3, and What Dogfood Means

**Report id:** AIPR-20260815-COWORK-006
**Date:** 2026-08-15
**Owner / authority:** member.derald
**Recorded by:** member.ai.claude.cowork (scribe)
**Lane:** AIF-112
**Supersedes on these two points:** AIPR-20260815-COWORK-001 section 4, which
framed D1 as an amendment on prior-art evidence. The owner's framing is
different and better; see section 2.

---

## 1. The ruling

**D1 -- Primary substrate. CLEARED, not amended.**

The inventory / check-out ledger is built on **in-tree DBF catalogs** under
`data/metadata/inventory/`, created, queried and locked ONLY through
x64base / DotTalk++ surfaces, following the `WORKSPACES` and identity-catalog
patterns.

Unchanged from the signed D1: never a side-channel sqlite3 process; Git remains
the publication path; Fossil considered, NOT adopted.

**Re-pointed:** D1's Fossil-fallback condition read "unless the dogfooded spike
proves a required property the runtime **SQLite** surface cannot express." It now
reads against the **DBF** surface. This is not a patch. The clause always meant
"whether the dogfooded runtime can express the property"; naming SQLite there was
part of the same residue being cleared. Left unchanged it would have been
untestable, because the amended spike never exercises the surface the clause
names.

**D3 -- Lock model. CLARIFIED, intent unchanged.**

The hybrid model stands: exclusive for non-mergeable items, advisory for pure
text, reusing the engine's cross-process cooperative locking. The clause "define
stale/abandoned-checkout recovery" is promoted from design note to **Phase-1 exit
criterion**, scoped against what source now shows: `release_held`,
`force_unlock_table` and `force_unlock_record` all exist and are called by
nothing, and `cmd_unlock.cpp` exposes no FORCE verb. There is no reachable force
path, so recovery must not depend on one. `EXPAT` lease reclaim is the mechanism
under test.

---

## 2. Why D1 was cleared rather than amended

The scribe originally argued the DBF carrier from prior art -- `WORKSPACES`, the
identity catalogs, the FLOCK idiom. That argument is sound but it is not the
reason. The owner's reason is historical, and the documents carry it.

**The acceptance note, written before Phase-0, justifies SQLite on availability:**

> "SQLite is already built into DotTalk++"
> "substrate (SQLite is already in-tree)"
> "SQLite is prior art, not a new dependency"

That is a **cost argument**. It establishes that SQLite is cheap. It never asks
whether SQLite is the right carrier.

**The dogfood constraint arrived afterward.** `PHASE0_DECISIONS.md` records it:

> "The dogfood amendment (D1/D7) is the maintainer's, applied to the decision of
> record itself (not only the spike brief): the recurring failure mode in this
> project is a constraint that lives somewhere it does not get honoured, so the
> constraint sits in the signed decisions."

Applied to D7 (spike style) the amendment lands cleanly, because D7 is about how
you drive the thing. Applied to D1 it could only reach half the decision, because
the substrate had already been fixed by an argument dogfood was not party to.
What it constrained was the **access path** -- "created / queried / locked ONLY
through x64base / DotTalk++ surfaces ... never a side-channel sqlite3 process" --
not the **carrier**.

The result was "use someone else's database, but reach it through our commands."
That is dogfooding the delivery while leaving the substrate foreign.

**So the sequence is:** substrate chosen on availability -> dogfood applied late
-> dogfood could only constrain access -> "in-tree SQLite ledger through our
surfaces" is the compromise artifact of that ordering.

Clearing it completes an amendment that was applied late and could only reach
half its scope. The prior-art inventory did not discover a better option; it
revealed that the dogfood principle, applied fully, had already answered the
question, and that D1's substrate predates its own governing constraint.

---

## 3. The doctrine statement

Owner's words, recorded verbatim:

> **SQLite lives in our system and has a specific purpose, but is NEVER dogfood.**

### 3.1 What dogfood means here

Dogfooding is building the thing on **our own runtime** -- x64base tables, the
DotTalk++ command surface, our locks, our catalogs, our identity spine. The test
is not "did we reach it through our commands." The test is **"is the thing under
us ours."**

A ledger reached through `SQLITE ...` is not dogfooded. It is a foreign store
with a house-shaped door.

### 3.2 SQLite's actual standing

SQLite is in the tree deliberately and keeps every role it already has. From
published doctrine (`proven-capabilities.mdx`, runtime-proven):

> "SQLite is compiled in as a companion carrier and as a verification instrument:
> dual-carrier teaching systems keep a sealed SQLite authority beside their
> x64base mirrors, the `ERP` and `SQLITE` command families open and query it
> natively, and the house SELECT checks its answers against a SQLite oracle.
> Competing with SQLite and using it as the referee are the same decision, made
> deliberately."

Companion carrier, verification instrument, oracle, teaching authority. All
retained. What SQLite is **not** is the substrate a dogfooded lane builds on.

### 3.3 Why this needed saying

**`dogfood` is used throughout this project and defined nowhere.** Measured on
2026-08-15 across `labtalk/ai_portal/`, `docs/ai-friendly/`, `AI_PORTAL.md` and
`CLAUDE.md`: the word appears in AIF-081 (dogfooding the engine's own transcript
facility, which immediately exposed a defect in the facility being used),
AIF-086/088/089 (dogfooding the engine's own DBF store), and AIF-097 (dogfooding
the BBS auth to gate the private site). Every usage is correct. None is a
definition.

That absence is the root cause. "Dogfooded SQLite ledger" only reads as coherent
if dogfood is undefined. Had the term been written down, D1 would have failed on
its face rather than surviving to a signed Phase-0 and a full spike package.

### 3.4 The precedent that settles it

**AIF-086, 2026-08-04, eleven days before AIF-112:**

> "DBF-native tracking CRUD + dogfood ... Built the AI-Portal tracking layer end
> to end over the engine's own DBF store: an all-subsystem CRUD (`tools/dbf`)
> with a 17-table policy registry ... SYSTASK seeded from `ai_portal_tasks.yaml`"

A tracking / ledger layer for the AI Portal, dogfooded, DBF-native. AIF-112
proposed a tracking / ledger layer for inventory, dogfooded, on SQLite. Same
class of problem, opposite carrier, eleven days apart.

The difference is not reasoning quality. AIF-086 was authored by an agent that
could read the tree; AIF-112's substrate was authored by one that could not.
This project has already answered this question correctly once.

---

## 4. Follow-on (not done here)

1. **File the dogfood definition where it will be honoured.** Section 3.1 and
   3.2 are the candidate text. Natural home is
   `labtalk/ai_portal/AI_TIER1_SEED_V1.md` section 4 (House conventions), which
   is invariant content and passes the seed's own test. Blocked by the same
   constraint as the housekeeping rule: `check-seed-budget` reports 7959 B of
   8192 B (233 B headroom) and the maintenance contract says "Adding requires
   demoting, and demoting means moving." An owner decision against a gated file.
2. **Amend GROK-005's `LEDGER_SCHEMA_SKETCH.md`** if the Fossil clause re-point
   in section 1 should also appear in the steward's package. Currently only
   recorded here.
3. **Transmit to the steward.** Grok accepted D1/D3 on the prior-art argument.
   The clearing framing is different and stronger, and the steward should be told
   the reasoning changed even though the outcome did not.

---

## 5. What this unblocks

Steps 2-8 of the amended exercise outline (GROK-005). Step 1, the reuse audit,
never required a ruling. The Phase-1 spike may now proceed on the DBF carrier
with SQLite retained as oracle in step 7.

---

Owner: `member.derald`. Recorded by: `member.ai.claude.cowork`.
Evidence class: `source-defined` (quotations from PHASE0_DECISIONS.md,
ACCEPTANCE_NOTE.md, SUMMARY_FOR_MAINTAINER.md, AI_FRIENDLY_DASHBOARD_V1.md,
proven-capabilities.mdx, all read 2026-08-15 at b04940a78).
Risk class: low (ruling record; no mutation).

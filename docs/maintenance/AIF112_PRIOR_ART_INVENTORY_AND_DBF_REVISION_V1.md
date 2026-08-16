---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-001
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session request
    scope: >
      Prior-art inventory for AIF-112 and a proposed DBF-native revision of
      locked decisions D1 and D3. Read-only survey of docs/maintenance and the
      published website content tree. No source mutation, no registry mutation,
      no change to Grok package AIPR-20260815-GROK-003 (left byte-intact).
  report:
    path: docs/maintenance/AIF112_PRIOR_ART_INVENTORY_AND_DBF_REVISION_V1.md
    kind: review_needed_change_package
  primary_topics:
    - "AIF-112"
    - "prior art"
    - "document control"
    - "check-in check-out"
    - "DBF catalogs"
    - "record locking"
    - "release_held defect"
---

# AIF-112 -- Prior-Art Inventory and Proposed DBF-Native Revision

**Package id:** AIPR-20260815-COWORK-001
**Date:** 2026-08-15
**Author:** member.ai.claude.cowork (scribe)
**Owner:** member.derald
**Steward:** member.ai.grok.xai
**Lane:** AIF-112 (Document Control / Inventory / Check-in-Check-out PDLC)
**Status:** review-needed; proposes amendment to LOCKED decisions D1 and D3
**Responds to:** AIPR-20260815-GROK-003 (Phase-1 spike package)

ASCII only. No C++ src/** mutation. Grok's package left byte-intact.

---

## 0. Executive summary

The Phase-1 spike package (AIPR-20260815-GROK-003) specifies a SQLite ledger
reached through the `SQLITE` command family. This document argues that premise
should be amended before the spike runs, for one structural reason and one
technical one.

**Structural.** The steward that authored the package runs at
`access_mode: remote`. It cannot read the tree. Its own schema sketch opens with
"Reuse first. Before creating new tables, inspect whether the runtime already
has lock, grant, or reservation tables that can be extended or mirrored." That
instruction was impossible for the author to execute. The SQLite choice is an
artifact of that blindness, not a finding.

**Technical.** Every ledger this project already runs is a DBF catalog under
`data/metadata/`, written under FLOCK, attributed through `current_member()`,
and append-only with supersede semantics. Three of them are runtime-proven. The
inventory ledger is the same kind of object. Building it on SQLite would prove
that SQLite can hold a lock table, which was never in question, while routing
around the engine surface that actually needs proving.

**The finding that should reset the spike goal.** The engine's lock-release
lifecycle has a verified hole: `locks::release_held` is declared, defined, and
called by nothing. D3 requires "define stale/abandoned-checkout recovery," and
that path does not currently work. That is a better Phase-1 question than the
one the package asks, and it can only be asked on the DBF path.

**Recommendation:** amend D1 (carrier) and D3 (locking substrate), keep every
other locked decision, and re-run the spike against the engine's own lock
lifecycle with SQLite retained as the verification oracle.

---

## 1. Why this document exists

`AI_SYSTEMS_CROSSWALK_V1.md` classifies the landing zone that received the
Phase-1 package:

| Stable ID | Component | Current state | Authority class |
|---|---|---|---|
| `ai.intake.external` | External AI intake (`docs/maintenance/external_ai_intake/`) | active landing zone | **source material, not authority** |

External packages are input. They do not set schema. This document is the
assessment step that classification implies, not a rejection of the package --
Phase-0 decisions, the proof bar, the evidence template, and the status
vocabulary (PLANNED / PARTIAL / SUPPORTED) are all sound and are carried
forward unchanged.

### 1.1 The visibility asymmetry, stated plainly

`AI_RUN_TRACEABILITY_CONTRACT_V1.md` already models the five roles and the
`handle_binding` distinction. What it does not yet state as an operating rule is
the consequence for design work:

> An agent at `access_mode: remote` can reason about a system it cannot read.
> It will produce a plausible generic design. Plausibility is not reuse.

This is not a criticism of the steward. It is a property of the access mode, and
it is predictable enough to plan around. Suggested standing rule, offered for
the owner's decision:

**Proposed rule R1.** A schema or storage-carrier decision must be authored or
countersigned by an agent with tree access, or by the maintainer. Remote agents
may propose the shape; the carrier is decided against observed prior art.

---

## 2. Prior-art inventory

Everything below was read in-tree on 2026-08-15. Evidence classes are quoted
from the source documents, not assigned by this report.

### 2.1 Transport and inter-agent communication -- ALREADY SOLVED

| Component | Record | State | Authority class |
|---|---|---|---|
| AI-BBS (`ai.transport.bbs`) | `src/bbs/`, `src/cli/cmd_bbs.cpp` | runtime-observed, hardening open | transport, not authority |
| BBS worklog (`ai.handoff.worklog`) | `docs/ai-friendly/AI_BBS_WORKLOG_HANDOFF_LANE_V1.md` | source-defined small end | convenience handoff |
| Session coordinator (`ai.coordination.sessions`) | `tools/coordination/session_coordinator.py` | active local tool | coordination, not authorization |
| AIF claim ledger (`ai.work.aif_claims`) | `coordination/aif/AIF-*.claim` | active | allocation record |

The worklog board already carries a handoff vocabulary in production use:

```
BBS POST board.worklog AIF-052 :: RUN=AIPR-20260725-001 | STATE=... |
  DID=... | OPEN=... | NEXT-AGENT=... | RISK=low, dev-only
```

**Implication for AIF-112:** the lane needs no new inter-agent messaging. Any
check-out notification, handoff, or "who holds this" broadcast rides existing
transport. Do not design a second one.

### 2.2 The BBS daemon -- the concurrency substrate already exists

`AI_BBS_M6_STANDALONE_DAEMON_V1.md` (built, runtime-observed 2026-07-25):

- Binary `dottalk_bbsd`, CMake flag `DOTTALK_BUILD_BBSD`, entry
  `src/tools/bbsd_main.cpp`
- Binds `127.0.0.1:8765`, loopback only; boot task `DotTalkBBSD`
- `--data <dir>` "Must match the CLI's data root so identity catalog + board
  tables line up"
- Known/deferred: "Single-connection accept loop (serialized identity session);
  concurrency is M4.1"

Locking, proven twice and recorded in two places:

> "Server enforces per-board POSTPERM; BBS writes take table FLOCK; listener
> uses `SO_EXCLUSIVEADDRUSE`."
> -- `SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md`, and again as a
> registry proof row in `REGISTRY_ADDITIONS_AI_BBS_2026-07-25.md`

> "The engine has cross-process cooperative FLOCK and the BBS store already
> appends under it, so machine concurrency is handled."
> -- `PROOF_CURATION_LANE_V1.md`

**Implication for AIF-112.** Two processes -- the CLI shell and `dottalk_bbsd`
-- already write the same DBF catalogs concurrently, under cooperative FLOCK,
with attribution, in production. That is precisely the substrate an inventory
check-out ledger requires, and it is already proven. It also gives the spike a
genuine second process to contend with, which a single shell session cannot
provide.

Caveat to record honestly: the accept loop is single-connection, so this proves
cross-*process* coordination, not many-client contention. For an exclusive
check-out ledger, cross-process is the property that matters.

### 2.3 Existing DBF ledgers -- the templates

House conventions, from `SYSTEM_SCHEMA_MAP_AND_NORMALIZATION_V1.md`:

> "physical names <= 10 chars (classic-browsable); 64-bit ids/epochs stored as
> `N(20,0)` decimal text with `0` = unset; enums as small `N` codes; bools as
> `L`."

| Catalog | Location | State | What it proves |
|---|---|---|---|
| Identity / RBAC (9 tables) | `data/metadata/identity/` | runtime-proven | bi-temporal validity, optimistic concurrency, permission gating |
| BBS (`SYSBOARD`, `SYSTHREAD`, `SYSPOST`) | `data/metadata/bbs/` | runtime-proven | attributed append-only rows under FLOCK |
| `WORKSPACES` | catalog table | runtime-proven 2026-08-11 | attributed catalog, supersede history, FLOCK per append, hash lineage |
| `SYSRULING` | `include/portal/ruling_schema.hpp` | schema authored, not built | append-only status transitions |
| `SYSLANE`/`SYSRUN`/`SYSTASK` | proposed, `TRACKING_STATE_DOGFOOD_LANE_V1.md` | not built | "who is working on what" |

#### `SYSGRANT` -- the nearest existing lease

From the identity catalog (AIF-045, runtime-proven): "the request->approve->
expire workflow is entirely SYSGRANT rows," carrying `VFROM/VTHRU` bi-temporal
validity and `ROWVER` optimistic concurrency.

A check-out with an expiry IS a grant with an expiry. This is the closest
existing semantic match in the tree, and it is already proven.

#### `WORKSPACES` -- the nearest existing physical template

> "`WORKSPACES` catalog table (x64 flavor; canonical posture: PK tag on
> WS_NAME): `WS_NAME C`, `SAVED_AT` timestamp, `AUTHOR C` (current_member),
> `NOTES C`, `SHA256 C` (payload hash, lineage), `SNAPSHOT M`. ... upserting by
> name, **FLOCK per append as the BBS store does**. **Oracle gate:** immediately
> read the memo back and byte-compare against the string ... Mismatch = hard
> fail, loudly."
> -- `WORKSPACE_MEMO_RESIDENCE_PLAN_V1.md`

Two rules from it transfer directly:

> "**Attribution mandatory.** The catalog row records `current_member()`
> (AIF-075); an unattributed snapshot poisons a trust-based store."

> "Recommend append-history with a `SUPERSEDED` flag -- it is the
> no-perishable-literals rule applied to snapshots, and it costs one field."

Write path, from `MEMO_RESIDENT_MINIDB_V1.md`: "WS_ID allocated (max+1 under the
catalog FLOCK), prior live row of the name superseded."

And, directly relevant to 2.1: workspaces are described as "queryable,
relatable, attributed to a member, **distributable over the BBS**." The
precedent chain from catalog to transport is already written down.

`PROOF_CURATION_LANE_V1.md` names it as the general pattern:

> "Precedent in the tree: `WORKSPACES.dbf` is exactly this shape already -- a
> table whose rows describe things that live elsewhere."

An inventory item is by definition a row describing a thing that lives
elsewhere. This is the same object.

### 2.4 Existing check-in / check-out -- for lanes and files

`AI_SESSION_COORDINATION_PROTOCOL_V1.md` (active; `tools/coordination/
session_coordinator.py`), verbs: `checkin`, `checkout`, `claim-aif`,
`lock <path>`, `unlock <path>`, `status`, `quip send|read`.

> "`aif/AIF-NNN.claim` -- durable allocation ledger. Claiming a number is an
> atomic `O_CREAT|O_EXCL` create: if two sessions race for the same number,
> exactly one wins the create"

> "`locks/<file>.lock` -- transient advisory lock on a contested shared doc.
> Cooperative: check before you edit; stale locks (older than the reap window)
> are reapable."

Doctrine worth inheriting verbatim: "Locks are advisory but binding by
agreement"; "Presence is courtesy, not permission"; "This coordinates, it does
not authorize."

Stated limits: "Coordinates local concurrent sessions on one machine/working
tree ... It is not a distributed lock service"; "Clock-skew affects
stale-reaping windows; keep the reap window generous."

**Implication.** AIF-112 is the DBF-backed generalization of a working system,
from lanes-and-files to arbitrary inventory items. The verb set, the
advisory/exclusive split, and the stale-reap concept are all already designed
and in use. The generalization is what is new.

### 2.5 The engine locking surface

| Surface | Status | Source |
|---|---|---|
| `LOCK` (family: concurrency) | supported | `src\cli\cmd_lock.cpp` |
| `UNLOCK` (family: locking) | supported | `src\cli\cmd_unlock.cpp` |
| `SET EXCLUSIVE ON|OFF`, `SET MULTILOCKS ON|OFF` | supported | set-family |
| `xbase_locks` | runtime-evidenced | `src/xbase/xbase_locks.cpp` |

`feature-crosswalk.mdx` lists "Record locking and unlock lifecycle" as
**runtime-evidenced**. Record locks and lock-file keys were widened 32->64-bit
in 2026-07; record-lock files are named `.lock.<recno>`.

---

## 3. The blocking defect

`WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md`, invariant I5, verbatim:

> "`current_owner()` is a process singleton computed once
> (`src/xbase/xbase_locks.cpp:60-63`); the stale-lock reaper fires only on a
> dead pid (`:244`, `:315`), which can never happen between two workspaces
> sharing one process; and `locks::release_held` is declared, defined (`:407`),
> and called by NOTHING. So intra-process isolation equals inter-process
> isolation ONLY IF workspace close releases what the workspace held --
> otherwise a normally-closed workspace leaves live-pid lock files that nothing
> but `FORCE UNLOCK` can clear, for the life of the shell."

Priced surface, from the same review: "the 43 lock call sites across 13 files
(review U3)."

### Why this matters more than the carrier question

D3 (LOCKED) requires: "Reuse the engine's cross-process cooperative locking;
define stale/abandoned-checkout recovery."

The first clause is sound -- the mechanism exists and the BBS store proves it.
The second clause currently has no working implementation to build on. A
check-out ledger whose holder can close normally and leave an unclearable
live-pid lock is a ledger that deadlocks in ordinary use, not in an edge case.

This is the highest-value thing Phase-1 can establish, and **it is invisible on
the SQLite path**, because a SQLite lock table would not touch `xbase_locks` at
all. The package as written would return a green proof bar while leaving the
actual blocker undiscovered.

---

## 4. Proposed amendments

Only two locked decisions are affected. Everything else in Phase-0 stands.

### D1 -- carrier (PROPOSED AMENDMENT)

**Current (LOCKED):** "In-tree DotTalk++ SQLite ledger, created / queried /
locked ONLY through x64base / DotTalk++ surfaces (the SQLITE command family,
work areas, tables), never a side-channel sqlite3 process (dogfood)."

**Proposed:** In-tree DBF catalogs under `data/metadata/inventory/`, created,
queried and locked ONLY through x64base / DotTalk++ surfaces, following the
`WORKSPACES` and identity-catalog patterns. Never a side-channel sqlite3
process. **SQLite is retained in its established house role as verification
oracle** -- the referee that checks the answer, per
`proven-capabilities.mdx`: "SQLite is compiled in as a companion carrier and as
a verification instrument."

**Rationale.** The dogfood rule is better served by the native carrier. The
no-side-channel constraint is unchanged and in fact strengthened. SQLite is not
removed from the lane; it is returned to the role the project already assigns
it.

### D3 -- locking (PROPOSED CLARIFICATION)

**Current (LOCKED):** "Hybrid: exclusive check-out for non-mergeable items
(binaries, capsules), advisory for pure text (Git already merges text). Reuse
the engine's cross-process cooperative locking; define stale/abandoned-checkout
recovery."

**Proposed clarification:** unchanged in intent, with the recovery clause
promoted to the Phase-1 spike goal and scoped against the I5 defect. Phase-1
must determine whether stale/abandoned recovery is reachable without engine
change, or whether it requires wiring `release_held` into area/workspace close
(a C++ change, therefore a separate lane and a separate authorization).

### Unchanged

D7 (live instance, no naked sqlite3), the reuse-first rule, Fossil as
considered-not-adopted, no C++ src/** mutation in this spike, the fence
(Triggers, Identity, Tuple freeze, AIF-098, site-and-guard-hardening residue),
the proof bar, the status vocabulary, and P1-P7.

Note on D7: `python-integration.mdx` states "`pydottalk` is not the DotTalk++
command shell." pydottalk is a binding over `DbArea`, record, field, memo-read
and physical CRUD. For commands in the `LOCK`/`UNLOCK` families, the CLI is the
required driver. D7's "pydottalk or the CLI" should be read as "the CLI, with
pydottalk available for record-level assertions."

---

## 5. Proposed DBF-native schema

Names <= 10 chars. Ids and epochs `N(20,0)`, `0` = unset. Enums small `N`.
Bools `L`. Attribution via `SYSMEMBER` ids. Append-only where history matters;
current state = highest `ACQAT` per `ITEMID`, exactly as `SYSPOST` and
`SYSRULING` do it.

### `INVITEM` -- inventory items

| Field | Type | Notes |
|---|---|---|
| ID | N(20) | item id (PK) |
| IKEY | C(64) | portable key, e.g. `item.capsule.aif112.s1` |
| KIND | N(2) | 0 File, 1 Capsule, 2 Doc, 3 Sample, 4 Other |
| REF | C(200) | opaque reference. NOT assumed to be a filesystem path |
| TITLE | C(64) | short human label |
| MERGEABLE | L | .T. advisory permitted; .F. exclusive required |
| CREATEDBY | N(20) | FK SYSMEMBER, from `current_member()` |
| CREATEDAT | N(20) | epoch |
| STATUS | N(2) | 0 Active, 1 Retired |
| VFROM / VTHRU / ROWVER | N(20) | validity + version stamp |

`REF` opacity is the capsule requirement from the original sketch, preserved.

### `INVCHKOUT` -- check-outs (append-only)

| Field | Type | Notes |
|---|---|---|
| ID | N(20) | checkout id (PK), max+1 under catalog FLOCK |
| ITEMID | N(20) | FK INVITEM |
| MEMBERID | N(20) | FK SYSMEMBER -- the holder |
| MODE | N(2) | 0 Exclusive, 1 Advisory |
| STATE | N(2) | 0 Held, 1 Released, 2 Broken, 3 Expired |
| ACQAT | N(20) | epoch acquired |
| RELAT | N(20) | epoch released, 0 while held |
| EXPAT | N(20) | epoch lease expiry, 0 = no expiry |
| RUNID | C(32) | `AIPR-YYYYMMDD-NNN`, ties to `ai_runs` |
| NOTE | C(120) | one line, not the argument |
| SUPERBY | N(20) | superseding row id, 0 = current |
| ROWVER | N(20) | optimistic concurrency |

`EXPAT` is the lease field `SYSGRANT` already justifies, and it is the
mitigation for the I5 defect: a lease that expires is recoverable even when
`release_held` never fires.

### `INVEVENT` -- omitted

Per P3, skipped. `INVCHKOUT` append-history carries it. Add only if the spike
shows a gap.

### Permissions

Gate through `SYSPERM` with deny-precedence via
`dottalk::identity::agent_permitted(perm)`: `inv.register`, `inv.checkout`,
`inv.release`, `inv.break`. `inv.break` should be maintainer-only, mirroring the
`FORCE UNLOCK` posture.

---

## 6. Revised Phase-1 spike

### Goal

Determine whether the engine's own lock lifecycle, over DBF catalogs, can
express exclusive check-out, advisory sharing, and **stale/abandoned recovery**
-- the last being the open question raised by I5.

### Run sheet

Exact subcommand spellings must come from the runtime. Capture them first.

**Step 0 -- discover.** `HELP LOCK`, `CMDHELP LOCK`, `HELP UNLOCK`,
`SET EXCLUSIVE`, `SET MULTILOCKS`, `HELP WORKSPACE`. Record verbatim. Record
instance start method, version, and tip for the evidence header.

**Step 1 -- reuse audit.** Inspect `SYSGRANT` (request/approve/expire),
`WORKSPACES` (attributed supersede catalog), and `session_coordinator.py status`.
Record what each already gives you. This step is the one most likely to be
rushed and it is the one the standing rule exists for.

**Step 2 -- THE PROBE (highest value; do this before building anything).**
Verify I5 empirically:

1. In CLI session A, open a table and acquire a record or table lock.
2. Close the area normally -- do not exit the process.
3. Inspect for a surviving `.lock.<recno>` / FLOCK artifact.
4. From `dottalk_bbsd` (a genuinely different pid, sharing the data root),
   attempt a conflicting acquire.
5. Observe whether the stale reaper clears it. Per I5 it will not: the pid is
   alive.
6. Confirm whether `FORCE UNLOCK` is the only recovery.

Record the result precisely. **If I5 reproduces, that is the Phase-1 headline
and it outranks the rest of the proof bar.** It means exclusive check-out cannot
be made recoverable without wiring `release_held` into area close -- a C++
change, out of scope here, and a new lane.

**Step 3 -- catalogs.** Create `INVITEM` and `INVCHKOUT` through the runtime
under `data/metadata/inventory/`. Confirm visibility via the runtime's own table
list.

**Step 4 -- register.** Three rows: one `KIND=0` File, one `KIND=2` Doc, one
`KIND=1` Capsule with a synthetic capsule id. Confirm `REF` accepts the capsule
id with nothing downstream treating it as a path.

**Step 5 -- lock proof.** Acquire exclusive as `spike.a`; second exclusive
acquire as `spike.b` must fail; release; re-acquire must succeed. Record *how*
the second acquire fails: engine-enforced refusal is a materially stronger
result than a SELECT-then-decide check, which is convention rather than
enforcement.

**Step 6 -- stale recovery.** Using `EXPAT`, set a short lease, let it lapse,
and confirm an expired hold can be reclaimed without `FORCE UNLOCK`. This is the
D3 recovery clause and the mitigation for whatever Step 2 found.

**Step 7 -- oracle.** Use SQLite in its house role: mirror the final
`INVCHKOUT` state and confirm the DBF answer and the SQLite answer agree,
following the `SQLSEL_SELECT_V1` precedent. This keeps SQLite in the lane
without making it the carrier.

**Step 8 -- hygiene.** Confirm nothing was written anywhere that promotes to the
publication tree. Note: `next build` copies `public/` verbatim into `out/`, and
`publish:github-pages` blanket-copies `out/` with no exclusions, so the entire
site tree is public by construction.

### Amended proof bar

Carries all eight original items, with two added:

- [ ] I5 probe executed and result recorded (reproduces / does not reproduce)
- [ ] Lease expiry (`EXPAT`) reclaim demonstrated, or recorded as not reachable

---

## 7. Counter-argument on the record

`PROOF_CURATION_LANE_V1.md` argues against DBF migration for registries:

> "'One file per record means two sessions never touch the same file' is a
> property a single DBF gives up. Text fragments diff and merge without a tool;
> a binary table does neither."

Its recommendation is "projection, not migration."

**Assessment.** The objection is real but does not transfer cleanly here. It
concerns registries that humans edit in Git, where mergeability is the dominant
property. An inventory check-out ledger is machine-written, single-writer per
row by design, and its whole purpose is to *prevent* concurrent edits rather
than merge them. The property being given up is one this lane does not want.

It does, however, imply a constraint worth adopting: **the ledger should not be
committed to Git.** It is runtime state, like the BBS catalogs, not source. That
also satisfies the "keep it private" requirement in the original proof bar.

Recorded here so the next gate can weigh it rather than rediscover it.

---

## 8. Open questions for the owner

1. Accept or reject the D1 amendment (SQLite carrier -> DBF carrier, SQLite
   retained as oracle).
2. Accept or reject proposed standing rule R1 (carrier decisions require tree
   access or maintainer countersignature).
3. Confirm the ledger is runtime state and excluded from Git.
4. If the Step 2 probe reproduces I5: authorize a separate lane for wiring
   `release_held` into area close, or accept lease-expiry (`EXPAT`) as the
   Phase-1 mitigation and defer the engine fix.
5. Confirm `inv.break` is maintainer-only.

---

## 9. What the steward should do with this

member.ai.grok.xai cannot read the tree and did not have access to any of the
prior art above. This document is the missing input, not a correction of
judgement. On receipt, the steward can:

1. Accept or contest the D1/D3 amendments on the evidence quoted here.
2. Re-issue the schema sketch against the DBF conventions in section 5.
3. Amend `EXERCISE_OUTLINE.md` to lead with the Step 2 probe.
4. Update `EVIDENCE_TEMPLATE.md` with the two added proof-bar items.

The Phase-1 package remains byte-intact on disk; nothing in it was edited by
this report.

---

Lane: AIF-112. Owner: `member.derald`. Author: `member.ai.claude.cowork`.
Evidence class: `source-defined` (in-tree survey with quoted citations; no
runtime execution). Risk class: low (no source mutation, no registry mutation).
Next gate: owner ruling on D1/D3, then execute the revised spike.

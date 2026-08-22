# Handoff -- Multi-workspace lane (AIF-078, coworker on AIF-070)

    from        : member.ai.claude.cowork
    for         : a GUI chat session with NO repo access, picking this lane up cold
    owner       : member.derald
    doctrine    : labtalk/ai_portal/AI_TIER1_SEED_V1.md, then
                  docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md
    posture     : design LANDED and committed. Runtime BARELY STARTED. One verb
                  built (USE ... AGAIN [ALIAS]), uncommitted on the maintainer's
                  working tree at time of writing.
    date note   : RESOLVED 2026-08-22. This file's own mtime is
                  2026-08-21 23:55, so it was written on 08-21 and the session
                  environment was correct. The 2026-08-12 comments are simply
                  older work from this lane, and the build stamp had already
                  moved to 2026-08-20 by the following day. The host clock is
                  fine; the filename is misdated and sorts wrong against it.
    amended     : 2026-08-22 by member.ai.claude.cowork (same member, later
                  session). Sections 2.1, 2.2 and 5 CORRECTED -- see the
                  correction notice below. Nothing else altered.

This is a **pointer document**. It deliberately does not restate the design's six
invariants: two shims that restate will diverge, and in this tree they already
have (AIF-082 6.8). Read the design doc for the design. What is here is the
runtime state, the constraints found by RUNNING things, and the traps.

Verify every claim below rather than trusting it. The session that produced it
shipped five test markers that could not fail, and caught them by reading
transcripts of PASSING runs.

**CORRECTION NOTICE (2026-08-22).** Section 2.1 was wrong, and section 5 told
the next session to prioritise it. Both are corrected in place. The error is
worth naming because it is this document's own trap 4 inverted: trap 4 asks
whether a GREEN could have gone red. 2.1 asserted a capability was ABSENT after
measuring one verb, without asking whether a second verb supplied it. One did.
An asserted absence needs the same falsification test as an asserted presence.

---

## 0. Orientation, in order

1. Read `docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md`. It is the
   target design, hostile-reviewed, corrected, committed. It is the authority.
2. Read `docs/maintenance/WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md`
   for the AIF-070 / AIF-078 seam and what each lane owns.
3. Then section 2 below, which is the part the design doc does NOT yet know.

If you have no repo access, sections 2 and 3 are the load-bearing content and
are written to stand alone.

---

## 1. State, by evidence tier

Tiers are the house's: design-intended < source-evidenced < runtime-proven.

**Runtime-proven (measured, transcripts exist):**

- `USE <table> AGAIN` -- a second, independently positioned cursor on an
  already-open DBF. Physical order only; refuses memo-carrying tables.
- `USE <table> [AGAIN] ALIAS <name>` -- names the instance. Explicit duplicate
  alias is refused; an implicit collision is auto-derived (`<stem>2`) and
  ANNOUNCED; all-digit aliases refused; malformed clause refused. Every refusal
  leaves the target area untouched.
- Two aliased cursors on ONE table can be related to each other, and declaring
  the relation positions the child. The self-join works.

**Source-evidenced (read, not run):**

- Whether the child TRACKS the parent across parent movement. A marker for it
  exists (`UA_T12b`) and had NOT been run when this was written. See section 4.

**Design-intended only (NO runtime whatsoever):**

- Concurrent named workspaces. Workspace membership and groups. Per-workspace
  area ownership. Any `ws[n].table` addressing. Per-workspace COMMIT/ROLLBACK.
  Lock owner as `(pid, workspace)`. RESIDENCE as an axis.
- `WORKSPACE` today means save/load a posture plus close-all. There is ONE live
  set of work areas, always. There is nothing to drive.

**Blunt version for the owner's question "can I demo multi-workspace?":** no.
Work areas plus relations, yes, and that predates this lane entirely.

---

## 2. Constraints found by RUNNING, which the design does not yet account for

These are the reason this handoff exists. Each was discovered by execution, not
inspection, and at least one invalidates part of the design's assumptions.

### 2.1 CORRECTED -- relations already bind INDEPENDENTLY NAMED endpoints

**The original claim was that `SET RELATION TO <field> INTO <alias>` matches
parent.F against child.F, that the engine cannot name the two endpoints
separately, and that a join grammar for independent endpoints is unplanned,
uncosted and probably the larger half of the work. Measured 2026-08-22: wrong.**

There are TWO relation verbs in this engine, and the original measured only the
older one.

- The classic dBASE/VFP-compatible verb takes a single field and does match the
  same name on both sides. That part of the original was accurate.
- The native verb is `SET RELATIONS ADD <parent> <child> ON f1[,f2...]
  [TO child_f1[,child_f2...]]`. It documents that syntax in its own source
  header, parses the `TO` token, and passes two DISTINCT field lists through.
  Composite keys are supported on both sides.

The underlying API takes parent fields and child fields as separate vectors, and
carries a child-side name list separate from the common-name list. The
common-name form is implemented by passing the SAME list twice. So independent
endpoints are the primary capability and common-name is sugar over it -- the
opposite of the original reading.

**This is in live use, not merely available.** Across the workspace postures on
disk, 28 of 208 RELATION lines carry an explicit `TO` with differently-named
endpoints. They include a table joined to ITSELF on two different fields, which
is the canonical organisational-hierarchy join.

**Consequence for the lane, which reverses the original.** The owner's sketch

    set relation ws[1].dbarea.record[3].field[3] to ws[3].dbarea[2].record[1].field[1]

splits into addressing and join grammar, as the original said. But BOTH halves
are already built:

- **join grammar** -- shipped, as above;
- **addressing** -- shipped. The design doc's invariant I4 states the qualified
  surface is the existing canonical dotted form, ALREADY parsed by the
  qualified-reference parser (status: supported) and ALREADY rendered by the
  data-address diagnostic with a current-workspace sentinel. The design
  explicitly WITHDREW a bracket-and-colon spelling because it dies in the
  shipped parser and would be a third address spelling beside a working one.

So nothing here needs inventing. What is missing is RUNTIME, and the design doc
prices it honestly: dozens of all-slot enumerations across many files, a
resolver that must gain a scope parameter and an ambiguity signal across all its
call sites, and a large number of lock sites. Mechanical, not conceptual.

A design session that assumes the join grammar is the hard part will be wrong.

### 2.2 A relation from an area INTO ITSELF is accepted

Observed: `REL: BOSS -> BOSS ON MGR` followed by `OK`. A one-node cycle is not a
join. The relation engine has recursion guards elsewhere, so this looks like a
missing check at declaration rather than a decision. Belongs to the relation
engine, not to USE. Not filed.

**CORRECTION (2026-08-22): this holds only for the DEGENERATE same-field case.**
A table related to itself on two DIFFERENT fields is the canonical
organisational-hierarchy join, and the live corpus contains one. A blanket
refusal of self-relations would break a legitimate and shipped pattern. The
narrow claim -- same table, same field on both sides, which can only ever match
a row to itself -- stands.

### 2.3 The marker language cannot assert that an area is EMPTY

The expression evaluator behind `?` binds a NULL area unless the area is OPEN.
Being closed is precisely what such a marker wants to assert, so NO symbol
resolves there -- not a field name, not RECNO, not RECCOUNT. Every attempt is a
false green or a silent error.

Corollary, and worse: **an errored marker prints NOTHING.** It does not go red,
it goes ABSENT. A suite scored by counting greens still reads full while a claim
has quietly left it. This was observed live.

The technique that works instead: park a KNOWN occupant in the target area
first, then assert it SURVIVED. Sentinel occupancy converts an unaskable
question into an answerable one. Use a sentinel whose value differs from every
other fixture, or the marker cannot discriminate.

### 2.4 RECCOUNT is real but reaches only one evaluator

The DBF record count is a stored header field, reachable in the engine. It was
surfaced as an expression symbol, but on the path that serves scan and `FOR`
predicates -- NOT the `?` marker path, which is a different evaluator. Usable in
a FOR clause over an open area; unavailable to markers. Stated because an
earlier version of the spec header claimed otherwise.

### 2.5 A guard that runs after the damage is not a guard

The memo refusal originally ran AFTER the target area was reset and the file
opened, then printed "Nothing was opened." Both halves false: the file was
opened, and the area's previous occupant was destroyed. Hoisted above the reset.
`AGAIN` means the file is already open elsewhere, so the probe reads a live
area's field list and touches no filesystem -- correctness here was free.

This is the project's signature defect ("something reports success without doing
its job") occurring INSIDE the guard written to prevent silent corruption.

### 2.6 Dead identity fields on DbArea, and a setter that compiles to nothing

Confirmed at the owner's prompting:

- `_db_name` has three writers and ZERO readers anywhere in the tree.
- The `_setLegacyName` SFINAE wrapper selects its EMPTY fallback, because
  `DbArea` has no `setName()`. It has always been a silent no-op, under a
  comment reading "legacy alias".
- `AREA` prints "Logical name" and "Legacy name()" from the same field, which is
  why they always agree.

The alias currently lands in the logical name, because that is the field the
name resolver actually compares -- so aliases resolve with no change at the
resolver's call sites. The table-name-versus-alias split those dead fields were
evidently shaped for needs a `DbArea` accessor, and `xbase.hpp` is a wide
include, so it is a full-rebuild change that should be priced, not slipped in.

**Generalise before trusting any other `_setX(a, v, 0)` wrapper in that family:**
the detection idiom fails SILENTLY at compile time when the API is absent. No
test can reach that failure.

---

## 3. Traps for a GUI session with no repo access

1. **Do not cite file:line.** This handoff deliberately carries almost none.
   Line numbers rot, and a session that cannot open the file cannot check them.
   The session that wrote this quoted "15 call sites" from a committed document
   that measures 18.
2. **Do not state counts.** Marker counts in this lane changed four times in one
   day. The house rule is "measure it", and the regression catalog entry for this
   spec now deliberately states no count.
3. **Everything in section 1's runtime-proven list was proven HERE, on one
   toolchain, in one sitting.** Nothing is proven anywhere a GUI session can
   check. Say so when repeating it.
4. **A green is not evidence until you know how it could go red.** The check is
   mechanical: if the command under test were DELETED, would this still be green?
   Five markers in this lane failed that check. Two were caught only by reading
   the transcript of a run that passed.

---

## 4. Open, and owed

**Unrun:** `UA_T12b`, which asks whether the child TRACKS parent movement, as
distinct from being positioned once at declaration. Both outcomes are useful and
they are different guarantees. A one-shot relation would leave `UA_T12` green and
`UA_T12b` red, which is the informative result, not a failure. Do not weaken the
marker to make it green.

**Stale:** the regression catalog entry for the USE_AGAIN spec does not yet
mention the self-join arms. String edit, next rebuild.

**Uncommitted at time of writing** (maintainer's tree, sandbox cannot commit):
the USE verb and its alias clause, the RECCOUNT accessor, the regression catalog
text, the help/message catalog, and the spec itself. Verify against
`git --no-optional-locks status --short -uall`. Keep `-uall`: this repo sets
`status.showUntrackedFiles=no`, so a bare status shows nothing for a new file.

**Design revisions owed** (the design doc does not know these yet):

- R1 proposed a read-only AGAIN. It shipped WRITABLE with two refusals.
- The ALIAS arm is not in the design at all. It should be, because it is what
  makes a second cursor addressable, and addressability is what relations need.
- Section 2.1 as originally written is WITHDRAWN (see its correction). The
  design does not reflect it because there was nothing to reflect.

**Rulings still open:** whether `WORKSPACE SELECT` restores a workspace's own
area selection (owner instinct was yes); group save, parked with AIF-070; the
RECALL-versus-ROLLBACK flag.

---

## 5. If you do only one thing

**SUPERSEDED 2026-08-22.** The original text sent the next session to the owner
with section 2.1 as a structural gap needing a ruling before further design.
There is no gap: both halves are shipped (see corrected 2.1). Following that
instruction would have spent the owner's attention on a settled question.

**What to do instead:** read the design doc's honest-counts table and its open
questions, then start where the counts say -- registry, DEFAULT and the
ownership chain, which touch none of the enumerated surfaces. The expensive part
of this lane is not grammar or addressing. It is that area ownership lives in
side tables today: the relation graph is one map keyed on a bare uppercased
parent name with no owner field, so two workspaces holding a table of the same
name collide silently on that key. The reconciliation doc calls that the
sharpest item and it is right.

**One genuinely open question is worth carrying up**, and it is not 2.1: the
area type carries no alias, no slot and no owner back-pointer, which is WHY
every one of these is a side table. The design's I1 says the workspace handle
and the slot index both become members of it. That is a wide-header change and
a full rebuild, so it should be priced deliberately rather than slipped in --
and everything else in the lane is waiting behind it.

---

## 6. Verification appendix (added 2026-08-22)

Sections 1-5 deliberately carry almost no `file:line`, per trap 1, because the
stated audience cannot open files. This appendix is the exception and is marked
as such: it exists so a session WITH repo access can falsify the corrections
above rather than trusting them. Expect these to rot; re-derive rather than
quote.

Measured at `68dcd6710`:

- The native relation verb documents its own syntax in the header comment of
  `src/cli/cmd_relations.cpp` (`SET RELATIONS ADD <parent> <child> ON f1[,f2...]
  [TO child_f1[,child_f2...]]`), parses the `TO` token in the same file, and
  calls the four-argument `add_relation`.
- `src/cli/set_relations.cpp` declares `add_relation(parent_area, child_area,
  parent_fields, child_fields)` and stores `child_names` separately from the
  common-name list `names`; the three-argument convenience overload calls the
  four-argument form with the same vector twice.
- The classic verb path in `src/cli/cmd_set_relation.cpp` calls the
  three-argument form -- this is the one the original section 2.1 measured.
- `28` of `208` RELATION lines under `dottalkpp/data/workspaces/*.dtschema`
  carry an explicit `TO`. Re-derive with grep rather than trusting the count;
  it changes as postures are saved.
- Addressing: see invariant I4 of
  `docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md`, which names the
  shipped parser and renderer and records why the bracket spelling was
  withdrawn.

**Method note, since this document is partly about method.** The original
section 2.1 was produced by running one verb and observing its trace. That is
good evidence for what that verb does and no evidence at all about what the
engine can express. An asserted absence is a universal claim, and a universal
claim is not established by one example. Trap 4 already says this for greens;
it applies unchanged to reds.

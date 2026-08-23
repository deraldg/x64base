---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-114
  recorded_at_utc: 2026-08-22T22:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: GUI API
    run_id: COWORK-20260822-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: eef1cf5ea
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 -- "2 assign
      yourself coworker and resolve it too", then the explicit ruling "yes we key
      both ends", then "now that you know better do better". Authorises this
      ruling and fixes D9.1. Authorises NO code. Sec 9b (2026-08-23) rests on
      the steward's standing architectural directive of the same session --
      "modify the new product to the existing dottalkpp product, so truth can
      flow from the bottom up" -- and likewise authorises NO code.
  review:
    first_draft: rejected by independent review, same session. See sec 9.
  report:
    path: docs/maintenance/AIF078_D9_RELATION_KEY_AND_CLOSURE_RULING_V1.md
    kind: ruling
---

# AIF-078 -- D9: both ends carry a handle; the handle addresses an edge, it does not partition the closure

Status: **ruling, review-needed.** D9.1 is the STEWARD's, given in-session and
recorded here. D9.2-D9.5 are the author's and are not self-approved.
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260822-001`.
Date: 2026-08-22. Baseline `eef1cf5ea`.

**This document authorises no build.** It fixes the storage shape, the refusal
policy and the verification standard for **I1.2**, so I1.2 is cut once.
Depends on **D8** (`AIF078_D8_LANE_SEAM_RULING_V1.md`).

**This is the ruling the plan deferred to.**
`AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md:279-281` puts workspace-scoped
relations out of scope with *"Own ruling, own work."* This is that work.

## 1. The question, and the fact that reframes it

I1.2 re-keys `relations_store()` (`src/cli/set_relations.cpp:60`) from
`UPPER parent name` to something carrying the workspace. Two documents read as
though they disagree:

**AIF-120 R26** (`AIF120_RELATION_SET_RULING_V1.md:100-104`):

> Where a relation exists between work areas, the unit of serialization is the
> **relation set** -- the transitive closure of related areas -- not the
> individual work area.

narrowed at `:125` from *"against one workspace"* to *"against one relation
set"*, which reads as though a relation set sits inside one workspace.

**The qualifier lane** (`WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_LANE_V1.md:327`,
Q9 at `:375`):

> The engine already has one tree. `SET RELATION`'s parent->child traversal
> graph. Containment would be a second tree over the same objects. They must
> stay distinct: a relation crossing a containment boundary should be legal, as
> a foreign key crosses schemas.

**The fact that reframes it, measured this session: a cross-workspace edge is
creatable TODAY, and nothing declares it.** `add_relation`
(`src/cli/set_relations.cpp:524-529`) resolves both endpoints through
`cli::find_open_area_by_name_ci`, which walks every slot with **no handle
filter** (`src/cli/workarea_util.cpp:49-60`) and gates only on `isOpen()`. Open a
parent in one workspace and a child in another -- both resolve, the edge binds,
and `refresh_from_parent_name` then follows the child **by name** (`:418`),
first match wins. The plan records the same thing as a fact at `:279-280`:
*"a relation can span two workspaces' areas."*

So this is not a greenfield choice. **It is a decision about an existing,
undeclared behaviour**, and that must be stated plainly rather than dressed as a
new guard.

## 2. The ruling

> **AMENDED 2026-08-22 -- READ SEC 9a FIRST.** D9.1 keys on
> `WorkspaceIdentity`, not the raw handle. **D9.3 is WITHDRAWN**: there is
> no refusal, because the owner had already ruled cross-workspace relations
> into a separate explicitly-qualified list on 2026-08-12. The text below is
> the original and is kept as the record of what was reversed.

> **D9.1 -- BOTH ENDS CARRY A HANDLE. Steward, 2026-08-22: "yes we key both
> ends."** The store key is `(parent_handle, UPPER parent_name)`;
> `Relation::child` becomes `(child_handle, UPPER child_name)`. An edge is
> addressable across handles by construction.
>
> **D9.2 -- the handle ADDRESSES an edge; it does not PARTITION the closure.**
> R26's transitive closure follows edges regardless of handle. A relation set MAY
> span workspaces. The closure is defined over edges, not over membership.
>
> **D9.3 -- cross-workspace edge CREATION is refused, and the refusal is a
> BEHAVIOUR REMOVAL, recorded as such.** `add_relation` refuses when its two
> endpoints resolve to different handles, with a named message. What is removed
> is an **undeclared accident**, not a feature: today the edge binds but the
> follow resolves by name with first-match-wins, so it produces what the
> qualifier lane calls *"plausible, well-formed, wrong rows"* (`:260-262`). No
> spec asserts it; no document promises it; the house has already deferred
> cross-workspace addressing for beta-1
> (`PSEUDO_CHAT_RETURN_LANE_V1.md:151-164`, maintainer-relayed, 2026-07-22).
> **The refusal is lifted by a ruling and a demand case, not by a patch.**
>
> **D9.4 -- the refusal must be exercised by a spec that can go RED**, or D9.3
> is not a guard but an AIF-079 mechanism with no call sites. Two workspaces are
> drivable today, so the spec is writable today (sec 5).
>
> **D9.5 -- scoped close computes the closure FIRST.** If the closure of an area
> being closed extends outside the workspace being closed, close reports and
> refuses rather than silently orphaning an endpoint. Under D9.3 this is
> unreachable for newly created edges; it is NOT unreachable for edges created
> before D9.3 lands, or restored from a posture. Stage 3's work, specified here.

## 3. Why address and scope are different things, and why that dissolves the conflict

R26 governs the **lock domain**: navigating any member repositions the others
*without passing through their interfaces*, so the serialization unit is the
whole closure. That says what must be locked together. It says nothing about
where members may live.

Q9 governs **legality**: containment and navigation are two trees over the same
objects, and constraining one by the other is a category error.

D9 keeps both. The closure is the lock domain (R26); nothing in the model
forbids it spanning workspaces (Q9); and creation is refused for now on
operational grounds, not model grounds (D9.3). R26's `:125` narrowing is
strengthened, not contradicted -- locking per workspace would sometimes be too
**small**.

The load-bearing reason to key both ends is **R26.1**, not the collision
argument: *"A target cannot compute the lock domain from a handler's code. It has
to know the relations."* **A store that cannot be walked without guessing is a
store from which no lock domain can be computed.** Today the walk guesses twice
-- once at the key, once at `set_relations.cpp:418`.

**And one thing survives that the first draft never explained.**
`ScopedEngineSelect` does not break when an edge's ends differ, because it
selects by **engine slot**, which is workspace-global (`set_relations.cpp:184`
-> `engineSlot()`). `workspace_multi_regression.dts` drives `SELECT 0..7` freely
across four workspaces. That is why D9.2 is implementable at all, and it belongs
in the ruling rather than in a reviewer's notes.

## 4. Scope of I1.2 under D9

**In.**

1. `RelKey { uint64_t ws; std::string upper_name; }` with a hash; store becomes
   `unordered_map<RelKey, vector<Relation>>`. `Relation::child` becomes the same
   pair. Both types are file-local to `set_relations.cpp`, named in no header
   (verified across `include/` and `src/`), so they change freely.
2. The `relations_store()` references -- **29 at this baseline**, all in
   `set_relations.cpp`, none elsewhere. Roughly half already hold a `DbArea*` and
   read `wsHandle()` directly; the remainder are name-only and need the handle
   threaded. Count re-measured at authoring time; treat it as perishable.
3. The D9.3 refusal plus its D9.4 spec.
4. **Handle 0 is reserved** for "no such workspace"
   (`workspace_membership.hpp:164-166`) and is `_ws_handle`'s value on a closed
   area (`src/xbase/dbarea.cpp:121`). `add_relation` already requires both areas
   OPEN, so a 0-handle key is unreachable through that path.
   **But the invariant is not enforced at its source:**
   `workspace_membership.hpp:97` is
   `inline void set_current_handle(std::uint64_t h) noexcept { current_handle_ref() = h; }`
   -- **no validation**. 0 is rejected only at the call site
   (`cmd_workspace.cpp:3956-3959`). One future caller passing 0 stamps handle 0
   onto every subsequently opened area, and those areas are `isOpen()`.
   **`set_current_handle` should reject 0 at the API**, and that belongs with
   I1.2 because I1.2 is what makes handle 0 load-bearing.
5. **`merge_relation` (`src/gui/core/session.cpp:1113-1132`) must be brought
   into agreement or explicitly excluded, in writing.** Its identity predicate is
   `lower(parent) == lower(parent) && lower(child) == lower(child)`, plus a key
   check in which **an empty key is compatible with anything**. `workspace` is
   not in the predicate at all -- even though `WorkspaceRelationInfo` carries the
   field (`include/gui/core/model.hpp:164`) and
   `gui_workspace_format.cpp:146` already filters on it. Re-keying the CLI store
   while the GUI keeps a workspace-blind identity **recreates the two-resolver
   defect I1.3a just closed, one layer up.** The empty-key-is-compatible arm is
   separately the AIF-118 shape: absent treated as fine.

**Out.**

6. **The persisted forms.** D8.2: `RelationSpec` gains no handle; the DTSHEMA
   posture `RELATION` line is not versioned by this lane.
7. **Scoped close (D9.5's guard).** Stage 3.
8. **`slot_of_area_ptr`.** Independent -- and it is a *deletion*, not a rewrite:
   `cli::slot_of_area` (`src/cli/workarea_util.cpp:174-180`) already is the fix,
   and I1.1's note records that the shared version answers correctly for a closed
   area where the scan returns -1. Do not smuggle it into the re-key, where its
   timing evidence would be entangled.

**Named, not fixed -- the round trip gets WORSE, and D9 owns saying so.**
`export_relations` (`:748`) flattens the whole map to names;
`import_relations(clear_existing=true)` (`:766`) destroys everything then re-adds
through `add_relation`, which requires both areas open. That round trip is
**already lossy** today. Under D9.3 it becomes lossy in a new way: an edge that
spans workspaces round-trips today and will be **refused on import** after D9.3.
The first draft claimed *"I1.2 does not make it worse"*; that was wrong, and the
correction is the point -- a cross-workspace edge in an existing saved posture
becomes unrestorable. **This must be in I1.2's own ruling as a migration note,
not discovered at stage 6.**

## 5. Verification, and what a green does and does not prove

Every area resolves to handle 1 unless `WORKSPACE NEW` / `WORKSPACE SWITCH` has
run, so **I1.2 is behaviourally inert on the default path by design.**
Therefore:

- **`REGRESSION ALL` proves no-regression, not correctness** -- and less than it
  looks. `RELJOIN` (`src/cli/cmd_regression.cpp:284-289`) and `NAME_AMBIG`
  (`:462-467`) both carry `in_default_suite = false`, so **the default suite runs
  no relation spec by name.** Both must be invoked explicitly. A ruling claiming
  a green `REGRESSION ALL` as evidence for a relation change claims a green that
  never ran the relevant spec -- the FIELDMGR_APPEND shape.
- **Two workspaces are drivable and were mutation-tested today.**
  `dottalkpp/data/scripts/workspace_multi_regression.dts` -- `WORKSPACE NEW`
  x3, `UNDER`, `WORKSPACE SWITCH`, a shared file opened in two workspaces,
  eleven markers, header recording *"MUTATION TESTED 2026-08-22 -- THE ARMS ARE
  LIVE AND INDEPENDENT."* **The D9.4 spec is writable today.** An earlier draft
  gated I1.2 on this being unknown; it was known, in this lane, on the same date.
- **Three relation/workspace specs exist and are unregistered** in
  `kRegressionSpecs`: `workspace_multi_regression.dts`,
  `workspace_multi_demo.dts`, `rel_scanlimit_honesty_regression.dts`. Unreachable
  by name. Registering the first is stage-3/4 evidence this lane already paid for.
- **The ambiguity ledger is expected to stay ZERO even with two workspaces**,
  because `cmd_use.cpp:944-972` auto-renames a duplicate stem -- the multi
  script yields `MWSHARE` / `MWSHARE2`, not a collision. R112's measured-zero
  gate therefore is not automatically satisfied by running that script.
  **Driving the ledger non-zero needs a deliberate fixture** and remains
  unmeasured.

## 6. The options as they actually stood, priced

Recorded because the steward asked for pros and cons and because D9.3 removes
something.

| | A -- partition | B -- span freely | **C -- key both ends, refuse creation (RULED)** |
|---|---|---|---|
| Closure | stops at workspace | spans | spans (D9.2) |
| Creation | refused | permitted | refused (D9.3) |
| For | simplest invariant; scoped close trivially safe; **matches VFP, whose `SET RELATION` is strictly within a data session** | faithful to Q9; no refusal branch | store cut once; keeps Q9 open; refusal is a declared, red-capable guard |
| Against | contradicts Q9 in a doc this lane owns; un-foreclosing later is a second re-key | dangling endpoints on close with no demand case; lock domain exceeds the handler's workspace, which R26.1 says it cannot compute | **ships a branch with no user -- one letter from AIF-079 unless D9.4 is honoured**; removes a working-by-accident behaviour |

**Why C.** If the demand case never arrives, C costs one branch more than A. If
it arrives, C costs a ruling and a branch removal where A costs a second re-key
of the same map plus every call site. It is *"buy the option, not the feature"*
(`SESSION_CLOSEOUT_WORKSPACE_QUALIFIER_NAMESPACE_DEPTH_2026-07-30.md:99`)
applied to a different object -- **and the same sentence's conclusion, *"Do not
build the workspace runtime -- there is no demand case,"* has since been
overturned by the maintainer's ruling of 2026-08-01 (Doc 1:44-50). The maxim
survives its own conclusion; both halves are quoted here so the next reader is
not misled by half of a sentence.**

## 7. What would falsify D9

- **A demand case for cross-workspace relations.** D9.3 is wrong on arrival and C
  collapses toward B. Cheap: remove a branch.
- **A ruling that a workspace IS a VFP data session in the strict sense.** Then
  partitioning is the compatible behaviour, D9.2 reverses, and D9.1's child
  handle becomes ceremony. **Still the most likely way D9 is wrong**, and a
  maintainer call this ruling does not make.
- **D9.4 not being honoured.** Then C's own stated failure mode has occurred and
  D9.3 is AIF-079.
- **A saved posture in the wild containing a cross-workspace `RELATION` line.**
  Then the migration note in sec 4 is not a note, it is a blocker.

## 8. Evidence tier

**Measured:** sec 1 (the workspace-blind resolver, `:524-529`, `:418`), sec 4
items 1-2, 4, 5 (`merge_relation`'s predicate read in full, including the
empty-key arm), item 8, the round-trip note (`:748`, `:766`); sec 5 (both
`in_default_suite` flags, the script's contents and header, the three
unregistered specs, the auto-rename at `cmd_use.cpp:944-972`).
**Source-evidenced:** sec 1's two quotations, sec 3, sec 6's VFP row.
**Chat/AI output:** sec 2's D9.2-D9.5, sec 6's pricing, sec 7.
**Explicitly NOT measured:** whether the ambiguity ledger can be driven non-zero
(sec 5, last bullet); whether any saved posture in the wild carries a
cross-workspace `RELATION` line (sec 7). Both are runs, not reads.

## 9. First draft, rejected -- recorded

An earlier draft was sent back by independent review. Corrections folded above:

1. It framed cross-workspace edges as an open design choice. **They are
   creatable today** and the plan records it at `:279-280`. D9.3 is now
   explicitly a behaviour removal.
2. It asserted *"I1.2 does not make it worse"* about the export/import round
   trip. **D9.3 makes it worse in a specific way** -- sec 4's migration note.
3. It stated 28 store references; the count is **29**, and the draft's own verify
   command returned 29.
4. It said `add_relation` requires both areas open *"in the current workspace."*
   It requires them open **anywhere** -- that is the whole point of sec 1.
5. It never found `merge_relation` or the persisted `RELATION` lines. Sec 4
   item 5 and D8.2.
6. It gated I1.2 on whether two workspaces could be driven. **They can, and were
   mutation-tested the same day.**
7. It cited `:123` for R26's narrowing; the sentence is at `:125`.
8. It quoted half of the *"buy the option"* sentence and omitted the clause that
   opposed it. Sec 6 now quotes both halves.

## 9a. AMENDMENT 2026-08-22 -- D9 conformed to an owner ruling it had reversed

Authorised by the steward in-session ("go") after this author read
`WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` (`AIPR-20260812-010`, review-needed,
**revised after a hostile review**, citations independently re-derived at
`28a14d653`, lane line `AIF-078, coworker on AIF-070`). **That is this lane's
own design note, ten days older than D9, and D9 was written without reading
it.** Third instance in one day of authoring on top of an unread authority.

### What it contradicted

Section 1, under *"ruled by the owner in brainstorm and kept"*:

> Relations are stored **PER WORKSPACE** -- each workspace owns its relation
> map, so `CUSTOMERS`-vs-`CUSTOMERS` never collides because the key never
> leaves its workspace. **Cross-workspace relations are a separate, explicitly
> qualified list.**

**D9.3 refused cross-workspace edge creation.** The owner had already ruled
they exist, held separately and requiring qualification. A refusal is not a
cautious default when a standing ruling says otherwise -- it is a reversal.

Section 2, adopting hostile-review D5's cut:

> the registry is KEYED on the existing `dottalk::reference::WorkspaceIdentity`
> ... **The in-memory handle is a private interning index, never a public
> identity.**

**D9.1 keyed on the raw handle**, which publishes an interning index as
identity -- one of the three uncomparable spellings that review existed to
collapse.

### The amended ruling

> **D9.1 (amended).** Both ends of a relation edge carry a workspace. The
> steward's *"yes we key both ends"* is untouched; the SPELLING changes.
> The public, persisted, compared and qualified identity is
> **`dottalk::reference::WorkspaceIdentity`**
> (`include/reference/data_address.hpp:30-39` -- `logical_name`,
> `profile_path`, `session_id`, with `operator==` and `unspecified()`
> shipping). The in-memory store MAY key on the interned `uint64_t` handle for
> O(1) lookup, because that is private; it may never hand that number out as
> identity, persist it, or compare across a boundary.
>
> **D9.2 (stands, reinforced).** The handle does not partition the closure.
> The design's separate cross-workspace list is precisely a closure that spans,
> which is what R26 defines and Q9 wanted.
>
> **D9.3 (WITHDRAWN and replaced).** No refusal. Each workspace owns its
> relation map -- so same-named parents in two workspaces cannot collide,
> because the key never leaves its workspace -- and **cross-workspace relations
> live in a separate, explicitly qualified list.** Crossing is always spelled,
> never implied, which is the same shape the owner ruled for
> `COMMIT ALL` vs `COMMIT GLOBAL` (design sec 3, R4).
>
> **D9.4 (stands, repointed).** The red-capable spec no longer exercises a
> refusal. It exercises the QUALIFICATION REQUIREMENT: an unqualified
> cross-workspace reference must be reported, never first-matched. That is
> invariant I4 -- *"ambiguity is reported, never first-match"* -- and it is
> what `find_open_area_by_name_ci` cannot do today, since it returns a bare
> `DbArea*` and gains a diagnostic out-parameter across all its call sites.
>
> **D9.5 (stands, strengthened).** Scoped close computes the closure first.
> Invariant I5 adds the half D9.5 did not have: closing a workspace must also
> RELEASE ITS LOCKS, because `locks::release_held` is declared, defined
> (`src/xbase/xbase_locks.cpp:407`) and **called by nothing**, and the
> stale-lock reaper only fires on a dead pid -- so two workspaces in one
> process are not isolated until close releases what the workspace held.

### Consequences for I1.2's scope (sec 4 above)

- The store becomes **per workspace**, not one map with a composite key. Sec 4
  item 1's `RelKey{ws, name}` is superseded: the partition IS the map.
- A second structure is needed for the qualified cross-workspace list. Sec 4
  did not price it.
- The qualified spelling is **already parsed and rendered** -- the canonical
  dotted form `WS.#n.TABLE.RECNO(k).FIELD`, `QualifiedReferenceParser`
  (`src/reference/qualified_reference.cpp`, status supported) and
  `DataAddress::diagnostic_text()` (`src/reference/data_address.cpp:180-246`,
  `CURRENT_WORKSPACE` sentinel at `:193`). I1.2 invents no grammar.
- Sec 4's migration note **inverts**: D9.3's refusal was what made an existing
  cross-workspace edge unrestorable on import. With no refusal, that hazard
  goes away; what replaces it is that such an edge must land in the qualified
  list rather than in a workspace's own map.

### Also stale, carried into D8 and corrected here

- **The DTSHEMA v4 per-area `ws=` field is WITHDRAWN** by invariant I3: *"a
  posture never records which workspace owned an area, because it is loaded
  INTO a workspace named by the command."* D8.3 repeated the reconciliation
  note's "one bump, both fields" including that field.
- **Design sec 3 lists `USE ... AGAIN` as "NEW VERB, must be built".** It
  SHIPPED, same date, with the memo refusal and the auto-rename (registered
  spec `USE_AGAIN`). R1's proposed read-only default for the second instance
  is not what landed -- coherence was MEASURED (UA_T3), not designed away.
- **`include/reference/data_address.hpp:56-59` reads "searched-and-absent: no
  runtime workspace registry, no containment invariant, no cycle guard, no
  depth cap."** All four now exist in `include/xbase/workspace_membership.hpp`.

### The reconciliation this opens, and it is not mine to make

`workspace_membership.hpp` keys on a `uint64_t` handle carrying a name string.
Design sec 2 says identity is `WorkspaceIdentity` and the handle is private.
**What shipped is not what was designed.** D8 recorded Q-R2 as closed because
an object exists; this amendment records that the object does not match its
specification. Reconciling the two -- conform the registry, or amend the design
to what shipped -- is a ruling of its own and the steward's call.

## 9b. RE-AMENDMENT 2026-08-23 -- 9a picked its spelling from a document, and the tree disagrees

> **SUPERSEDED IN PART, same day, by D10.4**
> (`AIF078_D10_WORKSPACE_IDENTITY_LADDER_RULING_V1.md`). 9b's RUNTIME half --
> the store keys on the handle -- stands, and so does the measurement below.
> **Its PERSISTENCE half is wrong:** 9b said persist the workspace NAME,
> reaching for `Entry::name` because that was the field it could see, and
> `Entry` is the SESSION rung. A persisted edge carries the **chain-root
> `WS_ID`** with `WS_NAME` alongside. Read 9b for the measurement; read D10 for
> the ruling.

Authorised by the steward's standing architectural directive, in-session
2026-08-22: *"we have spent the day improving workspaces, the gui is brand new,
and as such more disposable than the engine so modify the new product to the
existing dottalkpp product, so truth can flow from the bottom up."* That
directive settles which side of a spec-vs-runtime disagreement gives way, and
9a resolved one in the other direction.

### The defect in 9a

9a corrected two instances of authoring on top of an unread authority, and
committed a third variety of the same error in the act of doing it. It moved
D9.1's key from the shipped handle onto
`dottalk::reference::WorkspaceIdentity` **because a design note said identity
was spelled that way**. It did not measure whether anything constructs one.

This is the shape the staged plan's standing rule (sec 11h) exists to stop:

> A ruling may cite a project-doc or chat-held copy for **narrative**, never
> for a **fact about the tree**. Facts are read from the tree at authoring
> time.

"`WorkspaceIdentity` is the public identity" is a fact about the tree. It was
taken from a document.

### Measured at authoring time, 2026-08-23, working tree at `f2d4727f`

`grep -rn "WorkspaceIdentity" include src --include=*.hpp --include=*.cpp
--include=*.h` returns **17 lines in exactly three files**:

- `include/reference/data_address.hpp` -- 5 (the declaration and accessors)
- `src/reference/data_address.cpp` -- 6 (its own definition, `operator==`,
  `unspecified()`, and a function-local `static const` default at `:153`)
- `src/tests/test_pdlc_foundation_smoke.cpp` -- 6

**Zero in `src/cli`, `src/xbase`, or `src/gui`.** Every construction of a
populated `WorkspaceIdentity` in this tree is in one test file. Nothing that
opens a workspace, switches one, joins an area to one, or closes one produces
one. It is an AIF-079 instance -- a mechanism built with zero call sites --
and 9a proposed keying the relation store on it.

Worse than unused: **two of its three fields have no producer at all.**
`profile_path` and `session_id` are written nowhere outside that test. The
shipped registry entry (`include/xbase/workspace_membership.hpp:66-78`) is
`Entry{ name, parent, members }` -- it has a name, and it has neither of the
other two. Keying on `WorkspaceIdentity` today does not read an identity; it
requires inventing two values at the moment of use, which is fabrication
wearing a struct.

What DOES ship, and is exercised by three registered specs
(`WORKSPACE_SCOPE`, `WSMULTI`, `USE_ARGS`), is the handle: `std::uint64_t`,
monotonic within a session, never reused after `destroy()` so a stale handle
resolves to nothing rather than to a stranger, `kDefaultHandle = 1` precisely
so 0 can mean "no workspace"
(`workspace_membership.hpp:63`, `:204-213`, `:235-240`).

### What 9a was right about, and it is the reason this is a split and not a revert

A handle is **session-scoped**. It cannot be written into a `.dtschema` and
read back next week, because next week's handle 2 is a different workspace.
That is a real defect in "key both ends on the handle" and it is exactly what
`WorkspaceIdentity` was shaped to solve. 9a saw the right problem and reached
for an unbuilt answer.

D8 already drew the line this needs: **the seam is persistence vs runtime.**

### The re-amended ruling

> **D9.1 (re-amended).** The steward's *"yes we key both ends"* is untouched
> for the third time. Both ends of a relation edge carry a workspace. The
> SPELLING is split on the D8 seam:
>
> - **Runtime, in-process, in-memory:** the workspace is the interned
>   `std::uint64_t` handle. It is what the engine maintains, what every area
>   already carries as `_ws_handle`, what the registry keys, and the only
>   workspace identity any runtime writer in this tree produces. O(1), no
>   allocation, no fabricated fields.
> - **Persisted or crossing a process boundary:** the workspace is its
>   **NAME**, as `workspace_membership::Entry::name` holds it and
>   `name_of()` returns it -- the one field of `WorkspaceIdentity` that has a
>   producer. `profile_path` and `session_id` stay `unspecified()` until
>   something writes them; a persisted edge that carries two invented values
>   is worse than one that carries a name and says so.
>
> **D9.2 - D9.5 stand as amended in 9a.** The per-workspace map, the withdrawn
> refusal, the separate qualified cross-workspace list, the qualification
> requirement under I4, and the lock release under I5 are all unaffected by
> which token spells a workspace.

### The reconciliation, now with a recommendation instead of a shrug

9a closed by naming the disagreement and declining to resolve it: *"What
shipped is not what was designed ... a ruling of its own and the steward's
call."* It remains the steward's call. This section adds what 9a owed it -- a
measurement and a recommendation.

**Recommended: amend the design note, not the runtime.**
`WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` sec 2 reads *"the in-memory handle
is a private interning index, never a public identity."* Under the bottom-up
directive the shipped registry is the senior artifact: it exists, it is
exercised by three green specs, and it is what the GUI redesign will consume.
The design note is correct that a raw session handle must never be PERSISTED
or COMPARED ACROSS A BOUNDARY -- and D9.1 above concedes exactly that half by
persisting the name. What it should give up is the claim that the handle is
private in-process, because in-process is the only place it is used.

**Not recommended, and stated so it is a choice rather than an omission:**
conforming the registry to `WorkspaceIdentity` would mean inventing a
`profile_path` and a `session_id` for every workspace so that a struct built
for a future consumer can be satisfied by a present one. That is the tail
wagging the dog, and the directive says which end is the dog.

### What would falsify 9b

- A runtime writer of `WorkspaceIdentity` outside `data_address.cpp` and the
  test -- then it is not an AIF-079 instance and the measurement is wrong.
- A producer landing for `profile_path` or `session_id` (an AIF-070 profile
  path, say) -- then the struct has content and persisting the bare name is
  the lossy choice.
- A steward ruling that the design note wins. It is his note and his call;
  this section is a recommendation with its arithmetic shown, not a decision.

## 10. Good Neighbor note

- **What changed.** This document. No code, no build, no test.
- **Whose area.** AIF-078's, under D8.1. It reaches into the GUI lane at sec 4
  item 5 (`merge_relation`) and interprets AIF-120's R26 at sec 3 -- R26 is not
  amended, and if its author reads D9.2 as a change rather than a reading, R26's
  owner wins.
- **What authorization.** The steward, in-session 2026-08-22: *"2 assign yourself
  coworker and resolve it too"*, then *"yes we key both ends"* (which IS D9.1),
  then *"now that you know better do better."*
- **How to verify.** `sed -n '520,535p' src/cli/set_relations.cpp`;
  `sed -n '49,60p' src/cli/workarea_util.cpp`;
  `sed -n '1113,1132p' src/gui/core/session.cpp`;
  `sed -n '284,289p;462,467p' src/cli/cmd_regression.cpp`;
  `sed -n '92,98p' include/xbase/workspace_membership.hpp`;
  `grep -c 'relations_store()' src/cli/set_relations.cpp`.
- **How to verify sec 9b, and it is the whole of its argument.**
  `grep -rn "WorkspaceIdentity" include src --include=*.hpp --include=*.cpp --include=*.h`
  -- expect 17 lines in three files, none of them under `src/cli`, `src/xbase`
  or `src/gui`; `sed -n '66,78p' include/xbase/workspace_membership.hpp` --
  expect `Entry` to carry `name`, `parent`, `members` and neither
  `profile_path` nor `session_id`; `sed -n '204,213p;235,240p'
  include/xbase/workspace_membership.hpp` for the monotonic, never-reused
  handle.
- **How to undo.** Delete this file. No code depends on it. To undo sec 9b
  alone, delete the section: 9a stands on its own and its closing paragraph
  already leaves the reconciliation open.

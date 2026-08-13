---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260812-010
  recorded_at_utc: 2026-08-12T00:00:00Z
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
    baseline_commit: 28a14d653
  authorization:
    requested_by: maintainer
    scope: >
      Owner mission: multiple workspaces as a working runtime capability with a
      workspace manager, modelled as GROUPS. This revision folds in a hostile
      design review (2026-08-12) and the owner's residence requirement: RAM and
      memo-resident workspaces carry their own tables and indexes. No build
      authorised by this document.
  report:
    path: docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md
    kind: design_note
---

# Workspace Manager and Groups -- Target Design (revised after hostile review)

    status      : review-needed -- design note, NO build authorised
    lane        : AIF-078, coworker on AIF-070 (owner coworker rule, 2026-08-12)
    owner       : member.derald
    verified    : citations re-derived against 28a14d653 by an independent
                  review agent, 2026-08-12
    supersedes  : the first draft of this file (uncommitted), whose remap
                  mechanism, WS_NONE, W-Q1 fork, owner_ array, and CURSOR/CURRENT
                  prerequisite are all withdrawn below, each with its reason

---

## 0. Provenance

The first draft was reviewed hostile on 2026-08-12 by a clean-context agent
instructed to attack it. Verdict accepted in full: 11 design defects, 6
unpriced costs, 5 prior-art misses, and one structural cut. The worst finding
was self-referential: the draft's "corrected" line numbers matched no commit in
the repository, while its evidence section claimed every citation had been
re-derived -- a document reporting success without doing its job, the exact
defect class it hunts. This revision keeps nothing it cannot cite at
`28a14d653`.

A second opinion (SuperGrok/xAI, 2026-08-12, owner-relayed) endorsed the
revised design in full -- Relation/Reference split and the ordinal cut named
as the two highest-value moves, R2 answered yes, the ROLLBACK-not-RECALL
reading confirmed, and AGAIN's refuse-until-built posture seconded. Recorded
with its epistemic weight stated: that review verified nothing at file:line
and is downstream of this document, so its agreement is corroboration, not
independent evidence (the EVALDIFF lesson: parity is not correctness). Asking
what BOTH reviews missed -- consumers neither read -- produced the GUI finding
in sec 4.

Owner input folded in the same day: workspaces are groups (2026-08-01);
first-come-first-served slots, non-congruent tables, pointer-chain ownership
(2026-08-12); relaxed file sharing arbitrated by record locking; RELATION vs
REFERENCE as distinct address kinds; `WORKSPACE CLOSE ws[n] | ALL`; and --
this revision's trigger -- **residence**: some workspaces live in RAM or in a
memo and carry their own tables and indexes with them.

---

## 1. The target, as invariants

**I1. An area belongs to exactly one workspace -- and there is no null.**
Bare `USE` outside any workspace opens into an implicit, always-present
workspace named `DEFAULT`, which behaves like every other workspace. `DbArea`
carries the workspace handle as a member, beside a slot-index member (the
AIF-078 P1 recommendation; both are facts about the area that the area should
know). The first draft's `WS_NONE` is withdrawn: review D8 showed null-owned
areas become orphans no workspace can adopt and leave the ambiguity rule
undefined; review T4 showed it teaches students that a table can belong to no
database. `DEFAULT` is also what makes classic scripts work unchanged: every
verb they run scopes to `DEFAULT` and behaves exactly as today.

**I2. A workspace owns its areas by chain, never by scanning all slots.**
Scale is bounded by the `MAX_AREA` build vector, and the honest statement is
that three compile-time arrays currently pin it: `XBaseEngine::_areas`
(`include/xbase.hpp:494`, inline member), `table_state`'s
`std::array<AreaState, MAX_AREA>` (`src/cli/table_state.cpp:79-80`), and any
registry map. Raising the cap is the separately-priced G0 ladder (4096 now,
16384 after the slot-in-DbArea fix, 65536 gated on moving the engine off the
stack). The first draft's "1000 x 10000 bounded by memory not design" is
corrected: 10^7 areas is a cap-raise project with its own gates, including the
still-missing `static_assert(max_areas <= INT_MAX)` (filed 2026-07-30, open).

**I3. Slots are first-come-first-served, globally unique -- and postures
speak in ORDINALS.** This is the review's structural cut, adopted. LOAD never
translates a recorded slot number into a new one; it walks the posture's
`AREA` lines in order, allocates a fresh slot per line, and resolves
`CURSOR k` / `CURRENT k` by POSITION in that sequence. There is no remap
table, so the first draft's remap hazard (a `CURSOR` line arriving early
remaps through an empty table silently) cannot exist -- an early ordinal is an
out-of-range index, an ordinary bounds check. This also deletes the proposed
v4 per-area `ws=` field: a posture never records which workspace owned an
area, because it is loaded INTO a workspace named by the command. SAVE
renumbers `AREA` lines 0..N-1 in emission order. The posture format does not
change shape; its numbers change meaning from "slot" to "position", which
`schema_save_to_string` already treats as write-only history. One review
concern dissolves by construction rather than by fix: hostile-review T2 noted
`workspace_session_state.dts` runs `SELECT 21` / `SELECT 24` against slots I3
declares volatile -- but a destructive LOAD into DEFAULT closes DEFAULT's
slots first, so first-come allocation reproduces 0..N-1 exactly as today, and
every classic script (including that registered spec) keeps its slot numbers.
Only scripts that LOAD INTO a second workspace see fresh slots, and those are
new-feature scripts written with the feature in mind.

**I4. Names resolve within their workspace; crossing requires qualification;
ambiguity is reported, never first-match.** The qualified surface is the
EXISTING canonical dotted form -- `WS.#n.TABLE.RECNO(k).FIELD` -- already
parsed by `QualifiedReferenceParser` (`src/reference/qualified_reference.cpp`,
status: supported) and already rendered by `DataAddress::diagnostic_text()`
(`src/reference/data_address.cpp:180-246`, `CURRENT_WORKSPACE` sentinel at
`:193`). The first draft's `ws[1]:AREA` colon syntax is withdrawn: review D6
showed it dies in the shipped parser at the colon, and inventing a third
address spelling beside a supported parser and renderer repeats the DTSHEMA
lesson at the grammar layer. Resolution scoping is honest about its three
distinct rules (review U2): a user-typed name resolves in the CURRENT
workspace; a posture-replayed name (`RELATION`, `KEY` lines) resolves in the
TARGET workspace being constructed; a stored relation refresh resolves in the
relation's OWNING workspace. One resolver, one scope parameter, three callers
that pass different scopes -- and a signature that can carry ambiguity back
(`workarea_util.hpp:32` returns a bare `DbArea*` today; it gains a diagnostic
out-parameter, which is a change at all 15 call sites).

**I5. Lock owner becomes (pid, workspace); closing a workspace RELEASES its
locks.** The second clause is not decoration -- it is what makes the first
true. Review D7, all verified: `current_owner()` is a process singleton
computed once (`src/xbase/xbase_locks.cpp:60-63`); the stale-lock reaper fires
only on a dead pid (`:244`, `:315`), which can never happen between two
workspaces sharing one process; and `locks::release_held` is declared, defined
(`:407`), and called by NOTHING. So intra-process isolation equals
inter-process isolation ONLY IF workspace close releases what the workspace
held -- otherwise a normally-closed workspace leaves live-pid lock files that
nothing but `FORCE UNLOCK` can clear, for the life of the shell. Build items:
owner string gains a workspace suffix; `close_area_if_open`
(`cmd_workspace.cpp:1283`) calls `release_held` for the closing area; the
43 lock call sites across 13 files (review U3) are the priced surface.

**I6. RESIDENCE is a workspace property, and RAM is namespaced per
workspace.** New in this revision, from the owner's requirement. Two axes,
recorded in the registry entry and the catalog row:

    carrier   : FILE | MEMO            (where the posture/container lives)
    residence : DISK | RAM             (where the tables live when open)

Consequences, each grounded:

- **Per-workspace RAM subtree.** `hydrate_minidb` lands container members at
  the RAM root by bare basename today. Two RAM workspaces carrying the same
  table name would collide on the ramfs path, second overwriting first --
  cross-workspace clobber with a success message. Fix is structural, not
  procedural: hydration lands under `ramRoot/<wsname>/`, and the v3
  self-location mechanism (roots injected after line 1 of the payload, per
  load, globals never mutated) already carries exactly this re-pointing. The
  collision becomes impossible rather than guarded.
- **VDISK lifecycle is refcounted by RAM-resident workspaces.** Today unmount
  drops ALL RAM files ("RAM disk unmounted; all RAM files dropped" -- the
  owner's own transcript). Under coexistence that is `schema_close_all()` one
  layer down: one workspace's dismiss must not vaporise another's working set.
  `WORKSPACE CLOSE ws[n]` on a RAM workspace erases `ramRoot/<wsname>/`;
  the mount itself drops only when the last RAM-resident workspace closes.
  The two-exit close (save-state or dismiss) becomes per-workspace instead of
  per-mount.
- **Residence determines index-engine availability, and the registry records
  why.** LMDB never lives in RAM (ramfs contract: LMDB must mmap a real OS
  file -- the owner ruling "lmdb only for disks", proven in WORKSPACE_RAM
  where the LMDB attach fails by design and native CDX fallback attaches). A
  RAM workspace therefore carries CDX/CNX only; the registry entry records
  residence so a refused LMDB attach can say "RAM workspace" instead of
  failing generically.
- **Memo sidecars follow the subtree rule on the real filesystem.** The DTX
  layer bypasses the ramfs (bypass-ledger member 1), so sidecars land on real
  disk under the mount dir. Under multiple RAM workspaces they land under the
  per-workspace subtree, or two workspaces' sidecars collide exactly as the
  tables would have.
- **A MINIDB workspace is self-contained by construction** -- posture, table
  bytes, index bytes, and sidecars in one length-prefixed container, hydrated
  with zero disk reads. Nothing in this design changes that; the WORKSPACES
  catalog is opened transiently under its FLOCK for fetch and does not hold
  an area slot.

**Plus, ruled by the owner in brainstorm and kept:**
- `WORKSPACE CLOSE ws[n]` and `WORKSPACE CLOSE ALL`. No orphan-file question:
  closing releases areas and locks (I5); a file stays open while any area in
  any workspace holds it.
- Relations are stored PER WORKSPACE -- each workspace owns its relation map,
  so `CUSTOMERS`-vs-`CUSTOMERS` never collides because the key never leaves
  its workspace. Cross-workspace relations are a separate, explicitly
  qualified list. (This also repairs review D2: posture `RELATION`/`KEY`
  lines replay into the TARGET workspace's map through the target scope,
  never through a global name search.)
- Two address kinds, named apart: RELATION (area-to-area, cursor-driven,
  follows the parent cursor) and REFERENCE (cell-anchored:
  workspace.area.record.field). REFERENCE is `DataAddress`, which already
  exists, already nests (`WorkspacePath` is a vector), and already renders
  the canonical form.
- Groups: named, overlapping sets of workspaces over the registry. The
  all-workspaces pointer is the universal group. (Vocabulary note from the
  review, T3, accepted: this design says GROUP because "set" is taken twice;
  it must also stop overloading RELATION/REFERENCE further. The two kinds
  above are the last two names this design mints.)

---

## 2. Identity: one spelling, not three

Review D5: the first draft put three uncomparable spellings of "which
workspace" in play. Adopted fix (the review's second cut): the registry is
KEYED on the existing `dottalk::reference::WorkspaceIdentity`
(`include/reference/data_address.hpp:30-39`, `operator==` shipping). The
in-memory handle is a private interning index, never a public identity.
`WorkspaceEntry` becomes the registry's row FOR a WorkspaceIdentity, carrying
runtime-only state: interned handle, slot chain head, current-area-within-
workspace, residence, carrier, catalog `WS_ID` when memo-carried.

Two consequences the first draft missed:

- **`DbAreaIdentity::generation` gets its first writer.** Review D4: a
  REFERENCE captured before SAVE compares false to the same cell after LOAD,
  because equality is slot-based (`data_address.cpp:54-58`) and I3 reallocates
  slots -- and `generation`, the field that exists to catch exactly this, has
  zero writers in the tree. The registry increments an area generation on
  every slot rebind. Cross-LOAD reference identity then has a defined answer
  (same workspace identity + same table identity + same record selector;
  generation distinguishes "same slot, different life").
- **Per-workspace current area is a real item, not a footnote.** Review U6:
  `infer_parent_from_workarea()` (`set_relations.cpp:110-118`) anchors REL on
  the single global `workareas::current_slot()`. Under coexistence the anchor
  is `entry.current_area` of the workspace being operated on, and
  `XBaseEngine::_current` becomes "current area of the CURRENT workspace" --
  one more consumer of the registry, on the critical path of gate W4.

---

## 3. Command surface

    WORKSPACE LOAD <name> [INTO <ws>]     -- INTO omitted = INTO DEFAULT,
                                             destructive WITHIN that workspace
                                             only. Classic one-workspace use is
                                             therefore unchanged by construction,
                                             not by promise.
    WORKSPACE CLOSE ws[n] | <wsname>      -- releases its areas, its locks, its
                                             RAM subtree. Selection moves to the
                                             CURRENT workspace's current area,
                                             never to an arbitrary survivor
                                             (review D9: the normalize fallback
                                             at cmd_workspace.cpp:465-483 scans
                                             all slots and would select into a
                                             foreign workspace).
    WORKSPACE CLOSE ALL                   -- today's semantics, said explicitly.
    WORKSPACE SELECT <ws>                 -- sets the current workspace.
    WORKSPACE LIST                        -- registry projection: name, carrier,
                                             residence, areas, groups, locks held.
    WORKSPACE GROUP ADD|REMOVE|LIST       -- membership over handles.
    USE <file>                            -- opens into the CURRENT workspace.
    COMMIT ALL / ROLLBACK ALL             -- scoped to the CURRENT WORKSPACE
                                             (owner ruling, 2026-08-12). "ALL"
                                             means all areas OF THIS WORKSPACE,
                                             consistent with every other verb.
    COMMIT GLOBAL / ROLLBACK GLOBAL       -- the explicit every-workspace forms
                                             (same ruling). Crossing workspaces
                                             is always spelled, never implied.
    USE <file> AGAIN                      -- NEW VERB, must be built (review D1:
                                             the duplicate-open guard at
                                             cmd_use.cpp:537-555 no-ops on any
                                             already-open file, and no refcount
                                             exists anywhere). Until AGAIN lands,
                                             same-file-in-two-workspaces is
                                             REFUSED loudly, not silently
                                             no-opped -- the owner's default
                                             stands and the relaxation is a
                                             later, separately-gated step.

`WORKSPACE OPEN` (review D10): scoped to the current workspace like every
other verb. Its close-everything behaviour survives only as
`WORKSPACE CLOSE ALL` said out loud. The dirty-check it triggers
(`dirty_prompt.cpp:157-173`) is scoped the same way and its prompt names the
workspace.

---

## 4. What must change -- honest counts (review U1-U3)

| Surface | Priced in first draft | Actual |
|---|---|---|
| all-slot `< xbase::MAX_AREA` enumerations | 6 sites | **68 sites, 27 files** (19 in cmd_workspace.cpp alone; includes CLOSE ALL, COMMIT, ROLLBACK, SET ORDER sweeps, LIST STRUCTURE, dirty_prompt) |
| `find_open_area_by_name_ci` | "a scope parameter" | **15 call sites, 3 scoping rules, signature change** (returns bare `DbArea*` today) |
| lock call sites | absent from the table | **43 sites, 13 files** |
| per-workspace current area | absent | new item, critical path for W4 |
| `USE` duplicate-open guard | one site | **two same-named functions** (`cmd_workspace.cpp:451` and `cmd_use.cpp:303`); the second governs USE |
| GUI consumers | absent from both reviews | **CLI output text is an API**: the GUI matches markers (`gui/core/session.cpp:164` "WORKSPACE OPEN: scanning directory:", `:610` "Selected area ", `:357` parses shell output for index attachments) so summary-line wording changes break the GUI mirror silently -- and the GUI carries its OWN dtschema parser (`load_dtschema2_areas`, `:470`), a third reader of the posture format that must track ordinals and v4 or drift. A live two-things-that-never-compare, pre-existing, made hotter by this design |

Phasing follows from the counts: registry + DEFAULT + chain (touches nothing
listed above); then the resolver and its 15 sites; then the 68 enumerations
mechanically, each deciding "this workspace" vs "all workspaces" explicitly;
then locks; then residence namespacing; then groups, which by then are a set
over handles.

---

## 5. Gates

Field-value markers throughout (FIELDMGR_APPEND doctrine); every spec
self-bootstrapping, sandboxed, self-erasing, registered.

| Gate | Proof | Anti-decoration clause |
|---|---|---|
| W0 | `REGRESSION ALL` green with the registry live and only DEFAULT populated | marker asserts registry reports exactly one workspace AND the suite is green in the same run |
| W1 | two workspaces loaded INTO, both live, a value read from each | values differ by construction so a cross-wire cannot pass |
| W2 | LOAD INTO shortfall aborts; the OTHER workspace untouched | assert the other workspace's value AND its area count after the refusal |
| W3 | same table name in both; unqualified = reported ambiguity naming both; qualified reaches each | the ambiguity MESSAGE is asserted, not just nonzero exit |
| W4 | relations do not cross: parent in A never slaves a child in B; posture RELATION lines bind inside their target workspace | replay the D2 sequence verbatim as the fixture |
| W5 | save from B emits exactly B: **count of AREA lines == B's chain length**, then round-trip values | review D3: without the count assertion this gate cannot fail |
| W6 | one workspace in two groups; enumerate both; remove from one, other intact | -- |
| W7 | locks: A locks, A closes, B immediately locks the same record | proves release-on-close; the D7 sequence verbatim |
| W8 | residence: two RAM workspaces carrying the same table name; both hydrate; both read by field value; closing one leaves the other's RAM subtree intact; unmount only after both close | the collision this revision exists to prevent |

---

## 6. Withdrawn from the first draft, with reasons

| Item | Reason |
|---|---|
| slot remap table + 4 keyword handlers | review cut: ordinals delete the mechanism and its hazard |
| v4 per-area `ws=` field | postures load INTO a named workspace; ownership is not the posture's to record |
| W-Q1 (LOAD destructive-vs-additive fork) | dissolved: LOAD is always into a named workspace; INTO DEFAULT preserves classic behaviour |
| `WS_NONE` | D8 orphans, T4 teaching harm; replaced by DEFAULT |
| `owner_` side array as the association | I1: the area carries its workspace; a side table can desync, a member cannot |
| `ws[i]:` colon syntax | D6: does not parse; the dotted canonical already ships |
| CURSOR/CURRENT test prerequisite | already satisfied: WORKSPACE_SESSION asserts both by field value (SS_T1/SS_T2), runtime-proven 2026-08-11 |
| "recursion guarded by DEPTH/SELF_REF" | D11: DEPTH is written "0" unconditionally and read by nothing; it is a column, not a check. Nesting's owner makes it real; this design claims nothing from it |

Kept intact from the first draft: sec 2a (the v4 boundary and the
DTSHEMA/DTSCHEMA migration -- reader widens now, writer flips at v4, FMT is
the constraint because superseded catalog rows are append-only). The review
verified all three grounds and it carries one change: v4's queue drops from
three items to two (`kind` + spelling), since `ws=` is withdrawn. The v4
spelling flip has an assigned owner (owner statement, 2026-08-12); this
design defers to that lane and keeps only the reader-widening as its own
prerequisite-free item.

---

## 7. Open questions -- the short list that remains

- **R1.** `USE ... AGAIN` semantics when it lands: does the second area share
  the OS file handle or reopen? (Locking already arbitrates records either
  way; the question is buffer coherence between two areas on one file inside
  one process.) **Proposed default for v1: the second and subsequent areas
  open READ-ONLY.** Coherence then has no write side and dissolves; two
  writable areas on one file becomes a later, separately-gated relaxation
  with its own marker, exactly like AGAIN itself.
- **R2.** Does `WORKSPACE SELECT` change the engine's current AREA too, or
  only the workspace scope? (Owner instinct earlier: selection is workspace
  state -- `entry.current_area` -- which implies yes, SELECT restores that
  workspace's own selection.)
- **R3.** Group verbs: address-only in v1 (owner leaning, reconciliation
  Q-R3), or is `WORKSPACE SAVE GROUP <g>` wanted early? Persistence of a
  group is catalog work and belongs with AIF-070's surface.
- **R4. RULED (owner, 2026-08-12): per-workspace.** COMMIT ALL / ROLLBACK ALL
  scope to the current workspace; COMMIT GLOBAL / ROLLBACK GLOBAL are the
  explicit every-workspace spellings. This makes the transaction verbs
  consistent with CLOSE and SAVE -- "ALL" always means "all of mine", and
  crossing is always spelled. One flag recorded for the owner: the ruling
  arrived as "commit global recall globall"; it is recorded here as ROLLBACK
  GLOBAL on the reading that "recall" was shorthand, because RECALL is an
  existing verb in this engine (un-delete, cmd_recall.cpp) and RECALL GLOBAL
  would collide with it -- the same verb-collision class the WRITEBACK ruling
  rejected COMMIT and FLUSH for. If RECALL GLOBAL was meant literally, say so
  and this paragraph inverts.

---

## 8. Evidence tier

**Source-evidenced at `28a14d653`:** every file:line above; re-derived by the
independent review agent, not carried forward from the first draft.

**Runtime-observed, owner's console 2026-08-12:** the twelve
WORKSPACE_WRITEBACK markers, the VDISK unmount-drops-all line, the LMDB-
refused-in-RAM behaviour (WORKSPACE_RAM).

**Chat/AI output:** sections 1-7 as design. No code written. **This document
authorises no build.**

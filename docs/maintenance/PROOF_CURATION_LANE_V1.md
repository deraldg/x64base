# Proof curation lane (V1)

    Steward   : member.ai.claude.cowork
    Owner     : member.derald
    Opened    : 2026-08-13, tree at da02641b1
    Trigger   : owner ruling -- "the proofs ARE important, and we are harvesting
                enough that they need official curation"
    Status    : CHARTER. Section 3 is landed. Sections 4 and 5 are proposals and
                nothing in them is built.
    Parent    : the standing rule of 2026-08-13 -- "if we don't curate our work
                in rapid dev, we will lose our work in rapid dev"

---

## 1. What already exists, and it is more than it looked like

Credit first, because the machinery is good and three of this steward's first
four "findings" about it were wrong:

- **`labtalk/registries/proofs.d/`** -- 60 files, one record per file. The
  banner states the reason: *"One file per record means two sessions never touch
  the same file."* That is a real concurrency property, deliberately chosen.
- **`proofs.d/_header.yaml`** -- the controlled vocabulary (`proof_states`) as a
  proper fragment, not hand-maintained in generated output.
- **`tools/registries/registry_fragments.py`** -- a merge tool with header keys,
  computed indexes, and a dry-run default.
- **Filename-enforced uniqueness** -- `safe_name()` derives the fragment name
  from the record id, so a duplicate id cannot quietly coexist.

That is a primary key, a domain vocabulary, and collision-free concurrent
authoring. The design is sound. What follows is not a rescue.

## 2. What the day measured

**2.1 A domain constraint that nothing enforced.** `design_intended` was in use
across `ai_portal.yaml`, `portal.yaml`, `projects.yaml` and three proof
fragments, and had never been declared in `proof_states`. It was ALSO spelled
two ways -- `design-intended` (2) and `design_intended` (1). Same shape as the
Quantum Memo Zoo retrieval failure the same day: the token people write and the
token the index knows drifted apart, and nothing compared them.

**2.2 The generated file was behind its own fragments.** Re-running the merge
moved `proofs.yaml` from **57 records to 59**. Two fragments had been authored
and never merged. Every consumer of the flat file -- including the ECO map's
published "57 proof records" -- was reading a stale count, and nothing said so.

**2.3 Detection existed; enforcement did not.** The ECO ecoschema map caught 2.1
on the day it first published, rendering "3 proof(s) carry a state not in the
declared vocabulary" as a DEFECT panel. A generated map noticed what no gate
did. Detection in a report is worth having, but a report nobody opens on a
Tuesday is not a constraint.

**2.4 Subjects are already in the ids, and mostly unused.** 59 records across 31
distinct `proof.<segment>` namespaces:

    ai_portal 8, bbs 7, engine 5, pdlc 4, lmdb 3,
    wal 2, lab 2, aif078 2, ai_friendly 2            = 35 records, 9 homes
    22 singletons

Four singletons cannot be grouped at all, because the subject is fused into the
leaf rather than occupying a namespace segment:

    proof.owner_dogfood_caught_cross_slot_leak
    proof.golden_rule_verify_before_assert
    proof.cnx_orthogonality_recno_permutation
    proof.grok_lane1_coworker_kind_collision

Each sorts as its own namespace of one. The id scheme is `proof.<subject>.<name>`
by convention, and convention is all it is.

## 3. LANDED 2026-08-13

- `design_intended` declared in `proofs.d/_header.yaml`, terse to match its nine
  siblings.
- Two fragments normalized from `design-intended` to the underscore spelling
  that the rest of the tree uses.
- `registry_fragments.py merge --write` re-run. All 59 records now carry a state
  in the declared vocabulary: `runtime_observed` 34, `source_defined` 18,
  `design_intended` 3, `validated` 3, `case_registered` 1.
- The ECO bridge's DEFECT panel for undeclared states should now be empty. NOT
  VERIFIED -- the map needs regenerating and republishing to confirm, and that
  is ECO's lane, not this one. The map's published header also still reads
  "57 proof records" and will read 59 after regeneration.

One `design-intended` spelling REMAINS in `proofs.yaml` at line 358 and is
correct: it is English prose inside a `notes` field ("Duplex switch remains
design-intended"), not a state value. Recorded so the next sweep does not
"fix" it. A gate must test the STATE FIELD, not the file.

## 4. PROPOSED: dogfood the registry into the engine

Owner question, 2026-08-13: *"dogfood our system?"*

The asymmetry is real and measurable. The house already keeps its knowledge
about COMMANDS in its own tables -- `SYSCMD`, `SYSFUNC`, `SYSHELP`, `SYSMSG`,
`SYSARGS`, `SYSSUBCMD`, `SYSFLDDIC`, `SYSENTVAR` all live under
`dottalkpp/data/metadata/`. What it keeps in flat YAML is its knowledge about
PROOFS, projects, lanes and claims. The catalog got dogfooded; the evidence did
not.

And `proofs.d/` is, structurally, a hand-rolled table: primary key by filename,
domain constraint by header fragment, referential integrity by convention,
joined by a Python merge tool -- next to an engine that does all three natively.
Section 2.1 is what a domain constraint expressed as prose buys you.

**As a table, the wins are concrete rather than aesthetic:**

- `state` becomes a field with a `RULE` validated by `VALIDATE`, so
  `design-intended` is REFUSED at write rather than noticed at publish.
- `SET ORDER TO TAG SUBJECT` plus `SEEK` makes 2.4 a lookup instead of a filing
  exercise.
- `SMARTLIST FOR STATE = "design_intended"` and `SQLSEL` over the evidence.
- `REL` from a proof to its lane, its AIF claim, and its regression spec --
  three joins the flat files can only express as strings today.

**The counter-argument, which is not weak.** "One file per record means two
sessions never touch the same file" is a property a single DBF gives up. Text
fragments diff and merge without a tool; a binary table does neither. The engine
has cross-process cooperative FLOCK and the BBS store already appends under it,
so machine concurrency is handled -- but the HUMAN merge story gets worse, and
this project runs concurrent sessions as a matter of course.

**Recommended shape, therefore: projection, not migration.** Keep YAML as the
authored form. Add `SYSPROOF.dbf` as a generated projection alongside
`proofs.yaml`, and move VALIDATION to the table. The registry stays mergeable,
the constraint becomes enforced, and every query surface arrives for free. If
the projection proves itself, the direction of authority can flip later -- and
that is deliberately a separate decision, not a foregone one.

Precedent in the tree: `WORKSPACES.dbf` is exactly this shape already -- a table
whose rows describe things that live elsewhere.

## 5. PROPOSED: the gates this lane owes

1. **Vocabulary gate.** A state not in `proof_states` fails the pre-commit gate.
   Today the ECO map reports it and the gate does not.
2. **Freshness gate, and it must compare against TRACKED fragments.** A naive
   mtime comparison is not enough, and the day proved why. Running the merge
   also regenerated `ai_runs.yaml` at +227 -3, which looked like ordinary drift
   and was not: five fragments (`runs.d/AIPR-20260810-002` through `-006`) are
   AUTHORED AND UNTRACKED. That registry is not behind because a merge was
   skipped; it is behind because its source does not exist in the repository,
   so no clone can reproduce it. An mtime gate reports GREEN on exactly that
   condition -- the fragments are present and newer. The gate must ask whether
   every contributing fragment is TRACKED, not merely whether it is on disk.
3. **Namespace gate, advisory first.** A new id without a `proof.<subject>.<name>`
   shape gets a warning, so 2.4 stops growing while the existing four are
   rehomed deliberately rather than in bulk.

Ordering is deliberate: 1 and 2 are cheap and prevent recurrence; 3 changes ids,
which breaks references, and should not run until the subject taxonomy is agreed.

## 6. Non-goals

- Not renaming the four fused-subject ids in this pass. An id is a reference; a
  bulk rename is a separate, reviewed change.
- Not migrating authority into the engine. Section 4 proposes a PROJECTION and
  says plainly that the authority question stays open.
- Not touching the ECO map. Its regeneration and republication belong to the
  session that holds ECO.

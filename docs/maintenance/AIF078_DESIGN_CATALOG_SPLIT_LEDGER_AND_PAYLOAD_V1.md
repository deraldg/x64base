# AIF-078 DESIGN -- SPLIT THE CATALOG: AN IDENTITY LEDGER AND ITS PAYLOAD

    Status  : DESIGN, review-needed. NOT a ruling and NOT an implementation.
    Author  : member.ai.claude.cowork (run COWORK-20260827-001)
    Date    : 2026-08-27
    Lane    : AIF-078. Uses the lane's number; no new AIF claimed, because this
              is a design within an existing lane rather than a finding.
    Asked by: member.derald, in three moves that are the whole design --
              "the catalog of what", then "can we split the table", then
              "we can relate anything to them, make a key to link them if they
              need it".
    Prior   : AIF-078 D10.1 (a workspace is born durable), D10.2 (the chain-root
              WS_ID IS the durable identity), D10.3 (retirement is supersession);
              `docs/maintenance/PROOF_CURATION_LANE_V1.md` sec 4.

## 1. THE QUESTION THAT STARTED IT

Asked what `WORKSPACES.dbf` is a catalog OF, the honest answer turns out to be:
**three different things at once.** Measured from the create block
(`src/cli/cmd_workspace.cpp:2815-2835`) and from 252 live rows:

- an **identity** -- WS_ID, WS_NAME, PREV_ID lineage, SUPERSEDED
- a **saved posture** -- FMT `DTSHEMA 2/3`, which tables were open where, with
  which orders and cursors
- a **whole database** -- FMT `MINIDB 1`, tables and indexes carried in the
  SNAPSHOT memo field. `mcc_db` is 94,200 bytes of one.

Plus a fourth row kind that is none of those: FMT `BIRTH 1`, SIZE_B 0 -- an
identity with no payload, written as a payload row that says so
(`cmd_workspace.cpp:3097-3099`).

## 2. THE MEASUREMENT THAT MAKES THE SPLIT OBVIOUS

**`scan_catalog()` reads FOUR FIELDS.** `cmd_workspace.cpp:2996`, body at
`:3003-3014`:

    WS_ID       PREV_ID       WS_NAME       SUPERSEDED

It never touches FMT, SIZE_B, PAYLOAD_SHA, SNAPSHOT or any other column. And
every catalog operation funnels through it: SIX `open_catalog` call sites cover
NEW, SAVE, DESTROY, DELETE, LOAD and the registry report.

So the table already has two halves, and **only one of them is ever scanned**:

    LEDGER   WS_ID  WS_NAME  PREV_ID  SUPERSEDED  SAVED_AT  AUTHOR
    PAYLOAD  SCHEMA_NAME  FLAVOR  OS_COMPAT  FMT  PAYLOAD_SHA  SIZE_B
             EST_HYD_B  MAX_AREAS  DEPTH  SELF_REF  DBF_ROOT  IDX_ROOT
             VERIFIED_AT  SNAPSHOT(M)

## 3. THE PROPOSAL

Two tables, joined on WS_ID.

    WORKSPACES.dbf   the identity LEDGER. Narrow, no memo. One row per mint or
                     supersession. The chain lives here and stays unbroken.
    WSPAYLOAD.dbf    the saved STATE. One row per row that HAS a payload.
                     WS_ID is the foreign key. SNAPSHOT memo lives here only.

A birth stops being `FMT="BIRTH 1", SIZE_B=0` and becomes **a ledger row with no
payload row.**

## 4. FOUR ARGUMENTS, EACH GROUNDED IN SOMETHING MEASURED

**R6 -- absent must not be representable among present.** A birth is currently
encoded as a payload-shaped row whose contents mean "there is no payload". That
is the defect this house names most often, sitting in the catalog's own schema.
After the split, absence is the absence of a row.

**THE COUNT DISCIPLINE.** `COUNT` over `WORKSPACES.dbf` today returns a number
from an authority holding four kinds -- identities, postures, containers and
births -- with no discriminator applied. On 2026-08-27 that produced a census
whose numbers would not reconcile, which is how the FOR-predicate defect
(commit `7d7b81581`) was found. After the split, "how many identities" and "how
many saved states" are different queries against different tables and neither
can be mistaken for the other.

**WEIGHT ON THE HOT PATH.** `WORKSPACES.dtx` is **3,125,392 bytes** against a
**178,423** byte table -- 17x the table it decorates. `scan_catalog` is called
on every mint, save, retire and delete, and opens a table dragging a 3 MB memo
it never reads.

**IT GIVES L1's GAP A CHEAPER ANSWER.** Measured 2026-08-27: stopping adoption
of a catalog-only live head requires `WORKSPACE DELETE`, which flags the name's
ENTIRE chain -- 110 of 252 rows in one afternoon, dropping visible rows from 216
to 106. The verb itself says adoption is stopped by SUPERSEDED and not by the
flag, but there is no verb that does only the smaller thing, because supersede
and flag-the-history are welded together in one table. Separate the halves and
saved state can be cleared while the identity ledger and its high-water stand.

## 5. THE KEY ALREADY EXISTS -- AND D10.2 ALREADY RULED IT

`cmd_workspace.cpp:2869-2870`:

    unique_reg::set_unique_field(a, "WS_ID", true);
    unique_reg::set_primary_field(a, "WS_ID");

**WS_ID is already declared unique and primary.** The split does not CREATE the
key. It FREES it: today it is a primary key on a row that also carries up to
106 KB of memo, so nothing sensible wants to join to it.

And the ruling is already made. **D10.2 says the chain-root WS_ID IS the
workspace's durable identity.** The schema does not reflect its own ruling -- it
stores that identity as a column on a row that also holds a database. Every
consequence in sec 4 follows from that one gap.

## 6. WHAT BECOMES RELATABLE

The payload table stops being special; it is merely the FIRST thing related to
the ledger. Listed to show the shape, not as commitments:

- **locks** -- AIF-144 measured that a lock records `host:pid:ms` and no member.
  It records no workspace either. A lock that names the workspace it was taken
  in is a join away, once there is a narrow key to join to.
- **proofs** -- `PROOF_CURATION_LANE_V1.md` sec 4 proposes `SYSPROOF.dbf` and
  cites `WORKSPACES.dbf` as its precedent: "a table whose rows describe things
  that live elsewhere". That precedent gets better if the thing has a key.
- **regression runs** -- which spec minted which identity, on which run. Today
  that is inferred from SAVED_AT timestamps and name conventions; it took an
  hour on 2026-08-27 to establish that eight of twenty-one live heads came from
  that morning's own carrier proving.
- **members** -- who owns a workspace. The identity store already persists
  `profile_home_key` per member and nothing consumes it (AIF-144).
- **nesting** -- parent/child is a runtime handle today and durable only as
  PREV_ID lineage. A real edge could be a row.

## 7. WHAT IT COSTS, STATED RATHER THAN IMPLIED

- **Migration of 252 rows** into two tables, on durable data with real history.
  Not reversible by a flag.
- **`ensure_catalog` creates two tables; `open_catalog` opens two, or joins.**
  Joining them with the engine's own `REL` would be the system eating its own
  cooking, which is where `PROOF_CURATION_LANE`'s "dogfood our system?" question
  actually leads.
- **THREE SPEC ARMS BREAK, and they are named.**
  `workspace_identity_ladder.dts:117-119` reads FMT, SIZE_B and PREV_ID from one
  located row:

        WSL_T1_birth_row_is_self_describing   (ALLTRIM(FMT) = "BIRTH 1")
        WSL_T2_birth_row_carries_no_payload   (SIZE_B = 0)
        WSL_T3_birth_row_is_the_chain_root    (PREV_ID = 0)

  After the split, T3 still reads the ledger. T1 and T2 assert properties of a
  row that will no longer exist -- and their replacement is stronger: a birth is
  proven by the ABSENCE of a payload row rather than by two sentinel values. But
  absence cannot be asserted in this language (USE_AGAIN, three cuts), so those
  two arms need a contrast fixture, not a rewrite in place. **That is the
  hardest part of this design and it is not solved here.**
- `WSL_T5` and the `PG_*` arms read SUPERSEDED, which stays in the ledger.
  Unaffected.

## 8. WHAT THIS DOES NOT FIX

**It does not fix L2.** `workspace_identity_ladder.dts` writes through the
WORKSPACES slot and reads through the DBF slot (`SET PATH DBF workspaces`,
DATA-relative and pinned to production). That split is untouched by how many
tables the catalog has. Recorded so a good idea is not credited with solving an
unrelated problem.

It does not address the reporting defects, name reclamation, or concurrent
catalog writers.

## 9. ALTERNATIVES, NOT RULED

- **(a) Split as proposed.** Two tables, WS_ID the foreign key.
- **(b) Split the MEMO only** -- move SNAPSHOT to its own table, leave the other
  columns. Cheaper, fixes the 3 MB hot-path weight and nothing else. The R6 and
  count-discipline arguments survive unaddressed.
- **(c) Do nothing** and treat sec 4 as documentation. Defensible: the catalog
  works, and 252 rows is not a scaling problem. The cost of (c) is that every
  future consumer joins to a fat row or does not join at all.

Recommend (a). (b) is the honest half-measure and is listed so it is a rejected
alternative rather than an unconsidered one.

## 10. HOW TO VERIFY EVERY CLAIM ABOVE

    grep -n "scan_catalog" -A 20 src/cli/cmd_workspace.cpp     # reads 4 fields
    grep -c "open_catalog(a" src/cli/cmd_workspace.cpp          # expect 6
    sed -n '2815,2835p' src/cli/cmd_workspace.cpp               # the field set
    sed -n '2869,2870p' src/cli/cmd_workspace.cpp               # unique + primary
    sed -n '3097,3099p' src/cli/cmd_workspace.cpp               # BIRTH 1 / SIZE_B 0
    grep -n "WSL_T1\|WSL_T2\|WSL_T3" dottalkpp/data/scripts/workspace_identity_ladder.dts
    ls -l <DATA>/workspaces/WORKSPACES.dbf                      # 178,423
    ls -l <DATA>/workspaces/WORKSPACES.dtx                      # 3,125,392

The two file sizes are deliberately written with a placeholder root rather than
a repo path. The catalog is NOT TRACKED BY GIT -- verified 2026-08-27 with
`ls-files --error-unmatch` -- so citing it by path would make this document a
WIDOW source for the cited-paths gate. It is runtime data, not tree content.

## 11. GOOD NEIGHBOUR

- **What changed:** nothing executable. This document only.
- **Whose area:** `src/cli/cmd_workspace.cpp` and the durable catalog schema --
  engine and data. Any implementation wants an explicit go and a migration plan
  of its own.
- **Authorization:** the owner's "do it" for this DESIGN, 2026-08-27. The shape
  is not ruled; that is what this asks for.
- **How to verify:** sec 10, eight read-only commands.
- **How to undo:** delete this file. Nothing was implemented.

**Author does not self-approve.**

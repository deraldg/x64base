---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-100
  recorded_at_utc: 2026-08-22T00:26:04Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 4d65d9281
  authorization:
    requested_by: maintainer (member.derald), in-session. The multi-workspace
      descent of 2026-08-21 opened a memo-resident database in the Workbench for
      the first time. That gives Q-R5 of the AIF-070/AIF-078 reconciliation a
      MEASURED answer where it previously had only an anticipated one.
  report:
    path: docs/maintenance/AIF120_WORKSPACE_PATH_DEPTH_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R110: keep `WorkspacePath`, and strike the reason given for keeping it

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-22.

Answers **Q-R5** of `docs/maintenance/WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md`
(sec 4, sec 6):

> "Keep or revert Q7's `WorkspacePath`? Recommend keep-and-re-justify, revert if
> AIF-070 needs no nesting."

and the re-justification that section 4 proposed:

> "keep it, and re-justify it honestly -- as headroom for AIF-070's memo-resident
> case, which *is* structurally nested (a workspace inside a memo inside a row
> inside a workspace) ... **If AIF-070's whitepaper does not need nesting either,
> revert it.**"

**Ruling: keep the type. Strike that justification.** It is half true, and the
half that is true is the half that does not bear on an address.

---

## 1. What was measured

Three censuses, all read-only, all against the live corpus rather than the
design documents. They ship with this ruling as
**`tools/dbf/minidb_depth_census.py`** -- an independent re-implementation of the
container grammar (`include/dottalk/minidb.hpp:26-28`), the DTX record layout
(`include/memo/dtx_format.hpp`) and the X64 table header, so agreement with the
engine is evidence and not an echo. The script is tracked rather than left in
`tmp/`: R109b's lesson was that a check which does not ship with the document it
validates is an assertion, not a check.

### 1a. The container corpus -- `minidb_depth_census.py containers`

| | |
|---|---|
| containers scanned | **37** |
| members | **623** -- 325 `.dbf`, 252 `.cdx`, 46 `.dtx` |
| members that are themselves a `MINIDB 1` container | **0** |
| members that are themselves a `DTSHEMA` posture | **0** |

### 1b. One level further down -- `minidb_depth_census.py objects`

A file listing cannot see the recursion even if it is there: a memo-resident
workspace lives inside a `.dtx` *object*, not as a member file. So every live
object inside every carried `.dtx` was unpacked and classified.

| | |
|---|---|
| live memo objects inside carried `.dtx` members | **196** |
| of those, a `MINIDB 1` container | **0** |
| of those, a `DTSHEMA` posture | **0** |
| the 37 postures naming `WORKSPACES` (the self-reference vector) | **0** |

The 196 objects are ordinary memo text; the first is literally
`"carried through the container"`, a round-trip fixture.

### 1c. The live catalog -- `minidb_depth_census.py catalog`

The live catalog is `dottalkpp/data/workspaces/WORKSPACES.dbf` -- untracked by design: it is the running table the engine writes to, not a repo artifact, and staging it would freeze evidence that is supposed to stay live.  <!-- cite-check:ignore -->
106 rows, read with an independent DBF reader:

| column | value across all 106 rows |
|---|---|
| `DEPTH` | **0**, every row |
| `SELF_REF` | **F**, every row |
| `PAYLOAD_SHA` | **empty**, 0 / 106 |
| `EST_HYD_B` | **empty**, 0 / 106 |
| `FMT` | `MINIDB 1` x37, `DTSHEMA 3` x56, `DTSHEMA 2` x13 |
| `MAX_AREAS` | populated, 1 .. 43 |

The 37 `MINIDB 1` rows cross-check the 37 containers of 1a exactly.

`DEPTH` has exactly one writer, `src/cli/cmd_workspace.cpp:2419`, which writes
the string `"0"` unconditionally with the comment *"leaf until hydration says
otherwise"* -- and nothing anywhere says otherwise.

---

## 2. Finding F1 -- at rest, the nesting is real, and it is exactly one level

Depth 2 exists: a workspace holds a table, whose memo field holds a container,
which holds tables. That is not theoretical; it is the 37 rows above, and the
2026-08-21 descent opened one of them (13 tables, 11 index containers).

Depth 3 does not exist anywhere in the corpus. Not as a member, not as a memo
object, not as a self-referential posture. **0 of 623, 0 of 196, 0 of 37.**

The reconciliation doc's phrase *"a workspace inside a memo inside a row inside
a workspace"* is therefore **correct as written** -- and it describes depth 2,
which is a container and its contents, not a path.

## 3. Finding F2 -- at runtime it is not nesting, it is succession

This is the finding that decides Q-R5, and it was not available when the
reconciliation was written.

`schema_load_from_stream()` -- the **single** parser every carrier feeds
(`src/cli/cmd_workspace.cpp:1803`, called by the file carrier at `:2083`, the
memo carrier at `:2655`, the MINIDB carrier at `:2759`, the RAM carrier at
`:3235`) -- calls **`schema_close_all()` at `src/cli/cmd_workspace.cpp:1889`**,
before it opens a single area of the payload.

The Workbench does the same thing at an independently written call site:
`Session::mirror_workspace_posture()` closes every open area and clears the
area list (`src/gui/core/session.cpp:1906-1909`) before mirroring the payload.

So on **both** surfaces, and on **all four** carriers, opening the inner
workspace **closes the outer one first**. There is no instant at which the
carrier and the payload are both open.

**Consequence.** An address is a runtime surface. If the two workspaces never
coexist at runtime, no address ever needs two workspace segments. Depth 2 at
rest collapses to depth 1 at runtime *by construction*, on every path in the
tree. The memo-resident case does not generate a depth-2 **address**, and the
justification section 4 proposed does not hold.

## 4. Finding F3 -- the recursion apparatus is chartered and unexercised

`DEPTH`, `SELF_REF` and `PAYLOAD_SHA` were created as "the recursion guard's
declaration half" (`src/cli/cmd_workspace.cpp:2165-2190`). Measured: `DEPTH` is
hardcoded 0 by its only writer, `SELF_REF` has never been `T`, `PAYLOAD_SHA`
has never been written. There is no cycle guard, no depth cap, and no consumer
of any of the three -- which `data_address.hpp:57-59` already records as
`searched-and-absent`, and which the corpus now confirms.

`EST_HYD_B` is a narrower case and is **not** a defect: its first writer landed
under R107 (`cmd_workspace.cpp:2417`), and it reads 0 / 106 only because no
MINIDB save has happened since. Said out loud so the empty column is not later
read as the writer having failed.

---

## 5. The ruling

**Keep `WorkspacePath`** (`include/reference/data_address.hpp:60`). Reverting it
would delete the only place in the tree where the depth question is written
down, and F1 shows the question is real -- the format permits a container to
carry a `.dtx` that carries a container, and nothing forbids it. The corpus is
empty of that shape by habit, not by rule.

**Strike the AIF-070 nesting justification.** The header comment at
`data_address.hpp:50-51` cites the memo-resident case as a coming consumer of
depth > 1. F2 measures that false: hydration flattens, on every carrier, on
both surfaces. Replace it with what was measured, not with what was expected.

**Three consequences, in order.**

1. **Correct the comment.** `data_address.hpp:50-51` should say: at rest the
   memo-resident case nests one level; at runtime `schema_close_all()` /
   `mirror_workspace_posture()` close the carrier before opening the payload,
   so nothing in the tree produces a depth-2 address today. Depth > 1 stays
   reserved and unresolvable -- for the reason now measured, not the reason
   assumed.

2. **Pin the flattening.** F2 is an observation about today's code, and a
   reserved field with nothing defending it is how reserved becomes accidental.
   A test that a memo-resident load leaves the carrier's areas closed converts
   F2 into an invariant. The day someone makes carrier and payload coexist,
   that test fails -- and *that* is the moment `WorkspacePath` earns its depth,
   visibly, with a name on it.

3. **Populate `DEPTH` or stop calling it mandatory.** Its own charter comment
   says `MANDATORY recursion declaration`; its only writer hardcodes 0. An
   empty chartered column is house-legal (the public-status-board rule); a
   column that declares itself mandatory and is written with a constant is a
   different thing, and it is the one column a future cycle guard would trust.
   Either the hydrator writes the measured depth, or the comment is softened.

**What this does not decide.** Q-R5 is one question of six. This ruling touches
none of Q-R1 through Q-R4 or Q-R6, and it authorises no build: consequences 1-3
are proposals to the owner, not work in flight.

---

## 6. Evidence tier

**Source-evidenced:** sec 1 (three censuses, `tools/dbf/minidb_depth_census.py`,
re-runnable),
sec 2, sec 3 and sec 4 (every claim verified at file:line against
`D:\code\ccode` at `4d65d9281`).

**Chat/AI output:** sec 5. No code was written under this note.

---

## 7. Good Neighbor note

- **What changed.** Two new files:
  `docs/maintenance/AIF120_WORKSPACE_PATH_DEPTH_RULING_V1.md` (this ruling) and
  `tools/dbf/minidb_depth_census.py` (the evidence, re-runnable). No source file
  was edited, no build touched. No existing document was rewritten -- this
  ruling stands *beside*
  `WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md` and answers its Q-R5
  rather than editing another lane's note in place.
- **Whose area.** The question belongs to **AIF-078**
  (`member.ai.claude.cowork`, workspace-qualifier-namespace-depth). The
  measurement was taken from the **AIF-120** lane (`application-ui-dsl`) because
  that is where the memo-resident descent happened. The type it rules on,
  `DataAddress::workspace_path_`, is AIF-078's.
- **What authorization.** Maintainer direction in session, 2026-08-21 to
  2026-08-22: read the multi-workspace prior art and write up the corrections as
  a ruling. The author does not self-approve; this ships `review-needed`.
- **How to verify.** Re-run all three censuses in one command:

      python3 tools/dbf/minidb_depth_census.py all tmp/minidb <catalog>

  where `<catalog>` is the live `dottalkpp/data/workspaces/WORKSPACES.dbf` -- see sec 1c for why it is untracked.  <!-- cite-check:ignore -->

  The container payloads are the `SNAPSHOT` memo of each `MINIDB 1` catalog row,
  extracted 2026-08-21 to `tmp/minidb/` (37 `.bin` files, one per object id --
  scratch, untracked, and re-extractable from the catalog memo). The catalog
  is read live and is not modified; nothing in the script opens a file for
  writing. Then check the four cited lines: `cmd_workspace.cpp:1889`, `:2419`,
  `session.cpp:1906-1909`, `data_address.hpp:60`.
- **How to undo.** Delete this one file. Nothing else was touched, and no
  behaviour changed.

---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20261012-COWORK-213
  recorded_at_utc: 2026-10-12T02:20:37Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20261011-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 0eb1ee5df
  authorization:
    requested_by: >
      maintainer (member.derald), in-session 2026-10-11 -- "I noticed
      'students.dbf' missing in a couple of the mini-databases ... find the
      minidbs in workbench with the missing students.dbf and copy students.dbf
      with sidecars and indexes to the minidbs and save them. look for prior
      art first in copy and move ... we want a repeatable, elegant solution
      that works in the gui and the cli both." Then, after the investigation
      was reported: "write it up".
    scope: >
      DESIGN PROPOSAL. It proposes a read-only verb and argues for it from
      measured evidence. It RULES NOTHING -- the author does not self-approve
      and this ships review-needed. NO CODE WAS WRITTEN FOR THIS REPORT. No
      file was copied, no posture was re-saved, and the three flavor defects
      recorded in section 8 were left exactly as found.
  report:
    path: docs/maintenance/AIF120_WORKSPACE_VERIFY_AND_THE_COLUMN_THAT_HAS_NAMED_IT_SINCE_AUGUST_V1.md
    kind: design
---

# WORKSPACE VERIFY, and the column that has named it since August

Lane: AIF-120 (application-ui-dsl). Owner: `member.derald`.
Author: `member.ai.claude.cowork`. Status: **review-needed**.
Measured at `0eb1ee5df`.

**CORRECTED 2026-10-12, at `a67d65824`.** Section 3.3 was WRONG as first
committed. It reported that no index containers exist anywhere, having measured
only the DBF root. They exist, in the INDEXES root, which is a separate path
slot by design. The section now says so, says what it said before, and keeps the
one finding that survived the correction. Sections 4.5 and 5 cited the false
claim and are adjusted. Nothing in sections 1, 2, 6 or 7 depended on it.

No R-number is claimed. A proposal is not a ruling, and an R-number records a
ruling; section 7 names the three questions an owner would actually be ruling
on, and the number belongs with the answer.


## 1. The verb is already chartered. It has never been written.

The request that started this was a copy job: STUDENTS.dbf is missing from some
mini-databases, so copy it in. The investigation did not find a missing file.
It found that **nothing in the system compares a workspace's description of
itself against what is on disk**, and then it found that the engine already
says so, in a column it creates in every catalog:

    cmd_workspace.cpp:3152
        C("VERIFIED_AT", 19);  // last oracle re-verification (chartered; WORKSPACE VERIFY)

`WORKSPACE VERIFY` occurs **exactly once in the source tree**, in that comment.
There is no VERIFY token in the WORKSPACE dispatcher and no writer for the
column. `VERIFIED_AT` has three mentions, all in `cmd_workspace.cpp`, and all
three say the same thing -- that it is chartered and unfilled (`:3124`, `:3152`,
`:3945`).

The charter is explicit about what an empty column means, at `:3124-3126`:

    // PAYLOAD_SHA / EST_HYD_B / VERIFIED_AT / dimension fields are created
    // now and populated by later milestones -- an empty column is a
    // chartered claim, same rule as the public status board.

Catalog v2 is dated in its own comment to the owner design session of
2026-08-11 (`:3118`). So the claim is roughly two months old, it ships in every
`WORKSPACES.dbf` on disk, and this proposal is not asking for a new verb. It is
asking to fill a charter, and section 3 is the bill that came due while it sat
empty.

This document does not propose the copy the request asked for. Section 5
explains why the copy is the wrong first move, and section 8 records what the
copy would have carried if it had been run blind.


## 2. Three sources describe one workspace. Nothing compares them.

A workspace name resolves against three independent things:

1. the **MEMO carrier** -- a row in `WORKSPACES.dbf` whose `SNAPSHOT:M16` memo
   holds the posture text (`:3156` for the column, `:3944` for the write);
2. the **FILE carrier** -- a `DTSHEMA 2` file, conventionally
   `dottalkpp/data/workspaces/<name>.dtschema`;
3. the **directory on disk** -- the DBFs, index containers and memo files the
   posture's AREA lines name.

Each of the three can be read. Any two of them can disagree. No verb reads two
of them in one breath and says so. That is the whole finding, and every row of
section 3 is one instance of it.


## 3. What the three sources actually say right now

Measured at `0eb1ee5df`, against `D:/code/ccode/dottalkpp/data`.

### 3.1 `mcc_x64`: the two carriers disagree about two tables

`workspaces/mcc_x64.dtschema` carries a `WSID` line and **thirteen** AREA rows,
0 through 12. STUDENTS is `AREA 8`:

    AREA 8 | dbf=STUDENTS.dbf | index=STUDENTS.cdx | indextype=CDX | tag=none | alias=STUDENTS
    AREA 12 | dbf=TEST64.dbf | index=none | indextype=NONE | tag=none | alias=TEST64

The MEMO carrier the Workbench loads under the same name opens **eleven**
areas, and the two it does not open are exactly STUDENTS and TEST64. Both files
are present in `dbf/x64/`. This is the reported symptom, and it is not a
missing file: it is a short posture.

**RESOLVED 2026-10-12, after the measurement above.** The owner re-saved from a
thirteen-area open: `WORKSPACE SAVE: ... 13 area(s)` / `wrote memo 'mcc_x64'
(1452 B, oracle byte-compare OK)`. The MEMO carrier now matches the FILE
carrier. The divergence is gone for this name. What is not gone is that nothing
in the system would have told anyone it was there.

### 3.2 `mcc_v3`: there is no file carrier at all

`mcc_v3` loads eleven areas and has no `.dtschema` anywhere in
`dottalkpp/data/workspaces/`. The thirty-three files in that directory are
listed and `mcc_v3` is not among them. Its only copy is the short one, so for
this name there is no second source to compare against and no longer copy to
recover from.

**PARTLY RESOLVED 2026-10-12.** The same run wrote `mcc_v3` from the same
thirteen-area open, so its memo is no longer short. It still has no `.dtschema`,
so this section's actual claim -- that for this name there is no second source
to compare against -- stands unchanged.

### 3.3 The declared indexes exist. They live in a different root, and this author looked in the wrong one.

**CORRECTED 2026-10-12, and the correction is the most useful thing in the
section.** This read "The file carrier names twelve index files. Zero of them
exist", and tabulated zero `.cdx`, `.cnx` and `.inx` across five directories.
That measurement was taken in `dottalkpp/data/dbf/<flavor>/` and nowhere else.
It was wrong.

Indexes do not live beside their tables. A workspace owns **three** path slots
-- DBF, INDEXES and LMDB -- and they move as a set. That is R131, it is stated
at length in the WORKSPACE contract this document quotes elsewhere, and
`dottalkpp/data/scripts/x64.dts` sets all three. So `index=STUDENTS.cdx` in a
posture resolves against IDXROOT, never against the directory holding
`STUDENTS.dbf`.

Measured in the right place, `dottalkpp/data/indexes/`:

| root | containers |
|---|---|
| `indexes/x64` | 14 `.cdx`, 1 `.cnx`, 1 `.inx`, 17 `.cdx.meta` |
| `indexes/x32` | 15 `.cnx` |
| `indexes/vfp` | 14 `.cnx` |

All twelve `.cdx` that `mcc_x64.dtschema` declares are present in
`indexes/x64/`. The owner's run of 2026-10-12 confirms it from the other
direction: twelve of thirteen areas reported `[index: <stem>.cdx, attached]`.

**What survives is a better instance than the claim it replaces.**
`indexes/x64/` holds `TEST64.cnx` -- a CNX, which is the v32 index type, sitting
in the x64 index root, for the one table `mcc_x64.dtschema` declares as
`indextype=NONE`. The owner's run opened `Area 12: opened 'TEST64.dbf'` with no
index line at all. So there is an index container on disk for a table whose
posture says it has none, and it is the wrong type for the flavor. `SO_ID.inx`
is a second such artifact, an INX in a CDX root, named by no posture. Both are
section 3.6's shape -- present and undeclared -- and nothing reports either.

**The error itself is evidence for the proposal.** A VERIFY that resolved
`index=` beside the DBF instead of through IDXROOT would produce exactly the
false negative this section originally carried: twelve indexes declared, none
found, a workspace pronounced broken that is entirely intact. Three-slot
resolution is not an implementation detail of the verb. It is the first thing
the verb has to get right, and the author of this proposal got it wrong by hand
before the verb existed to get it wrong for him.

### 3.4 `mcc_x32` and `mcc_vfp` are byte-identical, and disagree with the live open

Both files carry twelve AREA rows with `indextype=CNX` and populated tags, and
both give STUDENTS `tag=LNAME`. Neither carries a `WSID` line, which
`mcc_x64.dtschema` does. The live open observed in the Workbench had STUDENTS
attached on `tag=SID`.

Two postures that are byte-identical under two names is itself unreported: the
catalog charters `PAYLOAD_SHA` for exactly this (`:3142`, "integrity +
cycle-detection material (chartered)") and that column is also empty.

### 3.5 A catalog row with no payload

The Workbench console reported, for a catalog row named `workspaces`:

    [gui.workspace.memo_read_failed] ... This row carries no SNAPSHOT token

The message text lives at `src/gui/core/gui_runtime_adapter.cpp:469` and is
raised as a warning at `src/gui/core/session.cpp:2127`. The engine already
distinguishes this case on purpose -- `cmd_workspace.cpp:3525` notes that a
BIRTH row legitimately carries no SNAPSHOT -- so the GUI is reporting a
legitimate row shape as a read failure. A row the catalog considers well-formed
and the GUI considers broken is a fourth kind of disagreement, between the
catalog and its reader.

### 3.6 On disk, in no posture at all

`dbf/x32/STUDENTS64.dbf` (22427 bytes) sits in a v32 directory, is named by no
AREA line in any posture, and carries a v64 version byte. `dbf/x64/` likewise
holds `FMGRTST.__fldbak.dbf` and `STUDENTS.dbf.bad`, neither in any posture.
Two further stray FILE carriers live inside data directories rather than in
`workspaces/`: `dbf/x64/my_workspace.dtschema` and
`dbf/x32/mixed.workspace.dtschema`.

The direction matters. Rows 3.1 to 3.5 are a posture claiming something disk
does not have. This row is disk holding something no posture claims. A
comparison that only walks the posture cannot see it, which is a constraint on
the design and is carried into section 5.


## 4. Prior art. Two thirds of this is already written.

Per the lane rule -- look for prior art before building -- what follows already
exists and must be reused rather than reinvented.

### 4.1 `preflight_missing_members()` already walks a posture against disk

`cmd_workspace.cpp:2573`. It parses the payload line by line, tracks `DBFROOT`
in line order, counts declared AREA rows into `declared_out`, resolves each
`dbf=` through `resolve_member_dbf()` and probes it with `member_exists()`,
returning the list that is missing. That is the comparison this proposal wants,
already written and already proven.

Three things stand between it and a VERIFY:

- it is **private to the LOAD path** and feeds a refusal, not a report;
- it checks **tables only**, by ruling (4.2);
- it answers one question (is a declared table absent) and not the inverse
  (is an undeclared table present), which section 3.6 needs.

### 4.2 The index exclusion is a ruling, not an oversight

`cmd_workspace.cpp:2562-2566`, verbatim from the comment:

    // INDEXES ARE NOT CHECKED, deliberately. An index file is derived and
    // rebuildable; the per-table CHOICE (index=/indextype=) travels in the
    // posture and find_index_for_dbf already falls back. Refusing a load over
    // a missing .cdx would refuse a workspace that is entirely recoverable.
    // Tables are the mandatory member -- the same line writeback draws.

This is the load-bearing distinction for the whole proposal. The reason LOAD
may not check indexes is that LOAD's output is a **refusal**, and refusing over
a derived artifact refuses a recoverable workspace. VERIFY's output is a
**report**, and a report may name a missing index precisely because naming it
costs nobody anything. The asymmetry is the argument: a read-only verb is
allowed to say what a mutating verb is forbidden to act on.

It also means section 3.3 is reportable without reopening the ruling at 2562.

### 4.3 WRITEBACK already refuses on a posture-versus-reality shortfall

`WORKSPACE WRITEBACK <name> [TO <root>] [WITH INDEXES] [CONFIRM]`
(`cmd_workspace.cpp:126`). The contract at `:505-509` states that enumeration
comes from the POSTURE's AREA lines and never from the session's attach order,
that a shortfall refuses before anything is written, and that replaced files are
kept one generation deep as `<name>.__wbak`. The comment at `:2546-2548`
preserves the exact sentence it prints, which names thirteen:

    "the posture declares 13 table(s); 12 are not open ... Nothing was written."

So the house already has gather-all-before-writing on the way out and
resolve-all-before-closing on the way in. VERIFY is the same walk with neither
leg -- it only reports -- which is why it is cheap and why it should come first.

### 4.4 "Oracle" already means something specific here

The column says "last oracle **re**-verification". The oracle it refers to is
implemented: at `cmd_workspace.cpp:3950` the SAVE path reads the memo back
through the field (not from memory) and byte-compares it, loudly, because a
field-width truncation had already slipped through once. So the mechanism exists
and runs **at write time**. VERIFY is that same oracle run **after the fact**,
which is what the "re-" in the column comment is asking for, and it needs no new
integrity machinery -- only a caller.

### 4.5 The copy prior art, and what it would actually have copied

The request asked for prior art "in copy and move". The answer is that **there
is no `cmd_move.cpp`** -- the intuition in the request was right, and a move
here is a copy plus a conditional delete.

`cmd_copy.cpp` has `copy_file_binary()` at `:106` and `copy_sidecars()` at
`:184`, reachable as `COPY ... WITH SIDECARS` via the `with_sidecars` flag at
`:663`. **`copy_sidecars()` carries four suffixes:**

    { ".inx" }, { ".cnx" }, { ".dtx" }, { ".dti.json" }

A second list in the same file enumerates nine suffixes plus a `.cdx.d`
directory -- `.inx .cnx .cdx .cdx.meta .dtx .dbt .fpt .dti.json` -- at
`:492-501`. That one is **not** the copy list. It belongs to
`remove_conversion_artifacts()` at `:487`, which is a cleanup helper that
deletes them.

So the two lists in one file disagree, and the copy list is a strict subset
missing `.cdx`, `.cdx.meta`, `.dbt`, `.fpt` and `.cdx.d`. For an x64-flavor
target, whose index type is CDX by the flavor rule in 4.6, **`COPY ... WITH
SIDECARS` would not carry the index**, and for any table with a memo it would
not carry the memo file either. Had the requested copy been run blind against an
x64 minidb it would have produced a table with neither, and reported success.

**AND THE DIRECTORY IS THE DEEPER PROBLEM, per 3.3.** `copy_sidecars()` builds
every candidate from `src_dbf.parent_path()`. Indexes resolve through IDXROOT, a
separate root entirely, so the suffix list is the second problem and not the
first: even with `.cdx` added, the function would look for it beside the DBF and
not find it. A copy meant to carry indexes has to be told where indexes live --
which is what `WORKSPACE WRITEBACK ... WITH INDEXES` already knows and `COPY`
does not.

This is reported as a finding, not fixed. Which of the two lists is right, and
whether COPY should resolve IDXROOT at all, are questions for the COPY contract
and its owner, not for this document.

### 4.6 The flavor rule, and `AREA`

The flavor-to-index-type rule is the engine's, stated in the WORKSPACE help at
`cmd_workspace.cpp:5214` and again at `:6277`:

    - Without CNX/INX/CDX, index files are chosen by DBF flavor: true x64/v128
      CDX, classic VFP/v32 CNX.

`AREA` already reports the per-table facts a VERIFY would need to render: its
usage block at `src/cli/cmd_area.cpp:29` lists record count, current record,
**DBF flavor** and **runtime kind** among its columns. VERIFY should render
through what AREA already knows rather than re-deriving flavor.

The request also specified that `x32.dts` populates v32 workspaces.
`dottalkpp/data/scripts/x32.dts` sets `SET PATH DBF DBF/x32` and `SET PATH
INDEXES INDEXES/x32` and has **no LMDB line** where `x64.dts` has one. That
asymmetry is real and is the correct input to any per-flavor path work; it is
not addressed here.


## 5. The shape this proposes

**`WORKSPACE VERIFY <name>`** -- read-only, reports, mutates nothing but
`VERIFIED_AT`, and is the same report in the CLI and the GUI because it renders
from one structure.

It resolves the name against all three sources of section 2 and prints them side
by side, per area, plus the two set differences:

- **declared and absent** -- a posture AREA whose `dbf=` is not on disk. This is
  `preflight_missing_members()` (4.1), promoted out of the LOAD path and given a
  report instead of a refusal.
- **present and undeclared** -- a DBF in the resolved root that no AREA names.
  This is new; 3.6 is why it is needed, and nothing today walks in this
  direction.
- **carrier disagreement** -- MEMO posture versus FILE posture under one name,
  with the AREA count of each. 3.1 is the whole reason, and this is the column
  that would have answered the original question in one line.
- **index status** -- declared `index=`/`indextype=` against what is on disk
  **in IDXROOT, not beside the DBF**. Section 3.3 is what happens otherwise.
  Reported and never refused on, per 4.2.

Three constraints the design must respect:

1. **It must not refuse.** The moment VERIFY can fail a workspace it inherits
   the ruling at 2562 and loses the right to mention indexes at all.
2. **It may write only `VERIFIED_AT`.** That is the charter at 3152 and the
   whole of it. `PAYLOAD_SHA` is a separate chartered column and filling it is a
   separate decision.
3. **One renderer, two drivers.** The request said it must work in the GUI and
   the CLI both. The transport for that is NOT settled -- owner ruling (4) of
   2026-09-25 deferred it, and `AIF120_THREE_DRIVERS_AND_ONE_PIPE_V1.md`
   (`6bc1fc477`) is the reconnaissance. VERIFY is a report and not a prompt, so
   it needs no ASK protocol and does not depend on that ruling; it should
   however emit a structure the GUI can table rather than text the GUI must
   scrape.

**Why this comes before the copy.** The request's copy has no safe target list
until this report exists. Section 3.1 says the file that was reported missing is
present on disk and absent from a posture, so copying it in would copy a file
over itself and leave the posture still short. Section 4.5 says the copy verb
hunts sidecars beside the table while indexes live in a separate root, so it
would carry no index at all. A copy run now would therefore do nothing useful,
report success, and make the next reader believe the problem was handled. The ordering is not caution for its own sake -- it is that the copy
cannot currently be aimed.


## 6. What this does not propose

- No `WORKSPACE REPAIR`, no `--fix`, no auto-save of a reconciled posture. A
  verb that both diagnoses and repairs cannot be trusted as a diagnosis.
- No change to `copy_sidecars()`. 4.5 reports the disagreement; the COPY
  contract owns the fix, and the house rule binds whoever changes it to update
  the whole fourteen-field usage block.
- No `cmd_move.cpp`. Its absence is recorded as confirmation of the request's
  own reading, not as a gap this document asks to fill.
- No re-save of `mcc_x64` or `mcc_v3`. That is a one-line owner action
  (`workspace close all` / `workspace open dbf` / `workspace save <name> memo
  v3`) and it would destroy the evidence in section 3 before anyone had ruled on
  it.
- No reopening of the transport ruling.


## 7. What the owner is actually being asked

1. **Fill the charter, or retire it?** `VERIFIED_AT` and `WORKSPACE VERIFY` have
   been a chartered claim since 2026-08-11. Either the verb gets written or the
   column should stop claiming it. Leaving it is the only option this document
   argues against.
2. **Is "present and undeclared" in scope?** It is the one part of section 5
   with no prior art, and the only part that requires walking disk rather than
   the posture. Dropping it makes VERIFY strictly a promotion of existing code;
   keeping it is what catches 3.6.
3. **Which carrier wins when they disagree?** This document deliberately does
   not answer that. It reports the disagreement. But a later REPAIR, if one is
   ever chartered, cannot be written until MEMO-versus-FILE precedence is ruled,
   and 3.2 shows the answer cannot simply be "the file" because for `mcc_v3`
   there is no file.


## 8. Not measured, and loose ends recorded

**Not measured.** The MEMO carriers of 3.1, 3.2 and 3.4 were read through the
Workbench, not parsed from `WORKSPACES.dbf` directly: an attempt to read that
DBF with a hand-written reader produced garbage, because version byte `0x64` is
not the classic 32-byte-descriptor-at-offset-32 layout, and the attempt was
abandoned rather than guessed at. The area counts in 3.1, 3.2 and 3.4 are
therefore the **loader's** counts, which is the right number for the symptom but
is not an independent read of the row. A VERIFY written inside the engine would
not have this problem, which is a further argument for the verb.

Also not measured: whether `PAYLOAD_SHA` being empty means the two identical
postures of 3.4 are a duplicate or a coincidence of content; and whether any
other catalog row shares the shape that produced the 3.5 warning.

**How the 3.3 error happened, recorded so it is not repeated.** The measurement
was an `ls` of `dbf/<flavor>/` with extensions counted, and it answered the
question "are there index files beside these tables". That is not the question a
posture asks. The three-slot design was stated in a contract this document had
already quoted, so the contradiction was available on the page and went
unnoticed: a count that disagrees with a documented design should be re-run
against the design before it is written down. The sequence that catches it in
one step is the owner's own -- `do x64` then `workspace open dbf`, which prints
the resolved INDEXES root and then says `attached` twelve times.

**Loose ends found en route, not acted on.** Three flavor defects:
`dbf/x32/STUDENTS64.dbf` carries version byte `0x64` in a v32 directory and is
in no posture; `dbf/sandbox/students_x64.dbf` carries `0x03`, so its name says
x64 and its bytes say v32; `dbf/sandbox/NULLSPEC.dbf` carries version byte
`0x32`, which is ASCII `2`, and is not a DBF. All three are reported here and
left as found. Each is a case a VERIFY that reported flavor through AREA (4.6)
would surface on sight.

Container inventory, for whoever picks up the minidb side: `sys/WORKSPACES.dtx`
holds 41 MINIDB containers, 24 of which carry a STUDENTS member and 17 of which
are two-member `MDMEMO.dbf` + `MDMEMO.dtx` fixtures. `dbf/sandbox/PKWS.dtx`
duplicates all 41 at identical offsets.

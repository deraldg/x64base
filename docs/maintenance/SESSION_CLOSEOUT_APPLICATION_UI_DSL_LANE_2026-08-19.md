---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-016
  recorded_at_utc: 2026-08-19T01:04:07Z
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
    baseline_commit: 6d52c6d6f
    head_at_closeout: 97659fd6c
  authorization:
    requested_by: maintainer (member.derald), in-session, "This is the best time to review
      the lane. Take a break and catch up on your house keeping and good neighbor policy."
    scope: >
      Session closeout for AIF-120, run COWORK-20260818-001. Records what landed,
      what was corrected, leftovers owed, notes owed to other areas, and the state
      the next session inherits.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_2026-08-19.md
    kind: session_closeout
---

# Session closeout -- AIF-120 `application-ui-dsl`, run `COWORK-20260818-001`

Owner: member.derald. Steward: member.ai.claude.cowork.
Baseline `6d52c6d6f` -> head `97659fd6c`, nine commits.

## 1. What landed

| commit | what |
| --- | --- |
| `3edb09eba` | **R11**, threading ruling -- gate 9 |
| `1a40c97a7` | `docs/ui` widow fix (maintainer's files, acted on a report) |
| `5c213dc4a` | **R12**, coordinate ruling -- gate 8 |
| `583408cde` | reader + SCX baseline tracked (widow fix) |
| `beea3e96b` | VFP 9 reads an x64base-written table -- first `runtime-proven` result |
| `3a62467fa` | 16 specimen fixtures tracked (widow fix) |
| `c21413a36` | **R13** -- VFP opened, ran and round-tripped an x64base-GENERATED `.SCX` |
| `97ebd2601` | corpus scan over 170 third-party forms; first `.VCX` |
| `97659fd6c` | case normalisation |

**Both blocking gates closed.** The charter named the coordinate ruling and the
threading ruling as preconditions before any syntax work. Both are ruled, both
review-needed.

**New capability, not just new documents.** `tools/vfp/write_vfp_binary.py` --
this project can now emit `.SCX`/`.SCT`, and Microsoft's Form Designer opens the
result, runs it against live data, and saves it back preserving our record set
exactly.

## 2. What was corrected, which is most of the value

Every item here was a claim this lane made and then had to withdraw. They are
listed because the pattern is the finding.

| claim | corrected by | correction |
| --- | --- | --- |
| "nothing has measured threading" (charter, 4x across 3 docs) | grepping for thread primitives | `src/gui/` is a 230 KB GUI core with a written threading contract; the charter searched for `DEFINE WINDOW` and could not see it |
| M5: "zero font properties; the document carries no metrics" | reading raw records to build a writer | every `.SCX` carries a font table in a trailing `RESERVED` record; the parser split on `=` and that record has none. **Retracted** |
| M4: "22 of 45 partial" | a third specimen | restated as "wizard 100%, native 0%" |
| M4 again | **170 files** | **13.7%**, and it tracks CONTAINERS not producers. Stated three ways in one session |
| 4b: "the format relies on ambient path, which does not travel" | one save | VFP rewrites `CursorSource` relative to the `.SCX`; addressing is relative-to-document and **does** travel |
| "no specimen contains an image, shape, line or grid" | **the maintainer** | `form1.scx` has 24 base classes including all four. The fact was already in the charter |
| "two of the sixteen trip the data-fixtures gate" | the gate itself | 0 of 18 tripped; the earlier result was carried over without re-checking |
| "menu evidence doubled to 410 records" | `cmp` | the four new `.MNX` are byte-identical copies; still 205 |

**Seven of eight are the same error: asserting absence, or a generalisation,
without measuring.** The lane's own rule -- *a search shaped by the object you
have cannot find an object with a different schema* -- was demonstrated on the
lane repeatedly, by its steward, in a session that quoted the rule while breaking
it. The eighth (data-fixtures) is the sibling error: carrying a measured result
forward to a case that was never measured.

**The mechanism that caught them is worth keeping.** Four of the eight were
caught by attempting to WRITE the format rather than read it; one by a maintainer
who knew his own files; one by `cmp`; one by a gate; one by a save. None were
caught by re-reading.

## 3. Leftovers -- mine, and what remains

| item | state |
| --- | --- |
| `tools/vfp/_to_delete/__pycache__/` | **my scratch**, moved there because this sandbox cannot unlink across the mount. **Needs `Remove-Item`.** |
| `tools/vfp/generated/OPENX64FORM.FXP` | VFP's compiled output, untracked by design. A `.gitignore` line would stop it recurring |
| `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | **modified, uncommitted** -- see section 4 |
| widow sweep | clean; all 10 AIF-120 documents' citations resolve into `HEAD` |
| fixture manifest | 24 rows, all verified on size and sha256 |
| `D:\dev\vfp-corpus` | populated outside every repo; `PROVENANCE.md` records source, commit `8827135c2c60`, and the **unresolved licence** |

**Not mine, but unprotected:** 17 files under `docs/` and `docs/maintenance/`
have been modified and uncommitted since 2026-08-15/17 by other sessions,
including `GATE_GOVERNANCE_LANE_V1.md` and three `SESSION_CLOSEOUT_*`. Reported,
not touched.

## 4. The intake row was stale, and it is the row others read

`AI_INTERACTION_INTAKE_QUEUE_V1.md:165` still said **"CHARTERED, NOT STARTED --
the coordinate-model ruling is a PRECONDITION and is not made."** Both
preconditions are now ruled. Updated in place, field count preserved (8), row
count unchanged (117), ASCII clean.

This is the lane's own row and the edit is within this steward's area. It is
called out because a stale status row is the coordination equivalent of a widow:
other sessions act on it.

## 5. Coordination -- an honest gap

**This run worked for roughly five hours while checked OUT.** The agent advised
the maintainer to run `checkout` when the leftover lock was cleared, then kept
working. Consequences: no presence record for other sessions to see, and the
generated `TIER0_STATE.md` run table records only `COWORK-20260817-001`.

Re-checked in at closeout. The advice was wrong in the moment -- checkout belongs
at the END of work, and this steward moved it earlier for tidiness.

**A tooling gap this exposed:** `session_coordinator.py unlock` fails with
`PermissionError` on `p.unlink()` for any agent on a mounted tree, which is
precisely the population the coordinator serves. `lock` succeeds, `unlock` cannot.
Workaround used: move the lock file aside. Suggested fix: fall back to
truncate-and-mark when `unlink` raises, since the reaper already reads age.

## 6. Notes owed -- Good Neighbor

**To `COWORK-20260817-001`** (same member, prior run, AIF-120 author):
this run amended your charter and status document repeatedly -- AMENDMENT (d) and
(e), the R-ledger, the open list, M4 three times, M5 retracted, and a correction
to your `ls-files` characterisation of the `docs/ui` check. Authorisation:
maintainer assigned the lane to this session. Verify:
`git log --oneline 6d52c6d6f..97659fd6c -- docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md`.

**To `member.derald`, `docs/ui/`:** reported as an untracked widow, not modified
by this run; you fixed it in `1a40c97a7`.

**To whoever owns `tools/staging/prepush_gate.py`:** `is_data_fixture()` keys on
file extension, so `.SCX`, `.SCT`, `.MNX`, `.MNT`, `.VCX`, `.VCT` pass as
source/docs while `.DBF`/`.FPT` are stopped -- although per R10 the designer
formats **are** DBF tables. In this session 14 DBF-format binaries passed as
source in one commit and 16 in another. Adding the designer suffixes to
`DATA_SUFFIXES` is a one-line change. Not made; not this lane's file.

**To whoever owns `tools/coordination/session_coordinator.py`:** see section 5.

## 6b. ADDENDUM -- the session continued well past this closeout

This closeout was written when the lane stood at R13 and gate 10 was "ready to
start". The maintainer said keep going, and it did. Recorded here rather than in a
second closeout, so there is one place to look.

**Rulings R14 through R19**, all review-needed:

| ruling | what | how it was found |
| --- | --- | --- |
| **R14** | method bodies never enter v1; the table carries a handler REFERENCE | 2,404 real procedures, 86% navigate the object model |
| **R15** | the formats share TWO layers -- the DBF container AND a `name = value` property language with shared keys | testing every column of every record instead of the expected one |
| **R16** | a stated dimension is advisory when CONTENT determines it | two conformant renders of one document, side by side |
| **R17** | a BOUND control's width is in the data schema, not the design | r=0.9982 and r=0.9977 on two independent forms |
| **R18** | a structural link must never be inferred from a field the format lets be blank | `.MNX` nesting: 2 of 9 openers have an empty `NAME` |
| **R19** | `FLOW=free` is what most real forms ARE, not an inference failure | 84% of 228 container groups; withdrew this session's own 5b framing |

**Gates:** 8 and 9 ruled; **10 drafted, reconciled twice**, and implemented;
**11 spiked on a second backend for both forms and menus.**

**Tooling that now exists**, all in `tools/uidef/` unless noted:
`../vfp/write_vfp_binary.py` (VFP accepts its output), `uidef.py` (schema, DBF
writer, conformance validator), `import_scx.py`, `import_mnx.py`, `uidef_tk.py`,
`uidef_tk_menu.py`, `author_uidef.py`, `dispatch_test.py`, `infer_flow.py`.

**Runtime-proven results:** VFP 9 opened, ran and round-tripped an x64base-generated
`.SCX`; a Tk form and a Tk menubar built from UIDEF tables alone; all three R11
dispatch clauses verified with thread identities compared.

**Six evidence renders** under `docs/maintenance/evidence/`.

**The pattern held to the end.** Of the six later rulings, five were produced or
corrected by making something and looking at it -- two VFP rejections, five
renders, a validator that caught the author violating R5, `cmp` stopping a false
count, and a fixed algorithm inverting a conclusion this session had already
committed. **The reading phase produced plausible documents; production found what
was wrong with every one.**

**Corrections this session made to itself, total: eleven.** Eight are listed in
section 2; R19 withdrawing 5b, the contract reconciled twice against its own newer
rulings, and the `X64FORM.SCX` case normalisation are the rest.

## 6c. SECOND ADDENDUM -- rulings R20 through R25, same run

Section 6b ended at R19. The maintainer said "go go go" and the run continued
through six more rulings. Recorded here so there is still one place to look.

| ruling | what | how it was found | commit |
| --- | --- | --- | --- |
| **R20** | a menu item may select a capability the HOST provides; `DISPATCH` gains `host` | decoding the last undecoded `OBJCODE`; 21 of 67 items | `8de1b655c` |
| **R21** | serialization is per HANDLER and NAVIGATION triggers it, not mutation; a completion is delivered at most once | two handlers contending on the real `STUDENTS.dbf`; per-op locking scored the same as no lock | `bf2da2852` |
| **R22** | a capability mapping is a translation and needs an independent witness; refusal must be visible | the caption guard caught its own author's mis-mapping on its first run | `9696b9692` |
| **R23** | `FLOW` is the container's field; an unspecified `grid` is refused, not stacked | rendering `row` and `column` for the first time and finding they were unreachable | `52831534b` |
| **R24** | a document's requirements are computable from the table alone; a reference is not a measurement | the manifest, run once, over six documents | `e6205e11c` |
| **R25** | a bound control's width follows its MASK, not its field | joining `BINDING` to a real schema and re-running R17 | `abe250c52` |

**Runtime-proven this half:** two handlers contending on a 200-record DBF cursor,
with the failure and the fix both measured; a container destroyed with a worker in
flight, and the `cancelled` and `failed` states reached for the first time; host
capabilities doing real clipboard work on Tk with 11 of 18 refused by name; three
fonts applied through `FONTREF`; a `pageset` rendered as a notebook.

**Tooling added:** `contend_test.py`, `lifetime_test.py`, `uidef_tk_host.py`,
`manifest.py`, `author_flow.py`, `author_fonts.py`, `author_tabs.py`.
**Ten evidence artefacts added** under `docs/maintenance/evidence/`.

**Four defects in committed code, all the same shape.** `FLOW` read off the child
instead of the container (R23.1). `FONTREF` written by the importer and read by
nobody (R24.2). `pageset` produced by the importer and rendered by nobody (R24.3).
`InputMask` carried under VFP's spelling, load-bearing and unnamed (R25.5). Every
one survived because **production and consumption were never checked against each
other.** A round trip is not a test if only one end is implemented. `manifest.py`
is the cheap standing version of that check.

**Corrections this session made to itself: twenty.** Eleven are in sections 2 and
6b. The other nine:

| # | what | how it was caught |
| --- | --- | --- |
| 12 | the ledger claimed the charter carries "rulings R1 through R20"; it stops at R12 | checking the claim before propagating it as R21 |
| 13 | R11.4's heading said "mutating work" where its own body said "moves the record pointer" | the 0 ms buffer case: the write survived, the walk still broke |
| 14 | the lifetime test's own pump outlived its window | the test printing the defect it was written to prove |
| 15 | `tools.data_browser` mapped onto the caption "Class Browser" | the caption guard, on its first run, one minute after being written |
| 16 | every label rendered with literal double quotes | opening the screenshot |
| 17 | R19's corpus figures inflated by 9 DataEnvironments classified as `row` | asking what a "container group" actually is |
| 18 | four committed tools carried a hardcoded `/tmp/gen` on `sys.path` | reading a file for a different reason |
| 19 | the manifest's `FONTREF` check compared an index against `OBJID`s | reading the contract's field table before writing up the finding |
| 20 | a stale `.git/index.lock` from my own timed-out `git status` over the bridge | the maintainer's commit failing |

Number 19 is the one to keep: **a drift check that was itself drift**, written
inside the tool built to catch drift. Number 20 has a rule attached -- `git status`
is not a read, it takes the index lock, so it runs as
`git --no-optional-locks status` over the bridge from now on.

## 7. What the next session inherits

**Ready for owner review:** rulings **R1 through R25**, all `review-needed`. The
author does not self-approve and none of these has been approved by anyone.

**Decisions that are the owner's, not the author's:**

- **`tabindex` has no home.** 1,664 corpus objects carry it. `ORDINAL` is *layout*
  order; tab order is a second independent order over the same children. A
  generated frontend with the wrong tab order is wrong, so this is not decoration.
  Named `PROPS` key, or a second ordinal?
- **`FLOW` on non-containers is unvalidated.** `import_mnx.py` writes
  `FLOW = column` on every menu item. Harmless only because the menu renderer
  ignores `FLOW` -- the same condition that hid R23.1. The validator cannot check
  it because a menu container is marked by `Container = .T.` in `PROPS`, not by
  `KIND`. Give menu containers a `KIND`, or teach the validator the flag.
- **`coordination/aif/AIF-120.claim` records `run_id: COWORK-20260817-001`** while
  this run is `COWORK-20260818-001`. Rewriting a claim rewrites the record and
  inventing a `continued_by` field could break whatever parses it. Left alone
  deliberately.
- **The two defects the contract records against itself** stand unchanged: section
  12's permission to refuse `FLOW = free` (which refuses the majority permanently),
  and section 4's refuse-the-whole-document rule (which rejects 82% of real forms).

**Untested, in the order I would take them:**

1. **Two `worker` handlers contending.** R21 ran one worker against the UI thread.
   Two workers is the same shape and has not run.
2. **Contention across work areas.** R11.4 serializes "against one workspace"; two
   workspaces joined by `SET RELATION` is a second sharing channel nothing has
   touched.
3. **A real second backend.** `manifest.py`'s `minimal` profile describes a target
   nobody has built. It exercises the checker and proves nothing about wx.
4. **`row` and `column` against real imports.** All 14 such groups are in
   third-party corpus forms whose licence is undetermined, so they stay outside the
   repo. The authored document proves the consumer, not those documents.

**Unexplained, and honestly so:** 271 FONT rows carried and unreferenced after the
corpus re-import; FONT metric fields 4 through 9; the digit-mask slope, fitted on
four points; `gender` at 20 px and `major` at 50 px, which no model here produces;
`RESERVED4` (values `2` x154, `1` x16).

**Deferred by the maintainer's own scope call:** `.FRX` reports. Measured under M7
and R15, unruled.

**Do not repeat:** before asserting something does not exist, vary the query and
read the exit code. Before generalising from specimens, count how many you have.
Before writing a check, read the field table -- number 19 above. And before
believing a field works, find the consumer that reads it; four of this session's
defects were fields nobody read.

## 8. Learning from FoxPro, not bound by it

Added at the maintainer's instruction, and it is a correction to how this record
could otherwise be read. Six rulings deep, a reader could come away thinking the
DSL is defined as "what VFP does". It is not. VFP is the **teacher**, because it is
a designer format with thirty years of real documents in it and therefore a source
of measurements rather than opinions. It is not the ceiling.

Sorting this session's findings by how far they travel is worth doing explicitly,
because the two kinds have been written in the same voice:

**Portable claims -- they constrain any target and any source format:**

- R13, requiredness is per direction, not per field.
- R14, the table carries a handler reference and never a body.
- R16, a stated dimension is advisory when content determines it.
- R20, an item may select a capability the HOST provides.
- R21, serialization is per handler and navigation triggers it.
- R22, a translation table needs an independent witness; refusal must be visible.
- R23, `FLOW` belongs to the container; an unspecified layout is refused.
- R24, a document's requirements are computable from the table alone.
- R25's **mechanism**: width follows the mask, and the schema determines the mask.

None of those mention FoxPro. They would be true of a Qt designer file or a
hand-authored document, and several were discovered against Tk, not VFP.

**Facts about this corpus -- true, measured, and not laws:**

- R18's `OBJCODE 77` plus document order. That is how `.MNX` stores nesting. The
  portable half is the *rule* it produced -- never infer a structural link from a
  field the format lets be blank.
- R19's 88% `free`. That is how these forms were authored, not how forms must be.
- R25's constants: 7.00 px per `X`, 62 px for a date, the 6.43 digit slope. One
  wizard, one font, one machine. The mechanism travels; the numbers do not.

Where the two were mixed, the ruling says so. Where a number is a fit rather than
a law, the ruling says that too -- R25 section 8 flags its own four-point slope.

The consequence for the next session: **the design table is free to carry things
VFP has no way to express**, and R24's manifest is the machinery that makes that
safe, because a target can refuse what it cannot do without anyone having to
restrict the table to the intersection of what every source format happens to
support. `tabindex` is the first live example -- VFP has it, the table has nowhere
to put it, and the answer is not constrained by how VFP stores it.

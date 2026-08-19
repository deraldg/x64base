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

## 7. What the next session inherits

**Ready:** gate 10 is drafted and implemented; what remains is owner review of
R1-R19 and the two defects the contract records against itself (section 12's
permission to refuse `FLOW = free`, and section 4's refuse-the-whole-document rule
which rejects 82% of real forms). It goes in with four things this lane did
not have yesterday: R13's per-direction requiredness; relative-to-document
addressing; container-versus-control geometry normalisation; and measured proof
that `.SCX`, `.MNX`, `.FRX` and `.VCX` each encode shared concepts differently.

**Open:** gate 11 (a second backend generated from the TABLE); `RESERVED4`
undecoded (values `2` x154, `1` x16 across the corpus); the licence question on
`D:\dev\vfp-corpus`; no syntax, no parser, no registry entries.

**Do not repeat:** before asserting that something does not exist in this tree,
vary the query form and read the exit code. Before generalising from specimens,
count how many you have. This session produced eight corrections and seven of
them were one mistake.

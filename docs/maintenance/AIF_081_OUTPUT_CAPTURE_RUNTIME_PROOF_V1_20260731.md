# AIF-081 Output Capture Differential -- Runtime Proof V1

    lane        : AIF-081
    charter     : docs/maintenance/OUTPUT_CAPTURE_COMPLETENESS_LANE_V1.md
    proves      : F1
    owner       : member.derald
    steward     : member.ai.claude.cowork
    run         : 2026-07-31_cowork_output_capture_completeness
    tier        : runtime-proven (differential, single host, single build)

---

## 0. Why this document exists

The lane charter marks F1 `runtime-proven`. The artifacts backing that claim are
`dottalkpp/data/tmp/idxstale_transcript.log` and `dottalkpp/data/tmp/alt_probe.log`,
which are throwaway diagnostic output under `tmp/` and are deliberately NOT
committed. A claim of `runtime-proven` whose evidence is uncommitted is exactly
the invisible-evidence failure this lane's own charter cites (AIF-062, AIF-078,
and AIF-080's missing intake row).

This document therefore carries the evidence itself: figures, the complete
one-directional difference, and a reproduction procedure deterministic enough
that a reader can regenerate both files and re-derive every number below. The
transcripts remain disposable BECAUSE this document is not.

---

## 1. Claim under proof

> `DOTSCRIPT <script> OUT <file>` does not capture output written through
> `cli::cmdout`, which is the entire user-facing command surface. `SET ALTERNATE`
> does. Their coverage is not complementary: ALTERNATE's capture is a strict
> superset of DOTSCRIPT OUT's.

This is falsifiable in three independent ways, all of which were checked:

1. A single line present in `DOTSCRIPT OUT` and absent from `SET ALTERNATE`,
   other than DOTSCRIPT OUT's own banner, would refute "strict superset."
2. Any `cmdout`-routed line appearing in the `DOTSCRIPT OUT` transcript would
   refute the mechanism.
3. Equal line counts would refute the premise that anything is lost at all.

---

## 2. Environment

    binary       : dottalkpp/bin-wsl-lean/dottalkpp
    version      : dottalk++ v0.6 (2026-07-30, b702b5a5 dirty)
    object built : 2026-07-31 03:15:49  (index_manager.cpp.o)
    linked       : 2026-07-31 03:16:05
    host         : WSL2, Ubuntu 24.04.4, GCC 13.3.0, x86_64
    data root    : dottalkpp/data
    script       : dottalkpp/data/scripts/index_maintenance_failure_proof.dts

Trace state during BOTH runs: `DOTTALK_INDEX_TRACE` and `DOTTALK_APPEND_TRACE`
were UNSET, which means both trace families were ACTIVE. Both default to ON when
unset (`src/xindex/index_manager.cpp:449-457`, `src/cli/append_support.cpp:74-82`).
This is stated because an unpinned rerun on a host that exports either variable
as `0` will produce different figures. See section 6.

---

## 3. Procedure

Both runs were issued at TOP LEVEL via stdin, not from a wrapper script.
DOTSCRIPT nesting is capped at main plus exactly one subscript
(`src/cli/cmd_dotscript.cpp:61`, enforced at `:491` with `g_dotscript_depth >= 2`).
Depth is tested BEFORE increment, so the proof script runs at depth 1 and its
`DO ..\X32` bootstrap at depth 2. A wrapper issuing the `DOTSCRIPT` line would
have pushed that bootstrap to depth 3 and been refused. The A/B shape is
constrained by that rule, not chosen freely.

    cd /mnt/d/code/ccode/dottalkpp/data

    # Run A -- DOTSCRIPT OUT
    echo 'DOTSCRIPT scripts/index_maintenance_failure_proof.dts OUT tmp/idxstale_transcript.log' \
      | ../bin-wsl-lean/dottalkpp

    # Run B -- SET ALTERNATE
    printf '%s\n' \
      'SET ALTERNATE TO tmp/alt_probe.log' \
      'SET ALTERNATE ON' \
      'DOTSCRIPT scripts/index_maintenance_failure_proof.dts' \
      'SET ALTERNATE OFF' \
      | ../bin-wsl-lean/dottalkpp

Both runs executed the SAME script against the SAME binary, and both completed
with all six `E_*` markers `.T.`. The script is self-bootstrapping and
self-erasing (creates and deletes a throwaway v32 `IDXSTALE` table), so run B
did not inherit state from run A.

---

## 4. Result

    measure                        Run A (OUT)   Run B (ALTERNATE)
    ---------------------------    -----------   -----------------
    raw lines                           42              89
    distinct lines                      28              64
    E_* assertion markers                6               6
    engine trace lines                  26              26
    corrective REPLACE warning       ABSENT           present

Set difference over distinct lines, both directions:

    lines in ALTERNATE and not in OUT : 37
    lines in OUT and not in ALTERNATE :  1

The single line unique to Run A, verbatim and complete:

    DOTSCRIPT OUT: tmp/idxstale_transcript.log (write)

That is DOTSCRIPT OUT announcing its own transcript file, which Run B had no
occasion to emit. It is not command output. **Falsification test 1 therefore
finds no counter-example, and the superset relation holds.**

### 4.1 What the 37 lost lines are

Every one is `cmdout`-routed. By class:

  - table lifecycle : `Created ...IDXSTALE.dbf [MSDOS/DBASE]`,
                      `Opened ... with 0 records.`, `Closed.`
  - record ops      : `Appended blank record 1..4`,
                      `REPLACE: Replaced field #1/#2 at rec 1..4`
  - index ops       : `CNX: created: "..."`, `CNX ADDTAG: added 'LNAME'.`,
                      `REINDEX CNX -> REBUILD`, `CNX container: ...`,
                      `[1] LNAME : OK`, `REBUILD: done  OK=1  SKIP=0  FAIL=0`,
                      `SET ORDER: CNX TAG 'LNAME' (ASC)`
  - cursor          : `Recno: 1/2/4`, `Found at 1.`
  - teardown        : `ERASE: deleting 2 file(s) ...`, `Deleted: IDXSTALE.dbf`,
                      `Deleted: IDXSTALE.cnx`, `ERASE complete. Deleted: 2, Failed: 0`
  - session         : `Echo is OFF`, `ALTERNATE TO: ...`, `Alternate is ON`
  - **the finding** : `REPLACE: record written, but index update failed;`
                      `REINDEX/REBUILD needed.`

**Falsification test 2 finds no counter-example: not one `cmdout` line reached
Run A's transcript.**

The last entry is the one that matters. The script exists to demonstrate that a
CNX replace leaves the index stale AND that the engine says so. Run A's
transcript preserves the machine-facing half of that proof
(`[INDEX TRACE] ... staleBefore=no leftStale=yes`) and discards the
human-facing half entirely. A reader given only Run A's transcript would
correctly conclude the index went stale and could NOT conclude the user was
ever told.

---

## 5. Scope -- what this does NOT establish

Recorded so the tier is not read wider than it was earned.

  - Single host, single build, single preset (`wsl-lean`). MSVC UNVERIFIED.
  - Proves LOSS, not the absence of other losses. `SET ALTERNATE` is a superset
    OF DOTSCRIPT OUT; nothing here shows ALTERNATE is complete in absolute
    terms. Output emitted before `SET ALTERNATE ON` is necessarily outside it,
    and `OutputRouter::console_note` (`output_router.cpp:390-397`) writes via
    `write_direct_console_locked` and was not exercised by this script.
  - Says nothing about `SET PRINT`, `SET DEVICE`, `EXPORT`, or `TUPTALK EXPORT`.
  - The mechanism in charter section 3 is SOURCE-evidenced, not proven here.
    This document proves the BEHAVIOUR; the four cited sites explain it.

---

## 6. Determinism note

Both trace families default ON, so an unpinned rerun on a host exporting either
variable as `0` yields different figures. To reproduce the numbers in section 4
exactly, pin them ON:

    DOTTALK_INDEX_TRACE=1 DOTTALK_APPEND_TRACE=1 <command>

To observe the blast-radius case from charter F4 instead -- the transcript that
looks populated but is not -- pin them OFF:

    DOTTALK_INDEX_TRACE=0 DOTTALK_APPEND_TRACE=0 <command>

Under that second setting Run A's transcript reduces to the six `E_*` marker
lines plus the DOTSCRIPT banner: an evidence file that exists, is non-empty,
carries assertions, and contains no engine message whatsoever. That variant was
NOT executed and is a PREDICTION derived from section 4's classification, not a
measurement. It is the first thing to run if this lane is picked up.

---

## 7. Provenance

Charter and findings: `docs/maintenance/OUTPUT_CAPTURE_COMPLETENESS_LANE_V1.md`
(commit 49dfec789). Intake row: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`,
AIF-081. Claim: `coordination/aif/AIF-081.claim`.

The proof script under test is itself AIF-079 item E evidence
(`index_maintenance_failure_proof.dts`, registered as regression `IDXSTALE`,
commit 3ee720ed8). It was not modified for this proof. Its two prior versions
passed while proving nothing, which is why its markers are field comparisons
behind cursor guards; that history is recorded in its own header and is the
reason it was a suitable subject here -- it produces both trace output and
corrective command output in one run, which is what makes the two capture
facilities separable.

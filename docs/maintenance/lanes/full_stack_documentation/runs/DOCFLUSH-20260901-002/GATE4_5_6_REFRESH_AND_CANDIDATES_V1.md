# DOCFLUSH-20260901-002 -- Gates 4, 5 and 6

    run       : DOCFLUSH-20260901-002 (v8)
    baseline  : 45f699a23  (2026-09-01)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    motto     : normalize -- smooth -- improve

    Gate 4  HELP refresh executed        OWNER-RUN ON THE HOST. PASS.
    Gate 5  metadata candidates          candidates produced, nothing imported
    Gate 6  manual candidate             candidate only, boundary_fail_rows=0
    E5      harvest after the build      PASS, 14/14

## Gate 4 -- the HELP refresh, run by the owner on the host

Not a sandbox result. Run on the host at `45f699a2 dirty`, exe built
`Sep 01 2026 16:59:53`, in the cookbook's order:

    CMDHELP BUILD LEGACY          462 command rows, 2368 arg rows
    CMDHELP BUILD . <src>         29700 line rows, 666 topics
                                  3536 usage-contract rows mined from 207 files

**Ordering, which is what the gate is actually for -- all four PASS:**

    exe newer than catalogs   exe    2026-09-01 16:59:53
    legacy before store       LEGACY 2026-09-01 17:00:52
    store newer than exe      store  2026-09-01 17:03:42   (3m after the exe)
    generation stamp          both tables 2026-09-01
    store integrity           666 topics reachable, every line row names one

LEGACY ran first, which was required: `include/dotref.hpp` is in the 28-file
contract change set and foxref feeds the legacy builder.

**The half-run is closed.** The store was 2026-08-26 with LEGACY 63h45m ahead of
it -- a build that had run one half and not the other. Both halves now share a
three-minute window.

    docpush_preflight.py:  PREFLIGHT PASS
      "Phase 0/0.5 foundation is clean; proceed to Phase 1."

### The size of what was stale

    topics      473  ->   666      (+193)
    line rows 10846  -> 29700      (+18854)

By SOURCE, the new store: `USAGE_CONTRACT` 15724, `SOURCE_MINER` 7536,
`SHARED_MSG` 2651, `DOTREF` 1006, `CURATED_DOC` 868, `EDREF` 786, `FOXREF` 667,
`REGISTRY` 462. By KIND: `SYNTAX` 6105, `USAGE` 6078, `SOURCE_FACT` 4302,
`NOTE` 4212, `SUMMARY` 2391, `RELATED` 1968, `STATUS` 1564, `EXAMPLE` 1078.

**1078 EXAMPLE rows.** v7 reported 795 off the stale store and called example
coverage the largest contract deficit; the owner corrected the reading, and the
rebuilt store now shows the figure was also stale. Two independent reasons the
claim was wrong.

### What the rebuild did NOT do, and it matters

`SRCFILE_DRIFT/UNCOLLECTED` is unchanged at 60, still naming
`include/dottalk/scratch_sidecar.hpp`. See the correction in the Gate 0.5 record:
`SRCFILE.dbf` lives under `dottalkpp/data/comments/` and is written by
`tools/comments/reharvest_source_comment_catalog.py`, not by `CMDHELP BUILD`.
The comments harvest is its own stage and no cookbook Phase 4 command reaches it.

`CSV_VS_TABLE/STALE_CSV` is also unchanged: SYSCMD table=212, csv=203. The
rebuild does not regenerate the CSV mirror either.

`stack_audit_v1.py` after the rebuild: **0 FAIL / 21 WARN**, same as before it.
The contract debt is a source-side fact and a HELP rebuild does not touch it.
Worth stating plainly because a big green rebuild invites the opposite reading.

## E5 -- the entry condition runs usually fail

Checked BEFORE re-exporting, against the canonical harvest:

    E5 FAIL: 9/14 tables match; manifest_findings=5
      HELP_CMD_ARGS       source 2368  harvest 2614   first mismatch row 7
      HELP_HELP_ARTIFACTS source 14844 harvest 14694  first mismatch row 2456
      HELP_HELP_LINE      source 29700 harvest 29480  first mismatch row 1523
      HELP_HELP_SECTION   source 14844 harvest 14694  first mismatch row 2344
      HELP_HELP_TOPIC     source 666   harvest 670    first mismatch row 2

Exactly the failure the cookbook predicts: a harvest that predates the Phase 4
build, so a manual assembled from it omits the new commands. Note
`HELP_HELP_TOPIC` harvest 670 vs source 666 -- the stale harvest was HIGHER,
so "the harvest is behind" would not have been caught by a row-count heuristic
that only looks for growth.

**Re-exported after the build**, to a candidate, never to canonical -- the
exporter's own `--out` help says *"candidate harvest workspace (NOT the canonical
harvested/)"*:

    runs/DOCFLUSH-20260901-002/harvest_candidate_v1/    14 tables, 63487 rows
    manifest sha256 968C04F537D14D39...

    E5 PASS: 14/14 tables match current HELP/META; manifest_findings=0;
             mutation_performed=0

The canonical `harvested/` workspace is untracked and was NOT written. Promoting
the candidate over it is a separate authorization and is not requested here.

## Gate 5 -- metadata candidates

`metacollect` built from source in the sandbox in **19.7 seconds**
(`g++ -O0 -std=c++17`, the twelve TUs `dt_meta` enumerates). No cmake needed.
This is the CLAUDE.md figure holding at this baseline; it is a sandbox build and
predicts the host rather than standing in for it.

    runs/DOCFLUSH-20260901-002/metacollect_phase/candidate_v1/
      SYSCMD_IMPORT_candidate_v1.csv     218 rows   CA75A5FDBF5496F8...
      SYSARGS_IMPORT_candidate_v1.csv    231 rows   DF22E083F369168F...
      SYSFUNC_IMPORT_candidate_v1.csv     75 rows   87BD96B1E4F9E634...
      metacollect_evidence_v1.csv       1190 rows

**Candidate-only. Nothing imported into live metadata.** That import is a
separate gate and a separate authorization, and v8 does not request it.

**One number, three values, and this is the lane's own signature:**

    SYSCMD live table          212
    SYSCMD CSV mirror          203     (CSV_VS_TABLE/STALE_CSV)
    SYSCMD metacollect candidate 218

Three artifacts claiming to say how many commands there are, none agreeing. The
candidate being highest is expected -- it is source-derived and the table lags --
but the CSV sitting 9 below the table it mirrors is the copied-not-crossed fact
the north star warns about. Recorded, not reconciled: reconciling it is the
metadata import gate's work, not a doc run's.

`SYSFUNC` 75 agrees with `normcheck_v1`'s 75 implemented / 75 catalogued.

## Gate 6 -- manual candidate

Run against **the fresh harvest candidate**, not the stale canonical workspace --
which is the whole point of doing E5 first.

    inventory        sections=25 media=19 appendices=13 manifests=5
                     harvest files=14/14, selection_mode=explicit
    validate         25 checks, validation_fail_rows=1, review_rows=0
    export-manifest  manifests_after_export=5
    build-dry-run    boundary_fail_rows=0
                     dry_run_markdown 177512 bytes, sha256 1A3DB0AEA47517B1...
                     dry_run_hash_matches_current_combined=0

**`boundary_fail_rows=0`** -- the candidate-only requirement. No publication
rebuilt, no media touched, no x64base table created, no protected-system
mutation, no runtime data mutation.

**The single validation FAIL is `PYTHON_312`:**

    check_id,status,value,expected,note
    PYTHON_312,FAIL,3.10.12,>= 3.12,Manualgen requires Python 3.12 or newer.

That is the interpreter self-check, not a content finding -- exactly what
`CLAUDE.md` predicts ("runs on sandbox 3.10 with only the version self-check
failing"). **All 24 substantive checks PASS**, including every harvest check:
`HARVEST_SELECTION_EXPLICIT`, `HARVEST_REQUIRED_FILES` 14/14,
`HARVEST_CSV_READABLE` 14/14, and the three `HARVEST_NONEMPTY_*` rows.

**Gate 6 is PROVEN GREEN as of 2026-09-02.** Re-run on the host under
`.venv312`, against the promoted canonical harvest:

    MANRUN-20260902T121419Z-DB8760CB
    selected_harvest_workspace=docs\manuals\developer\manualgen\harvested
      files=14/14  selection_mode=explicit
    validation_fail_rows=0  validation_review_rows=0  boundary_fail_rows=0

**The stop condition was honoured and it held.** The prediction was "if any row
other than PYTHON_312 changes state on 3.12, stop -- that means host and sandbox
disagree about CONTENT, not just the interpreter." Measured, row by row, against
the sandbox 3.10 checks file:

    rows: sandbox 25   host 25
    CHANGED  PYTHON_312: FAIL -> PASS
    changed count: 1

One row, and it is the interpreter self-check. All 24 substantive checks read
identically on both toolchains, so the sandbox prediction is now confirmed
rather than merely unrefuted. Gate 6 passes.

`dry_run_hash_matches_current_combined=0` is expected and is not a finding: the
dry run is built from a store that gained 193 topics, so it SHOULD differ from
the current combined manual. A match here would have meant the new HELP had not
reached the manual.

Evidence copied into the run: `manualgen_phase/validate_checks_v1.csv`.

## Entry conditions after these three gates

    E1  dev run closed at Gate 7     open; Gate 7 is next
    E2  CMDHELPCHK reflection PASS   NOT RUN. Host only. Not claimed.
    E3  contracts 100 percent        PASS  (census 1080/1080)
    E4  refcheck + normcheck         PASS  (both re-run at this baseline)
    E5  harvest after the build      PASS  (14/14, candidate)
    E6  command-catalog.mdx          HOLD  (site branch unruled)
    E7  backup + rollback named      OWNER-RUN. The Phase 4 transcript does not
                                     show the backup step; confirm before Gate 7.
    E8  per-mutation authorization   Phase 4 authorized and performed by the
                                     owner directly. Gates 5 and 6 produced
                                     candidates only.

**Two rows still block Phase 8: E2 and E7.** E2 needs `CMDHELPCHK` on the host
against the new store. E7 needs confirmation that a dated backup was taken before
the rebuild -- if it was not, the rollback path for this refresh has no named
target, and that is worth knowing now rather than at the next one.

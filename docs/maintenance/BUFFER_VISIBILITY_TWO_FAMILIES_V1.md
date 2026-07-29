---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260729-002
  recorded_at_utc: 2026-07-29T23:10:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: member.derald
    owner: member.derald
    committer: member.derald
  session:
    id: not_exposed
    chat_reference: MAINTAINER_ATTESTED
    run_id: AIPR-20260729-001
    chat_handle: ""
    handle_binding: MAINTAINER_ATTESTED
    continues_run: null
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 4a9ff7525
  authorization:
    requested_by: maintainer
    scope: AIF-074 -- buffer-visibility architecture finding
  report:
    path: docs/maintenance/BUFFER_VISIBILITY_TWO_FAMILIES_V1.md
    kind: finding
---

# Two Read Families, and the Seam Between Them

**Date:** 2026-07-29 - **Status:** `review-needed` - **Lane:** AIF-074
**Owner:** `member.derald` - **Author:** `member.ai.claude.cowork`

## The finding in one sentence

x64base has two internally coherent ways of reading a table, and every
buffer-visibility defect found so far sits at exactly one place: where a
**classic predicate scan** is paired with a **tuple-family renderer**.

## Why this matters

Under `TABLE BUFFER ON` a `REPLACE` is recorded in the buffer and not written to
the DBF until `COMMIT` (`cmd_replace.cpp` contract). A reader must therefore
choose a source: committed table bytes, or the buffered working set. Choosing
either consistently is correct. Choosing one for the FILTER and the other for
the DISPLAY produces a row that visibly fails the predicate that selected it --
a wrong answer that looks like an answer, the defect class this lane already
closed twice (RDB-06 silent truncation, SQ-05 silent zero).

## The two families

| Family | Filter evaluates against | Renders from | Source of truth | Coherent |
|---|---|---|---|---|
| **Tuple-stream** -- `SMARTBROWSER`, `TUPLE`, `RBROWSE`(?) | `TupleRow` via `expr_tuple_glue` | `TupleRow` | buffered working set | **yes** |
| **Classic scan** -- `DISPLAY`, `COUNT FOR`, `LOCATE`, `SCAN`, `SET FILTER`, `EXPORT` | `DbArea` current record via `eval_bool_compiled` | `DbArea` | committed table | **yes** |

Each family is self-consistent by construction, and each is defensible:

- The tuple-stream family is a **working view**. It shows what the session has
  done, including uncommitted edits. Its design intent is explicit --
  `expr_tuple_glue.hpp:11` ("Bind the dottalk::expr AST engine to TupleRow for
  tuple-value FOR evaluation") and BETA-6.2 ("FOR filters evaluate on tuple
  values only").
- The classic family reports **committed truth**. `EXPORT` writing committed
  values is the clearest case: a durable artifact should carry durable data.

## The seam: hybrids

A hybrid scans classically (predicate on `DbArea` = committed) but renders
through a buffer-aware path. There are exactly two in the tree.

| Hybrid | Status |
|---|---|
| `SQLSEL SELECT` | **CLOSED by R18.** Projection moved to committed via `TupleBuildOptions::overlay_table_buffer=false`; filter and projection now share one source. Runtime-verified self-consistent (probe v2, block D) |
| `SMARTLIST` | **OPEN.** Runtime-verified split (probe v2, block C): `SMARTLIST FOR MAJOR = "CSCI"` matched record 1 on its committed value and printed `MAJOR = MATH`, the buffered value. The inverse also holds -- `FOR MAJOR = "MATH"` omits the record just edited to MATH |

`SMARTLIST` matters more than the count suggests: HELP designates it the
"Preferred listing command for user-facing ordered output". `LIST`, by contrast,
is a DEVELOPER tool and does not maintain cursor control
(`cmd_list.cpp`: `cursor_restore: best effort`) -- comparing against it proves
nothing about user-facing consistency, a mistake made and corrected during this
investigation.

## The lifecycle is guarded at the boundary (observed, 2026-07-29)

Worth stating alongside the defect, because it bounds the risk. `QUIT` with a
dirty buffer does not silently discard it:

```
. quit
TABLE: uncommitted changes detected (all areas (1 dirty)). COMMIT changes? (y/N)
```

So buffered work is never lost by walking away -- the session asks. Combined
with `cmd_commit.cpp`'s write-ahead journal (redo log + COMMIT marker fsynced
BEFORE any DBF byte moves, commit aborted if the sync fails, committed journals
replayed at `USE` via `recover_table_buffer_journal`), the DURABILITY story is
sound end to end. **The finding in this document is about VISIBILITY, not
durability**: buffered edits are safely kept and correctly committed; they are
simply not shown consistently by every reader while they are pending.

## Remedies for SMARTLIST -- two, both defensible, owner's call

1. **Pull it classic.** Render committed values; filter already is. Matches
   `DISPLAY` and `EXPORT`; matches the R18 decision for SQLSEL. Cheapest, and
   makes "listing" mean durable truth everywhere.
2. **Push it tuple-stream.** Evaluate `FOR` against `TupleRow` via
   `expr_tuple_glue`, as `SMARTBROWSER` already does. Matches `SMARTBROWSER` and
   `TUPLE`; makes "listing" mean working view, consistent with a session that
   can see its own pending edits.

The choice is not technical but definitional: **is SMARTLIST a preview surface
or a truth surface?** Whichever is chosen, it belongs in the contract, because
today the command is silent about which it is.

## Evidence

| Claim | Tier | Source |
|---|---|---|
| SMARTLIST filter/display split | `runtime_observed` | `labtalk/proofs/runs/20260729_aif074_buffer_visibility_probe_v2.txt` |
| SQLSEL self-consistent post-R18 | `runtime_observed` | same transcript, block D |
| DISPLAY, EXPORT read committed | `runtime_observed` | same transcript, blocks B and E |
| TUPLE reads buffered | `runtime_observed` | `20260729_aif074_buffer_visibility_probe.txt`, block B |
| SMARTBROWSER filter reads TupleRow (filter and display agree) | **`runtime_observed`** | `labtalk/proofs/runs/20260729_aif074_smartbrowser_tuple_filter_interactive.txt` -- inclusion AND exclusion both tested; source: `expr_tuple_glue.hpp:11`, `db_tuple_stream.cpp:207-219`, `app_smart_browser.cpp:61,66,297` |
| Buffered REPLACE does not touch the DBF | `source_defined` | `cmd_replace.cpp` usage contract |

## Open items

1. **Runtime-verify SMARTBROWSER. CLOSED 2026-07-29 -- CONFIRMED.** The
   tuple-stream family's coherence, this document's load-bearing claim, is now
   `runtime_observed`. With record 1 buffered `CSCI -> MATH`:
   `FOR MAJOR = "MATH"` **matched** it (so the filter reads buffered values) and
   `FOR MAJOR = "CSCI"` **excluded** it (so the filter is real, not a no-op).
   Filter and display read one source; SMARTBROWSER agrees with itself.
   Transcript: `labtalk/proofs/runs/20260729_aif074_smartbrowser_tuple_filter_interactive.txt`.

   Method note worth keeping: this required an INTERACTIVE run by the maintainer.
   Two tests were needed, not one -- the inclusion test alone could not
   distinguish a correct buffered match from a filter that matched everything,
   because the fixture's two records were both MATH under buffering. The
   exclusion test is what made it proof.

   Attempt 1 (superseded, retained as a method lesson) (`buffer_visibility_probe_v3_smartbrowser.dts`, 2026-07-29):
   **invalid, no evidence produced.** The probe assumed that under script mode
   `std::getline(std::cin, line)` would hit EOF and return `PagerAction::Quit`
   (`app_smart_browser.cpp:178`), so the pager would paint one page and exit.
   It does not. Stdin still carries the script, so the pager consumed the ENTIRE
   remainder of the file as pager commands -- `TABLE BUFFER ON`, the `REPLACE`,
   every test block and the cleanup -- repainting record 3 roughly forty times.
   The buffered edit under test was never created. Transcript retained as a
   negative result: `bufvis_probe_v3.txt` (not promoted to `proofs/runs`, since
   it proves nothing about the question).

   Consequence: the script's teardown never ran; `BUFVIS3.dbf` was left in
   SANDBOX and needs a manual `ERASE TABLE BUFVIS3 CONFIRM`.

   Viable next approaches, in order of cost: (a) the owner runs SMARTBROWSER
   interactively for thirty seconds with a buffered edit in place -- the pager is
   built for a human and a human can answer this immediately; (b) determine
   whether `SMARTLIST TUPLES` ("emits tuple bridge output",
   `cmd_smartlist.cpp:15,49,59`) routes its `FOR` predicate through
   `expr_tuple_glue` -- if so it is a scriptable proxy for tuple-family
   filtering, and if not it is merely SMARTLIST again. **(b) must be verified by
   reading, not assumed** -- the failure above was exactly an unverified
   assumption about runtime behavior taken from a source read.
2. **Rule on SMARTLIST** (remedy 1 or 2 above).
3. **Unprobed surfaces:** `RBROWSE`, the TUI grid, `SET FILTER` interaction with
   buffered edits, and whether SMARTLIST renders the `*` buffered-delete marker
   from `smartlist_output.cpp:115-118` (transcript column spacing was
   inconclusive).
4. **Contract wording** for whichever surfaces keep which semantics. Today the
   split is undocumented on every surface except SQLSEL (post-R18).

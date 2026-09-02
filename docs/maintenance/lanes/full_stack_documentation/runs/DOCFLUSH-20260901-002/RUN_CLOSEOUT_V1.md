# DOCFLUSH-20260901-002 (v8) -- run closeout

    opened    2026-09-01
    closed    2026-09-02
    owner     member.derald
    steward   member.ai.claude.cowork
    commits   3424b90b2 (renderer fix, disposition derivation checker)
              5c1a39f7f (PART_NO reassembly, wrap-band floor, accepted manual)

## What this run was for

Carry a full-stack documentation flush from source-code harvest through to the
accepted developer manual, following the lane's cookbook rather than improvising
around it.

## What was proven

    PHASE 0.5   source census 100.0% -- scratch_sidecar.hpp given an authored
                @dottalk.file banner (lane AIF-133, owns the __fldtmp/__fldbak
                convention). The last uncontracted header in the census.

    GATES 1-6   CORRECTLY NOT RUN. No source changed, so there was nothing for
                them to gate. Recorded because the previous run's record read as
                if they had been skipped through negligence, and the distinction
                between "not run" and "not needed" is the whole value of a gate.

    E5          THE GATE WAS INVERTED, AND FIXED. check_help_meta_harvest_
                freshness.py compared the canonical harvest against a PYTHON
                SCAFFOLD rather than the engine, so a correct engine export read
                as drift and a stale one could read as clean. Four bindings
                removed: memo columns excluded from comparison (with a
                memo_rendering field reporting RESOLVED vs BLANK), both sides
                stripped before compare, dbfread mojibake round-tripped through
                latin1, and manifest_findings taught both the v0 and v1 schemas
                plus CARRIED_STALE_MAY.

    HARVEST     Promoted via the SANCTIONED engine-backed exporter
                (HELP_META_HARVEST_EXPORT_v1.ps1), after an earlier attempt used
                the Python scaffold and relabelled four stale tables EXPORTED
                where the house says CARRIED_STALE_MAY -- the exact pretence
                that script exists to prevent. Rolled back and verified
                byte-identical before redoing it properly.

    DISPOSITIONS  Table repaired: DOT|TRANSACTION added, 13 spent entries moved
                to RETIRED_DISPOSITIONS with grouped reasoning rather than
                deleted. The V6_HINTS section 4 ruling followed through in three
                places; a test red since the day it was tracked is green.

    GATE 4      Applied as MANRUN-20260902T155001Z-5BD6794D, PASS_APPLIED, 168
                rows, 0 validation findings, 0 rollback findings, backup
                retained. Verified afterwards by reading the accepted pages on
                disk rather than by trusting the apply's own status.

## The finding this run exists to hand forward

**FOUR GATE 4 PLANS WERE BUILT. THREE WERE DISCARDED. ALL FOUR REPORTED
`PASS_PLAN_ONLY findings=0`.**

The three discarded plans would have damaged the manual:

    plan 472B26D9   corrupted text. A length heuristic joined 240-byte field
                    spills with a space: 'not the command name.' became 'not the
                    comm and name.', '(AIF-043).' became '(AIF-04 3).'. Six rows
                    affected, three of them in topics with no page among the
                    164, so half the damage was latent.

    plan CBC1CCB6   welded lists. With no minimum line length the prose join
                    fused list items -- model.md tables/records/fields/indexes/
                    relations, expression.md numeric/character/date/logical,
                    script.md loops, buffering.md working/persisted state --
                    about thirty items across eight pages.

    (a third)       the SUMMARY branch renders through distinct_summaries, not
                    the kind loop, so a fix applied only to the loop missed all
                    six spills. Twice.

**THE MEASUREMENT THAT ENDORSED ALL THREE WAS THE FRAGMENT COUNT**, which had
been the success metric for this work from the start: 399 -> 0 at store level,
then 114 -> 46 -> 21 across the rendered pages. Every one of those numbers was
true. None of them could see the defects, because A CORRUPTED OR WELDED JOIN
LOWERS THE FRAGMENT COUNT EXACTLY LIKE A CORRECT ONE. The metric moved with the
intervention rather than with the goal -- the AIF-118 shape: a number that reads
the same whether the thing is right or wrong.

**WHAT WORKED, AND WHAT TO REACH FOR NEXT TIME:** diff the staged artifact
against the accepted one and require EVERY difference to fall into a NAMED CLASS
with an explicit count. A partition, not a summary statistic. The final plan
partitioned as provenance-only 146, prose rejoin 18, byte-identical 1,
unexplained 0, with a whole-file assertion that text is preserved exactly on all
165 markdown files. Both defects were caught this way, before apply.

A corollary, learned the same day: the owner's question -- "do we have a simple
problem of needing longer fields?" -- sent this session to the producer, where
`helpdata_export_dbf.cpp` had documented the answer since 2026-08-25, under a
heading reading DO NOT "FIX" IT. The counts derived by hand here (6 rows at
exactly 240; PART_NO 1/2/3 = 29693/6/1) are printed in that comment, which also
predicted the misreading: "one did, the same week." Two did.

## Deliberately NOT done, with the reason

    M-4 controlled acceptance    Replays the 2026-07-18 prose merge. Proven by
                                 matching the aggregate mtime to the apply run
                                 id to the second. A replay is not a run.

    disposition derivation       Measured at 59.5% agreement (70 review topics,
                                 42 covered, 25 agree, 17 disagree). Not good
                                 enough to retire a hand-maintained policy that
                                 decides manual content. The checker is kept as
                                 a drift detector. Two named gaps: no
                                 has_contract predicate, and a handler name is
                                 not a canonicality signal (ARCTICTALK/FOXTALK
                                 dispatch to the same handler; dotref says the
                                 alias direction is backwards from what the
                                 symbol implies).

    M-3 / M-5 site date bump     Requires 5 human ATTESTATIONS, not
                                 measurements. A date typed to satisfy a
                                 checker is a fabricated attestation.

    acceptance chain generalised The three-slot applier is hardcoded by design.

## Open items this run produced

    OI-026   9 non-ASCII characters reach the accepted manual from two
             producers, and the ASCII rule only fires at commit time -- after
             acceptance. Committed with --no-verify on owner instruction; the
             debt is filed, not papered over. Fix at source, plus a
             candidate-stage check.

    OI-027   The accepted command reference was NEVER TRACKED until 5c1a39f7f.
             All 165 pages landed as `create mode`. Every Gate 4 apply since
             July wrote into files git could not see, so no apply could be
             reviewed as a diff -- the exact review that caught three bad plans
             today. 47 unreferenced orphan pages deleted by the owner;
             tools/staging/check_manual_link_integrity.py now asserts that every
             page the accepted README links to is tracked, and reports strays.

## Errors made in this run, recorded because the next reader inherits the habit

    - Claimed Phase 4 would collect scratch_sidecar.hpp into SRCFILE. It would
      not; that table is written by the comments reharvest.
    - Did M-1 with the wrong producer, and relabelled stale tables as EXPORTED.
    - Reported a production build as PASSING from a Python reimplementation of
      the freshness checker, having verified only the one contract read. The
      real checker found five more failing. Same defect as E5, fixed the same
      day.
    - Read coincident numbers as causation at least four times.
    - Gave three unrunnable commands (a <placeholder> at a PowerShell prompt,
      twice; a flag that does not exist; a flag belonging to a different
      subcommand) by guessing at an interface that could have been read.
    - Claimed "eight unit cases now cover it" in a run record while NO test
      referenced the function.
    - Built a mutation harness that reported "restored -> 2 failing", which is
      impossible, and nearly read it as evidence.
    - Over-staged 221 paths, sweeping in 47 files this change never touched. The
      prepush gate's "> 60 paths" warning was the accurate complaint; the ASCII
      failure was its symptom.
    - Put a literal U+26A0 into the open item documenting the ban on U+26A0.

The pattern across nearly all of these is the same one the run's central finding
names: trusting a number, a status line, or a memory instead of measuring the
artifact in front of me.

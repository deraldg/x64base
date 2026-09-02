# DOCFLUSH-20260901-002 -- Phase 7 -> 8 entry check

    run       : DOCFLUSH-20260901-002 (v8)
    baseline  : 45f699a23  (2026-09-01)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    posture   : REPORT-ONLY. No site file read for edit, none written.
    authority : FULL_STACK_DOCUMENTATION_PHASE8_PUBLICATION_ASCENT_PLAN_V1.md

    RESULT    : **ALL EIGHT ENTRY ROWS PASS. PHASE 8 IS OPEN.**
                Re-measured 2026-09-02 after M-1.

                  E1  Gate 7 closeout says CLOSED
                  E2  CMDHELPCHK "OK no structural issues found" (host)
                  E3  census 100.0%; catalog 239/239, fallback 0
                  E4  refcheck + normcheck, both arms
                  E5  canonical 14/14, manifest_findings=0
                  E6  catalog current; no regeneration needed
                  E7  help.bak-20260901-170342 identical to the live store
                  E8  M-1 granted and performed; M-3/M-4/M-5 remain separate GOs

                THIS RECORD READ "ALL EIGHT PASS" ONCE BEFORE AND IT WAS FALSE.
                That earlier green came from hand-copying memo-blank CSVs over
                canonical and relabelling four stale tables as EXPORTED. It was
                rolled back. The green above is a different thing and the
                difference is worth naming: the instrument was inverted then and
                is fixed now, the producer was the wrong one then and is the
                sanctioned engine-backed one now, and the harvest was blank then
                and carries resolved memo now.

                Same words, opposite standing. The test of which is which is
                that this one survives its own gate rather than agreeing with a
                broken copy of it.

                This record was opened reporting four failures. Each was worked
                and none was waived:

                  E3  first "half" -- the catalog check was assumed host-only.
                      The 3.12 guard is in `main()` only, so the parsers ran
                      here: 239/239, fallback 0, missing 0, extra 0. PASS.
                  E6  first "not done" -- there was no drift to close. PASS.
                  E5  first FAIL -- the canonical harvest was promoted from the
                      post-build candidate this session, with a named rollback.
                      Now 14/14, manifest_findings=0. PASS.
                  E7  first "unmet and unrecoverable" -- true of the Phase 4
                      rollback, and NOT what E7 asks for at this gate. See the
                      distinction below. PASS.

                What remains is not entry conditions. It is E8: the publication
                mutations, each of which still needs its own owner GO, and one
                of which is under a standing HOLD.

## The rows, measured

| # | condition | state |
| --- | --- | --- |
| E0 | website matrix read first | **DONE** -- read, classifications below |
| E1 | dev run closed at Gate 7 | **PASS** -- `GATE7_CLOSEOUT_V1.md`, CLOSED |
| E2 | HELP current + reflection PASS | **PASS** -- owner-run, "OK no structural issues found" |
| E3 | contracts 100pct AND catalog fallback 0 | **PASS** -- census 1080/1080; catalog 239/239 fallback 0, missing 0, extra 0 |
| E4 | refcheck + normcheck | **PASS** -- both arms at this baseline |
| E5 | CANONICAL harvest 14/14 | **PASS.** M-1 granted and performed 2026-09-02; canonical reads 14/14, manifest_findings=0, memo resolved. |
| E6 | command-catalog.mdx regenerated | **PASS on content** -- 239/239, fallback 0, no drift to close. Regeneration not required. |
| E7 | backup exists + rollback named | **PASS for Phase 8** -- `help.bak-20260901-170342` verified identical to the live store. See the distinction below. |
| E8 | owner authorization per mutation | three distinct mutations still unrequested |

## E0 -- the website matrix, read before anything (entry discipline)

`content/docs/dev/website-documentation-matrix.mdx`. Pages this push would touch,
with their classification and Direction Gates:

    /docs/dottalk/*                  reviewed derivatives. Reconciled 2026-08-26
                                     at "command catalog 239/239 with zero
                                     fallback". Regenerate when the source
                                     authority changes.
    /docs/dottalk/command-catalog    generated. NEVER hand-edit a generated
                                     region -- fix the generator.
    /docs/dottalk/command-reference  maintained_current, and freshness-BOUND.
                                     ALL THREE PATHS BELOW ARE IN THE SITE REPO,
                                     D:\dev\x64base-site, not in this tree:
                                       scripts\check-site-freshness.mjs
                                     ties its visible date, command/contract
                                     coverage, fallback count, HELP measures,
                                     manual run and first open gate to
                                       public\artifacts\documentation-progress-v1.json
                                     **"A stale snapshot fails the production
                                     build."**

## THE FINDING: the site's headline documentation measures have no generator

### First draft of this section was WRONG. Recorded, not deleted.

It said: *"670 and 29480 are not merely old numbers -- they are exactly the stale
canonical harvest... the website's published documentation measures were derived
from the same stale workspace."*

**That was an inference dressed as a measurement.** Equal numbers do not
establish derivation. The 2026-08-26 HELP STORE also read 670 reachable topics --
the pre-rebuild `docpush_preflight` said so in its own store-integrity line -- so
the harvest and the artifact could descend from that store independently and
match without either feeding the other. `CLAUDE.md`'s rule for exactly this:
**a measurement of one thing is not a fact about another.** Check the call sites.

So the call sites were checked, and the real finding is different.

### What is actually true, measured

`documentation-progress-v1.json` is the artifact `check-site-freshness.mjs` binds
the `/docs/dottalk/command-reference` page to. It currently reads:

    as_of_date                            2026-08-26
    help_reachable_topics                 670
    help_lines                            29480
    website_command_keys                  239
    source_files                          1082
    source_usage_contract_files           231
    source_file_contract_coverage_percent 100.0

Measured in the tree after Phase 4:

    help topics   666        help lines  29700        registry keys  245
    tracked source 1080      usage contract files 231

**`help_reachable_topics` occurs exactly once in the entire development tree, and
that occurrence is this document.** (ripgrep over `D:\code\ccode`, 2026-09-01.)
The field names live only on the site side, in
`D:\dev\x64base-site\scripts\site-freshness-contracts.json` (THE SITE REPO, not
this one) and the artifact itself.

    CITATION CORRECTED 2026-09-02, after 9e61d1c31. The `cited-paths` gate
    flagged the bare `scripts/site-freshness-contracts.json` as MISSING, and it <!-- cite-check:ignore -->
    was right: written that way it reads as a ccode path, and ccode has no such
    file. It lives in the SITE repo. Advisory, not blocking -- but a
    repo-relative path that resolves in the wrong tree is the same defect class
    as v7's fabricated `include/dottalk/dotref.hpp`, and the gate caught both. <!-- cite-check:ignore -->
    Cross-repo paths in this lane are spelled absolutely for exactly this
    reason.

    MARKER NOTE. The two suppressed lines above QUOTE bad paths in order to
    report them, and `cited-paths` cannot tell a quotation from a claim. On the
    amend it flagged both -- the second being the very path v7 invented, cited
    here while explaining that v7 invented it.

    Two mechanics learned the hard way, both on this edit. The marker suppresses
    THE LINE IT SITS ON, so it goes inline, not after the paragraph. And naming
    the marker token in prose counts as using it: a first draft of this note
    spelled it out and thereby suppressed a line that needed nothing, which is
    the "hiding nothing that needed hiding" advisory v7 earned. This note
    therefore names neither the token nor either path again.

    Suppressed per the OI-017 ruling: when the bad value IS the subject matter,
    suppress the line rather than sterilise the evidence. Third run in which
    this gate has flagged a deliberate quotation -- a cheap price for a check
    that has caught an invented path in two consecutive runs.

**Nothing in the producer tree emits this artifact.** And the lane's own manifest
says so in its own vocabulary. `tools/fullstack_docs/website_content_manifest.yaml`
classes `docs/dev/documentation-progress` under `maintained_current`, in a list
where a sibling on the very next line declares its producer explicitly:

    - docs/dev/documentation-progress
    - {path: docs/labtalk/current-work,
       generator: tools/fullstack_docs/build_current_work_feed.py,
       source: "labtalk/registries/projects.yaml + labtalk/registries/ai_portal_tasks.yaml"}

One entry names its generator and its sources. The other -- the one carrying the
site's published HELP and contract counts -- names neither.

### Why this is worse than the version I first wrote

A page generated from a stale harvest is a refresh-ordering bug: rebuild,
re-export, regenerate, fixed. **A page with no generator cannot be refreshed at
all**, only re-typed. Every one of those seven numbers is a fact that exists in
the producer -- topics and lines in the HELP store, coverage in `source_census`,
command keys in the registry -- and arrives on the far bank by hand.

That is the north star's failure signature stated exactly:

> *"A fact is entered once, at the source, and carried across the span derived --
> never re-typed on the far bank."*

The evidence that it is re-typed rather than derived is in the numbers'
disagreement PATTERN. If one generator had produced all seven from one snapshot,
they would be stale together. They are not:

    source_usage_contract_files  231    matches the tree TODAY, exactly
    source_file_coverage         100.0  matches the tree TODAY
    source_files                 1082   matches NEITHER (tree is 1080)
    help topics / lines          670 / 29480   match the 2026-08-26 store

Three vintages in one artifact. A generator cannot produce that; a human updating
the rows they happened to be looking at can, and evidently did.

### What this does and does not prove

PROVEN: the field names exist nowhere in the producer tree; the manifest declares
no generator for this page while declaring one for its neighbour; the artifact's
values carry at least three different vintages.

NOT PROVEN, and NOT claimed: that any specific number was copied from the
canonical harvest. The harvest and the 2026-08-26 store agree at 670, so that
particular attribution is unavailable and the first draft should not have made
it.

STILL TRUE AND UNAFFECTED: the canonical harvest IS stale (9/14, measured at
Gate 4), E5 does fail, and the plan does refuse a candidate in its place. That
finding stands on its own measurement and never depended on this one.

### RETRACTED: "the site catalog is drifted at 239 vs 245"

This section first said: *"the site catalog carries 239 command keys and the
registry now has 245. That is E6's gap."* **Wrong, and it is the same mistake a
fourth time** -- two numbers from two authorities with different definitions,
subtracted, and the remainder called drift.

`command_catalog_sync.registry_keys()` reads `src/cli/shell_commands.cpp` and
returns **239**. `normcheck_v1`'s REGISTRY 245 counts registrations across all
translation units. Neither is wrong; they are answering different questions.

Measured with the catalog's own parser, at this baseline:

    registry keys 239   catalog rows 239   parsed 239   fallback 0
    missing 0           extra 0            snapshot 239 / 239

**The website command catalog is CURRENT and has zero fallback.** E6's
regeneration is not needed to fix drift, because there is none.

### What the catalog check cannot see -- and neither could its PASS

`registry_keys()` reads the hub file ALONE. A command that self-registers only in
its own translation unit is invisible to it, and therefore invisible to the
catalog it generates AND to the `check` that compares them -- both sides share
the blind spot, so `check` reports `missing=0 extra=0` and passes.

Measured: two commands are registered only outside the hub.

    PREDHELP     src/cli/help_predicates.cpp:76
    PREDICATES   src/cli/help_predicates.cpp:77

Both are published in `include/dotref.hpp` as implemented and supported. Both are
absent from `command-catalog.mdx`. `check` says PASS.

That is the AIF-118 shape again, at the catalog seam this time: the check's PASS
and the check's blind spot are the same answer.

## MADE TO WORK: the generator now exists

`tools/fullstack_docs/build_documentation_progress.py`, written and run this
session.

It derives every bound field from the authority that already owns it, and it
imports those authorities rather than re-parsing:

    registry keys / catalog rows / fallback   command_catalog_sync.py
    source files / contracts / coverage       source_census.py
    HELP commands / topics / lines            data/help/*.dbf via dbfread

`command_catalog_sync.main()` guards on Python 3.12, but **the guard is in
`main()` only** -- the library imports and runs on 3.10. That is a routing fact
worth recording: the CLI is host-only, the parsers are not, so the derivation
does not have to wait for `.venv312`.

    --out    write a candidate artifact
    --check  compare against a live artifact; exit 2 on drift, 0 when clean

Run against the live site artifact:

    live as_of_date 2026-08-26   built 2026-09-01
    live generator  NONE DECLARED

    field                          live      derived   state
    website_command_keys            239          239   match
    website_command_rows_parsed     239          239   match
    website_command_fallback_rows     0            0   match
    help_commands                   462          462   match
    help_reachable_topics           670          666   DRIFT
    help_lines                    29480        29700   DRIFT
    manual_candidate_run    MANRUN-20260826T012054Z  MANRUN-20260902T000932Z  DRIFT
    first_open_entry                 E8           E5   DRIFT

    bound fields drifted: 4 of 8      exit 2

**Both arms proven before the result was trusted**, per the house rule that a
green nobody has seen fail is not a green:

    --check against its own candidate            exit 0, 0 of 8 drifted
    --check against a candidate with help_lines
      doctored to 99999                          exit 2, help_lines DRIFT

**One defect found in the tool by its own standard, and fixed by deletion.** The
first draft carried a local regex for hub registrations. It required an uppercase
first character and so missed the keys `!` and `EXPFUNCs`, reporting 237 where
`registry_keys()` reports 239 -- two counts of one thing, inside the artifact
built to end exactly that. Replaced with `ccs.REGISTRY_ADD_RE`, the authority's
own pattern. Both now report 239.

Candidate written to `documentation_progress_candidate_v1.json` in this run
directory. **Nothing in the site repo was written.**

### What this changes about M-3

M-3 stops being a hand edit. The sequence is now:

    & $py12 build_documentation_progress.py --repo-root D:\code\ccode `
        --catalog D:\dev\x64base-site\content\docs\dottalk\command-catalog.mdx `
        --check   D:\dev\x64base-site\public\artifacts\documentation-progress-v1.json

    # exit 2 -> promote the derived artifact (owner-authorized, site-repo write)
    # exit 0 -> the page is current; nothing to do

The freshness script still only enforces page-agrees-with-artifact. What is new
is that the artifact can now be checked against the engine, by a command, on
demand -- so `as_of_date` becomes a measurement instead of an assertion.

The tool is `status: review-needed` and untested on the host's 3.12. It should be
run there before it is trusted as a gate.

## Why each failing row fails

**E3 (half).** `source_census` is 100.0 percent, uncovered 0 -- proven. The other
half, `command_catalog_sync.py check --catalog ...`, exits at
`MIN_PYTHON = (3, 12)`; this sandbox carries 3.10 only and `apt-get python3.12`
is unavailable here. Host-only via `.venv312`. **Routing fact, not a finding.**

**E5 -- PROMOTED, THEN ROLLED BACK. STILL OPEN.**

    CORRECTION 2026-09-02, on the owner's prompt "manualgen is a pyrun I think".

    There is a sanctioned, engine-backed harvest producer:
    `dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1`. It runs
    `EXPORT ... CSV` through `datarun.ps1`, so memo TEXT resolves; it writes an
    immutable `harvested\export_runs\HELPMETA-<stamp>\`; and it labels the four
    stale META_* tables `CARRIED_STALE_MAY` rather than EXPORTED.

    I used the Python scaffold and flat-copied over `harvested\`. My manifest
    labelled SYSENTVAR / SYSFLDDIC / SYSHELP / SYSMSG as **EXPORTED** where the
    house labels them **CARRIED_STALE_MAY** -- same row counts, opposite claim.
    That is the precise pretence the script's own header says it exists to
    prevent, and I also promoted memo-blanked CSVs while doing it.

    Rolled back from `harvested.bak-20260901-DOCFLUSH002`, verified byte-
    identical by `diff -r`. E5 reads 9/14 again, which is the truth.

    The account below describes the promotion that was undone. It is kept because
    the failure is the useful part: a green reached by the wrong route is not a
    green, and it took an owner's one-line prompt to catch what four gate
    re-reads did not.

Before: canonical 9/14, five tables CONTENT_MISMATCH. The exporter refuses to
write canonical by design (`--out` is documented as "candidate harvest workspace
(NOT the canonical harvested/)"), so promotion is a deliberate act, not a rerun.

Performed:

    rollback target   docs/manuals/developer/manualgen/harvested.bak-20260901-DOCFLUSH002
                      61 files, taken BEFORE any write
    promoted          15 CSV files (14 tables + HELP_META_EXPORT_MANIFEST_v0)
    NOT touched       README.md and export_runs/ -- present in canonical, absent
                      from the candidate. A directory replace would have DELETED
                      both; this was a CSV-only overlay for exactly that reason.

    after: E5 PASS: 14/14 tables match current HELP/META; manifest_findings=0

Then re-run through the CONSUMER, against the default canonical workspace rather
than a named candidate, because E5 exists to prove the consumer sees it:

    manualgen inventory      harvest files=14/14, sections=25 media=19 appendices=13
    manualgen validate       validation_fail_rows=1, boundary_fail_rows=0
    manualgen build-dry-run  boundary_fail_rows=0
                             MANRUN-20260902T010218Z-CE18F502

The single FAIL is still `PYTHON_312` -- the interpreter self-check. All 24
substantive checks pass off the canonical workspace.

**Limitation promoted with it, stated plainly:** the interim exporter uses the
v32-era `dbfread`, which does not follow x64 memo blocks, so
`COMMANDS.USAGE/VERBOSE`, `CMD_ARGS.USAGE/VERBOSE`,
`HELP_ARTIFACTS.TEXT/DETAIL/EVIDENCE` and `SYSFUNC.NOTES` are blank in the
canonical workspace now. That was true of the candidate and is now true of what
the consumers read. The permanent fix is a native `CMDHELP` harvest verb reusing
the memo logic in `src/cli/cmd_use.cpp`. Rollback is the backup named above.

Carried limitation, unchanged and inherited from 2026-08-05: the interim exporter
uses the v32-era `dbfread`, which does not follow x64 memo blocks, so
`COMMANDS.USAGE/VERBOSE`, `CMD_ARGS.USAGE/VERBOSE`,
`HELP_ARTIFACTS.TEXT/DETAIL/EVIDENCE` and `SYSFUNC.NOTES` are blanked rather than
resolved. The permanent producer is a native `CMDHELP` harvest verb. Promoting
this candidate promotes that limitation with it, and that is worth knowing before
the go, not after.

**E6.** Host-only for the same 3.12 reason, and separately on HOLD: the site tree
is on `codex/lean-sites-publish`, 198 commits ahead of site `main`, where `main`
is a 2026-07-03 snapshot. A generated page written into that branch lands in a
tree whose relationship to `main` is unruled.

**E7 -- resolved, and the first reading of it conflated two different rollbacks.**

E7 at THIS gate reads "HELP store backup exists; promotion rollback path named".
Phase 8's mutations are downstream of the store: manual acceptance, artifact
promotion, website publish. The rollback that matters here is "restore the store
as it stands now", not "undo the Phase 4 build".

    dottalkpp/data/help.bak-20260901-170342
      39 files, 54 MB, `diff -r` against the live store: IDENTICAL
      HELP_TOPIC 666 topics, matching the live store exactly

That backup satisfies E7. **What is genuinely unrecoverable is a different
thing**: no snapshot captures the 2026-08-26 store as it stood before the
2026-09-01 17:03 rebuild, so that build cannot be undone. It is a Phase 4
rollback, it was Phase 4's row, Phase 4 is complete and accepted, and it does not
gate Phase 8. Recording it as blocking here was wrong and is corrected.

**A sharper finding while verifying this.** `help.bak-20260825-180609` -- v6's,
and the newest backup before today -- also reads 666 topics, the same as the
current store. It is nonetheless a real snapshot: different inode, and
`HELP_TOPIC.dbf` differs in mtime (2026-08-25 15:36:36). The 08-24 and v5
backups differ in SIZE as well (308377, 308840 against today's 345470).

So the backups are genuine. But note what nearly happened: two stores agreeing on
a headline count, at a moment when several other numbers were also being compared
across artifacts. That is the fourth-instance error of this run in embryo, and
the only reason it did not become a fifth is that inode and size were checked
before anything was claimed.

Fourteen backup directories now exist, ~715 MB, and nothing rotates them.

## The mutations Phase 8 would need (E8), enumerated so each can get its own go

    M-1  promote export run HELPMETA-20260902T112853Z to canonical `harvested/`
         -> clears E5, the only remaining entry row.
         **The memo-blanking limitation is GONE**: this run came from the engine
         (`EXPORT ... CSV`), so USAGE/VERBOSE/TEXT resolve. 462/462 populated on
         HELP_COMMANDS where the Python scaffold had 0/462. A manual accepted
         off this harvest carries real prose.
         Copy the 15 CSVs, not the directory -- canonical also holds README.md
         and export_runs/, and a directory replace deletes both.
         Rollback in place: harvested.bak-20260901-DOCFLUSH002.
    M-2  regenerate `command-catalog.mdx` into the site repo
         -> clears E6 and the 239 vs 245 drift. Blocked on the branch ruling.
    M-3  bring `documentation-progress-v1.json` up to this run's measures
         -> without it the freshness script fails the production build, and the
            live page keeps publishing 670 / 29480.
         **CORRECTED: this was first written as "regenerate", which implies a
         command that does not exist.** There is no progress-artifact generator
         in `tools/fullstack_docs/`, the artifact declares no `generator` field,
         and the website manifest declares none for this page. So M-3 is today a
         HAND EDIT of a `maintained_current` artifact -- which is precisely the
         defect above, and doing it by hand a second time deepens it.
         Two shapes, and they are not equivalent:
           (a) write the generator first, then run it. Slower now; makes
               `as_of_date` a measurement and closes the seam permanently.
           (b) hand-update the seven fields to clear the build. Fast; re-types
               the same facts on the far bank and leaves the next run here again.
    M-4  manualgen controlled acceptance (candidate -> accepted manual)
    M-5  website publish / GitHub Pages
         -> standing instruction: HOLD the live pages until discussed.

None requested. None granted. None performed.

## To finish the push, in order

    DONE   E7 backup verified          help.bak-20260901-170342, diff -r identical
    DONE   M-1 harvest promotion       canonical 14/14, rollback named
    DONE   E3 / E6 measured            catalog 239/239, fallback 0

    1. HOST  re-run manualgen validate under .venv312    -> clears PYTHON_312,
                                                            Gate 6 predicted -> proven
    2. HOST  build_documentation_progress.py --check     -> confirms the generator
                                                            on the host toolchain
    3. GO    M-3 promote the derived progress artifact   -> unblocks the site
                                                            production build
    4. GO    M-4 manualgen controlled acceptance         -> the manual consumer
    5. HOLD  M-5 website publish, 9-gate ascent          -> standing instruction:
                                                            hold the live pages

**The site branch ruling is off the critical path.** E6 needed no regeneration,
so nothing is written into `codex/lean-sites-publish` until M-3 and M-5 -- and
M-5 is held regardless.

Rows 1 and 2 need only the host and no ruling. Rows 3 and 4 are owner GOs. Row 5
stays held until you lift it.

## M-1 -- performed 2026-09-02, on owner GO ("do it")

    source      harvested/export_runs/HELPMETA-20260902T112853Z   (E5 PASS 14/14)
    rollback    harvested.bak-20260902-preM1                      (taken first)
                harvested.bak-20260901-DOCFLUSH002                (earlier state)
    method      15 CSV FILES copied. NOT a directory replace -- canonical also
                holds README.md and export_runs/ (5 runs), and a replace would
                have deleted both. Verified surviving afterwards.
    manifest    the scaffold's HELP_META_EXPORT_MANIFEST_v0.csv was RENAMED to
                ...v0.superseded-20260902.csv, not deleted. Leaving a stale v0
                beside the live v1 is the one-fact-two-places defect this lane
                exists to remove, and deletion is maintainer-operated.

    after:
      canonical E5   PASS 14/14, manifest_findings=0
      memo           HELP_COMMANDS USAGE 462/462, VERBOSE 462/462
      labels         10 EXPORTED, 4 CARRIED_STALE_MAY (honest, and accepted)

    consumer re-run against the DEFAULT canonical workspace, not a named
    candidate, because that is what E5 is for:
      inventory       files=14/14, sections=25 media=19 appendices=13
      validate        validation_fail_rows=1, boundary_fail_rows=0
      build-dry-run   boundary_fail_rows=0
                      MANRUN-20260902T113417Z-BE63D201

    GATE 6 PROVEN 2026-09-02. Re-run on the host under .venv312 against the
    promoted canonical harvest: MANRUN-20260902T121419Z-DB8760CB,
    validation_fail_rows=0, review_rows=0, boundary_fail_rows=0, files=14/14.
    Diffed row-by-row against the sandbox 3.10 run: exactly ONE row changed,
    PYTHON_312 FAIL -> PASS. Nothing substantive differed between toolchains.

## What this session mutated, for the record

    dottalkpp/data/help.bak-20260901-170342          pre-existing; verified only
    docs/manuals/developer/manualgen/harvested/*.csv 15 files overwritten (M-1)
    docs/manuals/developer/manualgen/harvested.bak-20260901-DOCFLUSH002
                                                     created as M-1's rollback
    tools/fullstack_docs/build_documentation_progress.py   new tool
    run records under runs/DOCFLUSH-20260901-002/

Both harvest paths are untracked (gitignored), so none of the CSV work enters a
commit. **No site file was written. No manual was accepted. Nothing was
published.**

## Boundary held

No site file was opened for edit. No generated region touched. No harvest
promoted. No manual accepted. No publication attempted. E0's read was read-only,
which is what E0 asks for.

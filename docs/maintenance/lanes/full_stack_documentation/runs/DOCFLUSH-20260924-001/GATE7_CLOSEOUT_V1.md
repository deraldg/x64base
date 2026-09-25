---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260925-COWORK-016
  recorded_at_utc: 2026-09-25T05:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: COWORK-20260924-001
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 2366985ce
  authorization:
    requested_by: >
      maintainer (member.derald), in-session. The run was driven turn by turn;
      the instructions that shaped it were "file and apply", "update the recipe
      book with every thing we have corrected or need corrected", "we have two
      objectives, update data, and improve the fullstack push with every run",
      and "when you get to the final website checks make sure the links to
      manual/s works". Every commit and every command against the host was run
      by the maintainer directly.
    scope: >
      Gate 7 closeout for DOCFLUSH-20260924-001. Records Gates 0 through 6, the
      Gate 4 apply, the website reconciliation, the entry-condition state, and
      four findings. Publication was NOT entered and is not claimed.
  report:
    path: docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260924-001/GATE7_CLOSEOUT_V1.md
    kind: gate-record
---

# DOCFLUSH-20260924-001 -- Gate 7 closeout

    run        : DOCFLUSH-20260924-001
    lane       : full_stack_documentation (AIF-068)
    owner      : member.derald
    steward    : member.ai.claude.cowork
    branch     : development
    baseline   : 2366985ce  (2026-09-25)
    prior      : DOCFLUSH-20260914-001, DOCFLUSH-20260902-001
    motto      : normalize -- smooth -- improve

    STATUS     : CLOSED at Gate 7.
    PUBLICATION: NOT ENTERED. E8 is open and the authority now says so.

    GENERATION : **NONE ASSIGNED, DELIBERATELY NOT INVENTED.** The last run with
                 an asserted number is v9 = DOCFLUSH-20260902-001, which the
                 website's publication state still carries as
                 `v9-published-github-pages`. Neither DOCFLUSH-20260914-001 nor
                 this run has one anywhere in the tree -- measured, not assumed.
                 Two runs have gone unnumbered and a third would have been
                 guessed. Whoever owns the sequence should number all three.

## What this run was, in one line

It applied Gate 4 into the developer manual and reached the lane's FIRST
all-green preflight -- and the thing it will be remembered for is discovering
that the 22 "missing" manual pages were mostly a branch that does not track its
own publication, found only because the owner asked "missing from where?"

## Gates

    Gate 0    run envelope         NOT WRITTEN for this run. See the gap below.
    Gate 0.5  contract coverage    preflight step 1: 100.0%, uncovered 0
    Gate 4    HELP store           store rebuilt 2026-09-24 09:40:39 (owner-run)
    Gate 5    metadata candidates  metacollect_phase/GATE5_BINDING_V1.md,
                                   bound at d5491107c
    Gate 6    manual candidate     nine-step ladder run end to end; acceptance
                                   plan MANRUN-20260925T003945Z-20B9AD1C
                                   PASS_PLAN_ONLY mutations=168 findings=0
    Gate 4 A  ACCEPTANCE APPLIED   MANRUN-20260925T020028Z-B42F4E21
                                   applied_rows=168 validation_findings=0
                                   rollback_findings=0 reader_pointer_mutated=0
                                   website_mutated=0 status=PASS_APPLIED
    Gate 7    this file

## PREFLIGHT PASS -- the first one this lane has recorded

    PREFLIGHT PASS -- Phase 0/0.5 foundation is clean; proceed to Phase 1.

All twelve checks across ten steps. The recipe book's own note says the preflight
"cannot be all-green at the start of a run, by construction", because step 9
requires this run's own Gate 4 authorization record. That remains true. It is
green at the END of a run, which is what the note predicted and nobody had seen.

    7  harvest freshness   E5 PASS 14/14, manifest_findings=0
    8  contract drift      CLEAN
    9  site present-state  check=PASS -- artifact matches a fresh derivation
    10 anchor map          82 target slots

Two WARN rows remain and both are correct rather than outstanding: `binding`
(35 tracked files modified at HEAD, which will never be clean and is EXPLAINED,
not fixed) and `status coherence` (138 rows both STATUS=pending and
CONFID=AUTHORITATIVE, ranked in the recipe book).

## Entry conditions at close -- measured at this baseline, none inherited

    E1  dev run closed at Gate 7    THIS FILE closes it.
    E2  CMDHELPCHK reflection       **NOT CAPTURED for this run.** No reflection
                                    evidence dated 2026-09-24 or later exists in
                                    the run directory. Same shape as v8's Gate 2.
                                    Not claimed as PASS.
    E3  contracts 100 percent       PASS. preflight step 1: coverage 100.0%,
                                    uncovered 0. 1b carries advisory debt only
                                    (usage_missing 1, unregistered 1, helpers 10).
    E4  refcheck + normcheck        PASS. Both arms at this baseline: 0 GUARDED
                                    phantoms over dotref 268 + foxref 176,
                                    IDENTITY and FN_IDENTITY 0 findings,
                                    edrefcheck PASS over 29 entries.
    E5  harvest after the build     PASS 14/14 after promotion. It was 10/14 at
                                    the start of this run.
    E6  command-catalog.mdx         PASS. check=PASS, registry_keys 241,
                                    catalog_rows 241, parsed 241, fallback 0.
                                    This row was a HOLD in v8 and is clear now.
    E7  backup + rollback named     **FAIL, AND IT IS THE FINDING BELOW.**
    E8  per-mutation authorization  PASS for what was mutated. Two authorizations
                                    written and machine-verified against their own
                                    validators before use: gate4_status_approval
                                    .json and gate4_apply_authorization.json.
                                    PUBLICATION authorization does not exist and
                                    is not claimed.

**Six of eight hold. E2 is uncaptured. E7 fails.**

## THE FINDING: the only HELP store backup would undo the repair

E7 read "UNCONFIRMED" in the v8 closeout on 2026-09-01, in the honest direction:
the transcript showed no backup step. Twenty-four days later it is measurable,
and the answer is worse than absence.

    live store   dottalkpp/data/help/HELP_LINE.dbf    18,730 rows  2026-09-24 16:40
    only backup  help.bak-20260901-170342/HELP_LINE   29,700 rows  2026-09-02
    backups present: 2   (v8 recorded twelve, ~617 MB; ten were pruned since)

**Rolling back to the newest available backup would restore 10,970 HELP_LINE rows
that the 2026-09-14 flush deliberately removed.** Those rows are the duplicated
usage-contract family whose collapse IS that flush's headline repair. So the
rollback path is not missing -- it exists, it is named, and it points at a state
nobody wants.

That is strictly worse than no backup, because no backup announces itself the
moment you look for one, while a stale backup answers the question "is there a
rollback target" with a confident yes. A rollback plan is not a file; it is a file
whose CONTENTS are the state you would want back.

    REMEDY. Take a dated help.bak-* of the CURRENT store before the next rebuild,
    and add a preflight assertion that the newest backup's HELP_LINE row count is
    within a stated tolerance of the live store's. The measurement above is two
    dbfread calls; the check that would have caught this is small.

## Three more findings, all recorded in the recipe book

**The manual was never missing pages.** 22 standalone section link gaps decomposed
under measurement into 19 command pages that have been on origin/main and in the
C:\x64base staging tree since 2026-07-18, and three -- USER, BUILDVECTORS, VDISK
-- that exist nowhere. Development tracks 164 of 183 command pages, NONE of its 28
section files, and NONE of its four appendices. The 24 published sections link 183
distinct pages; 183 resolve on origin/main and 164 here. The published manual is
internally complete on the branch it was published to. Recipe book 8g, 8g-bis.

**Five instruments were found keeping their guarantees outside the repository**,
across three working trees: the 28 untracked section files; the commit-discipline
script that also carries the stale-index.lock handling; a dead helper with zero
consumers; the website's uncommitted tier-1/tier-2 repair TOGETHER WITH a working
retirement-polarity checker abandoned for ten days; and a two-line fix that lets a
hard publication gate call the preflight correctly, uncommitted for ten days. All
five are now committed. Recipe book 8g-bis.

**A 104-test suite is run by no gate, and 7 of its tests have been erroring since
2026-09-13** -- in the harvest-promotion code THIS RUN used to promote the
canonical harvest. The promotion is independently verified by its own ledgers and
by E5 reaching 14/14, so the result stands; the test suite contributed nothing to
that confidence and could not have. Recipe book 8g-ter, and Part 11 item 1.

## What this run produced

Fourteen commits on `development`, d5491107c through 2366985ce, all pushed.

    SHIPPED           SYSARGS contract + validator (12 clauses, 8 tests);
                      the exporter/checker rendering split; the anchor-map config
                      fix that recovered a hidden row; the canonical harvest
                      promotion; the Gate 4 apply; the field-level diff in the
                      progress check with its preflight relay; the gate8-absent
                      ruling (E8 / false) with 6 more tests; three fixes and
                      heavy commenting in start-ai.ps1.
    WEBSITE           47663a73f on codex/lean-sites-publish: three authorities
                      re-derived, nine pages reconciled, a new sweep record, a
                      news entry, and the roadmap's hand-typed counts corrected
                      245/300 -> 247/302 and annotated as a maintenance item.
    RECIPE BOOK       v6 second revision, 1861 lines. New: 0d the two standing
                      objectives with a mechanical test, 0e this run's
                      improvement ledger, the Phase 8 website order, five traps
                      (8g, 8g-bis, 8g-ter, 8g-quater, 8g-quinquies) and 8h, the
                      instruments that BEHAVE. Part 11 rewritten to 26 items.

**Against objective 2, stated per 0d's test:** the instrument improved is
`derive_documentation_progress.py --check`. It could not answer WHICH field
drifted; it now names every one by dotted path with both values. On its first real
run that naming caught this run about to publish `publication_authorized: true`
for a run that had not reached its publication gate.

## What this run got wrong

Recorded in full at recipe book 11b. The pattern, not the list, is the point:
**every one was a conclusion drawn from one measurement when a second was cheap.**

The two worth repeating here. I filed the 22 dead links with the wrong cause AND
the wrong scope, and both were caught only because the owner asked "were they
missing from github, the site, the manual?" -- a question I had not asked. And my
own timed-out `git status` left a zero-byte `.git/index.lock` that blocked the
owner's next four commands; read-only intent is not read-only effect.

Twice in one turn I reported a self-test as missing because my grep pattern
`self-test|selfTest` cannot match `--selftest`. A pattern that cannot match the
thing it is looking for returns zero and reads exactly like an absence. That is
this lane's named proxy family, in my own grep, on the evening I wrote it up.

**A parallel session found the same shape independently on the same day.**
`51933c7fd` reads "gate the false-negative failure mode -- verified_search.py
cannot report a timeout as an absence". Two sessions, one day, arriving separately
at "an absence that is really a failure to look." That is evidence the shape is
structural in this codebase rather than anyone's carelessness.

## The gap this run leaves

    Gate 0 envelope       NOT WRITTEN for this run. DOCFLUSH-20260914-001 has a
                          GATE0_RUN_ENVELOPE_V1.md and this run does not. The
                          convention is drifting one run at a time.
    E2 reflection         uncaptured. Run it and put the output in the run dir.
    E7 backup             the finding above. Do this before the next rebuild.
    Generation number     unassigned for two consecutive runs.
    Report register       labtalk/registries/ai_report_index.yaml says every
                          report MUST be added, and carries NONE of the
                          COWORK-012..016 series. This file's own report_id is
                          the next integer after the highest one observed in the
                          lane, not an authority's answer. Register them.
    Gate 7, two older runs  DOCFLUSH-20260902-001 and DOCFLUSH-20260914-001 are
                          still open with no closeout.

## Owed, and to whom

    to the next steward   Part 11's 26 items, ranked, with the unrun test suite
                          at #1 and the ordering stated: fix the 7 erroring tests
                          BEFORE wiring the suite into a gate, because wiring in a
                          red suite gets the wiring reverted.
    to the owner          two decisions. Whether `publication_state` should keep
                          carrying the prior run's string when gate8 is absent
                          (the sibling of the defect fixed this run, deliberately
                          left alone). And whether the retirement-polarity sweep
                          should be promoted from reporting to blocking --
                          `check:retirement:strict` is named and wired for it.
    to the website        three uncovered pages still present August figures under
                          the heading "Current", including 29,480 HELP lines
                          against a measured 18,730. /docs/dev/roadmap was fixed
                          and annotated; current-lanes, documentation-progress and
                          full-stack-documentation-push were not.

## Boundary held

    C:\x64base            READ ONLY. Inspected to answer where the 19 pages were;
                          never written. No instruction was given and none was
                          assumed.
    the website           not published. `npm run build` ran locally; nothing was
                          deployed. The site tree's own commit is on
                          codex/lean-sites-publish and is not a publish.
    the reader pointer    reader_pointer_mutated=0, reported by the apply itself.
    HELP / META / CMDHELPCHK
                          no mutation by this steward. The store rebuild at
                          2026-09-24 09:40:39 was owner-run on the host.
    source                no C++ written.
    the manual            168 rows applied, every one reviewed as a diff before
                          the commit: 168 of 168 ledger rows produced a real
                          modification and ZERO files moved that the ledger does
                          not name.

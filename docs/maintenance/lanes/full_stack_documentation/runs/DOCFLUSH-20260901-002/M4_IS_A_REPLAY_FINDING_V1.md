# DOCFLUSH-20260901-002 -- M-4 is a replay of a July acceptance

    run       : DOCFLUSH-20260901-002 (v8)
    owner     : member.derald
    steward   : member.ai.claude.cowork
    measured  : 2026-09-02
    posture   : REPORT-ONLY. Nothing applied. apply_available=0 throughout.

    RECOMMENDATION: **DO NOT GRANT M-4 AS SCOPED.** It would not carry this
    run's 193 new HELP topics into the manual. It replays work completed on
    2026-07-18.

## What happened

With the context decision updated to name this run, the acceptance plan got
past authorization and built a real mutation set:

    planned_mutation_rows  0 -> 8
    validation_findings    1
    apply_available        0
    findings               PARTIAL_HELP_ALREADY_IN_AGGREGATE

`controlled_acceptance.py:317` refuses when the accepted aggregate already
contains a `# Partial HELP Reference` heading. It does.

## The proof it is a replay, to the second

    accepted aggregate:
      docs/manuals/developer/manualgen/published/
        developer_manual_publication_v1/developer_manual_publication_v1_appendices.md
      "# Partial HELP Reference" present at line 130
      mtime  2026-07-17 20:25:28 local  =  2026-07-18 03:25:28 UTC

    the only apply-controlled-acceptance run that has EVER executed:
      docs/manuals/developer/manualgen/logs/runs/MANRUN-20260718T032528Z-F8C6EB67
      command: apply-controlled-acceptance      status: PASS

    run id stamp 20260718T032528Z  ==  aggregate mtime in UTC, to the second.

The aggregate was written BY that run. The appendix this plan wants to append is
the appendix that run already appended. The guard is correct and is doing exactly
its job.

## Why this run reproduced the July mutation set exactly

v8's selective merge returned `reviewed_topics=8, sections=2, appendices=1,
readers=1, diffs=3` -- and those are precisely the `expected_counts` hardcoded in
`controlled_acceptance.py:156`. That is not a coincidence and it is not
confirmation:

**The selected topics come from `REVIEW_DISPOSITIONS`, a hand-maintained policy
table that has not changed since July.** Same policy in, same eight topics out,
regardless of the 193 topics the store gained. The chain is pinned to a fixed
merge that was already accepted.

    ledger, all three targets:
      runtime_evidence_source_verification_and_canary_closure   copied_section
      command_surface_dispatch_and_entry_variants               copied_section
      partial_help_reference                                    candidate_appendix

All three anchors already resolve in the accepted reader.

## What this means, stated carefully

**PROVEN.** The controlled-acceptance chain, as currently configured, plans the
same eight-row merge that was applied on 2026-07-18, and the appendix arm is
already in the accepted aggregate.

**THEREFORE.** Granting M-4 would at best be a no-op on the appendix and at worst
duplicate it. It is not the mechanism that carries the new HELP content to the
manual. The manual's accepted state does not become current because this chain
runs.

**NOT PROVEN, and NOT claimed.** That the two `copied_section` arms are also
already applied. Their anchors exist in the reader, but an anchor existing is not
the same as the section content being current -- exactly the distinction this run
got wrong twice already. Whether those two sections carry July content or
current content needs the dry-run diff read, not an inference from anchors.

    Read before deciding anything:
      generated/manualgen_controlled_acceptance_plans/
        MANRUN-20260902T122942Z-470C269F/CONTROLLED_ACCEPTANCE_DRY_RUN_REVIEW.md
        MANRUN-20260902T122942Z-470C269F/controlled_acceptance_mutation_ledger.csv

## The real question this exposes

The full-stack push made the PRODUCER current: HELP store rebuilt (473 -> 666
topics), harvest re-exported through the engine with memo resolved, canonical
promoted, every entry row green. The manual is a CONSUMER, and the path by which
new topics reach it is the disposition/curation chain -- **which is FAIL at this
run** (`missing_policy=1`, `extra_policy=13`), because its policy table drifted
against the same store growth.

So the honest picture:

    producer   current, proven, eight of eight entry rows
    consumer   pinned to a July merge; its selection policy is stale
    seam       E5 green, harvest correct, memo present -- the data IS there

The manual cannot absorb 193 new topics through a chain whose topic selection is
a 54-row hand-maintained table last updated in July. That is the same shape as
every other finding this session: **a hand-kept list standing where a derivation
belongs.** `REVIEW_DISPOSITIONS` is to the manual what
`collect_set_subcommands()` is to the reflection surface and what the old
`is_expression_function_name()` list was to CMDHELP.

## RESOLVED 2026-09-02: the disposition drift is closed

Owner instruction "resolve please". `REVIEW_DISPOSITIONS` repaired in
`tools/manualgen/manualgen_lib/disposition.py`:

    before   status=FAIL   missing_policy=1   extra_policy=13
    after    status=PASS   missing_policy=0   extra_policy=0   invalid_targets=0
                           approved_section_topics=477
    REVIEW_DISPOSITIONS 54 -> 42, RETIRED_DISPOSITIONS 13 (new)

**Two changes, both conservative.**

**1. `DOT|TRANSACTION` added** as `DEFER_NO_RUNTIME_IDENTITY`. Not an invented
policy -- `DOT|POLLING` is the existing entry for an identical case, worded
"Usage contract exists but no HELP command or active public SYSCMD identity."
TRANSACTION measures the same: `has_help=False`, `has_runtime=False`. The
rationale records that it dissolves when dotref is generated from the contracts.

**2. Thirteen spent entries RETIRED, not deleted.** They moved to a
`RETIRED_DISPOSITIONS` dict in the same file with the reasoning above each group.
Deleting would have cleared the finding and thrown away the decisions; the check
only cares that they leave the active set.

    PROMOTED (7)          BBS, BUILD INFO, BUILD VECTORS, CANARY, CMDREL,
                          FORMULA, NET -- still in the store, now classified
                          01_dot_supported_commands. They graduated out of
                          review, which is these entries SUCCEEDING.
    MINING ARTIFACTS (2)  CC PRINT (a phrase with no command authority) and
                          CODAYSL (a transposition of CODASYL). Gone, correctly.
    c8aa6a583 (4)         UDATE, UDATETIME, UNOW, UTIME. See below.

## RULED 2026-09-02: V6_HINTS section 4, candidate (b) ACCEPTED

**Owner ruling, in-session: "accept hint".** V6_HINTS section 4 offered three:

    (a) curate them in dotref as dual command+function
    (b) fix the filter so they stay function-only and HELP stops publishing
        them as unsupported
    (c) accept that the scalar form means every catalog function has a command
        surface, and decide what that implies for the catalog as a whole

**(b) is accepted.** `c8aa6a583` already implemented it, so the ruling ratifies
what shipped rather than requiring a change. `FILE`, `UDATE`, `UDATETIME`,
`UTIME` and `UNOW` are function-only. The section-4 defect -- five functions
carrying uncurated `supported=no` DOT command rows -- is closed.

Section 4 noted `FILE` was "the newest instance, so whatever is decided will
apply to the next function added too". Under (b) that is automatic: the filter
delegates to the function catalog, so any function added later is covered by
construction. That is the property (a) and (c) would not have given.

### Follow-through, both directions

    disposition.RETIRED_DISPOSITIONS   note changed from provisional to
                                       RATIFIED. The four stay retired
                                       permanently; no revert path needed.
    prose_review.PROSE_REVIEW_POLICY   the four REMOVED. AIF-068 had added them
                                       as APPENDIX_ONLY precisely because they
                                       were publishing as unsupported commands;
                                       ruling (b) removes the reason.
                                       16 -> 12 topics.
                                       APPENDIX_ONLY 7 -> 3, back to its
                                       pre-AIF-068 value, because those four
                                       WERE the appendix additions.
    test_prose_review                  re-baselined a second time, to 12 and
                                       {8, 1, 3}. Set and counts still EXACT.

    manualgen suite: 58 tests OK.
    Guard re-proven after both edits: smuggling one entry into the policy trips
    BOTH assertions (set names it, counts move 8 -> 9).

Two edits to one test in one session, and they are different in kind: the first
fixed a test that was stale on arrival, the second implemented a ruling. The
docstring keeps them separate so neither reads as the other.

## THE FOUR THAT MATTER: the consequence, measured before the ruling

Those four policy entries say "Physical HELP command exists." It no longer does,
and the cause is traceable:

    a350c00ef (before)  is_expression_function_name() held a 64-name literal
                        list. VERIFIED by reading that revision: it does NOT
                        contain UDATE, UDATETIME, UNOW, UTIME or FILE.
    c8aa6a583 (2026-08-25) replaced the list with a delegation to the function
                        catalog: get_function_doc(up(name)) != nullptr
    META_SYSFUNC        contains all five.
    cmdhelp.cpp:237     if (is_expression_function_name(n)) return {};
                        -- an empty summary for any catalog member.
    2026-09-01 rebuild  ran with that exe.
    result              UDATE/UDATETIME/UNOW/UTIME are no longer DOT topics.

**`c8aa6a583` is V6_HINTS section 4 candidate (b), shipped without the ruling.**
v5 left three candidate rulings open and one was implemented. This is the first
measurement of what it actually did: it removed four topics from the manual's
review space, and the disposition policy noticed before any human did.

Retiring those four entries RECORDS the effect. It does not ratify the change.
They sit in `RETIRED_DISPOSITIONS` precisely so that if the ruling reverts
`c8aa6a583`, they can be restored rather than reconstructed.

**The ruling is no longer abstract and should be taken.** It changes what the
manual documents.

## ALSO RESOLVED: a test that was red on arrival

Continuing down the chain, `test_prose_review` had two standing failures. They
were pre-existing -- verified by diffing the FAILURE NAMES, not just the count,
against the disposition backup before and after the repair above.

    PROSE_REVIEW_POLICY holds 16 topics; the test asserted the pre-AIF-068 8.
    counts: policy {ADDITIVE 8, CANARY 1, APPENDIX 7}
            test   {ADDITIVE 4, CANARY 1, APPENDIX 3}

**The code was right and the test was stale.** The history is unambiguous:

    2026-07-27  2d138e001  AIF-068 re-baselined the curation chain and moved
                           "prose + selective-merge policy to 16 topics" --
                           deliberate, and said so in the commit message.
    2026-07-31  5ca43a7ec  "track manualgen -- manual assembly pipeline,
                           PREVIOUSLY UNTRACKED". The test entered git four days
                           after the policy moved, still asserting the old set.

So it has been failing since the moment it was first version-controlled.

**Why that is worse than a wrong number.** A test that is red on arrival guards
nothing. A standing failure is indistinguishable from a new regression, so for
five weeks the boundary these two assertions exist to hold -- "this packet must
not grow silently" -- was unenforced. The suite reported 2 failures either way,
whatever anyone did to the policy.

Re-baselined to AIF-068 (16 topics, 8/1/7), with the history in the docstring
and each added key marked. The assertions remain EXACT, so the guard is
restored rather than relaxed.

**Proven, not assumed.** Smuggling one extra entry into the policy trips BOTH
assertions -- the set check names `DOT|SMUGGLED_IN`, and the counts check goes
8 -> 9. A green nobody has watched fail is not a green.

    manualgen suite: 58 tests, OK. First fully green run this session.

**Loose thread, flagged not chased:** AIF-068 added UDATE/UDATETIME/UNOW/UTIME
to the prose policy as APPENDIX_ONLY on 2026-07-27, and `c8aa6a583` removed them
as HELP topics on 2026-08-25. They are in a prose packet for topics that no
longer exist. That is the same four commands, the same unruled change, surfacing
in a third place -- and one more reason to take the V6_HINTS section 4 ruling.

## Recommended next step, and it is not M-4

Refresh the curation/disposition policy against the current store, so the
selective merge selects the topics that actually need review now:

    build-curation-candidate
    build-disposition-candidate        (currently FAIL: 1 missing, 13 extra)
    build-structural-reconciliation
    build-section-delta-candidates
    build-prose-review-batch           (no 2026-09-02 prose decision exists)
    then a selective merge that reflects the CURRENT store
    then controlled acceptance against THAT

That is the manual-assembly lane's work, it is larger than a doc push, and it
should be chartered rather than improvised at the end of a long session.

## Boundary held

    apply_available            0
    canonical_files_mutated    0
    accepted manual            untouched
    accepted reader pointer    untouched
    aggregate appendices       untouched (mtime still 2026-07-18 03:25:28 UTC)

Two plans were built, both report-only, both refused to arm themselves.

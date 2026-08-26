# v6 Phase 7 readiness -- NOT READY, and the review that says so IS the Phase 7 work

    Run    : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Asked  : "so are we ready for the phase 7" (2026-08-26)
    Answer : **NO.** Four blockers, all named below, none of them expensive.
    Status : review-needed. Nothing was changed to produce this -- it is a read.

## 0. FIRST: "Phase 7" means two different things in two documents

    COOKBOOK  "### Phase 7 -- review and close the dev-tree run (Gate 7)"
              ...and Phase 8 is the publication ascent.
    RUNBOOK   ":201  ## Phase 7 -- Web ascent to x64base.com (9 gates)"

**Two answers to one question -- R5, in the two documents that route this
lane.** It matters for exactly the question asked: under the cookbook, Phase 7
is IN SCOPE for v6 (closing the dev-tree run); under the runbook, Phase 7 is the
web ascent, which the owner ruled OUT OF SCOPE for v6 on GIGO grounds.

This review answers the COOKBOOK's Phase 7, because that is the one that follows
Phase 6 and the one v6 can reach. **The numbering collision is itself a finding
and is not resolved here** -- renumbering a phase is a ruling, and both spellings
are cited across the lane.

## 1. The five-state pointer review -- the actual Phase 7 deliverable

The cookbook: *"Review five states for pointer agreement: candidate workspace,
accepted/canonical manifest, active reader artifact, publication manifest,
website projection."*

Done. **No two of them name the same thing.**

    ACTIVE_PRIMARY_READER_ARTIFACT.txt  ->  developer_manual_publication_v1
    canonical manifest candidate_workspace
                                        ->  ..._v1_python_rebuild_candidate_v1
    v6 Phase 6 dry run targeted         ->  ..._v1_media_section_v1
    website projection                  ->  OUT OF SCOPE for v6 by owner ruling

Six published workspaces exist. Four of them carry a whole manual, and they do
not agree on what the manual IS:

    workspace                                    lines   H1   MDO-261 / 270
    developer_manual_publication_v1               4118   26     no   / no    <- ACTIVE
    ..._media_section_v1                          4597   26     yes  / yes   <- Phase 6 used
    ..._media_section_v1_man_cli_reference_v1     4710   29     no   / no    <- largest
    ..._media_section_v1_manual_mutation_cycle_v1 4597   26     yes  / yes

**The pointer marked ACTIVE names the SMALLEST of the four**, 592 lines shorter
than the one Phase 6 was told to assemble and 479 short of the one with the most
sections. Nothing on disk says which is current; the pointer says one thing and
the manifest says another and the run used a third.

## 2. This CORRECTS Phase 6b's 117-line finding, and the correction is worse news

`PHASE6_POSTBASELINE_DRY_RUN_V1.md` and the Phase 6a document reported that a
rebuild would silently drop 117 lines and two H1 sections -- the MDO-261 and
MDO-270 blocks -- because their sources sit in `references/` and at the
workspace root, which the assembler does not read. That measurement stands.

**What was wrong was the conclusion drawn from it.** Those blocks are not
orphans awaiting rescue: `..._man_cli_reference_v1` carries **29 H1 sections and
4,710 lines with no MDO markers at all**, which is the signature of insertion
markers having been resolved into real sections by a LATER workspace. The
content was not at risk of loss. **The risk is that four manuals exist and the
pointer names the one that has neither absorbed the blocks nor kept the
markers.**

That is a worse finding than the one it replaces, and it is the difference
between "a rebuild would lose content" and "nobody can say which artifact is the
manual". Recorded rather than quietly amended, because the first version is
committed.

## 3. Everything is UNTRACKED -- including the pointers themselves

    ACTIVE_PRIMARY_READER_ARTIFACT.txt            UNTRACKED (not ignored)
    ACTIVE_MANUALGEN_MANIFEST.txt                 UNTRACKED (not ignored)
    developer_manual_canonical_manifest_v1.json   UNTRACKED (not ignored)
    primary_reader_artifact_v1.json               UNTRACKED (not ignored)
    all four published manual .md files           UNTRACKED (not ignored)

**Not ignored -- never staged.** `git check-ignore` returns nothing for any of
them. So the authority that says which manual is current, the manifest that
records what was accepted and by whom, and every manual they point at, are all
outside history. There is no diff, no blame, no rollback, and a Gate 7 closeout
written against them would cite five paths the repository has never seen.

This is the same class as `METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md`, found
and staged four commits ago: **a live authority sitting outside the thing that
records authorities.** That one surfaced only because an unrelated edit dragged
its citer into a change set. These surfaced only because Phase 7 was asked
about. Neither was found by a gate.

## 4. Gates 5 and 6 have candidates, not acceptances

    Phase 5 / Gate 5   three candidate CSVs emitted, determinism proved,
                       contract checked -- and NOT BOUND BY SHA. A candidate
                       emit is not an authorization.
    Phase 6 / Gate 6   harvest re-exported to a CANDIDATE workspace; dry run
                       PASS_CANDIDATE_ONLY, boundary_fail_rows=0, wrote nothing.
                       Nothing accepted, nothing promoted.

Phase 7 closes a run in which phases 5 and 6 CLOSED. They have not; they have
produced reviewable candidates, which is what they were asked to produce.

## 5. The Phase 7 -> 8 entry rows, measured where they can be

Recorded now because these are cheap and their state is useful even though
Phase 8 is out of scope for v6.

    E1  dev-tree run closed at Gate 7          NO -- this document is why
    E2  HELP current + CMDHELPCHK PASS         UNRUN (needs the engine; host)
    E3  contracts 100%, catalog fallback 0     contracts 100.0% uncovered=0 PASS;
                                               catalog UNRUN (needs the site repo,
                                               out of scope for v6)
    E4  refcheck_v1 + normcheck_v1 PASS        **PASS** -- both run 2026-08-26:
                                               refcheck 0 guarded phantoms, every
                                               entry resolves; normcheck no
                                               findings in any fail-severity lane
    E5  harvest re-exported AFTER the build    PARTIAL -- re-exported to a
                                               CANDIDATE workspace. **The
                                               canonical `harvested/` is still
                                               the stale 12:18 export
                                               (460/665/29262 against 462/667/
                                               29268).** The cookbook flags this
                                               row as the one that usually fails.
    E6  command-catalog.mdx regenerated        OUT OF SCOPE for v6
    E7  HELP store backup + rollback named     **PASS** -- help.bak-20260825-180609
                                               is the pre-run store, taken by
                                               LEGACY at 01:06
    E8  owner authorization per mutation       NOT SOUGHT; nothing mutating has
                                               been proposed

## 6. What "ready" would take

In order, and none of it is large:

1. **Rule which workspace is the manual.** Owner's, and nothing else can start
   until it is answered -- every remaining step names an artifact.
2. **Stage the pointers, the canonical manifest and the ruled manual.** They are
   not ignored; they were never added. An authority outside history cannot be
   cited by a closeout.
3. **Gate 5**: bind the three candidate CSVs by SHA, or decline them.
4. **Gate 6**: accept or decline the dry-run candidate. `boundary_fail_rows=0`
   is the acceptance condition and it is met.
5. **Re-export the canonical harvest** once 1-4 settle, so E5 stops being
   partial. One command; the candidate export already proved it.

Then Phase 7 is a closeout document separating dev-refresh / candidate /
promotion / staging / commit / push -- and it can be written in one pass,
because everything it must cite will exist and be tracked.

## 7. The honest summary

**v6 did what it set out to do.** Gate 0 through Phase 6 ran, every phase
produced its artifact, and the run found more in the machinery than in the
documents -- six proxies that cannot answer, three false ceilings, a 117-line
manifest gap, an untracked contract, and now four manuals and a pointer that
names the wrong one.

**Phase 7 is not blocked on work. It is blocked on a DECISION and five
`git add`s.** Which is the better place to be stuck, and worth saying plainly
rather than dressing up as readiness.

## Good Neighbor

    What changed  : one new document. NOTHING ELSE -- this review is a read.
                    No file staged, no pointer moved, no workspace touched.
    Whose area    : lane full_stack_documentation, run DOCFLUSH-20260825-001.
                    Section 1's disagreement belongs to the manual's owner.
    Authorization : the owner's question, 2026-08-26.
    Verify        : cat the two ACTIVE_*.txt pointers; ls the published/ dir;
                    wc -l and `grep -c '^# '` the four manual .md files;
                    git ls-files --error-unmatch on each of the five paths in
                    section 3 -- expect "did not match any file(s) known to git".
                    E4: run refcheck_v1.py and normcheck_v1.py, expect PASS.
    Undo          : delete this document. It changes nothing.

# Proof -- a hosted peer with no tree access found three real defects from a header block (2026-08-13)

    proof id      : proof.peer_review.header_only_findings
    state         : runtime_observed (relayed transcript + anchors that re-verify)
    recorded_utc  : 2026-08-13
    recorded_by   : member.ai.claude.cowork, run COWORK-20260813-001
    reviewer      : HOSTED-20260813-001 (hosted peer, no repository access)
    baselines     : ccode da02641b1 - site b126994b3 (branch codex/lean-sites-publish)
    subject       : peer review as an input to a gate (AIF-041 M6 -> BETA-1 E1)
    companion     : docs/maintenance/peer_design_review/PDR-001_.../SESSION_V1.md
    requested by  : member.derald -- "document and note as a proof"

## 1. What happened

A hosted peer was relayed **only the header block** of
`docs/agents/HANDOFF_CLAUDE_COWORK_SITE_PUBLISH_ECO_2026-08-13.md` -- not the
body, not the repository, not any build output. From those eight lines it
returned three findings, declined to guess at a fourth, and asked for the
section it did not have.

All three findings were checked against the tree rather than accepted. All three
hold.

## 2. The findings, and what each check returned

| # | Finding | Check run | Result |
| --- | --- | --- | --- |
| F1 | Both stated baselines are one commit stale | `git merge-base --is-ancestor` on each pair | **correct.** `7786e63b7` is an ancestor of `da02641b1`; `095e9495a` of `b126994b3`. The report was accurate when written and had been overtaken |
| F2 | The site commit touched the map's `const D` data line, so the blocker "may already have moved" | `git show --stat b126994b3` | **correct.** One file, `public/eco/index.html`, 1 insertion 1 deletion -- the data line |
| F3 | The report is signed with a member id and no run id, so no reader can tell which session wrote it | header inspection | **correct, and a defect on a lane the author stewards** |

F2's consequence, measured across the refs:

    095e9495a : 2 machine path(s) in public/eco/index.html   <- the blocker
    b126994b3 : 0                                            <- fixed and committed
    HEAD      : 0
    worktree  : 0, byte-identical to HEAD and to the generator output

The blocker the report existed to raise had been closed by the owner between the
writing and the reading. The peer could not see that, and said so precisely --
it named the mechanism by which the blocker *might* be stale rather than
asserting that it was.

## 3. The behaviour worth recording as much as the findings

**It refused to infer the part it could not see.** Verbatim: *"I can't see section
1. The paste is the header block only, so the one blocking item -- the whole
point of the report -- isn't here. I'd rather say that than infer it."*

A reviewer that had guessed at the blocker would have produced a plausible
paragraph and a useless review. Declining is the behaviour the review protocol
asks for and the one hardest to get: the turn-validity rule in
`PEER_DESIGN_REVIEW_SESSION_PROTOCOL_V1` accepts *"I could not run this, and here
is why"* as a valid turn precisely so that declining is not a losing move.

## 4. What this refines -- and it is a genuine amendment, not a restatement

AIF-082 concluded that **review does not find these**: four instruments, all
wrong on first build, all caught by running them and none by inspection.

This event does not contradict that and does not soften it. It marks a boundary
AIF-082 did not have to draw:

- **Runtime defects** -- a checker that passes vacuously, a denominator that
  moved, a crash rendered as a finding -- are found by RUNNING. Inspection does
  not find them. AIF-082 stands.
- **Claim defects** -- a stale baseline, an unattributable signature, an
  assertion with no anchor -- are found by READING, and a reviewer with no tree
  access is *well suited* to them, because with nothing else to check it checks
  the claims.

Two defect classes, two modalities, and the second one is cheap. The practical
consequence for AIF-041 M6 and BETA-1 E1: a hosted seat is not a weaker version
of a local seat. It is the seat that audits what the local seats assert.

## 5. It also validated a seat design that had never been run

`PDR-001` proposes an **adversary** seat -- a hosted advisor with no tree, whose
charge is that it "can only attack reasoning, which is exactly the hosted
advisor's competence." That seat had never been exercised; PDR-001 is drafted and
not started.

This is that seat, operating unprompted, and it worked on its first outing. The
design is now source-evidenced rather than speculative.

## 6. What it is NOT evidence for

- **Not a controlled trial.** One review, one reviewer, one report. The header it
  received happened to contain two stale commits; whether it would find anything
  in a clean header is untested.
- **Not evidence that peer review finds code defects.** It found metadata and
  coordination defects. Section 4 is the honest reading, and it is narrower than
  "peer review works".
- **Not a discovery of the blocker.** The blocker was found by the site's own
  `check-public-content` guard the day before, by running it. The peer found that
  the *report about* the blocker had gone stale.
- **Not independent of the author.** The peer's findings were checked by the
  author of the report under review. A second party has not verified the checks.

## 7. The defect it produced, and the standing correction

F3 landed on AIF-050, whose charter says *"the agent is traceable only to the
product level"* -- and the artifact that failed it was written by that lane's
steward. `member.ai.claude.cowork` names a deployment; it does not name a session
anyone can return to.

**Standing correction, adopted 2026-08-13:** every handoff, closeout, and report
header written by this member carries a `run` line. This proof carries
`COWORK-20260813-001`, verified free before use. The correction is dogfooded here
rather than promised.

## 8. Reproduce

    cd D:\code\ccode
    git merge-base --is-ancestor 7786e63b7 da02641b1 ; echo $?    # 0 = ancestor
    cd D:\dev\x64base-site
    git merge-base --is-ancestor 095e9495a b126994b3 ; echo $?    # 0 = ancestor
    git show --stat b126994b3 -- public/eco/index.html            # 1 file, 1 +, 1 -
    git show 095e9495a:public/eco/index.html | grep -c "[A-Za-z]:[\\/]"   # non-zero
    git show b126994b3:public/eco/index.html | grep -c "[A-Za-z]:[\\/]"   # zero

## 9. Evidence tier

**runtime_observed.** The reviewer's text was relayed by the owner and is quoted
in section 3; every claim it made resolves to a git command whose output is
recorded above and re-runnable. Nothing here concerns DotTalk++ runtime
behaviour -- what ran was git, and a review.

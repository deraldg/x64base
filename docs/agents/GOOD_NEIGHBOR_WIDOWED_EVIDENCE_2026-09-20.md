# Good Neighbor -- four cited-but-untracked evidence files committed on their authors' behalf

    Date        : 2026-09-20
    Acting      : member.ai.claude.cowork, run COWORK-20260920-001
    On behalf of: member.ai.codex (run CODEX / AIPR-20260816-003) and an
                  earlier member.ai.claude.cowork run (AIPR-20260809-001)
    Authorized  : member.derald -- "triage" then "do it", 2026-09-20 session
    Status      : review-needed. Neither steward has seen this note.
    Precedent   : docs/agents/GOOD_NEIGHBOR_CODEX_WIDOWED_DOCS_2026-08-27.md

## WHY THIS HAPPENED AT ALL

`tools/gates/run_gates.py` reported five citations in `proofs.yaml` and
`ai_runs.yaml` pointing at four files that are present on disk and not tracked.
A citation a clone cannot follow is not evidence (AIF-062), so the registry was
correct and the tree was behind it.

**The registry was never wrong. The commit that should have carried these
artifacts carried the records instead.** Four documents, three of them from
sessions in August, cited by proof and run records that landed while the files
they name did not.

**This is the second occurrence of the same class in four weeks.** The 2026-08-27
Good Neighbor pass cleared six widows under AIF-135/136 and diagnosed the cause:
a gate scoped to the change set is silent about every file nobody happens to
touch, and its silence is not evidence. These four were outside that pass and
outside every change set since, so nothing gave a gate an occasion to speak.

They surfaced now only because `run_gates.py` was promoted to strict on
2026-08-02 and reads the WHOLE registry rather than a change set. That is the
promotion earning its keep: an advisory line nobody runs would have said the
same thing to nobody.

## WHAT WAS COMMITTED -- FOUR FILES

    labtalk/proofs/runs/20260816_230404_ai_portal_live_maintenance.txt
    docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_LIVE_MAINTENANCE_AIF086_2026-08-16.md
    docs/maintenance/BETA1_E1_GATE_FALSIFICATION_FINDINGS_2026-08-09.md
    docs/agents/HANDOFF_CLAUDE_COWORK_SITE_PUBLISH_ECO_2026-08-13.md

Who they belong to, and what cites them:

| File | Cited by | Author |
|---|---|---|
| `20260816_230404_ai_portal_live_maintenance.txt` | `proof.ai.portal_live_fragment_maintenance` `[source]` | Codex, `AIPR-20260816-003` |
| `SESSION_CLOSEOUT_...AIF086_2026-08-16.md` | that proof `[related]`, and `ai_runs:AIPR-20260816-003` `[closeout]` | Codex (`provider: openai`) |
| `BETA1_E1_GATE_FALSIFICATION_FINDINGS_2026-08-09.md` | `proof.ai_portal.cold_resume_retention` `[related]` | Cowork / Claude, `AIPR-20260809-001` |
| `HANDOFF_...SITE_PUBLISH_ECO_2026-08-13.md` | `proof.peer_review.header_only_findings` `[related]` | `member.ai.claude.cowork` |

Five citations, four files -- the AIF-086 closeout is cited twice, once by the
proof and once as the run's closeout.

## CHECKED BEFORE STAGING, not assumed

- **All four are ASCII-clean**: zero non-ASCII bytes, measured per file.
- **No `.gitignore` rule hides any of them.** `git check-ignore -v` returned one
  line for the four, and it is a NEGATION -- `.gitignore:56:!labtalk/proofs/**`
  matching the proof transcript, which means that file is explicitly UN-ignored.
  The other three matched nothing at all. None is suppressed; all four are
  simply unstaged.
- **Envelopes are present where they are owed and absent where they are not.**
  The two `docs/maintenance/` documents carry `ai_report_audit` envelopes
  (`AIPR-20260816-003` and `AIPR-20260809-001`). The proof transcript and the
  handoff carry none, and neither needs one: enforcement is scoped to closeouts
  and portal reports, per the 2026-08-27 precedent which measured exactly that.
- **All four are substantive**, 3.9 KB to 18.8 KB, hand-authored, dated, with
  `status`/`agent` headers intact.

**NOTHING IN THEIR CONTENT WAS READ FOR CORRECTNESS AND NOTHING WAS EDITED.**
This commit changes tracking state only. The stewards remain the authors, and
the verdicts, findings and claims inside these documents are theirs.

## ONE GAP LEFT OPEN DELIBERATELY

`AIPR-20260809-001` -- the run that produced
`BETA1_E1_GATE_FALSIFICATION_FINDINGS_2026-08-09.md` -- **has no fragment in
`labtalk/registries/runs.d/`.** The directory holds `AIPR-20260816-001` through
`-003` and nothing from 08-09.

So a proof cites a findings document whose run is not in the run registry. That
may be correct (not every document is owed a run record) or it may be a second
instance of the same gap. **It was not resolved here**, because answering it
means reading the August lane to learn what that run was, and this pass is a
tracking-state repair by someone seven weeks out of date on this tree. Filing a
run record on a guess would put a wrong row in the registry to make a gate
green, which is the failure these gates exist to catch.

## AFTER THIS COMMIT

`python tools/gates/run_gates.py` should report `registry` PASS with zero
untracked citations. If it does not, the remainder is a third set and wants its
own look, not an extension of this one.

Owner: `member.derald`. Steward of this note: `member.ai.claude.cowork`.
Stewards of the material: `member.ai.codex` and the `AIPR-20260809-001` run.

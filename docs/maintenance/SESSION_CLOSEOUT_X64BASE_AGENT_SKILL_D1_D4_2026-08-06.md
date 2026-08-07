---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260806-006
  recorded_at_utc: 2026-08-07T05:30:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: bc08afd1d
  authorization:
    requested_by: maintainer
    scope: >
      Owner ruled G0 with "develop and document, it is our thesis", converting
      AIF-090 from the skill programme to the D1-D4 repair lane. This closeout
      covers the repair implementation and its AIF-006 updates.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_X64BASE_AGENT_SKILL_D1_D4_2026-08-06.md
    kind: session_closeout
---

# Session Closeout -- AIF-090 D1-D4 repair implemented (AIF-090)

Date: 2026-08-06.
Owning lifecycle: PDLC (converted from packaging to repair by ruling R7).
SDLC lane: implementation.
Truth state: runtime-proven.
Proof state: transcript + git-verified.

## One-line summary

Fixed the four defects P0 found, each one proven by making its gate FAIL on a
known-bad input before trusting its green, and left the portal's headline metric
telling a smaller, truer story than the one it replaced.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Resolver | `labtalk/ai_portal/recall.py` | D2: hardcoded denominator deleted; corpus derived from the graph, entry path measured from the registry |
| Registry | `labtalk/registries/portal_recall_graph.yaml` | D2 `entry_path:` section; D3 two mechanism nodes + two edges |
| Gate | `tools/staging/check_seed_budget.py` | D4: new; parses the ceiling from the document's own header |
| Seed | `labtalk/ai_portal/AI_TIER1_SEED_V1.md` | D1 resolver pointer added; maintenance contract demoted out to pay for it |
| Doctrine | `labtalk/ai_portal/TIER1_MAINTENANCE_CONTRACT_V1.md` | new; the demoted contract, moved verbatim |
| Lane | `docs/maintenance/X64BASE_AGENT_SKILL_PDLC_LANE_V1.md` | R7, status, section 10 |

Commit `79888dfaa`, 7 files, +358 / -47.

## Verified (proof performed this session)

**Every gate was seen to FAIL before its green was trusted.** That rule is not
decoration here: the defect being repaired in D2 was a bound that could not fire.

- **D2 bound proven able to fail.** A fixture graph whose single trigger reaches
  every node produced `100% of the 22219 B corpus`, printed the WARNING, and
  returned **exit 2**. On the real graph the bound stays green and the two
  honest figures replace the misleading one.
- **D4 gate, 5/5 fixtures**, including the two that matter: it FAILED the real
  seed at 8,990 B (exit 2) before the demotion, and it refuses to let multi-byte
  content buy headroom, because a byte budget measured in characters is a
  denominator error -- the failure class AIF-082 recorded three times.
- **D1 verified by the gate it forced.** Seed 8,990 -> 8,148 B, 44 B headroom,
  `check_seed_budget.py` PASS. Five questions, repository-role table, git rules
  and comment marker each confirmed still present after the edit.
- **D3 verified by the resolver.** Graph 31 -> 33 nodes, 44 -> 46 edges,
  `--validate` PASS with no dangling edges and every node reachable;
  `commit_or_push` now returns `PREPUSH_GATE_REFERENCE_V1.md`.
- Full regression after all four: seed budget PASS, graph validate PASS,
  collision gate PASS, `ENTRY_PATH_BASELINE` present only inside the comment
  that explains its removal, zero non-ASCII across all six touched files.
- The maintainer's pre-commit run passed every gate on `79888dfaa`.

**Not verified:** no engine build, no runtime execution of `dottalkpp`. The
sandbox cannot build. The repairs are portal tooling, not engine behaviour.

## AI-facing docs updated (AIF-006 gate)

Lane charter (R7, status, section 10), handoff, intake row, dashboard row. All
four had said "G0 no-go recommended, awaiting ruling"; R7 settled it.
`CURRENT_TARGET.md` deliberately unchanged.

## Published

`79888dfaa` on `development`. Not promoted to `C:\x64base`. Not published to the
website.

## Handoff left (AIF-082 gate)

`docs/agents/HANDOFF_CLAUDE_COWORK_AGENT_SKILL_2026-08-06.md`, updated a second
time in one day. It has now been correct-then-stale twice, which is itself the
argument for handoffs being short and pointer-shaped.

## Still open -- for the next session

1. **The graph over-links, and now says so.** `onboard` reports 3.7x the entry
   path, `commit_or_push` 4.4x. The repaired bound exists to surface this and it
   is surfacing it. Trimming the graph -- probably by keeping tier-2 leaves out
   of a depth-1 result -- is the next measurement.
2. **`check_seed_budget.py` is not wired into `prepush_gate.py`.** It runs by
   hand. Per R4 it should run advisory for one cycle, then hard. Until then D4's
   own lesson applies to itself: a rule without a gate is a wish.
3. **44 B of headroom** in the seed is not much. The next addition will need a
   demotion, which is the contract working as designed, but it will surprise
   whoever hits it.
4. **`ascii_normalize.py` is likewise unwired.** It has 3 uncited non-ASCII files
   and the tracked whole-tree backlog available to it.
5. `_tmp/aif090_bound_fixture.yaml` was truncated to 0 bytes but could not be
   deleted from the sandbox. `_tmp/` is gitignored (`.gitignore:267`) so it can
   never be committed; delete it host-side at leisure.
6. Carried forward: 21 untracked `.md` at `docs/maintenance` root, the 7
   chat-spill `.txt`, the `yes`/`no` vs `true`/`false` editorial call, the
   `AI_TIER1_SEED_V1.md` `git diff --cached` correction, and the untested
   hosted-agent case that is the only surviving argument for a distributable
   bundle.

## The result worth recording honestly

Fixing D3 made the reported working set **larger**, 27,384 -> 44,260 B. The old
number was smaller because the graph was incomplete; the old percentage was
flattering because its denominator was frozen at a corpus nobody reads anymore.
Both numbers moved toward the truth and the truth is less impressive than the
claim it replaced.

That is the whole point. A metric that only ever flatters is not a metric. This
lane began as a proposal to build a skill, measured its own premise, killed the
proposal, and spent the effort on four defects in the instruments that were
already there -- one of which was a bound that had been written specifically so
a number could fail, and which could not.

## Provenance pointers

- Lane: `docs/maintenance/X64BASE_AGENT_SKILL_PDLC_LANE_V1.md` sections 9 and 10
- P0 evidence: `docs/maintenance/X64BASE_AGENT_SKILL_P0_MEASUREMENT_V1.md`
- Demoted contract: `labtalk/ai_portal/TIER1_MAINTENANCE_CONTRACT_V1.md`
- Method rule: `AI_PORTAL.md`, "Build It to Prove It" -- a checker is unproven
  until you have seen it FAIL
- Prior closeouts this day:
  `SESSION_CLOSEOUT_X64BASE_AGENT_SKILL_LANE_OPEN_2026-08-06.md`,
  `SESSION_CLOSEOUT_X64BASE_AGENT_SKILL_P0_2026-08-06.md`

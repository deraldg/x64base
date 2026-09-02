---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260902-COWORK-001
  recorded_at_utc: 2026-09-02T21:40:00Z
  agent:
    provider: Anthropic
    product: Claude Cowork
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 3424b90b2
  authorization:
    requested_by: maintainer
    scope: >
      Triage the x64base-site branch situation; close the repo-distribution gap
      in the portal onboarding after the maintainer identified it; untrap the
      Tier-1 seed byte ceiling; clear the external-AI intake advisories. Commits
      and pushes run host-side by the maintainer.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PORTAL_REPO_DISTRIBUTION_AND_SEED_CEILING_2026-09-02.md
    kind: session_closeout
---

# Session Closeout -- portal repo distribution and the seed ceiling (AIF-082)

Date: 2026-09-02.
Owning lifecycle: maintenance.
SDLC lane: maintenance.
Truth state: mixed (measured where stated; two items are decisions, not findings).
Proof state: git-verified (four commits pushed) plus test transcripts.

## One-line summary

A branch question exposed that `deraldg/x64base` holds four unrelated histories,
which the portal onboarding never said; closing that gap exposed the Tier-1 seed
at 99% of its ceiling, and untrapping that exposed a pointer to a document that
does not exist.

## The correction that matters most

**The steward was one step from recommending that `origin/HEAD` be repointed.**
That would have landed visitors to the public x64base repository on the website
instead of the engine. It was stopped by the maintainer asking a question the
steward had not thought to ask -- "does that conflict with my other projects on
github main like x64base?"

The root cause was not the branch tangle. It was that the steward reasoned about
repository layout from `git` output instead of walking the portal, in a tree
whose FIRST document's FIRST section is a three-row table headed "Where you are".
CLAUDE.md's standing instruction is to walk the portal before reasoning about how
a subsystem works. It was not followed.

**The tree's own gap, which is real and is now closed.** A reader who HAD read
section 1 still could not have learned the fact: the binding contract's Canonical
Roles table had three rows and omitted the website entirely; the seed listed the
site tree with `--` for Branch and named no remote; `repository_role_guard.py`
knew two roots, so its refusal of the site tree read as "unrecognised path"
rather than "known, and deliberately not a role". Fact entered once,
incompletely, then re-derived on the far bank and got wrong -- the missing-plank
signature from NORTH_STAR.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| repo distribution | `docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md` | website row added; new section "ONE REMOTE, FOUR UNRELATED HISTORIES" with the root table, a Local tree column, and four consequences |
| repo distribution | `labtalk/ai_portal/AI_TIER1_SEED_V1.md` | `--` filled with `codex/lean-sites-publish`; shared-remote invariant stated; stopping-rule question 1 amended |
| repo distribution | `tools/staging/repository_role_guard.py` | docstring section "KNOWN, AND DELIBERATELY NOT A ROLE"; **no behaviour change** |
| repo distribution | `tools/staging/test_repository_role_guard.py` | `test_website_root_is_deliberately_not_a_role`, both path spellings |
| seed ceiling | `labtalk/ai_portal/AI_TIER1_SEED_V1.md` | console-capture section demoted out; root hashes demoted to the contract |
| seed ceiling | `docs/maintenance/DOTTALKPP_LAUNCH_AND_DOTSCRIPT_OPTIONS_V1.md` | new section 5b receives the demoted host-side capture material |
| seed ceiling | `tools/staging/check_seed_budget.py` | headroom in lines; TIGHT band below 5% |
| seed ceiling | `tools/staging/test_check_seed_budget.py` | NEW -- 14 cases; the gate had none |
| intake | `docs/maintenance/external_ai_intake/virtual_workspaces_memo_resident_2026-07-28/MANIFEST.md` | `access_mode` corrected to a registered term; `git.*` added as `not_exposed` |
| vocabulary | `docs/glossary/glossary_master_v0.csv` | `TERM.CONTRACT.ACCESS_MODE` added to the EXISTING glossary |
| findings | `coordination/OPEN_ITEMS.md` | OI-029, OI-030 |
| findings | `docs/maintenance/lanes/full_stack_documentation/GATE_CORRECTIONS_REQUIRED_V1.md` | G9 |

## Verified (proof performed this session)

Named as measurements, with the method, because a green readback is not proof.

- **Four unrelated histories.** `git rev-list --max-parents=0` per ref: engine
  `7c56022a1`, dev `ee49498b1`, site `6ee42f04c`, pages `572f33cd5`.
  `git merge-base origin/main origin/codex/lean-sites-publish` returns nothing.
- **`C:\x64base` carries the ENGINE history**, per the maintainer's correction
  and then checked: its HEAD and `origin/main` share root `7c56022a1`. Staging is
  a role, not a separate project.
- **Which branch x64base.com serves.** Read from the DEPLOYED artifact,
  `origin/gh-pages:artifacts/site-release.json`: release 132, source_branch
  `codex/lean-sites-publish`, commit `cb3575556`. Stated as "as of last fetch",
  not "live" -- live verification is open item 42.
- **Guard behaviour unchanged.** Six path spellings probed and captured BEFORE
  editing, re-probed after, diffed identical.
- **The new guard test can fail.** Mutation: a website role spliced into
  `detect_role`. 28 OK -> exactly one failure carrying the intended message ->
  restored -> 28 OK.
- **Budget gate.** 14 new cases green; the repo's own `check-seed-budget`
  independently reported the same byte count the sandbox measured.
- **Intake cleared.** `audit_trail.py`: `intake_findings` 3 -> 0.
- **Demotion moved rather than deleted.** Each specific (`*>`, the capture
  examples, the `tmp/` note, the pinocchio wrappers) grep-confirmed present in
  the tier-2 doc and absent from the seed.

## AI-facing docs updated (AIF-006 gate)

Tier-1 seed, the binding repository-role contract, and the launch/DOTSCRIPT
options doc. `coordination/OPEN_ITEMS.md` gained OI-029 and OI-030;
`GATE_CORRECTIONS_REQUIRED_V1.md` gained G9. No lane was opened or closed and no
AIF number was claimed: this was maintenance on existing artifacts.

## Published

Promoted to `development` only. Four commits, maintainer-run host-side, pushed
`3424b90b2..f1779a899`:

    c0f0c1cc2  coordination: OI-029 -- retract the default-branch claim
    2226927ee  portal: teach repo distribution -- one remote, four unrelated histories
    8c4cc34dd  portal: clear the intake advisories
    f1779a899  docs: G9 -- cited-paths reads a proposal as a reference

**Not promoted to staging. Not published to the website.** The website publish
still owes E8 authorization; the v8 grant does not cover it.

## Handoff left (AIF-082 gate)

No separate handoff owed. What a next agent needs is not a technique, it is a
fact, and a fact belongs at its source rather than in a handoff file that must be
found: it went into the Tier-1 seed and the binding contract, where onboarding
already looks. Writing a `docs/agents/` file restating it would create the second
source of truth this session spent the day removing.

## Still open -- for the next session

Three decisions, each prepared so it is one step. **None is a steward's to make.**

**1. The seed ceiling (OI-030).** 7794 B of 8192, 398 B, about six lines. The
TIGHT notice fires on every commit and will keep firing. The threshold was
deliberately NOT tuned to clear it -- 398 B is 4.86%, just under the 5% band, and
moving the band to make the current state pass is fitting the gate to the data.

  - (a) Demote further. The pointer table is the largest remaining block at
    1155 B and some rows may be reachable by `recall.py` trigger instead.
  - (b) Raise the ceiling deliberately, amending
    `TIER1_MAINTENANCE_CONTRACT_V1.md` with a stated reason, on the grounds that
    the tree has legitimately grown since 8192 was chosen.
  - (c) is what must NOT happen: a future session raising it mid-task so its own
    commit passes. The gate's message now says so.

**2. The three site branches (OI-029).** Defused, not gone -- their upstreams
were unset, so a bare `git push` can no longer create a remote branch. Their
content was spot-checked as superseded. Confirm that still holds, then delete.
Deletion is maintainer-operated. Do not merge `main`; it is a different project.

**3. E8 for the website publish.** A distinct mutation needing its own grant.

Also open, lower value: G9 (cited-paths needs the `external_ai_intake/**`
carve-out the report-audit gate already has); the 7182 untracked files, of which
716 script basenames are cited by tracked files with no tracked namesake -- task
#41's bug at scale, four of them live instruction docs; and the recurring R-number
back-fill advisory.

## What this session got wrong, recorded because the pattern repeated

Three defects found today were the same shape -- **one answer for two conditions
needing opposite responses** -- and the steward produced two of them:

1. `cited-paths` cannot tell "cites a missing path" from "PROPOSES a path that
   must not exist yet" (G9). The first instinct was to edit the proposal to
   silence the gate, which would have destroyed content to quiet a false
   positive.
2. `check_seed_budget` said PASS identically at 50% and 99%.
3. A verification probe written THIS SESSION returned True for both "the bug is
   present" and "the bug is described in prose" -- caught only because the
   adjacent check disambiguated it.

The lesson is not "be careful". It is that this shape is the house's most common
defect (seed section 6) and the steward reproduced it while hunting it.

## Provenance pointers

- `docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md` -- binding roles
- `labtalk/ai_portal/AI_TIER1_SEED_V1.md` -- Tier-1 onboarding
- `docs/maintenance/DOTTALKPP_LAUNCH_AND_DOTSCRIPT_OPTIONS_V1.md` s5b -- demoted capture material
- `coordination/OPEN_ITEMS.md` -- OI-029, OI-030
- `docs/maintenance/lanes/full_stack_documentation/GATE_CORRECTIONS_REQUIRED_V1.md` -- G9
- `labtalk/registries/ai_report_audit.yaml` -- access-mode vocabulary
- `docs/glossary/glossary_master_v0.csv` -- TERM.CONTRACT.ACCESS_MODE

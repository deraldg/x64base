---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: <AIPR-YYYYMMDD-NNN>          # you propose; maintainer confirms
  recorded_at_utc: <YYYY-MM-DDTHH:MM:SSZ>
  agent:
    provider: <e.g. xAI | OpenAI | Anthropic>
    product: <e.g. Grok | Codex | Cowork>
    model: <model-or-not_exposed>
    access_mode: hosted_proposal          # REGISTERED mode. NOT "remote".
                                          # valid: local_write | local_read_only |
                                          # hosted_proposal | external_patch |
                                          # human_operated_tool | automation
  session:
    id: <opaque-session-id-or-not_exposed>
    chat_reference: <safe-task-reference-or-not_exposed>
  project:
    id: <project-id-from-labtalk/registries/projects.yaml, e.g. project.x64base.runtime>
    root: D:/code/ccode
  git:
    branch: development                   # REQUIRED. Never main for feature work.
    baseline_commit: <FULL 40-char sha of the CURRENT development tip>
  authorization:
    requested_by: maintainer
    scope: <one line: exactly what the maintainer authorized>
  report:
    path: docs/maintenance/external_ai_intake/<lane_slug>_<YYYY-MM-DD>/MANIFEST.md
    kind: outside_ai_package
---

# Outside-AI Delivery Package -- <lane title>

Fill every field. ASCII only: use `--` and `->`, no em-dash, en-dash, arrows,
or smart quotes (the house-style gate hard-blocks non-ASCII in added lines).
Delete guidance lines before returning. Report only states actually reached.

## 0. Baseline (prove it)

- Branch: `development` (NOT `main`; `main` is a lagging public snapshot).
- Baseline commit: `<full sha>` -- obtained via
  `git ls-remote --heads https://github.com/deraldg/x64base.git` then fetch.
- Re-baseline if your clone is stale before packaging; cite the tip you used.

## 1. Lane identity

- Proposed AIF: `AIF-NEXT (proposed -- maintainer assigns)`.
  Do NOT hard-code a number. You cannot see the live claim ledger; the maintainer
  claims via `python tools/coordination/session_coordinator.py claim-aif`.
- Owning lifecycle: <DotTalk++ SDLC | LabTalk SDLC | maintenance | PLDC>.
- SDLC lane: <intake | design | implementation | proof | review | promotion>.
- Truth state: <observed | source-defined | runtime-proven | mixed>.
- Proof state: <none | report | transcript | build | git-verified>.
- Risk class: <low | medium | high>.
- Next gate: <the specific gate this must pass next>.
- Status: <proposed | ready-for-review | blocked>.

## 2. One-line summary

<What this package proposes, in one sentence.>

## 3. Phase-0 go/no-go (required for any speculative change)

If the payoff is assumed rather than measured, gate it here before Phase-1 code.

- Problem / need (evidence, not assumption):
- The seam it touches: <e.g. `replaceFieldStored` wires `index_hooks` but does
  not notify a `cursor_hook`; `cmd_trigger.cpp` is a stub with no handler; live
  surface is `SET POLLING`>.
- Measurable acceptance (what proves success):
- Go / No-Go recommendation + why:

## 4. Contract preflight (read before proposing source)

Completed `labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`: <yes/no>.
Contracts and source-usage blocks read (name each):

- <path -- what it constrains>
- <path -- what it constrains>

## 5. Changed / new files (manifest)

| Path | New/Changed | Purpose | Risk |
| --- | --- | --- | --- |
|  |  |  |  |

Excluded by rule (do not include): binaries, build dirs, generated runtime data
(DBF/CDX/LMDB/help catalogs), formatting-only riders, cleanup, branch operations.

## 6. Unified patch

Provide the patch against the baseline commit (inline or attached). One coherent
lane per package -- do not blob multiple themes.

```diff
<git diff against baseline_commit>
```

## 7. Behavioral effects, mutations, risks

- Runtime behavior changed: <what, or "none">.
- Data / metadata / HELP effects: <report-only? any live mutation? -- must be none>.
- Backward compatibility / rollback: <how to undo>.
- Known risks and their mitigations:

## 8. Build + test instructions

- Build: <exact target(s), e.g. `cmake --build build --config Release --target dottalkpp`>.
- Tests / regressions to run: <named, e.g. a `.dts` under `dottalkpp/data/scripts`>.
- Environment notes: <WSL vs Windows, deps>.

## 9. Expected runtime proof

What the maintainer should see if the change is correct (transcripts, row counts,
exit codes). State it as an expectation; you did not run it on the real tree.
"A script that has never been run is not evidence" -- do not claim proof you lack.

## 10. Unresolved questions / drift / conflicts

- <open question for the maintainer>
- <any drift observed between your clone and expected state>

## 11. Provenance

- Baseline: `development` @ `<full sha>`.
- Files read on the tree: <list>.
- Verified against the tree vs. assumed: <state clearly which is which>.

---

## Return checklist (self-verify before handing back)

- [ ] Baseline is `development` at a real, current commit (not `main`, not a stale sha).
- [ ] `access_mode: hosted_proposal` and `git.branch` / `git.baseline_commit` filled.
- [ ] No hard-coded AIF number; marked proposed.
- [ ] ASCII only (`--`, `->`); no em-dash / smart quotes anywhere.
- [ ] Package is source/docs/config only -- no binaries, build dirs, data churn, branch ops.
- [ ] One lane per package; unified patch present against the cited baseline.
- [ ] Phase-0 stated (or explicitly N/A for a proven, non-speculative change).
- [ ] Contract preflight done and contracts named.
- [ ] Proof stated as expectation, not claimed as run.

---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260809-002
  recorded_at_utc: 2026-08-09T20:16:40Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: COWORK-20260809-002
    chat_reference: "cowork: specialty LMS intake + gateway abort patch (2026-08-09)"
  project:
    id: project.labtalk.campus
    root: D:/code/ccode/labtalk
  git:
    branch: development
    baseline_commit: 648967b7438bd6e45f2b99417d41f0902e4df4cd
  authorization:
    requested_by: maintainer
    scope: >
      Adopt the received Copilot specialty-LMS package as external-AI intake and
      process it into the system properly: preserve it unchanged, assess it
      against the tree, measure the LabTalk campus registries, and publish the
      corrected reading as a website deck. Separately and on explicit maintainer
      instruction ("it will bite us later ... if we don't now"), fix client-abort
      handling in the local reports gateway.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_SPECIALTY_LMS_INTAKE_2026-08-09.md
    kind: session_closeout
---

# Session Closeout -- Specialty LMS external intake and gateway abort handling (AIF-103)

Date: 2026-08-09.
Owning lifecycle: **LabTalk SDLC**.
Related lifecycles: **maintenance SDLC** (gateway patch, AIF-100 territory),
**PDLC** (website publication surface).
SDLC lane: `intake`.
Truth state: mixed -- source-defined for the architecture findings, measured for
the registry counts, runtime-proven for the gateway patch.
Proof state: transcript (gateway P1-P3), report (assessment), measurement
(registry counts).

## One-line summary

Adopted an external Copilot LMS proposal as preserved prior art, corrected it
against the tree, produced the first real measurement of the LabTalk campus
registries, published the corrected reading at `/lms-architecture/`, and fixed
client-abort handling in the reports gateway.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| External intake | `docs/maintenance/external_ai_intake/specialty_lms_ecosystem_2026-08-09/` | new: `MANIFEST.md`, `ASSESSMENT_LOCAL_WORKBENCH.md`, `SUMMARY_FOR_MAINTAINER.md`, `received_slides/` (13 slides preserved unchanged + a local viewer) |
| Discoverability | `labtalk/registries/ai_report_index.yaml` | two entries proposed: `AIPR-20260809-COPILOT-001`, `AIPR-20260809-003` |
| Reports gateway | `tools/reports/serve_dynamic_reports.py` | client-abort handling; 447 -> 479 lines |
| Closeout | this file | |

## Changed (website, D:\dev\x64base-site)

| Area | Files | Note |
| --- | --- | --- |
| Route | `app/lms-architecture/page.tsx`, `app/lms-architecture/Artifact.tsx` | 14-slide deck route; the component is a thin wrapper over one shared deck document so the standalone and site views cannot drift |
| Assets | `public/lms-architecture/deck.html`, `public/lms-architecture/sections/*.html` | viewer + 14 slide documents |
| Nav | `config/nav.ts` | `Architecture` entry between Documentation and Downloads |
| Matrix | `content/docs/dev/website-documentation-matrix.mdx` | `static` row for `/lms-architecture/` |

`Last audited` in the matrix was **not** advanced; that is a push-time action.

## Verified (proof performed this session)

**Gateway patch -- runtime-proven.** Three checks against the running gateway,
transcript teed to `D:\code\_bbsd_logs\gateway.log`:

```text
P0  curl -s -o NUL -w "%{http_code}" /AI/        -> 200   (precondition)
P1  curl -m 0.2 -o NUL /AI/                      -> curl (28); gateway logged
    2026-08-09 12:56:39 127.0.0.1 "GET /AI/ HTTP/1.1" 200 -
    2026-08-09 12:56:39 127.0.0.1 client closed connection during "/AI/"
    one line, no traceback
P2  upstream :3002 down, request a proxied path  -> clean 502, named upstream
    and WinError 10061; repeated in the log with no traceback
P3  build_reports.py renamed away, request /AI/  -> 503 + RuntimeError with the
    missing-file cause. NOT swallowed.
```

P3 is the overreach check: it proves the patch silenced the benign class only.
A 42 KB proxied body also came back byte-complete through the new write path,
which regression-checks the happy path.

**Registry measurement.** Counted from `labtalk/registries/*.yaml` at the
baseline commit: 4 labs, 16 lessons, 36 concepts (8 orphaned), 56 proofs, 9
apps, 14 portal sections, 5 LMS entries with `live_delivery: false` throughout.
Zero student-ready in either labs or lessons.

**Static checks.** `python -m py_compile` on the patched gateway: pass. YAML
parse of `ai_report_index.yaml`: pass, 5 reports. Envelope field check on both
new intake documents against `ai_report_audit.required_fields`: no missing
fields. Non-ASCII scan of all new/changed files: clean.

**Not verified.** The website deck was exercised by hand in the browser only; no
route test was added. The gateway patch was not exercised under concurrent load.

## Two false greens produced and caught this session

Recorded because they are the same defect class the seed names, and both came
from the assessing agent:

1. **A proof that passed against a dead server.** The first P1 used
   `curl -s -m 0.2 ... ; echo aborted`. `-s` suppressed the connection error, so
   `aborted` printed while nothing was listening. Rewritten with an explicit P0
   precondition and without `-s`.
2. **A finding asserted from a log rather than measured.** A "two gateways bound
   to :3000" claim was inferred from a 502 storm. `Get-NetTCPConnection` showed
   one PID. Withdrawn; the `allow_reuse_address = True` concern is downgraded
   from finding to open question.

## AI-facing docs updated (AIF-006 gate)

- `labtalk/registries/ai_report_index.yaml` -- two proposed entries.
- This closeout.
- **Not updated:** `docs/agents/CURRENT_TARGET.md`. No controlling-target change
  is claimed; the owner ruling of 2026-07-31 ("no single controlling lane")
  still stands.
- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- intake row for AIF-103.
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` -- Session Log row (AIF-006).

## Still open

1. **AIF-102 was claimed by mistake and must be released.** The publish script
   ran `claim-aif` unconditionally instead of reusing an existing claim for this
   run, so the dry pass took AIF-102 and the committing pass took AIF-103. Both
   claim files and both intake rows landed in `b06e91412`; the AIF-102 row was
   removed in the follow-up and the claim is released by:
   `python tools/coordination/session_coordinator.py release-aif --number 102 --run COWORK-20260809-002`
   The script now refuses to claim twice for the same run.
2. **The gateway patch belongs under AIF-100**, not AIF-103. It is reported here
   because it happened in this session; the lane assignment is the owner's.
3. **Q1-Q5 owner rulings** -- see the assessment, section 6. Q3 (do learner
   records live in x64base tables) and Q5 (does a lab proof carry
   engineering-proof weight) are the two that change what a campus build is.
4. **Line endings on the preserved payload.** `.gitattributes` now marks
   `external_ai_intake/**/received_slides/**` as `-text`, because `text=auto`
   would rewrite the received slides and quietly falsify the manifest's
   "preserved unchanged" claim. Added during this lane, not before it.
5. **`allow_reuse_address = True`** on `DynamicReportServer` -- open question,
   not a finding. On Windows this permits a later bind to displace an earlier
   one silently, which is the hazard `start-ai.ps1` exists to prevent. No
   evidence it occurred.
6. **`start-ai.ps1` writes no log.** Both spawned windows run under `cmd /k`
   with no tee, so runtime evidence lives only in scrollback. This cost real
   time this session. A `-Log` switch would make gateway evidence citable.

## Sandbox posture

This session ran in a Cowork mounted sandbox with write access to
`D:\code\ccode` and `D:\dev\x64base-site`. **No git command was run**, including
`git status`. No build was attempted; the sandbox cannot execute the engine.
`.git/HEAD` and `.git/refs/heads/development` were read as plain files to record
the baseline commit, which takes no lock.

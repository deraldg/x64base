---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260722-001
  recorded_at_utc: 2026-07-22T16:27:15Z
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.labtalk.sdlc
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 270da3eee002141db26e97052fc0472307612aa2
  authorization:
    requested_by: maintainer
    scope: formalize scope-calibrated educational and empirical lifecycle doctrine and wire it into the AI Portal, including x64base engine-only and lean build boundaries
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_2026-07-22.md
    kind: session_closeout
---

# Session Closeout — Scope-Calibrated Lifecycle Doctrine (2026-07-22)

Owning lifecycle: LabTalk SDLC and PDLC working-model governance.  
Operating mode: `maintenance`.  
Change class: `C0` documentation/governance record.  
Build target: `documentation_only`.  
Product profile: `not_applicable`.  
Index profile: `not_applicable`.  
Truth state: accepted maintainer doctrine recorded in authoritative development.  
Proof state: source/build topology inspected; YAML, path, whitespace/diff, and this report's audit envelope validated.  
Promotion state: development only; not staged, committed, pushed, or published.

## Outcome

The project now distinguishes educational completeness from empirical scope
discipline without treating either as an exception to best practice.

- The Laboratory Campus may traverse the complete PDLC/SDLC because the
  traversal itself is an instructional product.
- Production and maintenance work use the smallest sufficient gates for the
  change's consequences, risk, consumers, and delivery exposure.
- Budget or technical constraints may defer a gate, but the residual risk and
  next opportunity must be recorded; the truth label does not silently improve.
- A minor change does not automatically trigger a full source regression,
  metadata reharvest, manual assembly, documentation flush, and website release.
- A contract, persistence, cross-cutting, or publication change still expands to
  every demonstrably affected gate.

## Product-composition correction

The lifecycle selector now records the actual artifact before choosing gates:

- `xbase_engine`: the compiled x64base `xbase` static-library target;
- `dottalkpp_runtime`: the CLI/runtime executable;
- bindings or front ends;
- documentation only.

The source confirms that `xbase` and `dottalkpp` are separate CMake targets.
`DOTTALK_PRODUCT=LEAN|PROFESSIONAL|EDUCATIONAL|DEVELOPMENT` selects product
components independently from `DOTTALK_INDEX_MODE=NONE|LEGACY|LMDB`. Therefore
`LEAN` is neither engine-only nor no-index. An xbase-only or lean task begins at
its selected boundary and expands only through affected shared contracts,
consumers, release exposure, or an explicit teaching objective.

## Durable records

| Surface | Change |
| --- | --- |
| `docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md` | Canonical doctrine, vocabulary, mode/class matrix, proportional documentation rule, and build/profile boundary. |
| `labtalk/ai_portal/SCOPE_CALIBRATION_SEED_V1.md` | Mandatory material-work context seed. |
| `AI_README.md`, `AI_PORTAL.md`, `labtalk/ai_portal/README.md`, `labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md` | Canonical startup, task fields, and authority-boundary routing. |
| `labtalk/registries/ai_portal.yaml` | Registered seed and required planning fields. |
| `labtalk/registries/projects.yaml` | PDLC and SDLC project records point to the doctrine. |
| `docs/maintenance/PDLC_STUDENT_WORKING_MODEL_LANE_V1.md` | Scope selection added as a student/working-model skill. |
| `docs/maintenance/DOTTALKPP_SDLC_CHARTER_v0.md` | Artifact/product/index boundary added to runtime governance. |
| `labtalk/LABTALK_SDLC_FRAMEWORK_v0.md` | Campus lifecycle stack gains proportional gate selection. |
| `labtalk/LABTALK_CAMPUS_ARCHITECTURE_v0.md` | Educational completeness and production proportionality made explicit. |
| `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | Current lane state and session log updated. |

## Boundaries preserved

- No C++ or Python source was changed.
- No runtime build or regression suite was required for this `C0` documentation
  change.
- No source-comment/metadata reharvest, HELP generation, manual assembly, or
  data mutation was performed.
- `docs/agents/CURRENT_TARGET.md` was not changed because the active runtime
  objective did not change.
- `C:/x64base`, GitHub, the website repository, and x64base.com were not touched.
- Existing unrelated working-tree changes were preserved; no staging, commit,
  push, or publication was performed.

## Validation

- Python 3.12 + PyYAML parsed `ai_portal.yaml`, `projects.yaml`, and
  `ai_report_audit.yaml`: **PASS**.
- The AI report audit found no finding for this closeout: **PASS**.
- The repository-wide audit still reports 13 pre-existing findings across older
  closeouts (mostly code-fenced rather than true front matter, plus two missing
  Git fields). Those records were not changed by this scoped doctrine task.
- `git diff --check` on the tracked files touched by this task: **PASS** (line
  ending conversion warnings only).
- All seven source and documentation authority paths named by the new seed:
  **present**.

## Review gate

Human review should confirm that the mode/class matrix and product-boundary
terminology match the maintainer's intended teaching model. Promotion, if
desired, remains a separate authorized action.

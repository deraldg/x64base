# PDLC -- Programming Development Life Cycle, the student / working model (lane v1)

Status: **proposed / framing recorded** (dev). Not promoted.
Owning lifecycle: LabTalk education campus - DotTalk++ SDLC.
Project: `project.labtalk.pdlc` -- this lane was promoted to a project per AIF-040
(sibling: `project.labtalk.sdlc`, the SDLC working model).
Doctrine: `AI_PORTAL.md` "Representative by Design" (AIF-037) -- *source teaches*.
Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-039).

## Why this lane exists

DotTalk++ / x64base is a teaching system. It should carry an explicit,
documented **Programming Development Life Cycle** -- the craft-scale life cycle a
learner actually performs -- expressed so that the **student model** (how you learn
to build a program correctly) and the **working model** (how this project builds
real features) are *the same artifact viewed from two distances*. That equivalence
is the point: because source teaches, the process a student is taught must be the
process the project actually runs.

## Terminology map (the framing note)

Three different things hide under nearby names. Keeping them distinct is the whole
lesson.

| Term | Scale | What it is | Status |
| --- | --- | --- | --- |
| **PDLC -- Programming Development Life Cycle** | one program / feature (the desk) | The steps a programmer performs to build a single correct program: **analyze -> design -> code -> test & debug -> document -> maintain**. | Classic pedagogy; **still exactly right** at the craft scale. |
| **SDLC -- Software/Systems Development Life Cycle** | whole system / product (the org) | The envelope a system moves through: conception -> requirements -> design -> build -> test -> deploy -> maintain. | Current umbrella term; not obsolete. |
| **Methodology** (how you *run* the SDLC) | process style | **Waterfall** (sequential, phase-gated) -> **Agile** (iterative/incremental; Scrum, Kanban, XP) -> **DevOps / CI-CD** (operational extension). | Agile replaced *Waterfall*, not the life-cycle concept. |

The common confusion -- "did Agile replace PDLC/SDLC?" -- resolves cleanly: **Agile
replaced Waterfall (a methodology), not the life cycle (a concept).** You still have
a life cycle; Agile is only how you move through it. The older PDLC vocabulary is
ancestral, not wrong -- it is the lineage the modern practice descended from, and
showing that lineage is itself a lesson.

## Our model: a PDLC nested in an evidence-gated, Agile-descended SDLC

What this repo actually runs is neither pure Waterfall nor pure Agile. Each **lane**
is an Agile-style iterative track of **milestones**; but every milestone must be
*proven* before it advances, and documented as it happens. Inside a single
milestone, the programmer performs a full PDLC:

```text
PDLC (inside one milestone)          SDLC / lane governance (around it)
  analyze the problem          <->   intake row (AIF-NNN), truth state
  design the solution          <->   lane doc + contracts
  code                         <->   source change on the branch
  test & debug                 <->   proof: unit test / REGRESSION / teed transcript
  document                     <->   document-as-you-work (AIF-024)
  maintain                     <->   closeout updates startup (AIF-006), drift gates
```

So the student learns the six PDLC steps by watching a real milestone; the working
model is the same six steps operating at production scale with proof gates. One
artifact, two distances.

## Scope is a lifecycle skill

The full six-step cycle is taught because a student cannot responsibly reduce a
process whose stages are invisible. In working practice, however, each step is
performed at the depth justified by the change. A localized, reversible change
does not automatically require a repository-wide regression, complete metadata
reharvest, manual rebuild, and website publication.

Before choosing gates, name the operating mode and change class, then identify
the actual deliverable. The deliverable may be the compiled x64base `xbase`
engine library rather than the full `dottalkpp` executable. If DotTalk++ is the
deliverable, its `LEAN`, `PROFESSIONAL`, `EDUCATIONAL`, and `DEVELOPMENT`
compositions remain distinct from the independent `NONE`, `LEGACY`, and `LMDB`
index profiles. `LEAN` does not mean engine-only and does not mean no-index.

The student lesson is: learn the complete PDLC, select the smallest sufficient
gate set, and record both the reason for expansion and the risk of intentional
deferral. The canonical decision matrix is
`docs/maintenance/SCOPE_CALIBRATED_LIFECYCLE_DOCTRINE_V1.md`.

## Worked examples already in the tree (student-followable)

- **FIELDTYPE codec registry (AIF-030)** -> the **Tuple System extension** to accept
  every registered field type including custom: a clean analyze->design->code->prove
  arc a student can trace, and the integration point the tuple work extends.
- **DotScript arrays (AIF-038)** -> an *early-stage* PDLC: the analyze step (spec
  review found the runtime mismatches) is explicit before any design/code -- showing
  students that "analyze the problem" includes reconciling the design against reality
  (the lane's Phase 0).
- **Manual/website assembly (AIF-033/035)** -> the *document* and *maintain* steps
  made mechanical (drift gates), so students see documentation as part of the cycle,
  not an afterthought.

## What the student / working model needs (milestones)

- **M1 -- the framing (this doc). DONE (2026-07-20).** The terminology map + the
  PDLC<->SDLC nesting. **M1.1 DONE (2026-07-22):** scope calibration and actual
  build/product/index selection were added to the working model.
- **M2 -- the canonical PDLC six-step reference** page for LabTalk, with each step's
  DotTalk++ mechanism named (intake, lane, contract, proof idiom, closeout).
- **M3 -- a fully worked exemplar**: carry one small feature end to end through the
  six PDLC steps as a lesson (candidate: the tuple field-type extension, or a small
  array function once Phase 0 lands).
- **M4 -- publish** the model on the LabTalk campus (education pages) once the engine
  is pushed, per the standing gate.

## Relationship to the incoming projects

- **Tuple System extension (field types incl. custom)** -- a separate effort the
  maintainer is running; it is the primary worked example for this PDLC model and the
  downstream of the field-codec registry. When its materials/location are provided it
  gets its own implementation lane; this lane consumes it as the teaching exemplar.
- **PDLC project (this)** -- the documented student/working model itself.
- **SDLC working model (existing)** -- the lane/intake/closeout/proof-gate machinery
  already operating in this repo; the PDLC model documents and teaches it.

## Non-goals / honesty

This lane documents and teaches a life cycle; it does not invent a new one. The six
PDLC steps are classic and deliberately unchanged -- the contribution is mapping them
onto the project's real mechanisms so the student and working models coincide. Site
publication waits behind the engine push. Dev-only until the exemplar is proven.

## Provenance pointers

- Doctrine: `AI_PORTAL.md` (AIF-037 Representative by Design; AIF-024 Document As You
  Work; AIF-006 Closeout Updates Startup).
- Exemplars: `docs/maintenance/FIELD_TYPE_CODEC_LANE_V1.md` (AIF-030),
  `docs/maintenance/DOTSCRIPT_ARRAYS_LANE_V1.md` (AIF-038),
  `docs/maintenance/MANUAL_ASSEMBLY_LANE_V1.md` (AIF-035).
- LabTalk campus: `content/docs/labtalk/*` (education pages, publication-gated).

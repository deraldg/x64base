---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260809-003
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
    measurement_baseline_commit: 648967b7438bd6e45f2b99417d41f0902e4df4cd
    baseline_scope: session_start
  authorization:
    requested_by: maintainer ("we adopt it and process it into our system properly", 2026-08-09)
    scope: >
      Assess the received Copilot specialty-LMS package against the actual tree,
      measure the LabTalk campus registries, and record both. Produced the
      /lms-architecture deck route on the website as the reviewed counterpart to
      the received package. Also carried an unrelated gateway abort patch, which
      is reported separately in this session's closeout.
  report:
    path: docs/maintenance/external_ai_intake/specialty_lms_ecosystem_2026-08-09/ASSESSMENT_LOCAL_WORKBENCH.md
    kind: intake_assessment
  primary_topics:
    - external ai intake
    - LMS vocabulary collision
    - LabTalk registry measurement
    - AI Portal purpose
---

# Local Workbench Assessment -- Specialty LMS Ecosystem Package

    assesses                    : AIPR-20260809-COPILOT-001
    measurement_baseline_commit: 648967b7438bd6e45f2b99417d41f0902e4df4cd
    baseline_scope              : session_start
    evidence                    : source-evidenced for the architecture findings;
                                  measured (file counts) for section 3
    disposition                 : accept as prior art, reject as description

Read for this assessment, in the order `AI_README.md` prescribes:
`AI_TIER1_SEED_V1.md`, `TIER0_STATE.md`, `AI_README.md`,
`docs/agents/CURRENT_TARGET.md`, then `AI_PORTAL.md` (partial),
`labtalk/ai_portal/README.md`, `labtalk/portal/README.md`,
`labtalk/LABTALK_PORTAL_CONCEPT_v0.md`, and `labtalk/registries/*.yaml`.

## 1. Disposition

**Accept as prior art. Reject as a description of this project.**

The package is a competent piece of positioning work and a useful vocabulary
source. It is not a report about the tree, and nothing in it should be promoted
into manuals, website copy, or contracts as technical truth.

## 2. Vocabulary collision -- the root error

The producing agent read the AI-facing documents and mapped six words onto
learning-management concepts. In this tree those words belong to the **AI
development coordination system**.

| Term | Read as | Is |
| --- | --- | --- |
| lane | learner progression track | AIF work lane; claimed, chartered, intake row |
| proof | learner assessment gate | runtime evidence for an engineering claim |
| evidence class | taxonomy of learner submissions | evidence tiers: planned / source-evidenced / runtime-proven |
| member | student | actor identity (`member.derald`, `member.ai.claude.cowork`) |
| board | student forum | BBS agent handoff (`board.worklog`, AIF-057) |
| AI Portal | public LMS telemetry | AI development-partner onboarding surface |

The single clearest refutation is in `labtalk/ai_portal/README.md`, stated twice
and echoed in `AI_PORTAL.md`:

> The AI Portal is for AI to access the development environment as a partner.
> It is not a student portal for accessing an AI service.

The live `/AI/` view carries the same boundary in its own banner: *"INTERNAL --
review before any publication to x64base.com."*

**Why this matters beyond one document.** The evidence tiers govern what may be
asserted about engine behavior. If learner output ever enters that namespace, a
lab transcript becomes citable as proof of engine correctness. See Q5 below.

## 3. Measurement -- LabTalk campus registries

Counted from `labtalk/registries/*.yaml` at the baseline commit. This is the
part of the intake worth keeping.

| Registry | Count | Detail |
| --- | --- | --- |
| `labs.yaml` | 4 | 1 `first_runnable`, 2 `draft`, 1 `design_only` |
| lessons | 16 | 9 career, 7 student; 3 idea, 12 draft, 1 `proof_linked` |
| `concepts.yaml` | 36 | 20 reachable from a lab, 28 from a lab or lesson, 8 orphaned |
| `proofs.yaml` | 56 | 31 `runtime_observed`, 18 `source_defined`, 3 `validated` |
| `apps.yaml` | 9 | 4 `active_source`, 2 alpha, 2 draft, 1 seed |
| `portal.yaml` | 14 sections | 7 runnable runtime items, 21 interactive launchers |
| `lms.yaml` | 5 entries | `live_delivery: false` on every one |

**Student-ready: zero, in both labs and lessons.**

**The ratio is the finding: 56 proof records against 4 labs.** The evidence
machinery runs an order of magnitude ahead of the curriculum, because it was
built to prove an engine rather than to teach. The campus is real and it is
pre-student. The Portal Proof Rule is why that is visible rather than hidden.

Two things the count changed in this assessment's own earlier draft:

1. **The LMS pipe is not a bare placeholder.** `lms.yaml` carries a versioned
   envelope schema (`labtalk.lms.message.v1`), an outbox directory, and a
   runnable CLI. Only the transport is withheld: *"No endpoint, credential, or
   Moodle function mapping is configured."* A built pipe with the last inch
   deliberately left off is a decision, not a gap -- which makes the package's
   framing of SCORM/LTI absence as "correct by design" an overstatement of
   something already ruled on in code.
2. **The lessons registry is the surprise.** The nine career lessons are not
   stubs; they are post-mortems with measured evidence. That is the strongest
   teaching content in the tree, and it is about engineering judgment rather
   than database syntax. Whether that is the curriculum or a side effect is an
   owner question.

## 4. Corrections to the received package

Survives:

- x64base is not a standalone LMS and should not become one.
- The engine is substrate; the teaching layer sits above it. Matches the
  governance repo split (`deraldg/labtalk` owns campus, portal, labs, proofs).
- Not trying to be Moodle/Canvas/Open edX is a defensible posture.

Does not survive:

1. **AI Portal as LMS telemetry.** Inverted; the artifact says the opposite.
2. **"DotTalk++ is a specialty LMS."** It is a command language and runtime.
   Collapsing it with curriculum would make every lesson revision a runtime
   release.
3. **BBS as a student social layer.** It is identity-bound agent handoff.
4. **"SCORM/LTI absence is correct by design."** Overstated; see 3.1.
5. **xBridge Protocol.** Does not exist in the tree. It is the package's own
   coinage and its most load-bearing invention.
6. **"Architecturally elegant / coherent / safe" as a conclusion.** Possibly
   true; the package held no evidence for it.

## 5. The pattern worth recording

Three confident claims in this lineage were each checkable in under a minute and
each wrong: the portal's purpose, the interop posture, and the existence of the
saved artifact. The failure mode is not ignorance. It is **fluency operating
where a lookup was required** -- which is precisely what the Tier-1 retrieval
table and the "vantage point" question in the New-AI Checklist exist to catch.

Recorded here because the same failure appeared twice more during this session
from the assessing agent itself: a proof step written so that `curl -s` hid a
connection error and printed a pass against a dead server, and a "two gateways
bound to one port" claim inferred from a log rather than measured. Both were
caught, one of them only because the maintainer asked for the measurement.

## 6. Owner rulings owed

| # | Question | Blocks |
| --- | --- | --- |
| Q1 | Is the Moodle pipe a real destination or a placeholder to retire? | whether xAPI / LTI export ever matters |
| Q2 | Who is the student -- self-directed, a class, or the maintainer? | whether an instructor reporting surface is needed |
| Q3 | Do learner run records live in x64base tables, or stay YAML/transcripts? | whether the campus dogfoods the engine |
| Q4 | Does `labtalk` split to `deraldg/labtalk`, or stay in-tree? | registry path policy, independent versioning |
| Q5 | Does a lab proof carry engineering-proof evidential weight? | whether student output can be cited as runtime proof |

Q3 and Q5 are the load-bearing pair. Q3 because a teaching system for a database
engine that does not store its own records in that engine leaves its strongest
demonstration unused. Q5 because the tier vocabulary is doing real work for
engineering claims and would quietly stop meaning what it means.

## 7. Products of this intake

- `/lms-architecture/` on the website -- a 14-slide reviewed deck presenting
  the corrected reading, classified `static` in the website documentation
  matrix, with a `report-only, not repo authority` banner on every slide.
- `config/nav.ts` -- an `Architecture` entry between Documentation and
  Downloads.
- This assessment and the preserved package.

The website deck deliberately contradicts the received package and says so in
its own overview. Both are kept. They should not be reconciled.

# AI Portal Hardening Lane

Status: **Alpha/Experimental — active lane**
Started: 2026-07-12
Owner: Laboratory Campus / AI Friendly / DotTalk++ integration

## Purpose

This lane turns the current LabTalk registry browser and static AI assimilation
documents into a task-oriented AI Portal.

The AI Portal is **for AI to access the development environment as a partner**.
It is not a student portal for accessing an AI service. Its first job is to give
a new or resumed AI a fast, accurate start using durable project seeds rather
than chat memory.

The portal should prepare an AI for a specific series of project tasks by
following curated, typed jumps between projects and artifacts, selecting the
smallest sufficient evidence set, and producing an inspectable task context
packet.

The working metaphor is **frontal memory**. The implementation must remain
explicit and reproducible:

```text
task request
-> typed project and artifact jumps
-> authority and proof checks
-> bounded task context packet
-> guarded action plan
-> proof readback
-> SelfDoc / MDO / Laboratory Campus feedback
```

## Reference Shelf — Depth on Demand

`AI_README.md` defines the one canonical startup order. Do not treat the list
below as another mandatory first-read sequence. Pull these sources only when the
current task needs their additional depth.

1. `DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`
2. `SDLC_FAST_START_SEED_V1.md`
3. `SCOPE_CALIBRATION_SEED_V1.md`
4. `SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`
5. `DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`
6. `SEED_CONNECTION_PROTOTYPE_NOTE_V1.md`
7. `../diagrams/DOTTALKPP_SHELL_DISPATCH_AND_LOOP_CAPTURE_V1.md`
8. `EXTERNAL_AI_CHANGE_PACKAGE_V1.md`
9. `AI_PORTAL_HARDENING_LANE_V1.md`
10. `../portal/README.md`
11. `../LABTALK_PORTAL_CONCEPT_v0.md`
12. `../../AI_README.md`
13. `../../docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md`
14. `../../docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`
15. `../docs/co-development/recursive_coproject_model_v1.md`
16. `../registries/ai_portal.yaml`

## Onboarding Assessments

These dated reports test whether the Portal can re-orient an AI development
partner without relying on prior chat memory. They are reviewed observations,
not replacements for current source, runtime proof, contracts, registries, or
session closeouts.

- `AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md` - Codex cold-start
  re-onboarding, live read-only audit results, and synchronization findings.

## Delivery Posture

The lane is organized around usable increments rather than one long portal
rewrite.

- First usable target: task recipes plus deterministic context packets.
- Near-term prototype: connect task intent to the smallest required set of
  seeds, explain every connection, and expose missing or conflicting context.
- Hardened target: guarded execution and a task-centered portal interface.
- Full intent target: x64base-backed curation and a DotTalk++ teaching loop.
- If a gate runs for more than two weeks without a reviewable artifact, split
  or reduce that gate before continuing.

The planning baseline is substantially shorter than seven months. Dates remain
estimates; proof and safe integration determine promotion.

## Mandatory Public Status

The AI Portal lane is **Alpha/Experimental**. Portal, manual, website, and
generated-summary references must retain that label until graph validation,
context sufficiency, guarded execution, recovery, and evaluation gates are
complete. The portal must not be presented as production autonomous memory or
as an independent source of project truth.

Student and teaching systems may later consume reviewed AI Portal artifacts,
but student access to AI is not the purpose or primary interface of this lane.

## Authority Boundary

This lane organizes and packages truth. It does not manufacture truth.

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
SelfDoc preserves provenance.
MDO assembles reviewed documentation.
The AI Portal selects and explains task-relevant context.
```

Raw AI conversation, portal prose, generated packets, and public website copy
remain derivative material unless promoted through the existing evidence and
review lanes.

For x64base source and publication work, the mandatory location chain is:

```text
D:\code\ccode -> C:\x64base -> github.com/deraldg/x64base
development      clean staging  public snapshot
authority
```

The current development branch is discovered from the workspace. A new AI chat
must not create or switch branches without an explicit maintainer instruction.
The full cold-start and closeout rules are registered in
`DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`.

Every task must also enter through `SDLC_FAST_START_SEED_V1.md`, declare its
owning lifecycle and current SDLC lane, and preserve truth, proof, risk, gate,
and closeout state through implementation and publication.

Material work also applies `SCOPE_CALIBRATION_SEED_V1.md`. Declare whether the
task targets the x64base `xbase` engine library, the `dottalkpp` runtime, a
binding/front end, or documentation only; then record the selected product and
index profiles. `LEAN` is a product composition, not a synonym for engine-only
or no-index. Gate depth follows the selected artifact and affected consumers.

An AI is not DotScript-ready merely because it knows xBase or has read a
language summary. Before AI-authored `.dts` execution, the portal requires the
runtime-learning, syntax-evidence, bootstrap, safety-classification, and
transcript-review gates in `DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`.

Before source-code mutation, an AI must complete the contract preflight in
`SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`: read the contract shelf, registry,
lifecycle, subsystem contracts, and applicable source usage/contract blocks;
then identify constraints and drift before applying a patch.

## Tracking

Milestones and their current state are registered in:

```text
labtalk/registries/ai_portal.yaml
```

The LabTalk portal exposes that registry as the `AI Portal Work` section.

## Professional model and normalization status

The maintained architecture and cross-registry identifier checks are:

```text
docs/maintenance/AI_PORTAL_PROFESSIONAL_SYSTEM_MODEL_V1.md
labtalk/diagrams/ai_portal_professional_pfd_v1.mmd
labtalk/diagrams/ai_portal_schema_crosswalk_dfd_v1.mmd
labtalk/registries/portal_identifier_model.yaml
labtalk/reports/portal/portal_identifier_status_latest.md
```

The generated status classifies the historical `ticket` field as either a
lane reference or an external ticket reference. It does not rewrite historical
records. AIF claim backfill and the older use of `AIPR-*` report identities in
`run_id` remain explicit compatibility observations until an owner ruling
promotes a migration or hard gate.

### Cold-start and restart use

A new chat reaches this model through the conditional Portal row in
`AI_README.md`. A restarted chat, compacted chat, or handoff that will reason
about Portal identity or data flow must not rely on remembered counts or an old
chat summary. It should:

1. read `AI_TIER1_SEED_V1.md` and the current resume sources named by
   `AI_README.md`;
2. read `AI_PORTAL_PROFESSIONAL_SYSTEM_MODEL_V1.md` for the normalized
   relationships and authority boundary;
3. inspect `portal_identifier_model.yaml` rather than inventing field meanings;
4. run `python labtalk/ai_portal/validate_portal_identifiers.py --check` before
   trusting `portal_identifier_status_latest.*`; and
5. name which consumer it is updating: local dynamic `/AI/`, private local
   `/portal`, or reviewed public `/docs/labtalk`.

Those consumers are deliberately different. `/AI/` is a live local generated
operations surface. `/portal` is an ignored website workbench and cannot be a
public dependency. `/docs/labtalk/ai-portal` and
`/docs/labtalk/ai-portal-schemas` are reviewed public projections for partners
that cannot read the local development tree. None of the three becomes source,
runtime, HELP, metadata, proof, or owner-ruling authority.

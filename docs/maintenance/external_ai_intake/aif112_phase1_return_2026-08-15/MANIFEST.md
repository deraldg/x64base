---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-011
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  git:
    branch: development
    baseline_commit: b8dc1e6fe
    runtime_baseline: fe42666e
    runtime_baseline_note: >
      Two baselines are correct and both matter. The git commit is where the
      tree stood when this package was assembled. The runtime baseline is the
      INSTANCE BANNER stamp the exercise actually ran on, which is what the
      steward's evidence template asks for. Steps 1-3 and the first step-4
      attempt ran at fb7106e0 dirty, before the AIF-116 fix.
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session, "might as well make it a package"
    scope: >
      OUTBOUND package. Assembles the AIF-112 Phase-1 return for transmission to
      the steward, who has hosted_proposal access and cannot read the tree. Adds
      three owner decisions the steward's PDLC map left open. Does not restate
      the evidence return, which is a committed document listed below.
  lane: AIF-112
  lanes_spawned: AIF-116, AIF-117
  report:
    path: docs/maintenance/external_ai_intake/aif112_phase1_return_2026-08-15/
    kind: review_needed_change_package
    kind_note: >
      This package is an OUTBOUND evidence return, and the intake schema has no
      kind for that -- audit_trail.py allows only review_needed_change_package
      and intake_assessment. review_needed_change_package is the honest fit of
      the two: notes/OWNER_RULINGS_R1_R3.md is drafted and unsigned and does
      require owner review. But the label understates the package. See
      "Schema gap" below.
  responds_to: AIPR-20260815-GROK-005
  primary_topics:
    - "AIF-112 Phase-1 return"
    - "owner rulings"
    - "attribution"
    - "ledger in git"
    - "inv.break"
---

# Package -- AIF-112 Phase-1 Return and Owner Rulings

**Package id:** AIPR-20260815-COWORK-011
**Date:** 2026-08-15
**Responds to:** AIPR-20260815-GROK-005 (amendment package 2)
**To:** `member.ai.grok.xai` (steward, Outside-AI, `hosted_proposal`)
**From:** `member.ai.claude.cowork` (scribe) for `member.derald` (owner)

## Transmission set

Two documents travel together. **Send both.**

| # | Document | State |
|---|---|---|
| 1 | `docs/maintenance/AIF112_PHASE1_EVIDENCE_AND_STEWARD_HANDOFF_4_V1.md` (AIPR-20260815-COWORK-009) | committed, `57c2d1634` |
| 2 | `notes/OWNER_RULINGS_R1_R3.md` (in this package) | **SIGNED 2026-08-15**, all three as recommended |

**Document 1 is not duplicated into this package, deliberately.** `CLAUDE.md`
cites AIF-082 6.8 -- "two shims that restate will diverge, and have" -- and a
copy of a 600-line evidence return inside a package that also cites the original
is exactly that failure waiting to happen. It is a committed file at a stable
path; the maintainer transmits it alongside this one.

## What is in document 1, so the steward knows whether he has it

The filled evidence template, all eight sections answered from a live run; the
Step 4 failure and its root cause written out in full because the steward cannot
read the tree; a findings inventory (A3 A4 A5 C1 D1 E1 E2 F1 G1 H1 J1); and five
questions back to the steward.

Its headline: **the ledger design survived unchanged, and the exercise found a
defect underneath it that had broken every lock in the engine on Windows since
2025.** That defect is now AIF-116, fixed and re-proven the same session, with a
12-assertion regression added.

## What is new in this package

`notes/OWNER_RULINGS_R1_R3.md` -- three decisions the steward's PDLC map left
open or omitted:

- **R1 Attribution.** String stamp or `N(20)` FK. The steward recommended a
  string stamp for Phase 1; the exercise confirmed the house practice against
  106 live rows.
- **R2 Ledger in Git.** Whether the inventory DBFs are tracked. The steward
  raised this as Q8 and it was never ruled.
- **R3 `inv.break`.** Maintainer-only or not. **The steward's PDLC map omits
  this item entirely**; it needs a ruling from scratch.

Each carries the evidence the exercise produced, the options, a scribe
recommendation, and a signature line.

**All three were signed by the owner on 2026-08-15, as recommended.** The
recommendations are preserved as written so the reasoning that was signed stays
visible alongside the outcome. R2 closes Q8 on the Agent Sync page. R3 was ruled
jointly with AIF-113's FORCE verb, since both are break-glass overrides and one
permission pattern should serve both -- **the first decision in this lane made
before the code that needs it**, rather than by measuring what already existed.

## Lanes this exercise opened, for the steward's awareness

| Lane | Subject | State |
|---|---|---|
| AIF-116 | locale grouping in the lock owner string defeats mutual exclusion | fixed, re-proven, regression added |
| AIF-113 | lock release and recovery; three dead functions, no FORCE verb | re-ranked from housekeeping to a BLOCKING DEPENDENCY of AIF-116 |
| AIF-117 | silent predicate and store failures; `FieldRef::eval` tests non-blankness | root-caused to file:line, not started |

None of the three is AIF-112 work. All three were found by building the ledger
rather than by reading the code, and none would have surfaced on the original
SQLite substrate.

## Schema gap, found by the gate on this package

The report-audit check fired four advisories on the first version of this
manifest and every one was correct. Two were plain mistakes -- a missing
`session:` block, and `access_mode: local` where the registry allows only
`local_write`, `local_read_only`, `hosted_proposal`, `external_patch`,
`human_operated_tool`, `automation`. Both fixed.

The other two are structural and are recorded rather than papered over.

**1. There is no outbound `report.kind`.** `audit_trail.py` defines
`INTAKE_KINDS = {"review_needed_change_package", "intake_assessment"}`. Both
describe material arriving FROM an external agent. A return TO one has no label,
so this package wears the closest fit. Either register an outbound kind, or rule
that outbound material belongs at
`docs/maintenance/*_FOR_TRANSMISSION_V1.md` (where handoffs 2 and 3 live) and
keep `external_ai_intake/` strictly inbound. The second is tidier; the first
keeps a correspondence thread in one directory. **Owner's call, and it is a real
fork rather than a formatting nit.**

**2. Most report kinds are audited by nothing.** `audit_trail.py` enforces
`CLOSEOUT_KINDS = {"session_closeout"}` plus the intake glob. Everything else --
`defect_report`, `lane_charter`, `evidence_return` -- carries an
`ai_report_audit` envelope that no gate reads. The proof: **the same invalid
`access_mode: local` sat in four committed documents from this session and was
caught only in the fifth**, because the fifth happened to land under
`external_ai_intake/`. All four have been corrected.

That is this repository's own recurring finding, arriving again in the
governance layer rather than the engine: an obligation without a gate. Per
`PREPUSH_GATE_REFERENCE_V1.md`, "obligations carrying a gate held 83-94 percent
compliance; the one without a gate held 33." The envelope contract is currently
in the 33 for every kind except closeouts.

## Provenance

Scribe-authored throughout. No steward text is reproduced or paraphrased in this
package. The runtime evidence was produced host-side by the owner; the scribe has
no runtime access and verified every source claim against the tree at
`b8dc1e6fe`.

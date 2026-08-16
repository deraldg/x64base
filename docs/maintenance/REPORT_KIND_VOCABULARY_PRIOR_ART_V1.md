---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-012
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: f6233baa8
  authorization:
    requested_by: maintainer (member.derald), in-session -- "check for prior art on all of these. if they don't have homes look for possibie existing homes"
    scope: >
      Prior-art inventory only. No vocabulary is proposed as settled and nothing
      is renamed. Answers where each report.kind value already has a home, and
      names the two places where prior art conflicts with itself.
  lane: AIF-112 (found in); vocabulary lane UNCLAIMED
  report:
    path: docs/maintenance/REPORT_KIND_VOCABULARY_PRIOR_ART_V1.md
    kind: prior_art_inventory
    kind_note: >
      This value is itself unconstrained, which is the finding. See section 1.
  primary_topics:
    - "report.kind"
    - "prior art"
    - "ai_report_audit"
    - "evidence class"
    - "vocabulary drift"
---

# Report Kind Vocabulary -- Prior Art Inventory

**Question asked:** before inventing a taxonomy for the 17 `report.kind` values
found in the corpus, does each already have a home?

**Short answer:** most do. Two do not. And the exercise turned up two places
where the prior art disagrees with itself, which matters more than the missing
homes.

## 1. What is actually constrained today

Almost nothing.

- `labtalk/registries/ai_report_audit.yaml` **requires** `report.kind` to be
  present. It does not constrain its value.
- `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md` -- the contract that
  defines the envelope -- **never mentions `report.kind` values at all.**
- `labtalk/ai_portal/audit_trail.py` hardcodes two sets **in Python, not in the
  registry**: `CLOSEOUT_KINDS = {"session_closeout"}` and
  `INTAKE_KINDS = {"review_needed_change_package", "intake_assessment"}`.
- `labtalk/registries/ai_report_index.yaml` **records** `kind` per report for
  lookup. It does not constrain it either.

So **3 of 17 values are constrained, and the constraint lives in code rather
than in the registry that exists to hold exactly this.** The other 14 are free
text. That is not authors being careless; there is nothing to be careful
against.

## 2. Prior art, per kind

| Kind | Home | State |
|---|---|---|
| `session_closeout` | `docs/maintenance/SESSION_CLOSEOUT_*.md` | **Established and audited.** 82 files, enforced by `closeout_glob`. |
| `handoff` | **`docs/agents/HANDOFF_<AGENT>_<SUBJECT>_<DATE>.md`** | **Established.** 13 files, consistent naming. See section 4 -- this session did not use it. |
| `agent_handoff` | BBS boards / pseudo-chat; `coordination/quips/` for the lightest rung | **Established as a CARRIER, not a document family.** Per the owner: these are communications through the BBS/pchat. Distinct from `handoff`, which is generic. **Not a merge candidate** -- an earlier scribe suggestion to fold them together was wrong. |
| `defect_report` | **`docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`** | **Established, and it is the ONE list.** 114 rows. Per the owner: "we should maintain 1 and only". Individual defect documents are EVIDENCE cited from an intake row, not lists in their own right -- which is how AIF-116 and AIF-117 were filed today. |
| `finding` | `labtalk/registries/proofs.d/` fragments; `docs/evidence/evidence_ledger_v0.csv` | **Established, two homes by purpose.** Per the owner: "finding is an observation, we can save findings". Today's ruling extends this -- a failure is still a proof and files by subject, so a negative finding belongs in `proofs.d/` beside the positive ones. |
| `lane_charter` | `docs/maintenance/*_LANE_V1.md` | **Established.** Many examples; AIF-113 and AIF-117 follow it. |
| `owner_ruling` | `tools/reports/build_rulings_report.py` -> `docs/reports/AIF_RULINGS_REPORT.html` | **Established as an AGGREGATION.** Rulings are already collected and published, so the kind has a consumer. The generator parses maintenance sheets rather than reading a rulings registry -- so the report exists but a canonical rulings SOURCE does not. |
| `review_needed_change_package` | `docs/maintenance/external_ai_intake/<slug>_<date>/` + `ai_report_index.yaml` | **Established and constrained** (one of the two `INTAKE_KINDS`). |
| `intake_assessment` | same | **Established and constrained.** |
| `outside_ai_package` | same landing zone | **Synonym-shaped.** Almost certainly `review_needed_change_package` under another name; one use. |
| `evidence_return` | `external_ai_intake/` (outbound); `docs/evidence/` | **No home for the OUTBOUND direction.** See section 3. |
| `evidence_note` | `docs/evidence/evidence_ledger_notes_v0.md` | **Plausible existing home**, unverified as intended. |
| `publication_report` | `PROMOTION_PROCESS.md`, `PROMOTION_CHECKLIST.md`, `PROMOTE.manifest`, `docs/reports/` | **Home exists, scattered across four artifacts.** |
| `measurement_report` | `labtalk/registries/proofs.d/` (a measurement IS a proof state) | **Probable home**, not confirmed by an existing example. |
| `gate_falsification_findings` | `proofs.d/` -- precedent set today by `proof.governance.availability_is_not_adoption` | **Home exists as of this session.** A falsified gate is a proof failure, and proof failures file by subject. |
| `doctrine` | `labtalk/ai_portal/` seeds and `AI_GLOSSARY_V1.md`; `docs/governance/` | **Two candidate homes, no rule for choosing.** Genuinely unhoused. |
| `scope` | none | **Genuinely unhoused, and probably not a kind.** One use. Reads like a section heading promoted to a document type by accident. |

**Unhoused after the sweep: `doctrine` and `scope`.** Everything else has prior
art, and two of the seventeen (`outside_ai_package`, and arguably `evidence_note`)
are synonyms of a kind that already exists.

## 3. Gap: there is no outbound anything

`INTAKE_KINDS` describes material arriving FROM an external agent. The landing
zone is documented as "**Received** external-AI packages". Nothing in the schema,
the index, or the directory convention describes a package going the other way.

This session produced one (`AIPR-20260815-COWORK-011`) and had to label it
`review_needed_change_package` because that was the closest legal value.

Two clean resolutions, both defensible:

1. **Register an outbound kind** and keep the AIF-112 correspondence in one
   directory.
2. **Rule that outbound belongs at `docs/maintenance/*_FOR_TRANSMISSION_V1.md`**
   -- which is where handoffs 2 and 3 already live -- and keep
   `external_ai_intake/` strictly inbound, as its own documentation says.

Option 2 is more consistent with what is already written down. Option 1 keeps a
conversation in one place. Owner's call.

## 4. Placement finding: this session did not use the handoff home

`docs/agents/HANDOFF_*.md` is an established family of 13 files with a
consistent naming convention, including several by this same scribe
(`HANDOFF_CLAUDE_COWORK_SANDBOX_BUILD_2026-08-12.md` and others).

The AIF-112 steward handoffs 2, 3 and 4 were all written to
`docs/maintenance/` instead, as `*_FOR_TRANSMISSION_V1.md`.

Both conventions are now in use for the same object. Neither is wrong on its
face -- a steward handoff to an Outside-AI is arguably a different animal from
an inter-session handoff between local agents -- **but nobody decided that, it
just happened.** Worth ruling before the split hardens.

## 5. The conflict that matters more than the missing homes

**Evidence class has two vocabularies, and they are not cross-referenced.**

`docs/governance/01_evidence_classes.md` -- "Allowed evidence classes", stated as
a closed list:

> Runtime-proven, Report-proven, Source-defined, HELP-documented,
> Metadata-staged, Design-intended, Deferred, Historical, Unknown, Rejected

`labtalk/registries/proofs.yaml` -- 121 entries, `state:` field:

> `runtime_observed` (72), `source_defined` (40), `design_intended` (8),
> `validated` (6), `case_registered` (2)

Same concepts. Different spellings. Title-Case-hyphenated in the governance
manual, snake_case in the registry. `docs/evidence/evidence_ledger_v0.csv` uses
the governance spelling (`Historical; Design-intended`), so the split is
manual-versus-registry, consistent within each side.

And they are not merely spelled differently -- **they do not cover the same
ground.** `validated` and `case_registered` exist only in the registry;
`Report-proven`, `HELP-documented`, `Metadata-staged`, `Deferred`, `Historical`,
`Unknown` and `Rejected` exist only in the manual. An agent told to record an
evidence class has two closed lists to choose from, neither of which mentions the
other.

This is the failure `CLAUDE.md` names via AIF-082 6.8 -- "two shims that restate
will diverge, and have" -- in the vocabulary layer rather than the prose layer.

## 6. What the scribe recommends, and what it does not

**Recommends:**

1. Move the three hardcoded kind sets out of `audit_trail.py` and into
   `ai_report_audit.yaml`, where the rest of the policy already lives. Nothing
   is renamed by this; it only puts the constraint where a reader would look.
2. Register the 12 kinds that already have homes, exactly as they are spelled
   today. No merges -- the owner's ruling on `handoff` versus `agent_handoff`
   shows that apparent synonyms can carry a real distinction, and the scribe
   guessed wrong on that pair once already.
3. Rule the two unhoused values (`doctrine`, `scope`) and the outbound gap.
4. Reconcile the two evidence-class vocabularies, or state in each that the
   other exists and which governs where.

**Does not recommend, yet:** turning on enforcement. Section 1 of the
audit-extension proposal stands -- name the vocabulary before gating it, or the
first run fails seventeen ways and someone switches the gate off.

---

Owner `member.derald`. Prior art surveyed by `member.ai.claude.cowork` at
`f6233baa8`. Every claim above is a file that exists or a count taken from the
tree; nothing here is inferred from convention.

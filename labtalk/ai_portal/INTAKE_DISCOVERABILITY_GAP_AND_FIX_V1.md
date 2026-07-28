---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260728-002
  recorded_at_utc: 2026-07-28T19:12:54Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: claude-opus-4-8
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.labtalk.campus
    root: D:/code/ccode/labtalk
  git:
    branch: development
    baseline_commit: 2d777c535
  authorization:
    requested_by: maintainer
    scope: >
      Diagnose why the local workbench was slow to locate a received external-AI
      change package (Grok AIPR-20260728-GROK-002), then note the reason and the
      solution and close the AI-Portal discoverability gap. Drafts only — no
      commit, no push, no live registry mutation beyond the new index draft.
  report:
    path: labtalk/ai_portal/INTAKE_DISCOVERABILITY_GAP_AND_FIX_V1.md
    kind: portal_gap_analysis
---

# AI Portal — External-Intake Discoverability Gap and Fix (v1)

**Author / credit:** Claude Cowork (`member.ai.claude.cowork`, `local_write`),
diagnosing against authoritative `D:\code\ccode` on `development` @ `2d777c535`.
**Date:** 2026-07-28. **Priority:** maintainer-flagged.

## Summary

When the maintainer asked the workbench to find "the Grok post about virtual
databases and object-oriented memos," locating it took several failed full-tree
searches. The delay was **not** because the package was hidden — it was because
the AI Portal provides no path from itself to received external-AI packages and
no index of what has landed. This report notes the confirmed reason and the fix,
and delivers the first fix artifact: a report index that resolves any received
report by id, provider, or concept alias in one lookup.

## The incident

The target was external change package `AIPR-20260728-GROK-002` — *Virtual
Workspaces & Memo-Resident Mini-Databases*, from xAI Grok — preserved at
`docs/maintenance/external_ai_intake/virtual_workspaces_memo_resident_2026-07-28/`.
The workbench first searched the portal proper (`src/AIPortal/`,
`labtalk/ai_portal/`, `labtalk/registries/ai_portal.yaml`), found only governance
seeds and contracts, then fell back to full-repo `grep`/`find`, which timed out
three times on the size of the working tree before an intake-directory search
finally reached the package.

## Confirmed root cause

Each cause below was verified against the actual files, not assumed.

1. **The portal does not point to the intake landing zone.** The AI Portal holds
   contracts and seeds; received packages are filed under
   `docs/maintenance/external_ai_intake/`. Nothing in the portal entry points
   (`AI_README.md`, `AI_PORTAL.md`, the Collection Point contacts) names that
   location, so "posted into the AI portal" and "filed under docs/maintenance"
   are two disconnected facts.

2. **The audit validator never scans external-AI packages.**
   `labtalk/registries/ai_report_audit.yaml` sets
   `closeout_glob: docs/maintenance/SESSION_CLOSEOUT_*.md`, and
   `audit_trail.py` scans only that glob. Yet `AI_REPORT_AUDIT_CONTRACT_V1.md`
   *requires* the `ai_report_audit` envelope on "external AI `MANIFEST.md` change
   packages." So intake `MANIFEST.md` files are contractually in-scope for the
   audit but operationally **invisible** to it: no field validation, no
   report-ID uniqueness check, and — critically — no enumeration.

3. **No emitted index exists.** `audit_trail.py` already builds an internal
   `report_id -> path` map while checking uniqueness, but it discards it and,
   per cause 2, never sees intake packages anyway. There is no durable artifact
   mapping `report_id` / provider / date / concept topics / landing path /
   status that an AI could consult instead of grepping.

4. **The landing directory is an undocumented convention.**
   `EXTERNAL_AI_CHANGE_PACKAGE_V1.md` Local Intake Procedure step 1 says
   "preserve the received archive unchanged as intake evidence" but never names
   *where*. `docs/maintenance/external_ai_intake/<slug>_<date>/` is a de-facto
   pattern with no contractual anchor.

A compounding factor amplified all four: the folder slug
(`virtual_workspaces_memo_resident`) contains neither "grok" (present only in the
manifest metadata) nor the maintainer's concept words ("virtual databases",
"object-oriented memos"), so filename search cannot bridge description to
artifact.

## Process lesson (workbench side)

The correct first move was to read the governing contract
(`EXTERNAL_AI_CHANGE_PACKAGE_V1.md`) to learn the filing convention before
brute-forcing a large tree. Consulting the rule that governs *where a class of
artifact lives* should precede any full-repo search.

## The solution

Four parts. Part A is delivered in this pass; B–D are specified here for the
enforcement upgrade and held for maintainer approval (they touch a contract and
the validator, which under `AI_REPORT_AUDIT_CONTRACT_V1.md` requires an audited
changeset).

**A. Report index (delivered).** `labtalk/registries/ai_report_index.yaml` — the
single discoverability layer. Each entry carries `report_id`, provider/product,
date, `kind`, `topics`, free-text `aliases`, `path`, and `status`. Seeded now
with the three 2026-07-28 reports (the Grok package, the workbench assessment,
and this document). The `aliases` field is what makes "virtual databases /
object-oriented memos" resolve to `AIPR-20260728-GROK-002` without matching the
folder name.

**B. Name the landing zone in the contract.** Amend
`EXTERNAL_AI_CHANGE_PACKAGE_V1.md` step 1 to state that received packages are
preserved under
`docs/maintenance/external_ai_intake/<concept-slug>_<YYYY-MM-DD>/` and indexed in
`labtalk/registries/ai_report_index.yaml`.

**C. Extend the audit to cover intake packages, and emit the index.** Add
`external_intake_glob: docs/maintenance/external_ai_intake/**/MANIFEST.md` to
`ai_report_audit.yaml`; have `audit_trail.py` scan it (relaxing the
`report.kind == session_closeout` check to accept `review_needed_change_package`
and `intake_assessment`), fold intake report-IDs into the uniqueness check, and
emit / refresh `ai_report_index.yaml` on each run so filing a package and
indexing it become one step.

**D. Add a portal pointer.** One line in the Collection Point contacts and
`AI_README.md`: received external-AI packages land in
`docs/maintenance/external_ai_intake/`; look them up in
`labtalk/registries/ai_report_index.yaml`.

## What this closes

With Part A in place, the exact failure that triggered this report is already
gone: an AI (or the maintainer) resolves any received report from one small file
by id, provider, or concept alias — no full-tree search. Parts B–D make the
index self-maintaining and contractually anchored so the gap cannot silently
reopen as more packages arrive.

## Stage

- **Dev (`D:\code\ccode`):** Parts A–D delivered — index seeded
  (`ai_report_index.yaml`); validator extended to scan the intake landing zone
  advisorily and to `--emit-index` (append-merge that preserves curated
  aliases); contract step 1 now names the landing zone; front-door pointers added
  to `AI_README.md` and the Collection Point. All six audit unit tests pass.
  Nothing committed or pushed.
- **Audit backfill (maintainer chose full backfill) — DONE, audit now green:**
  the 21 pre-existing hard findings are resolved. All 16 envelope-less closeouts
  (2026-07-18…07-27) received reconstructed envelopes (`AIPR-<date>-BFn`,
  `access_mode: human_operated_tool`, agent identity `not_exposed`,
  `recorded_at_utc`/`baseline_commit` from each file's real introducing commit, a
  reconstruction note in `authorization.scope`); the 2 duplicate report-ids were
  renumbered; the project **name** was corrected to `project.x64base.runtime`;
  and the missing `git` block was added. Result: `enforced=67 valid=67
  findings=0`, six unit tests green. The three remaining items are **advisory**
  on the received Grok package (its own missing `git` block and non-canonical
  `access_mode: remote`) — genuine return-for-correction to the sender, not a
  local defect, and preserved verbatim as evidence.

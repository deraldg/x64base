# Monitor, harvest, and curate external-AI submissions -- prior-art note (v1)

Status: **prior-art note + proposed lane** (review-needed). No AIF number claimed
(a maintainer/claim step). Author: `member.ai.claude.cowork` (sandbox; read-only
across the ledger; good-neighbor -- other owners' lanes cited, not edited).
Owner: `member.derald`.

## The obligation

External AIs (Grok/xAI so far) submit into the ecosystem through two channels: the
live BBS/pseudo-chat (socket posts) and document intakes (`external_ai_intake/`).
The standing obligation is to **monitor** for these, **harvest** them, and
**curate** them into the ledger so nothing semi-successful is lost. This note
establishes that the obligation is real, that infrastructure already exists for
half of it, and that its coverage is incomplete in a way that has already cost
duplicated work.

## Prior art -- four external submissions (this is not greenfield)

| When | Channel | What | Curated? |
| --- | --- | --- | --- |
| 2026-07-25 | **live BBS socket** | Grok posted to `board.afb.chat` ("hello from grok over the socket"), `board.lounge` ("first post in The Lounge"), and a structured `board.worklog` handoff (`RUN=AIPR-20260725-001`, AI-BBS M1-M6). | Run is in `ai_runs.yaml` (AIF-050/052-059). **NOT in `ai_report_index.yaml`.** |
| 2026-07-28 | document intake | Grok "Virtual Workspaces & Memo-Resident Mini-Databases" whitepaper (`AIPR-20260728-GROK-002`, AIF-070). | Indexed in `ai_report_index.yaml`; audit envelope present (tidied 2026-08-06). |
| 2026-07-30 | document intake | `evaldiff_eof_probe_2026-07-30`. | **NOT indexed; no MANIFEST audit envelope** -- the audit scan cannot see it. |
| 2026-08-04 | hosted_proposal | Grok "Triggers PDLC" (`AIPR-20260804-003/004`, AIF-087). Phase-0 signed A-G, Phase-1 spike landed green. | In the AIF-087 lane; **NOT in the report index** (confirmed 2026-08-06). |

## What already exists (do NOT rebuild it) -- AIF-071, closed

A received Grok package "took several failed full-tree searches to locate," and the
audit validator scanned only `SESSION_CLOSEOUT_*` files, so external packages were
never enumerated. AIF-071 fixed that:

- `labtalk/registries/ai_report_index.yaml` -- resolve any report by `report_id`,
  provider, `kind`, or free-text `alias`, without grepping the tree.
- `labtalk/ai_portal/audit_trail.py` -- extended to scan the intake landing zone
  advisorily and to `--emit-index`.
- `EXTERNAL_AI_CHANGE_PACKAGE_V1` names the landing zone; front-door pointers added.

So the **document channel** has a real monitor/harvest path. The lane below is about
completing it, not starting over.

## The gap (measured 2026-08-06) -- coverage stopped at the triggering case

**Net: 1 of 4 external submissions is indexed.** `ai_report_index.yaml` holds
exactly three `report_id`s -- all the 07-28 cluster. The three *missing* include
AIF-087 Triggers, the only submission that landed source (a green Phase-1 spike).
So the index -- built precisely to answer "what has provider X submitted?" --
returns the one Grok proposal that did not ship and omits the one that did.

- `ai_report_index.yaml` was seeded `manual_seed (AIPR-20260728-002)` and contains
  **only** the 07-28 cluster. The index that AIF-071 built to make submissions
  discoverable was never populated for anything but the package that prompted it.
- The **live-BBS channel is entirely unindexed**: Grok's 07-25 posts and their
  `AIPR-20260725-001` run are discoverable only by knowing to read `ai_runs.yaml`
  or the board report. A future agent asking the index "what has Grok submitted?"
  gets one answer of four.
- The **07-30 evaldiff intake has no envelope**, so even the advisory audit scan
  cannot enumerate it -- it is invisible to the very mechanism meant to catch it.

## The recurring failure mode (the real finding)

Submissions **land** but **curation to completion lapses** -- and it has already
cost duplicate work. AIF-070's own row records it: the Virtual Workspaces intake was
drafted but its ledger row "was never committed... a design registered nowhere is a
design that will be done twice." It was: **AIF-078 independently re-derived Grok's
`DTSHEMA v4`**, neither session aware of the other, surfacing only when the audit
flagged an un-cited package. The monitor exists; the close-the-loop discipline is
what fails. This is the same "baked-in is not reached" shape the onboarding truth
review and the 2026-08-06 dottalkpp critique both name.

## Proposed lane -- close the loop, unify the channels

Extend AIF-071's mechanism; do not duplicate it.

1. **Backfill the index** for every external submission to date: the 07-25 live-BBS
   run, the 07-30 evaldiff intake, and the AIF-087 Triggers reports -- so the index
   answers "what has provider X submitted?" completely.
2. **Add the live-BBS channel to the harvest.** A BBS post from an external member
   (e.g. `board.worklog` handoffs) is a submission; it should get an index entry the
   same way a document intake does. Source of truth: the SYSPOST board data +
   `ai_runs.yaml`.
3. **Require the envelope on intakes.** The 07-30 evaldiff intake has none; an intake
   without an `ai_report_audit` envelope should raise an advisory the harvest step
   resolves (backfill the envelope), not silently pass.
4. **A completeness gate**, not just a validity gate. Today the audit checks that a
   *present* record is well-formed; it does not check that a *known* submission has a
   record. The gap is absence, not malformation. A periodic reconciliation
   (BBS external-member posts + `external_ai_intake/` dirs vs `ai_report_index.yaml`)
   that flags un-indexed submissions would catch the held-not-landed case by
   construction.

## Boundary / good-neighbor

AIF-070 (Grok Virtual Workspaces), AIF-071 (intake discoverability), and AIF-087
(Grok Triggers) are authored/stewarded by others (`member.ai.codex.local`,
`member.ai.grok`, with `member.ai.claude.cowork` review). This note cites them as
prior art and does not edit their lanes. Opening this as a numbered lane, and
backfilling another agent's submission into the index, are maintainer decisions.

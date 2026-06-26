# HELP Family Status Manifest v1

Status: active maintenance lane manifest
Scope: `HELP`, `CMDHELP`, `DOTHELP`, `FOXHELP`, `BBOX`, `DDICT`, `MANUAL`, `MAINT`
Workflow: [COMMENTS_HELP_PROOF_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md)

## Purpose

Capture the current help-family proof state in one place so the lane can move forward without re-reading every individual proof report.

This manifest is a continuity snapshot, not a source of runtime behavior by itself.

## Current lane infrastructure

- comments evidence workflow is active at [COMMENTS_HELP_PROOF_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md)
- help locale workflow is active at [HELP_LOCALE_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_LOCALE_WORKFLOW_v1.md)
- help pipeline split notes are active at [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md)
- cross-lane language inventory is active at [SYSTEM_LANGUAGE_AWARE_LANE_INVENTORY_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/SYSTEM_LANGUAGE_AWARE_LANE_INVENTORY_v1.md)
- reusable source-comment upsert tooling is active at [upsert_source_comment_contract.py](D:/code/ccode/tools/comments/upsert_source_comment_contract.py)
- canonical comments reload remains [SOURCE_COMMENT_RESET_RELOAD.dts](D:/code/ccode/dottalkpp/data/scripts/comments/SOURCE_COMMENT_RESET_RELOAD.dts)

## Infrastructure repairs now in force

1. `IMPORT` is CSV-record aware, so staged metadata rows with quoted multiline fields now survive canonical reload into live `SRC*` tables.
2. The source-comment harvester accepts both:
   - leading `//` contract blocks
   - leading `/* ... */` contract blocks
3. Command identity fallback now accepts either:
   - `command:`
   - `surface:`

These repairs matter because they move comments-lane failures back to real command or router issues instead of hiding them behind staging/import damage.

## Current command-family snapshot

| Target | Source | Comments | HELP DATA / CMDHELP build | CMDHELP visibility | DOTREF / FOXREF source | Runtime router / help | CMDHELPCHK | Current note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `HELP` | green | green | not primary gate | deferred | green | green | green for parent artifact gate | parent router surface is green; `CMDHELP HELP` remains a documented self-usage special case |
| `CMDHELP` | green | green | partially evidenced | green | green | green | green for parent artifact gate | parent build/report surface is green after CSV-aware import repair and SET-family artifact repair |
| `DOTHELP` | green | green | not primary gate | green | green | green | green for parent artifact gate | canonical compiled DOTREF proof surface |
| `FOXHELP` | green | green | partially evidenced | green | green | green | green for parent artifact gate | dual-catalog watchpoint: `foxref.hpp` plus parallel public `dotref.hpp` entry |
| `DDICT` | green | green | green in current same-pass closeout | green in current same-pass closeout | green | green | green in current same-pass closeout | block-header and `surface:` contract support now proven live and closed through current checkpoint proof |
| `MANUAL` | green | green | green in current same-pass closeout | green in current same-pass closeout | green | green | green in current same-pass closeout | historical router-red note is preserved as history only; current checkpoint proof is green |
| `BBOX` | green | green | green when operator-accepted | green when operator-accepted | green | green when operator-accepted | green when operator-accepted | fully closed in current proof chain |
| `MAINT` | green | green | green when operator-accepted | green when operator-accepted | green | green when operator-accepted | green when operator-accepted | fully closed in current proof chain |

## Report map

- [HELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [CMDHELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/CMDHELP_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [DOTHELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/DOTHELP_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [FOXHELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/FOXHELP_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [DDICT_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [MANUAL_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/MANUAL_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [BBOX_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/BBOX_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [MAINT_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/MAINT_COMMENTS_HELP_PROOF_REPORT_v1.md)
- [HELP_DOT_ROUTER_SMOKE_DDICT_MANUAL_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_DOT_ROUTER_SMOKE_DDICT_MANUAL_20260626_v1.md)
- [DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md)
- [HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_FAMILY_CMDHELPCHK_PARENT_PASS_20260626_v1.md)

## What is actually closed

- `HELP` source/comments/router/runtime proof is closed for the current runtime smoke set.
- `CMDHELP` source/comments/runtime proof is closed for the current runtime smoke set.
- `DOTHELP` source/comments/router/runtime proof is closed for the current runtime smoke set.
- `FOXHELP` source/comments/router/runtime proof is closed for the current runtime smoke set.
- the curated parent `CMDHELPCHK` artifact pass is green after the SET-family canonicalization repair.
- `DDICT` is closed through current same-pass `CMDHELPCHK` / HELP DATA / CMDHELP / DOTREF-router proof.
- `MANUAL` is closed through current same-pass `CMDHELPCHK` / HELP DATA / CMDHELP / DOTREF-router proof.
- `BBOX` is fully closed through `CMDHELPCHK`.
- `MAINT` is fully closed through `CMDHELPCHK`.

## What is still incomplete

1. Fresh `CMDHELPCHK` closure is still missing for:
   - no current help-family command in this manifest
2. `CMDHELP HELP` is currently reserved as a self-usage alias path, so it cannot be used as the parent topic-proof surface for `HELP` without a deliberate behavior change.
3. Older planning notes still exist in places where later reports already proved green closure.
4. Locale sidecar consumer behavior is not yet promoted into normal `CMDHELP`; canonical/source HELP remains the enforced default path.
5. Live HELP locale memo payloads are currently a data watchpoint:
   - locale sidecar tables are structurally correct
   - explicit `CMDHELP <topic> LOCALE <locale>` preview is working as a fallback-safe consumer
   - active `HELP_LINE_LOCALE` memo payloads currently prove missing-object damage in runtime data and need rebuild/reseed before true localized line rendering can be claimed

## Recommended next gate

1. Preserve current `CMDHELP HELP` behavior as a documented surface rule unless a behavior-change package is explicitly authorized.
2. Reconcile stale planning notes that still describe `DDICT`, `MANUAL`, or earlier parent help-family work as pending.
3. Continue the same same-pass proof discipline for the next command-family lane that gets promoted into the manifest.

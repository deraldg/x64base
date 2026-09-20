---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260816-003
  recorded_at_utc: 2026-08-16T23:04:04Z
  agent:
    provider: openai
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: codex-local-20260816-ai-portal-live-maintenance
  project:
    id: project.ai_systems.integration
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 119dc7af10f19e52895781b7721b5e5cd7fd9e60
  authorization:
    requested_by: maintainer member.derald in the active Codex task
    scope: development_AI_Portal_live_reports_and_maintenance_console
    excluded: direct_DBF_mutation_production_snapshot_write_site_source_mutation_staging_commit_push_publication
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_LIVE_MAINTENANCE_AIF086_2026-08-16.md
    kind: session_closeout
---

# Session Closeout -- AI Portal Live Maintenance (AIF-086)

Date: 2026-08-16

Owner: `member.derald`

Current steward: `member.ai.claude.cowork`

Contributing agent: `member.ai.codex.local`

Run: `AIPR-20260816-003`

Repository/branch: `D:\code\ccode` / `development`

## Outcome

Turned the local AI maintenance surface into a source-aware development
dashboard while preserving the reviewed-production snapshot boundary.

The live gateway now composes the authoritative `runs.d` and `proofs.d`
fragments in memory. It does not silently depend on stale flattened registries
and does not rewrite those snapshot inputs during a report request. The public
snapshot builder keeps its explicit flat-YAML default.

The console now provides:

- source freshness for live fragments versus reviewed snapshot inputs;
- portal, identity, and BBS catalog grouping with table health and row counts;
- typed field metadata, filtering, sorting, record drilldown, and JSON/CSV export;
- DotScript and RAM dry-run previews before direct execution;
- typed purge confirmation, expected `ROWVER` checks, and serialized writes;
- physical-deletion-aware, view-only tombstones and stale/out-of-order table-load rejection;
- loopback-only, strict-JSON, Origin-checked, per-session-token write requests;
- a health endpoint for the gateway, website upstream, source counts, and write posture.

Fresh-start health renders the live index before reporting ready, returns HTTP
503 for an unhealthy stack, and records every report-render failure. The gateway
also rejects a second listener on the same address and port.

`start-ai.ps1` now defaults to read + preview. Direct execution requires the
explicit `-EnableWrite` switch, and the console continues to require its own
acknowledgement before an execute request. Startup refuses occupied ports,
validates the gateway health payload, and never announces `READY` after a failed
start. It no longer terminates an unverified listener.

## Development and production split

| Surface | Source | Behavior in this run |
| --- | --- | --- |
| `http://localhost:3000/AI/` | `D:\code\ccode` | live development reports from fragments |
| `http://localhost:3000/AI/console` | `D:\code\ccode` | live read + preview maintenance dashboard |
| `http://localhost:3000/AI/health` | `D:\code\ccode` | machine-readable development health |
| `D:\dev\x64base-site\public\AI` | reviewed flat inputs | static production snapshot, unchanged |

The website checkout supplies the local Next.js upstream on port 3002. It is a
downstream projection, not the schema or live-report authority. No website
source or `public/AI` snapshot was changed.

## Filed artifacts

- startup posture: `start-ai.ps1`
- deletion-aware pure DBF reader: `tools/dbf/crud.py`
- maintenance API: `tools/dbf/maint_server.py`
- maintenance UI: `tools/dbf/maint_console.html`
- report gateway: `tools/reports/serve_dynamic_reports.py`
- report builder: `tools/reports/build_reports.py`
- fragment composer: `tools/registries/registry_fragments.py`
- focused tests under `tools/dbf/tests` and `tools/reports/tests`
- runtime transcript: `labtalk/proofs/runs/20260816_230404_ai_portal_live_maintenance.txt`
- proof fragment: `labtalk/registries/proofs.d/proof.ai.portal_live_fragment_maintenance.yaml`
- run fragment: `labtalk/registries/runs.d/AIPR-20260816-003.yaml`

## Verification

- 34 maintenance, gateway, report-source, and regression tests passed.
- 130 schema-registry tests passed.
- 28 CRUD logic tests passed.
- Python compilation and PowerShell parsing passed.
- the live health, console, and AI Portal report routes returned HTTP 200;
- browser interaction verified filtering and the guarded typed create workflow;
- the live report exposed the current AIF-086 fragment records;
- flat registry bytes and timestamps remained unchanged in the source tests.
- an independent read-only re-review of the final hardening changes returned PASS.

The full `D:\dev\x64base-site` production build was also attempted. Its existing
public-content guard rejected unrelated `derald.com` references in
`app/retro/page.tsx`, so this closeout makes no production build or deployment
claim.

## Table impact

No persistent DBF table was created, modified, or deleted. The console read the
existing portal, identity, and BBS stores only. `SYSCHATLNK` remains a
design/proof artifact and is not registered as a production maintenance table.

## Authority and publication state

This is a bounded contributing-agent implementation under existing AIF-086. It
does not transfer lane stewardship and does not claim the AIF-086 M2 or M3 exit
gate. It does not authorize or perform a commit, push, selective promotion,
`C:\x64base` mutation, production DBF migration, website snapshot refresh, or
public deployment.

## Follow-up gates

1. Review the fragment-only development delta before refreshing flat snapshot inputs.
2. Resolve or separately accept the website public-content guard finding.
3. Run the reviewed snapshot diff and publication gate before updating `public/AI`.
4. Add an owned-process supervisor if controlled restart/stop is required.
5. Keep direct DBF execution opt-in until cross-process writer journaling is implemented.

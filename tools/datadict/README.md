# Data Dictionary Tools

Start with the [Data Dictionary entry point](../../docs/datadict/README.md) and
[catalog authority assessment](../../docs/maintenance/reviews/DDICT_CATALOG_AUTHORITY_2026-10-09.md).
This directory mixes reusable evidence tools with historical source-patch and
catalog-promotion scripts. A directory listing is not an approved run sequence.

## Bounded current inventory

From the repository root on Windows:

```powershell
Set-Location D:\code\ccode
& .\.venv312\Scripts\python.exe -B tools/datadict/review/curation_inventory.py --output docs/maintenance/reviews/DDICT_CURATION_INVENTORY_2026-10-09.json
```

On other hosts use a Python 3.12+ interpreter from the repository root with the
same script and arguments. [curation_inventory.py](review/curation_inventory.py)
reads an explicit file list and direct children of named DDICT directories. It
uses the shared DBF reader, records live rows, schema fields, identifiers, hashes,
tracking state, tool option declarations, and exact duplicate candidates. It
writes only its JSON report under `docs/maintenance/reviews`; it neither imports
nor executes the inventoried maintenance scripts. Memo contents and index
integrity are outside this check.

## Tool families

| Directory or entry | Purpose and execution boundary |
| --- | --- |
| `review/curation_inventory.py` | Bounded report-only inventory; suitable starting point for this curation work |
| `orchestrate/redoc_orchestrator.py` | Historical dry-run orchestration/report generator. Most pipeline stages are PLANNED, NOT_RUN, or BLOCKED; a PASS manifest is not completed refresh. Default discovery walks the repository, so do not use it for this bounded review. |
| `extractors/` | Physical-dictionary extractor skeleton; inspect discovery roots and parser compatibility before reuse |
| `parsers/`, `reconcile/`, `validate/` | Transcript parsing, reconciliation, and staging validation tools; review input contracts and output paths first |
| `baseline/`, `diff/`, `disposition/`, `review/` | Snapshot comparison and review workflows; acceptance steps change evidence state |
| `dd-status.ps1` | Wrapper writes reports and can run acceptance-artifact closure. Its interpreter defaults and baseline pointer need checking before use. |
| `catalog/` | Historical catalog construction, source patching, promotion, rebuild, and proof-stage generators. Review each exact script; some generate execution scripts that copy/remove active artifacts. Not a general refresh API. |

The machine inventory records declared command-line options without treating them
as safety guarantees. An individual steward is not established by the filename;
the repository owner remains member.derald until ownership is assigned.

## Preserve the workflow distinction

The intended redocumentation flow is discovery -> extraction -> reconciliation ->
candidate facts -> validation -> review -> separately authorized promotion.
Current tools do not establish a single proven end-to-end refresh operation.
Do not rerun old apply scripts against today's source to recreate a historical
green status. Original packages, generated outputs, backups, and runtime
templates retain their separate locations and roles; see the
[consolidation plan](../../docs/maintenance/reviews/DDICT_CONSOLIDATION_PLAN_2026-10-09.md).

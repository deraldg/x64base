# Python Maintenance Launcher Plan v1

Status: plan-only.

## First-wave Python launcher candidates

- `maint_status.py`
- `maint_blackbox_map.py`

These should be report-only and read-only by default.

## Later Python launcher candidates

- `maint_lanes.py`
- `maint_comments_pipeline_scan.py`
- `maint_help_pipeline_scan.py`
- `maint_cmdhelpchk_status.py`
- `maint_manualgen_status.py`
- `maint_datadict_status.py`
- `maint_messaging_inventory.py`

## Python requirements

- Target Python 3.12.
- Use the standard library first.
- Read repository-relative paths from `--repo-root`.
- Write only generated report files under approved generated/report directories.
- Emit CSV and Markdown reports.
- Emit a boundary ledger for every launcher run.
- Refuse mutation unless a future guarded package explicitly authorizes it.

## No permanent PowerShell launcher rule

PowerShell remains acceptable for generated MDO package wrappers and Windows-local creation tasks. It is not the permanent cross-platform maintenance workflow language.

## First implementation gate

Before any `.py` launcher is created, a separate package must define:

- file name
- inputs read
- outputs written
- mutation boundary
- command-line interface
- report schema
- smoke/readback command

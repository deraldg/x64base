# DD-024 Stable Fingerprint / Exclusion Contract v0

## Purpose

DD-024 fixes the first repeatability flaw found during local DD-022/DD-023 testing: a redocumentation scan counted its own generated `docs/datadict/reports` output as newly added source evidence.

This package defines a stable fingerprint policy and ships a patched report-only orchestrator that excludes volatile/generated folders by default while still allowing generated evidence to be included deliberately.

## Local evidence that triggered DD-024

Observed local test:

```text
DDRUN-full-A-v0: source_files_scanned = 44708
DDRUN-full-B-v0: source_files_scanned = 44709
DD023 A-to-B diff: status REVIEW; added = 1
```

Interpretation: the second run saw output produced by the first run. That is self-observation noise, not source drift.

## Design rule

> Default source fingerprints must exclude generated and volatile outputs. Generated evidence can be included only by explicit selection.

## Default exclusion classes

DD-024 default exclusions include:

- VCS internals: `.git/`
- build outputs: `build/`, `build-msvc/`, `build-pro-md/`, `build-wsl/`, `build-tests/`, `build_rdi/`
- Python/runtime caches: `.venv/`, `__pycache__/`, `.pytest_cache/`
- package/build dependency trees: `vcpkg_installed/`, `target/`, `dist/`, `node_modules/`
- data-dictionary generated lanes: `docs/datadict/reports/`, `manifests/`, `staging/`, `tmp/`, `cache/`
- volatile manualgen lanes: generated, backups, logs, published manual outputs
- backend/runtime generated lanes: selected `dottalkpp/data/lmdb/`, backup/tmp/log areas

## New orchestrator behavior

The active tool remains:

```text
tools/datadict/orchestrate/redoc_orchestrator.py
```

It is now DD-024-aware but preserves DD-022-compatible output names:

```text
dd022_redoc_run_manifest.json
dd022_source_inventory.csv
dd022_run_summary.csv
dd022_step_status.csv
```

Additional DD-024 outputs:

```text
dd024_excluded_inventory.csv
dd024_exclusion_policy_effective.json
```

## New options

```text
--no-exclude-defaults
  Diagnostic only. Disables default exclusions.

--include-generated-evidence
  Includes docs/datadict generated evidence lanes deliberately.

--exclude <pattern>
  Adds a prefix or glob exclusion. May be repeated.
```

## Expected next local gate

After installing DD-024, run two full scans back-to-back and diff them:

```powershell
& $py12 .	ools\datadict\orchestrateedoc_orchestrator.py `
  --repo-root D:\code\ccode `
  --out-dir D:\code\ccode\docs\datadicteports\DDRUN-stable-A-v0 `
  --run-id DDRUN-stable-A-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL

& $py12 .	ools\datadict\orchestrateedoc_orchestrator.py `
  --repo-root D:\code\ccode `
  --out-dir D:\code\ccode\docs\datadicteports\DDRUN-stable-B-v0 `
  --run-id DDRUN-stable-B-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL

& $py12 .	ools\datadict\diffedoc_diff.py `
  --base D:\code\ccode\docs\datadicteports\DDRUN-stable-A-v0 `
  --candidate D:\code\ccode\docs\datadicteports\DDRUN-stable-B-v0 `
  --out-dir D:\code\ccode\docs\datadicteports\DDRUN-stable-A-to-B-diff-v0 `
  --run-id DD023-stable-A-to-B-diff-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```

Expected: `PASS`, with added/removed/changed all zero. If not, inspect `dd024_excluded_inventory.csv` and the DD-023 added/changed CSV.

## Boundary

DD-024 remains report-only. It does not launch DotTalk++, run builds, mutate source, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB catalog data, or promote dictionary facts.

# Source Objects

This package turns C/C++ source files into `dottalk.source-object/v1` objects.
It preserves the file as two lossless views (standalone comment sections and
code sections), carries every existing `@dottalk.usage v1` block, and checks a
single `@dottalk.location v1` block against the file's repository location.
The declared location `id` gives the object a stable identity across moves.
Committed Git history supplies author and date evidence when those claims are
not embedded in the source.

Run a bounded scan:

```powershell
python .\tools\source_objects\scan.py `
  --repo-root D:\code\ccode `
  --roots src\cli `
  --output-dir .\_tmp\source-object-scan
```

Outputs:

- `source_objects.jsonl`: objects intended for programmatic use.
- `location_contract_report.csv`: declared home versus observed home.
- `source_location_ledger.jsonl`: append-only observations when identity or
  location state changes; reuse the output directory to track moves over time.
- `scan_summary.json`: counts suitable for gates and dashboards.

Add `--strict-location` to return exit code 2 when any source has an
undeclared, incomplete, or mismatched location contract. Scanning is read-only;
the only writes are the requested report files.

#!/usr/bin/env python3
"""
DD-047 IMPORT Memo Field Assignment Repair Planner.

Report-only source inspection for the IMPORT memo-field defect found by DD-046.

Purpose:
  Verify that cmd_import.cpp still uses the plain a.set(fi, cols[c]) path and
  does not yet route x64 M-field values through the memo-aware conversion path
  proven by REPLACE.

This tool does not modify source files. It emits a repair report and gate ledger.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def find_first_line(text: str, needle: str) -> int:
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return i
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-047 report-only IMPORT memo-field repair planner")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD047-import-memo-field-assignment-repair-plan-v0")
    ap.add_argument("--cmd-import", default="src/cli/cmd_import.cpp")
    ap.add_argument("--cmd-replace", default="src/cli/cmd_replace.cpp")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    import_path = (repo / args.cmd_import).resolve()
    replace_path = (repo / args.cmd_replace).resolve()

    rows: List[Dict[str, Any]] = []
    failures = 0

    import_text = import_path.read_text(encoding="utf-8", errors="replace") if import_path.exists() else ""
    replace_text = replace_path.read_text(encoding="utf-8", errors="replace") if replace_path.exists() else ""

    checks = [
        {
            "check": "cmd_import_exists",
            "expected": 1,
            "observed": int(import_path.exists()),
            "line": "",
            "interpretation": "IMPORT source is present for repair inspection.",
        },
        {
            "check": "cmd_replace_exists",
            "expected": 1,
            "observed": int(replace_path.exists()),
            "line": "",
            "interpretation": "REPLACE source is present so proven memo helper path can be extracted/reused.",
        },
    ]

    plain_set_line = find_first_line(import_text, "a.set(fi, cols[c])")
    checks.append({
        "check": "import_uses_plain_set_for_csv_values",
        "expected": "present before repair",
        "observed": int(plain_set_line > 0),
        "line": plain_set_line,
        "interpretation": "Plain a.set(fi, cols[c]) is the defect path for x64 M fields.",
    })

    import_has_memo_branch = ("memo" in import_text.lower() and ("MemoStore" in import_text or "memo_backend" in import_text or "build_x64_memo" in import_text))
    checks.append({
        "check": "import_has_memo_aware_branch",
        "expected": 0,
        "observed": int(import_has_memo_branch),
        "line": find_first_line(import_text, "memo"),
        "interpretation": "Current IMPORT should not yet have memo-aware branch unless repair already landed.",
    })

    replace_has_helper = "build_x64_memo_stored_value" in replace_text
    checks.append({
        "check": "replace_has_x64_memo_stored_value_helper",
        "expected": 1,
        "observed": int(replace_has_helper),
        "line": find_first_line(replace_text, "build_x64_memo_stored_value"),
        "interpretation": "REPLACE has the proven memo conversion path that IMPORT should reuse.",
    })

    replace_uses_replaceFieldStored = "replaceFieldStored" in replace_text
    checks.append({
        "check": "replace_uses_stored_field_write",
        "expected": 1,
        "observed": int(replace_uses_replaceFieldStored),
        "line": find_first_line(replace_text, "replaceFieldStored"),
        "interpretation": "REPLACE writes stored object-id text through the stored-field write path.",
    })

    for c in checks:
        rows.append(c)

    # Review is expected if IMPORT is unrepaired; green only if source appears already memo-aware.
    unrepaired = bool(plain_set_line > 0 and not import_has_memo_branch)
    status = "IMPORT_MEMO_FIELD_REPAIR_REQUIRED" if unrepaired else "IMPORT_MEMO_FIELD_REPAIR_ALREADY_PRESENT_OR_REVIEW"
    failures = 1 if unrepaired else 0

    boundary_rows = [
        {"boundary": "report_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "source_files_modified_by_dd047", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_run_by_dd047", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "probe_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd047_import_memo_repair_source_checks.csv", rows,
              ["check", "expected", "observed", "line", "interpretation"])
    write_csv(out / "dd047_no_mutation_boundary_ledger.csv", boundary_rows,
              ["boundary", "observed", "required", "pass"])

    manifest = {
        "contract": "dd047_import_memo_field_assignment_repair_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "cmd_import": str(import_path),
        "cmd_replace": str(replace_path),
        "profiles": args.profile,
        "repair_required": int(unrepaired),
        "plain_set_line": plain_set_line,
        "import_has_memo_aware_branch": int(import_has_memo_branch),
        "replace_has_x64_memo_helper": int(replace_has_helper),
        "source_files_modified": 0,
        "build_run": 0,
        "protected_system_mutations": 0,
        "next_recommended_action": "Extract REPLACE x64 memo stored-value helper into shared helper and call it from IMPORT before rebuilding/rerunning DD-046.",
    }
    write_json(out / "dd047_import_memo_repair_plan_manifest.json", manifest)

    report = f"""# DD-047 IMPORT Memo Field Assignment Repair Plan

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Finding

DD-046 proved that `CREATE X64` creates a memo-bearing table and that `REPLACE` writes memo text correctly, but `IMPORT` imports CSV values into an `M` field as blank.

The source inspection confirms that IMPORT still uses the plain CSV assignment path:

```text
a.set(fi, cols[c])
```

Line observed: `{plain_set_line}`

## Repair direction

Do not make Python the canonical DBF writer.

Do not duplicate memo logic casually.

Preferred repair:

```text
1. Extract the proven x64 memo stored-value helper from cmd_replace.cpp into a shared CLI helper.
2. Preserve existing IMPORT CSV/header/append/write behavior.
3. In cmd_import.cpp, when the destination field is an x64 M field:
     convert CSV text to a memo object-id string using the shared helper.
     store that object-id string in the DBF field.
4. Keep ordinary a.set(...) behavior for non-memo fields.
```

## Proof after repair

```text
setpath dbf metadata\\datadict_create_probe
create x64 ddprobe (probeid C(20), title C(80), notes M)
import D:\\code\\ccode\\dottalkpp\\data\\metadata\\datadict_create_probe\\ddprobe_import.csv
count
goto 1
tup
goto 2
tup
```

Expected memo fields:

```text
P001 -> First memo row loaded through DotTalk++ IMPORT after CREATE X64.
P002 -> Memo text includes a comma, quotes, and UTF-8-ish source characters for CSV parser proof.
```

## Boundary

DD-047 is report-only. It does not modify source, run a build, mutate HELP/META/CMDHELPCHK, or touch active/sandbox catalog data.
"""
    (out / "DD047_IMPORT_MEMO_FIELD_ASSIGNMENT_REPAIR_PLAN.md").write_text(report, encoding="utf-8")

    print(f"DD-047 import memo repair manifest: {out / 'dd047_import_memo_repair_plan_manifest.json'}")
    print(f"status: {status}; repair_required: {int(unrepaired)}; source_files_modified: 0")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

REQUIRED = [
    ("DD096ZD2ZT", "docs/datadict/reports/DD096ZD2ZT-top-usage-contract-alignment-v0/dd096zd2zt_top_usage_contract_alignment_manifest.json", ["DD096ZD2ZT_TOP_USAGE_CONTRACT_ALIGNED"]),
]

HARNESS_REL = "tools/datadict/catalog/reviewed_source_patch_apply_harness.py"

OLD_FORBIDDEN_SNIPPET = "add(\"no_forbidden_active_mutation_terms\", int(not any(x in up for x in [\"PACK\", \"ZAP\", \"DELETE FILE\", \"REMOVE(\"])), 1, not any(x in up for x in [\"PACK\", \"ZAP\", \"DELETE FILE\", \"REMOVE(\"]), \"source patch should not introduce destructive active mutations\")"

NEW_FORBIDDEN_SNIPPET = "code_for_forbidden_scan = strip_cpp_comments_for_validation(candidate_text).upper()\n    add(\"no_forbidden_active_mutation_terms\", int(not any(x in code_for_forbidden_scan for x in [\"PACK\", \"ZAP\", \"DELETE FILE\", \"REMOVE(\"])), 1, not any(x in code_for_forbidden_scan for x in [\"PACK\", \"ZAP\", \"DELETE FILE\", \"REMOVE(\"]), \"executable source patch should not introduce destructive active mutations; comments are ignored\")"

COMMENT_STRIPPER_LINES = [
    "def strip_cpp_comments_for_validation(text: str) -> str:",
    "    \"\"\"Remove C/C++ comments before executable-forbidden-term validation.\"\"\"",
    "    out = []",
    "    i = 0",
    "    n = len(text)",
    "    in_block = False",
    "    in_line = False",
    "    in_str = False",
    "    in_char = False",
    "    escape = False",
    "    while i < n:",
    "        c = text[i]",
    "        nxt = text[i + 1] if i + 1 < n else \"\"",
    "        if in_block:",
    "            if c == \"*\" and nxt == \"/\":",
    "                in_block = False",
    "                i += 2",
    "                continue",
    "            if c == \"\\n\":",
    "                out.append(\"\\n\")",
    "            i += 1",
    "            continue",
    "        if in_line:",
    "            if c == \"\\n\":",
    "                in_line = False",
    "                out.append(c)",
    "            i += 1",
    "            continue",
    "        if not in_str and not in_char and c == \"/\" and nxt == \"*\":",
    "            in_block = True",
    "            i += 2",
    "            continue",
    "        if not in_str and not in_char and c == \"/\" and nxt == \"/\":",
    "            in_line = True",
    "            i += 2",
    "            continue",
    "        out.append(c)",
    "        if escape:",
    "            escape = False",
    "        elif c == \"\\\\\" and (in_str or in_char):",
    "            escape = True",
    "        elif c == '\"' and not in_char:",
    "            in_str = not in_str",
    "        elif c == \"'\" and not in_str:",
    "            in_char = not in_char",
    "        i += 1",
    "    return \"\".join(out)",
]
COMMENT_STRIPPER = "\n".join(COMMENT_STRIPPER_LINES)

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

def wt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def wj(path: Path, obj):
    wt(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def wc(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def patch_harness(text: str):
    if "def strip_cpp_comments_for_validation" in text and "code_for_forbidden_scan" in text:
        return text, "already_patched", 0
    if OLD_FORBIDDEN_SNIPPET not in text:
        return text, "old_forbidden_snippet_not_found", 0
    anchor = "def candidate_validation(candidate_text: str, base_text: str):"
    if anchor not in text:
        return text, "candidate_validation_anchor_not_found", 0
    text2 = text.replace(anchor, COMMENT_STRIPPER + "\n\n" + anchor, 1)
    text2 = text2.replace(OLD_FORBIDDEN_SNIPPET, NEW_FORBIDDEN_SNIPPET, 1)
    return text2, "comment_aware_forbidden_scan_patch_ready", 1

def main():
    ap = argparse.ArgumentParser(description="DD096Z-D2ZU repair D2ZS validator comment scan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096ZD2ZU-d2zs-validator-comment-scan-repair-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--apply-validator-repair", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    gen = out / "generated_d2zs_validator_comment_scan_repair"
    gen.mkdir(parents=True, exist_ok=True)

    blockers = 0
    pre_rows = []
    for lane, rel, expected in REQUIRED:
        p = repo / rel
        observed = read_json(p).get("status", "MISSING")
        passed = int(observed in expected)
        blockers += 0 if passed else 1
        pre_rows.append({"lane": lane, "manifest_path": str(p), "observed_status": observed, "expected_status": "|".join(expected), "pass": passed})
    wc(gen / "dd096zd2zu_precondition_ledger.csv", pre_rows, ["lane","manifest_path","observed_status","expected_status","pass"])

    harness = repo / HARNESS_REL
    original = read_text(harness)
    patched, patch_status, patch_changes = patch_harness(original)
    wt(gen / "reviewed_source_patch_apply_harness.py.patched_preview", patched)
    wt(gen / "DD096ZD2ZU_PATCH_NOTE.md", f"""# DD096Z-D2ZU D2ZS Validator Comment Scan Repair

The D2ZS candidate failed only:

```text
no_forbidden_active_mutation_terms
```

Cause: D2ZT correctly added a top usage contract that mentions forbidden operations such as PACK/ZAP as safety text.

Repair: make D2ZS strip C/C++ comments before scanning for forbidden executable mutation terms.

Patch status: `{patch_status}`
Patch changes available: `{patch_changes}`
""")

    required_missing = int(not harness.exists())
    source_files_written = 0
    backups_written = 0

    if args.apply_validator_repair:
        if blockers or required_missing:
            raise SystemExit("Precondition or harness missing; refusing --apply-validator-repair.")
        if patch_changes == 0:
            raise SystemExit(f"No validator repair changes available: {patch_status}")
        backup_root = repo / f"docs/datadict/backups/DD096ZD2ZU-validator-backup-{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup = backup_root / harness.relative_to(repo)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(harness, backup)
        backups_written = 1
        wt(harness, patched)
        source_files_written = 1

    failures = blockers + required_missing + (0 if patch_status in ["comment_aware_forbidden_scan_patch_ready", "already_patched"] else 1)
    if failures:
        status = "DD096ZD2ZU_D2ZS_VALIDATOR_COMMENT_SCAN_REPAIR_REVIEW"
    elif args.apply_validator_repair:
        status = "DD096ZD2ZU_D2ZS_VALIDATOR_COMMENT_SCAN_REPAIR_APPLIED"
    else:
        status = "DD096ZD2ZU_D2ZS_VALIDATOR_COMMENT_SCAN_REPAIR_READY"

    boundary = [
        {"boundary": "d2zs_validator_repair_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "validator_tool_written", "observed": source_files_written, "required": 1 if args.apply_validator_repair else 0, "pass": int(source_files_written == (1 if args.apply_validator_repair else 0))},
        {"boundary": "runtime_source_logic_rewritten", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cmd_ddict_source_written", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_replacement", "observed": 0, "required": 0, "pass": 1},
    ]
    wc(out / "dd096zd2zu_boundary_ledger.csv", boundary, ["boundary","observed","required","pass"])

    report = f"""# DD096Z-D2ZU D2ZS Validator Comment Scan Repair

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{now()}`

## Purpose

D2ZU fixes an over-strict validation check in D2ZS.

D2ZT added the correct top usage contract. That contract may mention forbidden operations as safety text, but the validator should not treat comments as executable source.

## Summary

- Harness: `{harness}`
- Precondition blockers: **{blockers}**
- Harness missing: **{required_missing}**
- Patch status: **{patch_status}**
- Patch changes available: **{patch_changes}**
- Validator tool written: **{source_files_written}**
- Runtime source logic rewritten: **0**
- `cmd_ddict.cpp` written: **0**

## Next

After D2ZU is applied, rerun D2ZS candidate validation. Expected result is `candidate_valid: 1` if that was the only failing check.
"""
    wt(out / "DD096ZD2ZU_D2ZS_VALIDATOR_COMMENT_SCAN_REPAIR_REPORT.md", report)

    manifest = {
        "contract": "dd096zd2zu_d2zs_validator_comment_scan_repair_v0",
        "run_id": args.run_id,
        "created_utc": now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "harness": str(harness),
        "precondition_blockers": blockers,
        "harness_missing": required_missing,
        "patch_status": patch_status,
        "patch_changes_available": patch_changes,
        "apply_validator_repair": int(args.apply_validator_repair),
        "validator_tool_written": source_files_written,
        "backups_written": backups_written,
        "runtime_source_logic_rewritten": 0,
        "cmd_ddict_source_written": 0,
        "build_file_edits": 0,
        "active_catalog_replacement": 0,
        "failures": failures,
        "next_recommended_action": "Rerun D2ZS candidate validation after applying D2ZU.",
    }
    wj(out / "dd096zd2zu_d2zs_validator_comment_scan_repair_manifest.json", manifest)

    print(f"DD096Z-D2ZU D2ZS validator comment scan repair manifest: {out / 'dd096zd2zu_d2zs_validator_comment_scan_repair_manifest.json'}")
    print(f"status: {status}; patch_status: {patch_status}; validator_tool_written: {source_files_written}; runtime_source_logic_rewritten: 0; failures: {failures}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22S1_5_HEADER_STANDALONE_ESCAPE_REPAIR_APPLIED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22S1_5_HEADER_STANDALONE_ESCAPE_REPAIR_BLOCKED"
NEXT_GATE = "REBUILD_PHASE22S1_AFTER_HEADER_ESCAPE_REPAIR"

TARGETS = [
    "src/help/message_catalog.hpp",
    "src/help/message_catalog.cpp",
    "src/cli/cmd_help.cpp",
    "src/cli/cmd_set.cpp",
]

BAD_STANDALONE = {"\\n", "\\n\\n", "\\r\\n", "\\n\\r\\n"}

def rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(path: Path):
    r = rows(path)
    return r[0] if r else {}

def write_csv(path: Path, data, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in data:
            w.writerow({k: row.get(k, "") for k in fields})

def sha(path: Path):
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def backup(path: Path, root: Path, repo: Path, out):
    dst = root / rel(path, repo)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    out.append({
        "TARGET_PATH": rel(path, repo),
        "BACKUP_PATH": rel(dst, repo),
        "BYTES": dst.stat().st_size,
        "SHA256": sha(dst),
        "ROLE": "pre_patch_source_backup",
    })

def repair_text(text: str):
    actions = []
    fixed_lines = []
    for line_no, line in enumerate(text.splitlines(keepends=True), start=1):
        body = line.rstrip("\r\n")
        nl = line[len(body):]

        if body.strip() in BAD_STANDALONE:
            actions.append({
                "LINE": line_no,
                "ACTION": "REMOVE_STANDALONE_ESCAPED_NEWLINE_LINE",
                "DETAIL": f"removed physical source line containing only {body.strip()!r}",
            })
            continue

        stripped = body.lstrip()
        lead = body[:len(body) - len(stripped)]
        if stripped.startswith("\\n") and (
            stripped[2:].startswith("}") or
            stripped[2:].startswith("bool ") or
            stripped[2:].startswith("void ") or
            stripped[2:].startswith("// MSG-") or
            stripped[2:].startswith("#include")
        ):
            fixed_lines.append(lead + stripped[2:] + nl)
            actions.append({
                "LINE": line_no,
                "ACTION": "REMOVE_LEADING_ESCAPED_NEWLINE_PREFIX",
                "DETAIL": "removed leading \\n before source token",
            })
            continue

        fixed_lines.append(line)

    return "".join(fixed_lines), actions

def scan_bad(text: str):
    bad = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if s in BAD_STANDALONE:
            bad.append({"LINE": line_no, "PATTERN": s, "DETAIL": "standalone escaped newline remains"})
        elif s.startswith("\\n") and not s.startswith("\\n\""):
            bad.append({"LINE": line_no, "PATTERN": s[:80], "DETAIL": "line starts with escaped newline artifact"})
    return bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)
    p14 = first(reports / "message_catalog_phase22s1_4_status_summary_v1.csv")
    messages = p14.get("MESSAGES", "12")
    text_rows = p14.get("TEXT_ROWS", "60")
    locales = p14.get("LOCALES", "de;en-US;es;fr;it")

    gates = []
    fail = 0
    def gate(name, ok, detail):
        nonlocal fail
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            fail += 1

    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22S1_4_REPAIR_GREEN",
         p14.get("STATUS") == "MESSAGE_CATALOG_PHASE22S1_4_BUILD_SYNTAX_LITERAL_NEWLINE_REPAIR_APPLIED",
         p14.get("STATUS", ""))
    for rp in TARGETS:
        gate(f"{rp.upper().replace('/', '_').replace('.', '_')}_PRESENT", (repo / rp).exists(), rp)

    backups, mutations, actions, remaining, errors = [], [], [], [], []
    status = STATUS_BLOCKED

    if fail == 0:
        try:
            broot = repo / "docs/messaging/backups" / f"MSG-022S1_5_HEADER_ESCAPE_REPAIR_BACKUP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            for rp in TARGETS:
                path = repo / rp
                original = path.read_text(encoding="utf-8", errors="replace")
                fixed, acts = repair_text(original)
                if acts:
                    backup(path, broot, repo, backups)
                    path.write_text(fixed, encoding="utf-8")
                    mutations.append({
                        "TARGET_PATH": rp, "ACTION": "UPDATE",
                        "BYTES": path.stat().st_size, "SHA256": sha(path),
                        "DETAIL": "removed standalone/leading escaped-newline artifact",
                    })
                    for a in acts:
                        actions.append({"TARGET_PATH": rp, **a})
                for b in scan_bad(path.read_text(encoding="utf-8", errors="replace")):
                    remaining.append({"TARGET_PATH": rp, **b})

            if remaining:
                fail += 1
                gate("NO_STANDALONE_ESCAPE_ARTIFACTS_REMAIN", False, f"{len(remaining)} rows remain")
            else:
                gate("NO_STANDALONE_ESCAPE_ARTIFACTS_REMAIN", True, "0 rows remain")
            status = STATUS_GREEN if fail == 0 else STATUS_BLOCKED
        except Exception as e:
            fail += 1
            errors.append(str(e))
            gate("PATCH_PHASE22S1_5", False, str(e))

    issues = "0" if status == STATUS_GREEN else str(fail)

    write_csv(reports / "message_catalog_phase22s1_5_status_summary_v1.csv", [{
        "STATUS": status, "MESSAGES": messages, "TEXT_ROWS": text_rows, "LOCALES": locales,
        "VALIDATION_ISSUES": issues,
        "SOURCE_MUTATION_AUTHORIZED": 1 if args.allow_source_mutation else 0,
        "SOURCE_FILES_MUTATED": len(mutations),
        "SOURCE_BACKUP_ROWS": len(backups),
        "STANDALONE_ESCAPE_REPAIR_ROWS": len(actions),
        "REMAINING_ESCAPE_ARTIFACT_ROWS": len(remaining),
        "BUILD_EXECUTED": 0, "RUNTIME_SMOKE_EXECUTED": 0,
        "ERRORS": "; ".join(errors), "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS","MESSAGES","TEXT_ROWS","LOCALES","VALIDATION_ISSUES","SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED","SOURCE_BACKUP_ROWS","STANDALONE_ESCAPE_REPAIR_ROWS",
         "REMAINING_ESCAPE_ARTIFACT_ROWS","BUILD_EXECUTED","RUNTIME_SMOKE_EXECUTED","ERRORS",
         "NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "message_catalog_phase22s1_5_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_5_patch_actions_v1.csv", actions, ["TARGET_PATH","LINE","ACTION","DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_5_source_mutation_inventory_v1.csv", mutations, ["TARGET_PATH","ACTION","BYTES","SHA256","DETAIL"])
    write_csv(reports / "message_catalog_phase22s1_5_source_backup_inventory_v1.csv", backups, ["TARGET_PATH","BACKUP_PATH","BYTES","SHA256","ROLE"])
    write_csv(reports / "message_catalog_phase22s1_5_remaining_escape_artifacts_v1.csv", remaining, ["TARGET_PATH","LINE","PATTERN","DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":len(mutations),"DETAIL":"Authorized source mutation limited to standalone/leading escaped-newline repair in Phase 22S1 touched files."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active CDX/index mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM":"COMMAND_REGISTRY","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No command registry mutation."},
        {"PROTECTED_SYSTEM":"MANUALGEN","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No manualgen mutation."},
        {"PROTECTED_SYSTEM":"DATADICT_SELF_DOC","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22s1_5_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {issues}")
    print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}")
    print(f"  source files mutated: {len(mutations)}")
    print(f"  source backup rows: {len(backups)}")
    print(f"  standalone escape repair rows: {len(actions)}")
    print(f"  remaining escape artifact rows: {len(remaining)}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())

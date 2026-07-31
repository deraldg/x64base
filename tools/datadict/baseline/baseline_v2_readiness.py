#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

STAT_READY = "READY_FOR_BASELINE_V2_AFTER_FRESH_STABLE_PROOF"
STAT_BLOCKED = "BLOCKED_MAINTENANCE_DISPOSITION"
STAT_REVIEW = "BASELINE_V2_REVIEW_REQUIRED"
STAT_NO_CHANGE = "BASELINE_V2_NOT_REQUIRED"

def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def find_manifest_or_dir(dd034: Path) -> Path:
    if dd034.is_file():
        return dd034
    p = dd034 / "dd034_daily_redoc_status_manifest.json"
    if p.exists():
        return p
    raise FileNotFoundError(f"Could not find dd034_daily_redoc_status_manifest.json under {dd034}")

def read_diff_rows(dd034_dir: Path) -> List[Dict[str, str]]:
    candidates = [
        dd034_dir / "dd028_baseline_check" / "diff" / "dd023_file_diff.csv",
        dd034_dir / "diff" / "dd023_file_diff.csv",
    ]
    for p in candidates:
        if p.exists():
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                return [dict(r) for r in csv.DictReader(f)]
    return []

def classify_path(path: str) -> Dict[str, str]:
    p = path.replace("\\", "/")
    lower = p.lower()
    if lower.startswith("docs/datadict/") or lower.startswith("tools/datadict/"):
        if lower.startswith("tools/datadict/"):
            return {"class":"DATADICT_TOOL_UPDATE","lane":"tooling_surface","severity":"MEDIUM","gate":"TOOL_REVIEW_REQUIRED","disposition":"ACCEPT_AS_DATADICT_TOOL_UPDATE_AFTER_SMOKE"}
        if "/review_queue/" in lower or "/baselines/" in lower:
            return {"class":"DATADICT_RUN_OR_BASELINE_ARTIFACT","lane":"datadict_lane","severity":"LOW","gate":"DATADICT_SELF_REVIEW_REQUIRED","disposition":"ACCEPT_AS_DATADICT_EVIDENCE_ARTIFACT"}
        return {"class":"DATADICT_DOC_POLICY_SCHEMA_UPDATE","lane":"datadict_lane","severity":"LOW","gate":"DATADICT_SELF_REVIEW_REQUIRED","disposition":"ACCEPT_AS_DATADICT_SELF_UPDATE_AFTER_REVIEW"}
    if lower.startswith("docs/manuals/developer/manualgen/reports/"):
        return {"class":"MANUALGEN_REPORT_EVIDENCE","lane":"manualgen_lane","severity":"MEDIUM","gate":"MANUALGEN_REVIEW_REQUIRED","disposition":"ACCEPT_AS_MANUALGEN_EVIDENCE_AFTER_REVIEW"}
    if lower == "docs/mdo_savepoint_journal.md":
        return {"class":"MDO_SAVEPOINT_JOURNAL","lane":"documentation_surface","severity":"LOW","gate":"DOC_REVIEW_REQUIRED","disposition":"ACCEPT_AS_SAVEPOINT_EVIDENCE"}
    if lower.endswith(".ps1") and (lower.startswith("mdo_") or lower.startswith("append_mdo_savepoint_mdo_")):
        return {"class":"MDO_MAINTENANCE_SCRIPT","lane":"runtime_or_maintenance_script_surface","severity":"HIGH","gate":"SCRIPT_BOUNDARY_REVIEW_REQUIRED;DD_SCRIPT_RESCAN_REQUIRED","disposition":"ACCEPT_AS_MAINTENANCE_SCRIPT_EVIDENCE_ONLY_IF_EXPLICIT"}
    return {"class":"UNCLASSIFIED","lane":"unclassified_surface","severity":"MEDIUM","gate":"HUMAN_TRIAGE_REQUIRED","disposition":"HUMAN_REVIEW_REQUIRED"}

def compute_status(rows: List[Dict[str, Any]], accept_maintenance: bool, accept_datadict: bool, accept_manualgen: bool) -> str:
    if not rows:
        return STAT_NO_CHANGE
    blockers = [r for r in rows if (r["class"] == "MDO_MAINTENANCE_SCRIPT" and not accept_maintenance) or r["class"] == "UNCLASSIFIED"]
    if blockers:
        return STAT_BLOCKED
    if accept_maintenance and accept_datadict and accept_manualgen:
        return STAT_READY
    return STAT_REVIEW

def main() -> int:
    ap = argparse.ArgumentParser(description="DD-035 report-only baseline-v2 readiness with maintenance disposition")
    ap.add_argument("--dd034", required=True, help="DD-034 daily status run directory or manifest")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD035-baseline-v2-readiness-v0")
    ap.add_argument("--current-baseline", default="DDBASE-stable-v1")
    ap.add_argument("--next-baseline-id", default="DDBASE-stable-v2")
    ap.add_argument("--repo-root", default=r"D:\code\ccode")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--accept-maintenance-evidence", action="store_true")
    ap.add_argument("--accept-datadict-self-update", action="store_true")
    ap.add_argument("--accept-manualgen-evidence", action="store_true")
    ap.add_argument("--fail-on-blocked", action="store_true")
    args = ap.parse_args()

    manifest_path = find_manifest_or_dir(Path(args.dd034))
    dd034_dir = manifest_path.parent
    manifest = load_json(manifest_path)
    rows_raw = read_diff_rows(dd034_dir)
    classified = []
    for rr in rows_raw:
        path = rr.get("path", "")
        c = classify_path(path)
        classified.append({
            "change_kind": rr.get("change_kind", rr.get("change", "")),
            "path": path,
            "object_kind": rr.get("object_kind", ""),
            "base_sha256": rr.get("base_sha256", ""),
            "candidate_sha256": rr.get("candidate_sha256", ""),
            "class": c["class"],
            "lane": c["lane"],
            "severity": c["severity"],
            "gate": c["gate"],
            "proposed_disposition": c["disposition"],
        })

    status = compute_status(classified, args.accept_maintenance_evidence, args.accept_datadict_self_update, args.accept_manualgen_evidence)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc).isoformat()
    class_counts = Counter(r["class"] for r in classified)
    lane_counts = Counter(r["lane"] for r in classified)
    sev_counts = Counter(r["severity"] for r in classified)
    gate_counts = Counter()
    for r in classified:
        for g in r["gate"].split(";"):
            if g:
                gate_counts[g] += 1
    maintenance_count = sum(1 for r in classified if r["class"] == "MDO_MAINTENANCE_SCRIPT")
    datadict_count = sum(1 for r in classified if r["class"].startswith("DATADICT_"))
    manualgen_count = sum(1 for r in classified if r["class"] == "MANUALGEN_REPORT_EVIDENCE")
    blocking_count = sum(1 for r in classified if (r["class"] == "MDO_MAINTENANCE_SCRIPT" and not args.accept_maintenance_evidence) or r["class"] == "UNCLASSIFIED")
    boundary = {"source_edits":0,"build":0,"runtime_launch":0,"help_meta_cmdhelpchk_mutation":0,"dbf_cdx_lmdb_catalog_mutation":0,"baseline_acceptance":0,"file_moves_or_deletes":0}
    manifest_out = {
        "schema":"dd035_baseline_v2_readiness_v0",
        "run_id":args.run_id,
        "created_utc":created,
        "status":status,
        "current_baseline":args.current_baseline,
        "next_baseline_id":args.next_baseline_id,
        "profiles":args.profile,
        "dd034_manifest":str(manifest_path),
        "dd034_status":manifest.get("status",""),
        "added":manifest.get("added",0),
        "removed":manifest.get("removed",0),
        "changed":manifest.get("changed",0),
        "review_rows":manifest.get("review_rows",0),
        "classified_rows":len(classified),
        "blocking_rows":blocking_count,
        "maintenance_script_rows":maintenance_count,
        "datadict_self_update_rows":datadict_count,
        "manualgen_evidence_rows":manualgen_count,
        "acceptance_flags":{"accept_maintenance_evidence":args.accept_maintenance_evidence,"accept_datadict_self_update":args.accept_datadict_self_update,"accept_manualgen_evidence":args.accept_manualgen_evidence},
        "boundary":boundary,
    }
    (out_dir/"dd035_baseline_v2_readiness_manifest.json").write_text(json.dumps(manifest_out, indent=2), encoding="utf-8")
    fields = ["change_kind","path","object_kind","class","lane","severity","gate","proposed_disposition","base_sha256","candidate_sha256"]
    write_csv(out_dir/"dd035_current_change_disposition_rows.csv", classified, fields)
    write_csv(out_dir/"dd035_class_rollup.csv", [{"class":k,"count":v} for k,v in sorted(class_counts.items())], ["class","count"])
    write_csv(out_dir/"dd035_lane_rollup.csv", [{"lane":k,"count":v} for k,v in sorted(lane_counts.items())], ["lane","count"])
    write_csv(out_dir/"dd035_severity_rollup.csv", [{"severity":k,"count":v} for k,v in sorted(sev_counts.items())], ["severity","count"])
    write_csv(out_dir/"dd035_gate_rollup.csv", [{"gate":k,"count":v} for k,v in sorted(gate_counts.items())], ["gate","count"])
    gate_rows = [
        {"gate":"dd034_input_present","observed":1,"required":1,"pass":1},
        {"gate":"no_unclassified_rows","observed":sum(1 for r in classified if r['class']=='UNCLASSIFIED'),"required":0,"pass":1 if sum(1 for r in classified if r['class']=='UNCLASSIFIED')==0 else 0},
        {"gate":"maintenance_evidence_accepted_when_present","observed":int(args.accept_maintenance_evidence or maintenance_count==0),"required":1,"pass":1 if args.accept_maintenance_evidence or maintenance_count==0 else 0},
        {"gate":"datadict_self_update_reviewed","observed":int(args.accept_datadict_self_update or datadict_count==0),"required":1,"pass":1 if args.accept_datadict_self_update or datadict_count==0 else 0},
        {"gate":"manualgen_evidence_reviewed","observed":int(args.accept_manualgen_evidence or manualgen_count==0),"required":1,"pass":1 if args.accept_manualgen_evidence or manualgen_count==0 else 0},
        {"gate":"report_only_boundary","observed":1,"required":1,"pass":1},
    ]
    write_csv(out_dir/"dd035_baseline_v2_gate_ledger.csv", gate_rows, ["gate","observed","required","pass"])
    write_csv(out_dir/"dd035_boundary_ledger.csv", [{"boundary":k,"observed":v,"required":0,"pass":1 if v==0 else 0} for k,v in boundary.items()], ["boundary","observed","required","pass"])
    plan = f"""# DD-035 generated baseline-v2 acceptance command plan
# Report-only package generated this plan. Review before execution.

$py12 = \"D:\\code\\ccode\\build\\vcpkg_installed\\x64-windows\\tools\\python3\\python.exe\"
$repo = \"{args.repo_root}\"

& $py12 .\\tools\\datadict\\orchestrate\\redoc_orchestrator.py --repo-root $repo --out-dir \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-A\" --run-id DDRUN-stable-v2-A --profile ENGINE --profile PROFESSIONAL
& $py12 .\\tools\\datadict\\orchestrate\\redoc_orchestrator.py --repo-root $repo --out-dir \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-B\" --run-id DDRUN-stable-v2-B --profile ENGINE --profile PROFESSIONAL
& $py12 .\\tools\\datadict\\diff\\redoc_diff.py --base \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-A\" --candidate \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-B\" --out-dir \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-A-to-B-diff\" --run-id DD023-stable-v2-A-to-B --profile ENGINE --profile PROFESSIONAL
& $py12 .\\tools\\datadict\\review\\change_classifier.py --dd023 \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-A-to-B-diff\" --out-dir \"$repo\\docs\\datadict\\review_queue\\DD025-stable-v2-A-to-B\" --run-id DD025-stable-v2-A-to-B --profile ENGINE --profile PROFESSIONAL
& $py12 .\\tools\\datadict\\review\\triage_report.py --dd025 \"$repo\\docs\\datadict\\review_queue\\DD025-stable-v2-A-to-B\" --out-dir \"$repo\\docs\\datadict\\review_queue\\DD026-stable-v2-A-to-B\" --run-id DD026-stable-v2-A-to-B --profile ENGINE --profile PROFESSIONAL
& $py12 .\\tools\\datadict\\baseline\\baseline_accept.py --scan \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-B\" --diff \"$repo\\docs\\datadict\\reports\\DDRUN-stable-v2-A-to-B-diff\" --triage \"$repo\\docs\\datadict\\review_queue\\DD026-stable-v2-A-to-B\" --out-dir \"$repo\\docs\\datadict\\baselines\\{args.next_baseline_id}\" --run-id DD027-{args.next_baseline_id}-acceptance --baseline-id {args.next_baseline_id} --profile ENGINE --profile PROFESSIONAL
& $py12 .\\tools\\datadict\\baseline\\baseline_status.py --repo-root $repo --baseline \"$repo\\docs\\datadict\\baselines\\{args.next_baseline_id}\" --out-dir \"$repo\\docs\\datadict\\reports\\DD034-check-{args.next_baseline_id}-current\" --run-id DD034-check-{args.next_baseline_id}-current --profile ENGINE --profile PROFESSIONAL
"""
    (out_dir/"dd035_accept_baseline_v2_commands.ps1").write_text(plan, encoding="utf-8")
    report = ["# DD-035 Baseline v2 Readiness with Maintenance Disposition\n", f"Run id: `{args.run_id}`\n", f"Status: **{status}**\n", f"Created UTC: `{created}`\n", "## Summary\n", f"- Current baseline: `{args.current_baseline}`\n", f"- Next baseline candidate: `{args.next_baseline_id}`\n", f"- DD-034 status: `{manifest.get('status','')}`\n", f"- Diff rows classified: {len(classified)}\n", f"- Data Dictionary self-update rows: {datadict_count}\n", f"- Maintenance script rows: {maintenance_count}\n", f"- Manualgen evidence rows: {manualgen_count}\n", f"- Blocking rows: {blocking_count}\n", "\n## Acceptance flags\n", f"- accept-maintenance-evidence: `{args.accept_maintenance_evidence}`\n", f"- accept-datadict-self-update: `{args.accept_datadict_self_update}`\n", f"- accept-manualgen-evidence: `{args.accept_manualgen_evidence}`\n", "\n## Class rollup\n", "| Class | Count |\n|---|---:|\n"]
    for k,v in sorted(class_counts.items()):
        report.append(f"| {k} | {v} |\n")
    report.append("\n## Boundary\nDD-035 is report-only. It does not accept or replace a baseline, edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or move/delete files.\n")
    if status == STAT_READY:
        report.append("\n## Next action\nRun `dd035_accept_baseline_v2_commands.ps1` after human review to create a fresh stable A/B proof and explicitly accept `DDBASE-stable-v2`.\n")
    else:
        report.append("\n## Next action\nResolve or explicitly accept the remaining disposition gates, then rerun DD-035 with the appropriate acceptance flags.\n")
    (out_dir/"DD035_BASELINE_V2_READINESS_REPORT.md").write_text("".join(report), encoding="utf-8")
    print(f"DD-035 readiness manifest: {out_dir/'dd035_baseline_v2_readiness_manifest.json'}")
    print(f"status: {status}; rows: {len(classified)}; maintenance: {maintenance_count}; datadict: {datadict_count}; blocking: {blocking_count}")
    if args.fail_on_blocked and status == STAT_BLOCKED:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

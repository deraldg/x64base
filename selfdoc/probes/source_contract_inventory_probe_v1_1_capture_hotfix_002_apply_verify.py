#!/usr/bin/env python3
"""
source_contract_inventory_probe_v1_1_capture_hotfix_002_apply_verify.py

REPORT_ONLY / VERIFY_ONLY probe-application and freshness verifier.

Run from:
    D:\code\ccode

Default mode verifies the installed v1.1 probe and current report freshness.

Optional --rerun mode:
    python selfdoc\probes\source_contract_inventory_probe_v1_1_capture_hotfix_002_apply_verify.py --rerun

--rerun runs, in order:
    python selfdoc\probes\source_contract_inventory_probe_v1_1.py
    python selfdoc\probes\source_contract_inventory_v1_1_classifier_gap_review.py
    python selfdoc\probes\source_contract_capture_hotfix_002_evidence_lanes.py

Reads:
    selfdoc\probes\source_contract_inventory_probe_v1_1.py
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\reports\source_contract_capture_hotfix_002_evidence_lanes.json

Writes:
    dottalkpp\docs\generated\reports\source_contract_inventory_probe_v1_1_capture_hotfix_002_apply_verify.md
    dottalkpp\docs\generated\reports\source_contract_inventory_probe_v1_1_capture_hotfix_002_apply_verify.json

Safety:
    VERIFY_ONLY / REPORT_ONLY
    No DotTalk++ source edits.
    No DBF writes.
    No HELP DATA rebuild.
    No CMDHELPCHK changes.
    No source-contract repairs.
    No v1.1 default promotion.
    No file moves/deletes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROBE = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
GAP_REVIEW = Path("selfdoc") / "probes" / "source_contract_inventory_v1_1_classifier_gap_review.py"
EVIDENCE_LANES = Path("selfdoc") / "probes" / "source_contract_capture_hotfix_002_evidence_lanes.py"

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
LANES_JSON = REPORT_DIR / "source_contract_capture_hotfix_002_evidence_lanes.json"

OUT_MD = REPORT_DIR / "source_contract_inventory_probe_v1_1_capture_hotfix_002_apply_verify.md"
OUT_JSON = REPORT_DIR / "source_contract_inventory_probe_v1_1_capture_hotfix_002_apply_verify.json"

EXPECTED_VERSION = "v1.1-capture_hotfix_002"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def extract_function(text: str, func_name: str) -> str:
    match = re.search(rf"^def {re.escape(func_name)}\(.*?(?=^def |\Z)", text, flags=re.DOTALL | re.MULTILINE)
    return match.group(0) if match else ""


def probe_checks(root: Path) -> dict[str, Any]:
    path = root / PROBE
    text = read_text(path)

    if not text:
        return {
            "probe_present": False,
            "probe_path": str(path),
            "version": "",
            "version_ok": False,
            "find_contract_blocks_present": False,
            "parse_fields_present": False,
            "anchors_line_comment_at_marker": False,
            "walks_upward_into_preamble": False,
            "parse_fields_uses_seen_marker": False,
            "parse_fields_ignores_preamble": False,
            "hotfix_002_markers_present": False,
            "probe_application_status": "PROBE_MISSING",
        }

    version_match = re.search(r'PROBE_VERSION\s*=\s*"([^"]+)"', text)
    version = version_match.group(1) if version_match else ""

    find_fn = extract_function(text, "find_contract_blocks")
    parse_fn = extract_function(text, "parse_fields")

    anchors = (
        'line_start = text.rfind("\\n", 0, marker_start) + 1' in find_fn
        and "start = line_start" in find_fn
    )
    walks_upward = "while start > 0" in find_fn and "prev_line" in find_fn
    parse_seen = "seen_marker" in parse_fn and "if MARKER in line" in parse_fn
    parse_ignores = "if not seen_marker" in parse_fn and "continue" in parse_fn
    hotfix_markers = "Capture hotfix 002" in find_fn or "capture_hotfix_002" in text

    if version == EXPECTED_VERSION and anchors and not walks_upward and parse_seen and parse_ignores:
        status = "APPLIED"
    elif version != EXPECTED_VERSION:
        status = "VERSION_NOT_UPDATED_OR_STALE_PROBE"
    elif walks_upward:
        status = "FIND_CONTRACT_BLOCKS_STILL_WALKS_INTO_PREAMBLE"
    else:
        status = "PARTIAL_OR_UNCLEAR_APPLICATION"

    return {
        "probe_present": True,
        "probe_path": str(path),
        "version": version,
        "expected_version": EXPECTED_VERSION,
        "version_ok": version == EXPECTED_VERSION,
        "find_contract_blocks_present": bool(find_fn),
        "parse_fields_present": bool(parse_fn),
        "anchors_line_comment_at_marker": anchors,
        "walks_upward_into_preamble": walks_upward,
        "parse_fields_uses_seen_marker": parse_seen,
        "parse_fields_ignores_preamble": parse_ignores,
        "hotfix_002_markers_present": hotfix_markers,
        "probe_application_status": status,
    }


def report_freshness(root: Path) -> dict[str, Any]:
    inv = read_json(root / INV_JSON)
    lanes = read_json(root / LANES_JSON)

    inv_summary = inv.get("summary", {}) if isinstance(inv.get("summary", {}), dict) else {}
    lanes_summary = lanes.get("summary", {}) if isinstance(lanes.get("summary", {}), dict) else {}

    inv_version = inv_summary.get("probe_version", "")
    lanes_inv_version = lanes_summary.get("inventory_probe_version", "")

    return {
        "inventory_report_present": bool((root / INV_JSON).is_file()),
        "evidence_lanes_report_present": bool((root / LANES_JSON).is_file()),
        "inventory_probe_version": inv_version,
        "evidence_lanes_inventory_probe_version": lanes_inv_version,
        "inventory_version_ok": inv_version == EXPECTED_VERSION,
        "evidence_lanes_version_ok": lanes_inv_version == EXPECTED_VERSION,
        "inventory_generated_at_utc": inv_summary.get("generated_at_utc", ""),
        "evidence_lanes_generated_at_utc": lanes_summary.get("generated_at_utc", ""),
        "evidence_validation_status": lanes_summary.get("validation_status", ""),
        "evidence_capture_review": lanes_summary.get("capture_review", ""),
        "evidence_classifier_review": lanes_summary.get("classifier_review", ""),
        "evidence_stale_evidence": lanes_summary.get("stale_evidence", ""),
        "evidence_do_not_repair": lanes_summary.get("do_not_repair", ""),
        "source_repair_recommended": lanes_summary.get("source_repair_recommended", ""),
    }


def run_step(root: Path, script: Path) -> dict[str, Any]:
    path = root / script
    if not path.is_file():
        return {
            "script": str(script),
            "ran": False,
            "returncode": None,
            "status": "SCRIPT_MISSING",
            "stdout_tail": "",
            "stderr_tail": "",
        }

    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return {
        "script": str(script),
        "ran": True,
        "returncode": proc.returncode,
        "status": "OK" if proc.returncode == 0 else "FAILED",
        "stdout_tail": proc.stdout[-2500:],
        "stderr_tail": proc.stderr[-2500:],
    }


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_md(path: Path, summary: dict[str, Any], run_results: list[dict[str, Any]]) -> None:
    lines = []
    lines.append("# Source Contract Inventory Probe v1.1 Capture Hotfix 002 Apply Verify")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `VERIFY_ONLY / REPORT_ONLY`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append(f"apply/verify status: {summary['apply_verify_status']}")
    lines.append(f"probe application status: {summary['probe_checks']['probe_application_status']}")
    lines.append(f"fresh inventory status: {summary['freshness_status']}")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("v1.1 default promotion: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Probe checks")
    lines.append("")
    lines.append("| Check | Value |")
    lines.append("|---|---|")
    for key, value in summary["probe_checks"].items():
        lines.append(f"| `{md_escape(key)}` | `{md_escape(value)}` |")
    lines.append("")
    lines.append("## Report freshness")
    lines.append("")
    lines.append("| Check | Value |")
    lines.append("|---|---|")
    for key, value in summary["report_freshness"].items():
        lines.append(f"| `{md_escape(key)}` | `{md_escape(value)}` |")
    lines.append("")
    if run_results:
        lines.append("## Rerun results")
        lines.append("")
        lines.append("| Script | Status | Return code |")
        lines.append("|---|---|---:|")
        for result in run_results:
            lines.append(f"| `{md_escape(result['script'])}` | `{md_escape(result['status'])}` | `{md_escape(result['returncode'])}` |")
        lines.append("")
    lines.append("## Recommended next action")
    lines.append("")
    lines.append(summary["recommended_next_action"])
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--rerun", action="store_true", help="Run v1.1 inventory, gap review, and evidence lanes after verifying probe application.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    before_probe = probe_checks(root)

    run_results: list[dict[str, Any]] = []
    if args.rerun:
        for script in (PROBE, GAP_REVIEW, EVIDENCE_LANES):
            result = run_step(root, script)
            run_results.append(result)
            if result["returncode"] not in (0, None):
                break

    after_probe = probe_checks(root)
    freshness = report_freshness(root)

    rerun_failed = any(result.get("returncode") not in (0, None) for result in run_results)

    if after_probe["probe_application_status"] != "APPLIED":
        status = "NOT_VERIFIED_PROBE_NOT_APPLIED"
        next_action = "Reapply capture_hotfix_002 or inspect the v1.1 probe function replacement before rerunning inventory."
    elif args.rerun and rerun_failed:
        status = "NOT_VERIFIED_RERUN_FAILED"
        next_action = "Inspect rerun stderr/stdout. Do not promote v1.1 or repair source."
    elif after_probe["probe_application_status"] == "APPLIED" and freshness["inventory_version_ok"] and freshness["evidence_lanes_version_ok"]:
        status = "VERIFIED_APPLIED_AND_FRESH_REPORTS"
        next_action = "Review evidence-lane counts. If rows still route to CAPTURE_REVIEW/CLASSIFIER_REVIEW, patch classifier/malformed assignment logic only; do not repair source."
    elif after_probe["probe_application_status"] == "APPLIED" and not freshness["inventory_version_ok"]:
        status = "PROBE_APPLIED_REPORTS_STALE"
        next_action = "Run with --rerun to refresh inventory and evidence-lane outputs."
    else:
        status = "PARTIAL_VERIFY_REVIEW_REQUIRED"
        next_action = "Inspect probe checks and freshness table before any further hotfix."

    summary = {
        "generated_at_utc": now(),
        "status": "VERIFY_ONLY_GENERATED",
        "apply_verify_status": status,
        "freshness_status": "FRESH" if freshness["inventory_version_ok"] and freshness["evidence_lanes_version_ok"] else "STALE_OR_UNVERIFIED",
        "rerun_requested": args.rerun,
        "probe_checks_before_rerun": before_probe,
        "probe_checks": after_probe,
        "report_freshness": freshness,
        "run_results": run_results,
        "recommended_next_action": next_action,
        "non_mutation_guards": [
            "did_not_edit_dottalkpp_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_source_headers",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_files",
        ],
    }

    (root / OUT_JSON).write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary, run_results)

    print("SelfDoc capture hotfix 002 apply/verify complete.")
    print(f"Status: {status}")
    print(f"Probe application status: {after_probe['probe_application_status']}")
    print(f"Inventory version: {freshness['inventory_probe_version']}")
    print(f"Evidence lanes inventory version: {freshness['evidence_lanes_inventory_probe_version']}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No source contracts were repaired.")
    return 0 if status.startswith("VERIFIED") or status.startswith("PROBE_APPLIED") else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
cmdhelpchk_phase2_reentry_plan.py

REPORT_ONLY / PLAN_ONLY reentry plan for CMDHELPCHK Phase 2.

Run from:
    D:\code\ccode

Reads, if present:
    dottalkpp\docs\generated\DOCS_INDEX.md
    dottalkpp\docs\generated\reports\doccheck_authority_v1.md
    dottalkpp\docs\generated\reports\artifact_intake_current.md
    dottalkpp\docs\generated\reports\source_contract_hotfix004_arch_intake_record.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_hotfix_004_promotion_review.json
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
    dottalkpp\docs\generated\packages\dottalkpp_doc_mgmt_phase1_working_*.zip

Writes:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_reentry_plan.md
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_reentry_plan.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_reentry_checklist.md

Purpose:
    Record that documentation management Phase 1 is packaged and
    prepare a safe, report-only reentry path into CMDHELPCHK Phase 2.

Safety:
    No DotTalk++ src/include edits.
    No source header repairs.
    No DBF writes.
    No HELP DATA rebuild.
    No CMDHELPCHK changes.
    No v1.1 source-contract default promotion.
    No moving/deleting project files.
"""

from __future__ import annotations

import glob
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
DOCS_INDEX = Path("dottalkpp") / "docs" / "generated" / "DOCS_INDEX.md"
PACKAGES_DIR = Path("dottalkpp") / "docs" / "generated" / "packages"

DOCCHECK_MD = REPORT_DIR / "doccheck_authority_v1.md"
ARTIFACT_INTAKE_MD = REPORT_DIR / "artifact_intake_current.md"
ARCH_INTAKE_JSON = REPORT_DIR / "source_contract_hotfix004_arch_intake_record.json"
PROMOTION_JSON = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.json"
INVENTORY_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"

OUT_MD = REPORT_DIR / "cmdhelpchk_phase2_reentry_plan.md"
OUT_JSON = REPORT_DIR / "cmdhelpchk_phase2_reentry_plan.json"
OUT_CHECKLIST = REPORT_DIR / "cmdhelpchk_phase2_reentry_checklist.md"

EXPECTED_HOTFIX_VERSION = "v1.1-hotfix_004_writer_binding"


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


def safe_get(data: dict[str, Any], key: str, default: Any = "") -> Any:
    return data.get(key, default) if isinstance(data, dict) else default


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def find_latest_phase1_package(root: Path) -> str:
    pattern = str(root / PACKAGES_DIR / "dottalkpp_doc_mgmt_phase1_working_*.zip")
    matches = sorted(glob.glob(pattern))
    return matches[-1] if matches else ""


def extract_doccheck_status(docs_index_text: str, doccheck_text: str) -> str:
    m = re.search(r"DOCCHECK status:\s*\*\*(.*?)\*\*", docs_index_text)
    if m:
        return m.group(1).strip()
    m = re.search(r"Overall status:\s*(.*)", doccheck_text)
    if m:
        return m.group(1).strip()
    return "UNKNOWN"


def build_plan(summary: dict[str, Any]) -> str:
    lines = [
        "# CMDHELPCHK Phase 2 Reentry Plan",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / PLAN_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"reentry status: {summary['reentry_status']}",
        f"doccheck_status: {summary['doccheck_status']}",
        f"phase1_package_present: {summary['phase1_package_present']}",
        f"source_contract_hotfix004_arch_recorded: {summary['source_contract_hotfix004_arch_recorded']}",
        f"v1_1_hotfix004_reviewed_candidate_not_default: {summary['v1_1_hotfix004_reviewed_candidate_not_default']}",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "source repairs: NOT AUTHORIZED",
        "```",
        "",
        "## Current checkpoint",
        "",
        "Documentation management Phase 1 is treated as packaged if the generated package exists and the documentation dashboard reports a completed DOCCHECK state. A `PASS WITH WARNINGS` state is acceptable for reentry planning, but warnings remain active work items.",
        "",
        "## Authority carry-forward",
        "",
        "| Item | State |",
        "|---|---|",
        f"| `source-contract hotfix004` | `{md_escape(summary['source_contract_hotfix004_state'])}` |",
        f"| `v1.1-hotfix_004_writer_binding` | `{md_escape(summary['v1_1_state'])}` |",
        f"| `Batch 0 source repair path` | `{md_escape(summary['batch0_source_repair_state'])}` |",
        f"| `cmd_help.cpp` | `{md_escape(summary['cmd_help_state'])}` |",
        "",
        "## Phase 2 mission",
        "",
        "CMDHELPCHK Phase 2 should become a report-only validator that crosswalks command surfaces, source contracts, generated HELP artifacts, and documentation authority records before any HELP DATA rebuild or source repair is considered.",
        "",
        "## Proposed Phase 2 build order",
        "",
    ]
    for idx, item in enumerate(summary["proposed_build_order"], 1):
        lines.append(f"{idx}. `{item['id']}` — {item['purpose']}")

    lines += [
        "",
        "## Gates",
        "",
        "```text",
        "Visibility before mutation.",
        "Classification before repair.",
        "Report-only before DBF writes.",
        "Explicit promotion before default authority.",
        "Source/runtime evidence outranks generated documentation.",
        "```",
        "",
        "## Do not do yet",
        "",
        "```text",
        "Do not rebuild HELP DATA.",
        "Do not modify CMDHELPCHK runtime logic.",
        "Do not add or repair source headers.",
        "Do not promote v1.1-hotfix_004_writer_binding to default.",
        "Do not let DOCGEN output become proof by itself.",
        "```",
        "",
        "## Inputs checked",
        "",
    ]
    for item in summary["inputs_checked"]:
        lines.append(f"- `{md_escape(item['path'])}`: `{item['state']}`")

    lines += [
        "",
        "## Recommended next action",
        "",
        summary["recommended_next_action"],
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    lines.append("")
    return "\n".join(lines)


def build_checklist(summary: dict[str, Any]) -> str:
    lines = [
        "# CMDHELPCHK Phase 2 Reentry Checklist",
        "",
        "## Preflight",
        "",
        "- [ ] Confirm `DOCS_INDEX.md` still reports `PASS WITH WARNINGS` or better.",
        "- [ ] Confirm the Phase 1 package zip exists.",
        "- [ ] Confirm hotfix004 is architecture-recorded and reviewed-but-not-default.",
        "- [ ] Confirm source repair path remains closed for Batch 0.",
        "- [ ] Confirm `cmd_help.cpp` remains `STALE_EVIDENCE / DO_NOT_REPAIR`.",
        "",
        "## Build sequence",
        "",
    ]
    for item in summary["proposed_build_order"]:
        lines.append(f"- [ ] `{item['id']}`")
        lines.append(f"      {item['purpose']}")
    lines += [
        "",
        "## Stop conditions",
        "",
        "- [ ] Stop if any tool recommends source repair from classification alone.",
        "- [ ] Stop if any tool proposes DBF writes before explicit HELP DATA rebuild authorization.",
        "- [ ] Stop if any tool silently promotes v1.1-hotfix_004 to default.",
        "- [ ] Stop if generated documentation contradicts source/runtime evidence.",
        "",
        "## Completion condition",
        "",
        "- [ ] CMDHELPCHK Phase 2 produces a report-only crosswalk with warnings classified into source, HELP artifact, metadata, documentation, stale evidence, or policy-review lanes.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    root = Path(".").resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    docs_index_text = read_text(root / DOCS_INDEX)
    doccheck_text = read_text(root / DOCCHECK_MD)
    artifact_intake_text = read_text(root / ARTIFACT_INTAKE_MD)

    arch_data = read_json(root / ARCH_INTAKE_JSON)
    arch_summary = arch_data.get("summary", {}) if isinstance(arch_data.get("summary", {}), dict) else {}

    promotion_data = read_json(root / PROMOTION_JSON)
    promotion_summary = promotion_data.get("summary", {}) if isinstance(promotion_data.get("summary", {}), dict) else {}

    inventory_data = read_json(root / INVENTORY_JSON)
    inventory_summary = inventory_data.get("summary", {}) if isinstance(inventory_data.get("summary", {}), dict) else {}

    package = find_latest_phase1_package(root)
    doccheck_status = extract_doccheck_status(docs_index_text, doccheck_text)

    arch_status = str(safe_get(arch_summary, "arch_intake_status", ""))
    promotion_status = str(safe_get(promotion_summary, "promotion_review_status", ""))
    inventory_probe_version = str(
        safe_get(promotion_summary, "inventory_probe_version")
        or safe_get(inventory_summary, "probe_version")
    )

    hotfix_arch_recorded = arch_status in {
        "RECORDED_REVIEWED_PROMOTION_CANDIDATE_NOT_DEFAULT",
        "RECORDED_EVIDENCE_COMPLETE_PROMOTION_REVIEW_STATUS_NEEDS_LABEL_REVIEW",
    }
    reviewed_not_default = (
        inventory_probe_version == EXPECTED_HOTFIX_VERSION
        and promotion_status in {
            "PROMOTION_CANDIDATE_REVIEW_PASSED_NOT_DEFAULT",
            "PROMOTION_CANDIDATE_APPROVED_WITH_SCOPE_NOTES",
        }
    )

    phase1_ok = bool(package) and doccheck_status in {"PASS", "PASS WITH WARNINGS"}
    source_repair_recommended = int(safe_get(promotion_summary, "source_repair_recommended", 0) or 0)

    if phase1_ok and hotfix_arch_recorded and reviewed_not_default and source_repair_recommended == 0:
        reentry_status = "READY_FOR_CMDHELPCHK_PHASE2_REPORT_ONLY"
        next_action = "Build `cmdhelpchk_phase2_crosswalk_probe_v0` as a report-only validator."
    elif phase1_ok:
        reentry_status = "READY_WITH_REVIEW_NOTES"
        next_action = "Review missing hotfix004 authority fields before CMDHELPCHK Phase 2 crosswalk."
    else:
        reentry_status = "HOLD_PHASE1_EVIDENCE_INCOMPLETE"
        next_action = "Resolve Phase 1 package/dashboard evidence before returning to CMDHELPCHK Phase 2."

    proposed_build_order = [
        {
            "id": "cmdhelpchk_phase2_crosswalk_probe_v0",
            "purpose": "Inventory command surfaces, source contracts, DOTHELP/CMDHELP outputs, and authority records into one report-only crosswalk.",
        },
        {
            "id": "cmdhelpchk_phase2_warning_classifier_v0",
            "purpose": "Classify crosswalk warnings into source, HELP artifact, metadata, documentation, stale evidence, intentional exception, and policy-review lanes.",
        },
        {
            "id": "cmdhelpchk_phase2_canary_plan_v0",
            "purpose": "Define runtime canaries for HELP/CMDHELPCHK without rebuilding HELP DATA.",
        },
        {
            "id": "cmdhelpchk_phase2_promotion_gate_v0",
            "purpose": "State explicit conditions for any later HELP DATA rebuild, CMDHELPCHK mutation, or source-contract promotion.",
        },
    ]

    inputs = [
        {"path": str(root / DOCS_INDEX), "state": "present" if (root / DOCS_INDEX).is_file() else "missing"},
        {"path": str(root / DOCCHECK_MD), "state": "present" if (root / DOCCHECK_MD).is_file() else "missing"},
        {"path": str(root / ARTIFACT_INTAKE_MD), "state": "present" if (root / ARTIFACT_INTAKE_MD).is_file() else "missing"},
        {"path": str(root / ARCH_INTAKE_JSON), "state": "present" if (root / ARCH_INTAKE_JSON).is_file() else "missing"},
        {"path": str(root / PROMOTION_JSON), "state": "present" if (root / PROMOTION_JSON).is_file() else "missing"},
        {"path": str(root / INVENTORY_JSON), "state": "present" if (root / INVENTORY_JSON).is_file() else "missing"},
        {"path": package, "state": "present" if package else "missing"},
    ]

    summary = {
        "generated_at_utc": now(),
        "status": "REPORT_ONLY_PLAN_GENERATED",
        "reentry_status": reentry_status,
        "doccheck_status": doccheck_status,
        "phase1_package_present": bool(package),
        "phase1_package": package,
        "source_contract_hotfix004_arch_recorded": hotfix_arch_recorded,
        "v1_1_hotfix004_reviewed_candidate_not_default": reviewed_not_default,
        "inventory_probe_version": inventory_probe_version,
        "promotion_review_status": promotion_status,
        "arch_intake_status": arch_status,
        "source_repair_recommended": source_repair_recommended,
        "source_contract_hotfix004_state": arch_status or "missing",
        "v1_1_state": f"{inventory_probe_version} / {promotion_status}",
        "batch0_source_repair_state": "closed" if source_repair_recommended == 0 else "review required",
        "cmd_help_state": "STALE_EVIDENCE / DO_NOT_REPAIR",
        "proposed_build_order": proposed_build_order,
        "inputs_checked": inputs,
        "recommended_next_action": next_action,
        "non_mutation_guards": [
            "did_not_edit_dottalkpp_src_or_include",
            "did_not_apply_source_repair_patches",
            "did_not_write_dbfs",
            "did_not_rebuild_help_data",
            "did_not_modify_cmdhelpchk",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_project_files",
        ],
    }

    (root / OUT_JSON).write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")
    (root / OUT_MD).write_text(build_plan(summary), encoding="utf-8")
    (root / OUT_CHECKLIST).write_text(build_checklist(summary), encoding="utf-8")

    print("CMDHELPCHK Phase 2 reentry plan complete.")
    print(f"Reentry status: {reentry_status}")
    print(f"DOCCHECK status: {doccheck_status}")
    print(f"Phase 1 package present: {bool(package)}")
    print(f"Hotfix004 arch recorded: {hotfix_arch_recorded}")
    print(f"v1.1 hotfix004 reviewed candidate not default: {reviewed_not_default}")
    print(f"Source repair recommended: {source_repair_recommended}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Wrote: {OUT_CHECKLIST}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if reentry_status != "HOLD_PHASE1_EVIDENCE_INCOMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())

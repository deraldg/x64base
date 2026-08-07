#!/usr/bin/env python3
"""
cmdhelpchk_phase2_promotion_gate_v0.py

REPORT_ONLY / PROMOTION_GATE_PLAN_ONLY probe for CMDHELPCHK Phase 2.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_validation_v0.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_validation_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_plan_v0.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_crosswalk_v0.json
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_hotfix_004_promotion_review.json
    dottalkpp\docs\generated\reports\source_contract_hotfix004_arch_intake_record.json

Writes:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_promotion_gate_v0.md
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_promotion_gate_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_promotion_gate_v0.json

Purpose:
    State explicit conditions for any later HELP DATA rebuild, CMDHELPCHK mutation,
    source repair, or v1.1 source-contract default promotion.

Safety:
    No DotTalk++ src/include edits.
    No source header repairs.
    No DBF writes.
    No HELP DATA rebuild.
    No CMDHELPCHK changes.
    No v1.1 source-contract default promotion.
    No project file moves/deletes.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"

CANARY_VALIDATION_JSON = REPORT_DIR / "cmdhelpchk_phase2_canary_validation_v0.json"
CANARY_VALIDATION_CSV = REPORT_DIR / "cmdhelpchk_phase2_canary_validation_v0.csv"
CANARY_PLAN_JSON = REPORT_DIR / "cmdhelpchk_phase2_canary_plan_v0.json"
WARNING_CLASSIFIER_JSON = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.json"
CROSSWALK_JSON = REPORT_DIR / "cmdhelpchk_phase2_crosswalk_v0.json"
HOTFIX004_PROMOTION_JSON = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.json"
HOTFIX004_ARCH_JSON = REPORT_DIR / "source_contract_hotfix004_arch_intake_record.json"

OUT_MD = REPORT_DIR / "cmdhelpchk_phase2_promotion_gate_v0.md"
OUT_CSV = REPORT_DIR / "cmdhelpchk_phase2_promotion_gate_v0.csv"
OUT_JSON = REPORT_DIR / "cmdhelpchk_phase2_promotion_gate_v0.json"


@dataclass
class GateRow:
    gate_id: str
    gate_name: str
    gate_type: str
    status: str
    priority: str
    current_evidence: str
    condition_to_open: str
    current_blocker: str
    allowed_now: bool
    requires_explicit_authorization: bool
    recommended_next_action: str
    rationale: str


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def get_summary(data: dict[str, Any]) -> dict[str, Any]:
    summary = data.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "pass"}


def num(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def make_gates(
    canary_validation: dict[str, Any],
    canary_plan: dict[str, Any],
    warning_classifier: dict[str, Any],
    crosswalk: dict[str, Any],
    hotfix_promotion: dict[str, Any],
    arch: dict[str, Any],
) -> list[GateRow]:
    validation_status = str(canary_validation.get("validation_status", ""))
    failed_checks = num(canary_validation.get("failed_checks", 0))
    warning_checks = num(canary_validation.get("warning_checks", 0))

    source_repair_count = num(warning_classifier.get("source_repair_recommended", 0))
    critical_stop_count = num(warning_classifier.get("critical_stop_count", 0))
    classifier_status = str(warning_classifier.get("classifier_status", ""))

    canary_plan_status = str(canary_plan.get("canary_plan_status", ""))
    crosswalk_status = str(crosswalk.get("crosswalk_status", ""))

    help_artifact_count = 0
    stale_evidence_count = 0
    policy_review_count = 0
    lane_counts = warning_classifier.get("phase2_lane_counts", {})
    if isinstance(lane_counts, dict):
        help_artifact_count = num(lane_counts.get("HELP_ARTIFACT_REVIEW", 0))
        stale_evidence_count = num(lane_counts.get("STALE_EVIDENCE", 0))
        policy_review_count = num(lane_counts.get("POLICY_REVIEW", 0))

    hotfix_status = str(hotfix_promotion.get("promotion_review_status", ""))
    hotfix_version = str(hotfix_promotion.get("inventory_probe_version", ""))
    hotfix_source_repair = num(hotfix_promotion.get("source_repair_recommended", 0))
    arch_status = str(arch.get("arch_intake_status", ""))

    gates: list[GateRow] = []

    report_only_open = (
        validation_status == "PASS"
        and failed_checks == 0
        and source_repair_count == 0
        and critical_stop_count == 0
        and "GENERATED" in classifier_status
        and "GENERATED" in canary_plan_status
    )

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-001",
        gate_name="report_only_phase2_continuation",
        gate_type="report_only",
        status="OPEN" if report_only_open else "HOLD",
        priority="HIGH",
        current_evidence=f"validation_status={validation_status}; failed_checks={failed_checks}; source_repair={source_repair_count}; critical_stop={critical_stop_count}",
        condition_to_open="Canary validation PASS, failed checks 0, source repair recommended 0, critical stop count 0.",
        current_blocker="" if report_only_open else "One or more report-only preconditions are missing.",
        allowed_now=report_only_open,
        requires_explicit_authorization=False,
        recommended_next_action="Continue report-only probes such as HELP artifact name alignment and cmd_help evidence refresh." if report_only_open else "Resolve failed report-only preconditions.",
        rationale="Report-only work may continue when evidence is coherent and non-mutating.",
    ))

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-002",
        gate_name="source_repair_gate",
        gate_type="mutation",
        status="CLOSED",
        priority="CRITICAL",
        current_evidence=f"source_repair_recommended={source_repair_count}; hotfix004_source_repair={hotfix_source_repair}",
        condition_to_open="Separate explicit human authorization after source freshness, classifier review, and patch proposal review.",
        current_blocker="No source repairs are authorized from classification, crosswalk, canary, or promotion-gate evidence.",
        allowed_now=False,
        requires_explicit_authorization=True,
        recommended_next_action="Keep source repair path closed.",
        rationale="Classification cannot authorize source edits.",
    ))

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-003",
        gate_name="help_data_rebuild_gate",
        gate_type="mutation",
        status="CLOSED",
        priority="CRITICAL",
        current_evidence=f"HELP_ARTIFACT_REVIEW rows={help_artifact_count}; stale_evidence={stale_evidence_count}; policy_review={policy_review_count}",
        condition_to_open="HELP artifact coverage/name alignment is reviewed, stale evidence is refreshed/explained, CMDHELP family scope is decided, and explicit rebuild authorization is given.",
        current_blocker="High-priority HELP artifact coverage and stale-evidence canaries are planned, not executed.",
        allowed_now=False,
        requires_explicit_authorization=True,
        recommended_next_action="Build HELP artifact name-alignment probe and cmd_help evidence refresh probe before considering rebuild.",
        rationale="HELP DATA rebuild must not happen while coverage/freshness questions are still open.",
    ))

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-004",
        gate_name="cmdhelpchk_mutation_gate",
        gate_type="mutation",
        status="CLOSED",
        priority="CRITICAL",
        current_evidence=f"crosswalk_status={crosswalk_status}; classifier_status={classifier_status}; canary_validation={validation_status}",
        condition_to_open="A later explicit implementation plan identifies required CMDHELPCHK changes, review passes, and mutation is authorized.",
        current_blocker="Current Phase 2 artifacts are report-only visibility/classification/planning tools.",
        allowed_now=False,
        requires_explicit_authorization=True,
        recommended_next_action="Do not modify CMDHELPCHK runtime logic yet.",
        rationale="CMDHELPCHK should not mutate until crosswalk warnings are understood and canaries are executable/reviewed.",
    ))

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-005",
        gate_name="v1_1_source_contract_default_promotion_gate",
        gate_type="authority_promotion",
        status="CLOSED",
        priority="HIGH",
        current_evidence=f"hotfix_version={hotfix_version}; promotion_review_status={hotfix_status}; arch_status={arch_status}",
        condition_to_open="Explicit promotion decision updates manifests/default authority after review of warning/canary implications.",
        current_blocker="v1.1-hotfix_004_writer_binding is reviewed-candidate-not-default.",
        allowed_now=False,
        requires_explicit_authorization=True,
        recommended_next_action="Keep v1.1 hotfix004 as reviewed candidate, not default.",
        rationale="Reviewed evidence is not the same as default authority.",
    ))

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-006",
        gate_name="help_artifact_name_alignment_gate",
        gate_type="report_only_subgate",
        status="OPEN" if help_artifact_count > 0 else "NOT_NEEDED",
        priority="HIGH",
        current_evidence=f"HELP_ARTIFACT_REVIEW rows={help_artifact_count}",
        condition_to_open="At least one HELP_ARTIFACT_REVIEW row exists and source repair count remains 0.",
        current_blocker="" if help_artifact_count > 0 and source_repair_count == 0 else "No HELP artifact rows or source repair guard failed.",
        allowed_now=help_artifact_count > 0 and source_repair_count == 0,
        requires_explicit_authorization=False,
        recommended_next_action="Build cmdhelpchk_phase2_help_artifact_name_alignment_probe_v0.",
        rationale="The nine accepted Batch 0 commands need HELP artifact coverage/name matching review, not source repair.",
    ))

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-007",
        gate_name="cmd_help_stale_evidence_refresh_gate",
        gate_type="report_only_subgate",
        status="OPEN" if stale_evidence_count > 0 else "NOT_NEEDED",
        priority="HIGH",
        current_evidence=f"STALE_EVIDENCE rows={stale_evidence_count}",
        condition_to_open="Stale evidence row exists and source repair count remains 0.",
        current_blocker="" if stale_evidence_count > 0 and source_repair_count == 0 else "No stale evidence row or source repair guard failed.",
        allowed_now=stale_evidence_count > 0 and source_repair_count == 0,
        requires_explicit_authorization=False,
        recommended_next_action="Build cmdhelpchk_phase2_cmd_help_evidence_refresh_probe_v0.",
        rationale="cmd_help.cpp must remain stale-evidence/do-not-repair until freshness is explained.",
    ))

    gates.append(GateRow(
        gate_id="CMDHELPCHK-P2-GATE-008",
        gate_name="cmdhelp_family_contract_scope_gate",
        gate_type="report_only_subgate",
        status="OPEN" if policy_review_count > 0 else "NOT_NEEDED",
        priority="HIGH",
        current_evidence=f"POLICY_REVIEW rows={policy_review_count}",
        condition_to_open="CMDHELP family-level backlog exists and source repair count remains 0.",
        current_blocker="" if policy_review_count > 0 and source_repair_count == 0 else "No policy-review row or source repair guard failed.",
        allowed_now=policy_review_count > 0 and source_repair_count == 0,
        requires_explicit_authorization=False,
        recommended_next_action="Build cmdhelpchk_phase2_cmdhelp_family_scope_plan_v0.",
        rationale="cmdhelp.cpp needs family-level scope planning, not simple command repair.",
    ))

    return gates


def write_csv(path: Path, rows: list[GateRow]) -> None:
    fields = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_md(path: Path, summary: dict[str, Any], rows: list[GateRow]) -> None:
    lines = [
        "# CMDHELPCHK Phase 2 Promotion Gate v0",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / PROMOTION_GATE_PLAN_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"promotion gate status: {summary['promotion_gate_status']}",
        f"report_only_continuation_allowed: {summary['report_only_continuation_allowed']}",
        f"mutation_gates_open: {summary['mutation_gates_open']}",
        f"source_repair_authorized: {summary['source_repair_authorized']}",
        f"help_data_rebuild_authorized: {summary['help_data_rebuild_authorized']}",
        f"cmdhelpchk_changes_authorized: {summary['cmdhelpchk_changes_authorized']}",
        f"v1_1_default_promotion_authorized: {summary['v1_1_default_promotion_authorized']}",
        "```",
        "",
        "## Gate table",
        "",
        "| Gate | Type | Status | Allowed now | Requires explicit authorization | Next action |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.gate_name)}` | `{md_escape(row.gate_type)}` | `{md_escape(row.status)}` | "
            f"{row.allowed_now} | {row.requires_explicit_authorization} | {md_escape(row.recommended_next_action)} |"
        )

    lines += [
        "",
        "## Closed mutation gates",
        "",
    ]
    for row in rows:
        if row.gate_type in {"mutation", "authority_promotion"}:
            lines += [
                f"### {row.gate_id} — {row.gate_name}",
                "",
                f"- Status: `{row.status}`",
                f"- Current evidence: `{row.current_evidence}`",
                f"- Condition to open: {row.condition_to_open}",
                f"- Current blocker: {row.current_blocker}",
                f"- Rationale: {row.rationale}",
                "",
            ]

    lines += [
        "## Open report-only subgates",
        "",
    ]
    for row in rows:
        if row.gate_type == "report_only_subgate" and row.status == "OPEN":
            lines += [
                f"- `{row.gate_name}`: {row.recommended_next_action}",
            ]

    lines += [
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
        "## Recommended next action",
        "",
        summary["recommended_next_action"],
        "",
        "## Inputs checked",
        "",
    ]
    for item in summary["inputs_checked"]:
        lines.append(f"- `{md_escape(item['path'])}`: `{item['state']}`")

    lines += [
        "",
        "## Non-mutation confirmation",
        "",
    ]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    canary_validation = get_summary(read_json(root / CANARY_VALIDATION_JSON))
    canary_plan = get_summary(read_json(root / CANARY_PLAN_JSON))
    warning_classifier = get_summary(read_json(root / WARNING_CLASSIFIER_JSON))
    crosswalk = get_summary(read_json(root / CROSSWALK_JSON))
    hotfix_promotion = get_summary(read_json(root / HOTFIX004_PROMOTION_JSON))
    arch = get_summary(read_json(root / HOTFIX004_ARCH_JSON))

    gates = make_gates(
        canary_validation=canary_validation,
        canary_plan=canary_plan,
        warning_classifier=warning_classifier,
        crosswalk=crosswalk,
        hotfix_promotion=hotfix_promotion,
        arch=arch,
    )

    report_gate = next((g for g in gates if g.gate_name == "report_only_phase2_continuation"), None)
    report_allowed = bool(report_gate and report_gate.status == "OPEN")

    mutation_gates_open = [g for g in gates if g.gate_type in {"mutation", "authority_promotion"} and g.status == "OPEN"]
    open_report_subgates = [g for g in gates if g.gate_type == "report_only_subgate" and g.status == "OPEN"]

    if not canary_validation:
        status = "HOLD_NO_CANARY_VALIDATION_INPUT"
        next_action = "Run cmdhelpchk_phase2_canary_validation_v0.py first."
    elif mutation_gates_open:
        status = "STOP_MUTATION_GATE_OPEN_UNEXPECTEDLY"
        next_action = "Stop; no mutation gate should open from this report-only plan."
    elif report_allowed:
        status = "REPORT_ONLY_PROMOTION_GATE_PLAN_GENERATED"
        next_action = "Proceed only with open report-only subgates: " + "; ".join(g.recommended_next_action for g in open_report_subgates)
    else:
        status = "HOLD_REPORT_ONLY_GATE_NOT_OPEN"
        next_action = "Resolve canary validation or classifier inputs before further Phase 2 work."

    inputs = [
        {"path": str(root / CANARY_VALIDATION_JSON), "state": "present" if (root / CANARY_VALIDATION_JSON).is_file() else "missing"},
        {"path": str(root / CANARY_VALIDATION_CSV), "state": "present" if (root / CANARY_VALIDATION_CSV).is_file() else "missing"},
        {"path": str(root / CANARY_PLAN_JSON), "state": "present" if (root / CANARY_PLAN_JSON).is_file() else "missing"},
        {"path": str(root / WARNING_CLASSIFIER_JSON), "state": "present" if (root / WARNING_CLASSIFIER_JSON).is_file() else "missing"},
        {"path": str(root / CROSSWALK_JSON), "state": "present" if (root / CROSSWALK_JSON).is_file() else "missing"},
        {"path": str(root / HOTFIX004_PROMOTION_JSON), "state": "present" if (root / HOTFIX004_PROMOTION_JSON).is_file() else "missing"},
        {"path": str(root / HOTFIX004_ARCH_JSON), "state": "present" if (root / HOTFIX004_ARCH_JSON).is_file() else "missing"},
    ]

    summary = {
        "generated_at_utc": now(),
        "status": "REPORT_ONLY_PROMOTION_GATE_GENERATED",
        "promotion_gate_status": status,
        "report_only_continuation_allowed": report_allowed,
        "open_report_only_subgates": [asdict(g) for g in open_report_subgates],
        "mutation_gates_open": len(mutation_gates_open),
        "source_repair_authorized": False,
        "dbf_writes_authorized": False,
        "help_data_rebuild_authorized": False,
        "cmdhelpchk_changes_authorized": False,
        "v1_1_default_promotion_authorized": False,
        "canary_validation_status": canary_validation.get("validation_status", ""),
        "classifier_status": warning_classifier.get("classifier_status", ""),
        "crosswalk_status": crosswalk.get("crosswalk_status", ""),
        "hotfix004_promotion_review_status": hotfix_promotion.get("promotion_review_status", ""),
        "arch_intake_status": arch.get("arch_intake_status", ""),
        "interpretation": "This promotion gate does not promote or mutate anything. It opens only report-only subgates where evidence says further investigation is safe. Mutation gates remain closed until a separate explicit human authorization and a later implementation plan.",
        "recommended_next_action": next_action,
        "inputs_checked": inputs,
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

    write_csv(root / OUT_CSV, gates)
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "gates": [asdict(g) for g in gates]}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary, gates)

    print("CMDHELPCHK Phase 2 promotion gate v0 complete.")
    print(f"Promotion gate status: {status}")
    print(f"Report-only continuation allowed: {report_allowed}")
    print(f"Mutation gates open: {len(mutation_gates_open)}")
    print(f"Open report-only subgates: {len(open_report_subgates)}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if status == "REPORT_ONLY_PROMOTION_GATE_PLAN_GENERATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

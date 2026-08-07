#!/usr/bin/env python3
"""
cmdhelpchk_phase2_canary_plan_v0.py

REPORT_ONLY / CANARY_PLAN_ONLY probe for CMDHELPCHK Phase 2.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_v0.json
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_warning_classifier_priority_v0.md

Writes:
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_plan_v0.md
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_plan_v0.csv
    dottalkpp\docs\generated\reports\cmdhelpchk_phase2_canary_plan_v0.json

Purpose:
    Convert classified CMDHELPCHK Phase 2 warning lanes into a small, reviewable
    canary plan. The plan defines what must be checked before any future
    CMDHELPCHK Phase 2 promotion, HELP artifact action, HELP DATA rebuild,
    or source-contract default promotion.

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
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"

CLASSIFIER_CSV = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.csv"
CLASSIFIER_JSON = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_v0.json"
CLASSIFIER_PRIORITY_MD = REPORT_DIR / "cmdhelpchk_phase2_warning_classifier_priority_v0.md"

OUT_MD = REPORT_DIR / "cmdhelpchk_phase2_canary_plan_v0.md"
OUT_CSV = REPORT_DIR / "cmdhelpchk_phase2_canary_plan_v0.csv"
OUT_JSON = REPORT_DIR / "cmdhelpchk_phase2_canary_plan_v0.json"


@dataclass
class CanaryItem:
    canary_id: str
    lane: str
    family: str
    scope: str
    priority: str
    status: str
    source_rows: int
    representative_tokens: str
    representative_paths: str
    pass_condition: str
    fail_condition: str
    recommended_next_action: str
    mutation_authorized: bool
    rationale: str


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def sample_values(rows: list[dict[str, str]], field: str, limit: int = 12) -> str:
    values = []
    seen = set()
    for row in rows:
        value = row.get(field, "")
        if value and value not in seen:
            values.append(value)
            seen.add(value)
        if len(values) >= limit:
            break
    if not values:
        return ""
    suffix = "" if len(seen) <= limit else " ..."
    return ", ".join(values) + suffix


def rows_where(rows: list[dict[str, str]], **conds: str) -> list[dict[str, str]]:
    out = []
    for row in rows:
        ok = True
        for key, value in conds.items():
            if row.get(key, "") != value:
                ok = False
                break
        if ok:
            out.append(row)
    return out


def build_canaries(rows: list[dict[str, str]], classifier_summary: dict[str, Any]) -> list[CanaryItem]:
    canaries: list[CanaryItem] = []

    source_repair_rows = [r for r in rows if b(r.get("source_repair_recommended", False))]
    canaries.append(CanaryItem(
        canary_id="CMDHELPCHK-P2-CANARY-001",
        lane="GLOBAL_MUTATION_GUARD",
        family="non_mutation_guard",
        scope="all classified warning rows",
        priority="CRITICAL",
        status="PASS" if not source_repair_rows else "FAIL",
        source_rows=len(rows),
        representative_tokens=sample_values(source_repair_rows, "token") if source_repair_rows else "",
        representative_paths=sample_values(source_repair_rows, "path") if source_repair_rows else "",
        pass_condition="No row recommends source repair and all mutation authorization fields remain false.",
        fail_condition="Any row recommends source repair or any report authorizes DBF writes, HELP rebuild, CMDHELPCHK mutation, or v1.1 default promotion.",
        recommended_next_action="Continue report-only planning if PASS; stop and review immediately if FAIL.",
        mutation_authorized=False,
        rationale="Classification can recommend investigation, but it cannot authorize mutation.",
    ))

    batch0 = rows_where(rows, phase2_lane="HELP_ARTIFACT_REVIEW")
    canaries.append(CanaryItem(
        canary_id="CMDHELPCHK-P2-CANARY-002",
        lane="HELP_ARTIFACT_REVIEW",
        family="generated_help_artifact_coverage",
        scope="accepted simple command contracts with no HELP artifact match",
        priority="HIGH",
        status="PLANNED",
        source_rows=len(batch0),
        representative_tokens=sample_values(batch0, "token"),
        representative_paths=sample_values(batch0, "path"),
        pass_condition="Each accepted command is resolved to an existing generated HELP/DOTHELP/CMDHELP artifact, or the naming/coverage rule explains the missing match.",
        fail_condition="Any accepted command is treated as a source repair target merely because a generated HELP artifact was not matched.",
        recommended_next_action="Build a HELP artifact lookup/name-alignment probe before any HELP DATA rebuild.",
        mutation_authorized=False,
        rationale="The nine Batch 0 rows are source-confirmed/do-not-repair; their open issue is generated HELP artifact coverage or naming.",
    ))

    stale = rows_where(rows, phase2_lane="STALE_EVIDENCE")
    canaries.append(CanaryItem(
        canary_id="CMDHELPCHK-P2-CANARY-003",
        lane="STALE_EVIDENCE",
        family="evidence_freshness",
        scope="stale evidence rows",
        priority="HIGH",
        status="PLANNED",
        source_rows=len(stale),
        representative_tokens=sample_values(stale, "token"),
        representative_paths=sample_values(stale, "path"),
        pass_condition="Stale row source hash/timestamp is refreshed or discrepancy is explained without source repair.",
        fail_condition="Stale evidence is promoted, repaired, or used as authority without refresh/explanation.",
        recommended_next_action="Build a focused cmd_help.cpp evidence refresh probe.",
        mutation_authorized=False,
        rationale="cmd_help.cpp remains stale evidence/do-not-repair; freshness must be resolved before authority decisions.",
    ))

    family = [r for r in rows if r.get("phase2_policy_family") == "command_family_usage_contract_backlog"]
    canaries.append(CanaryItem(
        canary_id="CMDHELPCHK-P2-CANARY-004",
        lane="POLICY_REVIEW",
        family="command_family_usage_contract_backlog",
        scope="family-level command usage contract backlog",
        priority="HIGH",
        status="PLANNED",
        source_rows=len(family),
        representative_tokens=sample_values(family, "token"),
        representative_paths=sample_values(family, "path"),
        pass_condition="Family-level CMDHELP contract scope is documented as a backlog item, not a simple command repair.",
        fail_condition="cmdhelp.cpp is flattened into ordinary command repair or auto-patched.",
        recommended_next_action="Plan a CMDHELP family-level usage contract separately from mechanical shape repair.",
        mutation_authorized=False,
        rationale="CMDHELP is a HELP builder/app subsystem and needs family-level treatment.",
    ))

    shape = rows_where(rows, phase2_lane="SOURCE_CONTRACT_SHAPE_REVIEW")
    canaries.append(CanaryItem(
        canary_id="CMDHELPCHK-P2-CANARY-005",
        lane="SOURCE_CONTRACT_SHAPE_REVIEW",
        family="shape_review_not_repair",
        scope="shape-review warning rows",
        priority="MEDIUM",
        status="PLANNED",
        source_rows=len(shape),
        representative_tokens=sample_values(shape, "token"),
        representative_paths=sample_values(shape, "path"),
        pass_condition="Shape-review rows are routed to planning/triage and not treated as source repair authority.",
        fail_condition="Shape-review rows generate repair patches without human review and source freshness checks.",
        recommended_next_action="Use existing shape-review planning lane; do not combine with HELP artifact coverage work.",
        mutation_authorized=False,
        rationale="Shape review is a classification state, not source repair authorization.",
    ))

    infra = rows_where(rows, phase2_lane="INTENTIONAL_EXCEPTION")
    canaries.append(CanaryItem(
        canary_id="CMDHELPCHK-P2-CANARY-006",
        lane="INTENTIONAL_EXCEPTION",
        family="command_infrastructure_or_helper",
        scope="infrastructure/helper/registry/dispatcher rows",
        priority="LOW",
        status="PASS" if infra else "REVIEW",
        source_rows=len(infra),
        representative_tokens=sample_values(infra, "token"),
        representative_paths=sample_values(infra, "path"),
        pass_condition="Infrastructure rows remain outside ordinary simple-command HELP obligations.",
        fail_condition="Infrastructure rows are reintroduced as missing simple command HELP rows.",
        recommended_next_action="Keep alternate contract/helper lane stable.",
        mutation_authorized=False,
        rationale="The shell, registry, helpers, and dispatch glue are architecture surfaces, not simple commands.",
    ))

    api = rows_where(rows, phase2_lane="API_OR_HEADER_CONTRACT_REVIEW")
    engine = rows_where(rows, phase2_lane="METADATA_OR_ENGINE_CONTRACT_REVIEW")
    ui = rows_where(rows, phase2_lane="UI_OR_BROWSER_CONTRACT_REVIEW")
    manual = rows_where(rows, phase2_lane="MANUAL_CLASSIFICATION")
    broad_count = len(api) + len(engine) + len(ui) + len(manual)
    canaries.append(CanaryItem(
        canary_id="CMDHELPCHK-P2-CANARY-007",
        lane="BROAD_BACKLOG_REVIEW",
        family="api_engine_ui_manual_backlog",
        scope="non-simple-command backlog lanes",
        priority="MEDIUM",
        status="PLANNED",
        source_rows=broad_count,
        representative_tokens=sample_values(api + engine + ui + manual, "token"),
        representative_paths=sample_values(api + engine + ui + manual, "path"),
        pass_condition="Broad backlog stays classified by family and does not block near-term canary validation.",
        fail_condition="Broad backlog is collapsed back into unclassified noise or repair pressure.",
        recommended_next_action="Sample representative rows from each broad backlog family in later batches.",
        mutation_authorized=False,
        rationale="Large counts are expected because the crosswalk scanned all 899 inventory rows, not only user command files.",
    ))

    return canaries


def write_csv(path: Path, rows: list[CanaryItem]) -> None:
    fields = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_md(path: Path, summary: dict[str, Any], rows: list[CanaryItem]) -> None:
    lines = [
        "# CMDHELPCHK Phase 2 Canary Plan v0",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / CANARY_PLAN_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"canary plan status: {summary['canary_plan_status']}",
        f"source classifier rows reviewed: {summary['classifier_rows_reviewed']}",
        f"canaries planned: {summary['canaries_planned']}",
        f"source_repair_recommended in classifier: {summary['source_repair_recommended']}",
        f"critical_stop_count in classifier: {summary['critical_stop_count']}",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "source repairs: NOT AUTHORIZED",
        "v1.1 default promotion: NOT AUTHORIZED",
        "```",
        "",
        "## Canary status counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in summary["canary_status_counts"].items():
        lines.append(f"| `{md_escape(status)}` | {count} |")

    lines += [
        "",
        "## Canary items",
        "",
        "| Canary | Lane | Family | Priority | Status | Rows | Pass condition | Next action |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{md_escape(row.canary_id)}` | `{md_escape(row.lane)}` | `{md_escape(row.family)}` | "
            f"`{md_escape(row.priority)}` | `{md_escape(row.status)}` | {row.source_rows} | "
            f"{md_escape(row.pass_condition)} | {md_escape(row.recommended_next_action)} |"
        )

    lines += [
        "",
        "## Representative details",
        "",
    ]
    for row in rows:
        lines += [
            f"### {row.canary_id}",
            "",
            f"- Lane: `{row.lane}`",
            f"- Family: `{row.family}`",
            f"- Scope: {row.scope}",
            f"- Representative tokens: `{row.representative_tokens}`",
            f"- Representative paths: `{row.representative_paths}`",
            f"- Fail condition: {row.fail_condition}",
            f"- Mutation authorized: `{str(row.mutation_authorized).lower()}`",
            f"- Rationale: {row.rationale}",
            "",
        ]

    lines += [
        "## Interpretation",
        "",
        summary["interpretation"],
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
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    classifier_rows = read_csv_rows(root / CLASSIFIER_CSV)
    classifier_json = read_json(root / CLASSIFIER_JSON)
    classifier_summary = classifier_json.get("summary", {}) if isinstance(classifier_json.get("summary", {}), dict) else {}

    canaries = build_canaries(classifier_rows, classifier_summary)

    status_counts = Counter(c.status for c in canaries)
    priority_counts = Counter(c.priority for c in canaries)

    if not classifier_rows:
        canary_status = "HOLD_NO_WARNING_CLASSIFIER_INPUT"
        next_action = "Run cmdhelpchk_phase2_warning_classifier_v0.py first."
    elif any(c.status == "FAIL" for c in canaries):
        canary_status = "STOP_CANARY_FAILURE_REVIEW_REQUIRED"
        next_action = "Review failed canary before continuing."
    else:
        canary_status = "REPORT_ONLY_CANARY_PLAN_GENERATED"
        next_action = "Build `cmdhelpchk_phase2_canary_validation_v0` or a focused HELP artifact coverage probe for the nine accepted command rows."

    summary = {
        "generated_at_utc": now(),
        "status": "REPORT_ONLY_CANARY_PLAN_GENERATED",
        "canary_plan_status": canary_status,
        "classifier_status": classifier_summary.get("classifier_status", ""),
        "source_contract_inventory_version": classifier_summary.get("source_contract_inventory_version", ""),
        "classifier_rows_reviewed": len(classifier_rows),
        "canaries_planned": len(canaries),
        "source_repair_recommended": classifier_summary.get("source_repair_recommended", 0),
        "critical_stop_count": classifier_summary.get("critical_stop_count", 0),
        "canary_status_counts": dict(status_counts.most_common()),
        "canary_priority_counts": dict(priority_counts.most_common()),
        "mutation_authorized": False,
        "source_repair_authorized": False,
        "dbf_writes_authorized": False,
        "help_data_rebuild_authorized": False,
        "cmdhelpchk_changes_authorized": False,
        "v1_1_default_promotion_authorized": False,
        "interpretation": "This canary plan converts warning-classifier lanes into a small set of reviewable checks. It intentionally separates HELP artifact coverage, stale evidence, family-level CMDHELP scope, shape review, intentional infrastructure exceptions, and broad backlog classification. It is a plan only and does not authorize mutation.",
        "recommended_next_action": next_action,
        "inputs_checked": [
            {"path": str(root / CLASSIFIER_CSV), "state": "present" if (root / CLASSIFIER_CSV).is_file() else "missing"},
            {"path": str(root / CLASSIFIER_JSON), "state": "present" if (root / CLASSIFIER_JSON).is_file() else "missing"},
            {"path": str(root / CLASSIFIER_PRIORITY_MD), "state": "present" if (root / CLASSIFIER_PRIORITY_MD).is_file() else "missing"},
        ],
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

    write_csv(root / OUT_CSV, canaries)
    (root / OUT_JSON).write_text(json.dumps({"summary": summary, "canaries": [asdict(c) for c in canaries]}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary, canaries)

    print("CMDHELPCHK Phase 2 canary plan v0 complete.")
    print(f"Canary plan status: {canary_status}")
    print(f"Classifier rows reviewed: {len(classifier_rows)}")
    print(f"Canaries planned: {len(canaries)}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_JSON}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if canary_status == "REPORT_ONLY_CANARY_PLAN_GENERATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

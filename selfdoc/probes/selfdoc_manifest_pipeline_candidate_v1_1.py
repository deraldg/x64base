#!/usr/bin/env python3
"""
selfdoc_manifest_pipeline_candidate_v1_1.py

PLAN_ONLY / REPORT_ONLY manifest-pipeline candidate update.

Run from:
    D:\code\ccode

Reads:
    selfdoc\tool_manifest.yaml
    selfdoc\pipeline_manifest.yaml
    dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_promotion_candidate_report.json

Writes:
    selfdoc\tool_manifest_candidate_v1_1.yaml
    selfdoc\pipeline_manifest_candidate_v1_1.yaml
    dottalkpp\docs\generated\reports\selfdoc_manifest_pipeline_candidate_v1_1.md
    dottalkpp\docs\generated\reports\selfdoc_manifest_pipeline_candidate_v1_1.json

Safety:
    PLAN_ONLY / REPORT_ONLY
    Does not overwrite existing manifests.
    Does not promote v1.1 to default.
    Does not edit source.
    Does not write DBFs.
    Does not modify CMDHELPCHK.
    Does not rebuild HELP DATA.
    Does not repair headers.
    Does not move/delete files.

Purpose:
    Record source_contract_inventory_probe_v1_1.py as
    PROMOTION_CANDIDATE_DOCUMENTED_NOT_DEFAULT.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"

INPUT_TOOL_MANIFEST = Path("selfdoc") / "tool_manifest.yaml"
INPUT_PIPELINE_MANIFEST = Path("selfdoc") / "pipeline_manifest.yaml"
PROMO_REPORT_JSON = REPORT_DIR / "source_contract_inventory_v1_1_promotion_candidate_report.json"

OUT_TOOL_CANDIDATE = Path("selfdoc") / "tool_manifest_candidate_v1_1.yaml"
OUT_PIPELINE_CANDIDATE = Path("selfdoc") / "pipeline_manifest_candidate_v1_1.yaml"
OUT_MD = REPORT_DIR / "selfdoc_manifest_pipeline_candidate_v1_1.md"
OUT_JSON = REPORT_DIR / "selfdoc_manifest_pipeline_candidate_v1_1.json"

STATUS = "PROMOTION_CANDIDATE_DOCUMENTED_NOT_DEFAULT"


def read_text_if_exists(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": f"{type(exc).__name__}: {exc}"}


def yaml_block_scalar(text: str, indent: int = 4) -> str:
    prefix = " " * indent
    if not text:
        return prefix + "''"
    lines = text.splitlines()
    return "|\n" + "\n".join(prefix + line for line in lines)


def build_tool_candidate(root: Path, promo: dict[str, Any], timestamp: str) -> str:
    summary = promo.get("summary", {}) if isinstance(promo.get("summary", {}), dict) else {}
    candidate_rows = promo.get("candidate_rows", []) if isinstance(promo.get("candidate_rows", []), list) else []

    rows_summary = []
    for row in candidate_rows:
        path = row.get("path", "")
        approved_role = row.get("approved_role", "")
        approved_family = row.get("approved_family", "")
        approved_action = row.get("approved_action", "")
        rows_summary.append(f"      - path: {path}\n        approved_role: {approved_role}\n        approved_family: {approved_family}\n        approved_action: {approved_action}")

    row_text = "\n".join(rows_summary) if rows_summary else "      []"

    return f"""# SelfDoc tool manifest candidate v1.1
# Generated UTC: {timestamp}
# PLAN_ONLY / REPORT_ONLY candidate.
# This file does not replace selfdoc/tool_manifest.yaml.
# v1.1 is documented as a promotion candidate, not as the default tool.

manifest_kind: selfdoc_tool_manifest_candidate
manifest_version: v1_1_candidate
status: {STATUS}
project_root: D:\\code\\ccode
default_promotion_authorized: false
source_repairs_authorized: false
dbf_writes_authorized: false
cmdhelpchk_changes_authorized: false

tools:
  - id: source_contract_inventory_probe_v0
    path: selfdoc/probes/source_contract_inventory_probe.py
    safety_class: REPORT_ONLY
    lifecycle_class: PROMOTED_BASELINE
    role: baseline source-contract inventory probe
    default_for: source_contract_inventory
    outputs:
      - dottalkpp/docs/generated/reports/source_contracts_inventory.md
      - dottalkpp/docs/generated/reports/source_contracts_inventory.csv
      - dottalkpp/docs/generated/reports/source_contracts_inventory.json

  - id: source_contract_inventory_probe_v1_1
    path: selfdoc/probes/source_contract_inventory_probe_v1_1.py
    safety_class: REPORT_ONLY
    lifecycle_class: PROMOTION_CANDIDATE
    status: {STATUS}
    role: source-contract inventory candidate with v1.1 vocabulary and command-scope roles
    default_for: null
    promotion_note: >
      Candidate is approved with scope notes but is not the default probe.
      Human review accepted refined roles for shell core, command registry,
      HELP subsystem, helpers, and expression/function API surfaces.
    promotion_evidence:
      - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_candidate_report.md
      - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_candidate_report.csv
      - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_candidate_report.json
    reads:
      - src/
      - include/
      - dottalkpp/docs/generated/reports/source_contract_extension_vocabulary_v1_1.csv
      - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_classifier_gap_review.csv
    outputs:
      - dottalkpp/docs/generated/reports/source_contracts_inventory_v1_1.md
      - dottalkpp/docs/generated/reports/source_contracts_inventory_v1_1.csv
      - dottalkpp/docs/generated/reports/source_contracts_inventory_v1_1.json
      - dottalkpp/docs/generated/reports/source_contract_inventory_v0_vs_v1_1.md
    non_mutation_guards:
      - no_source_edits
      - no_dbf_writes
      - no_cmdhelpchk_changes
      - no_help_data_rebuild
      - no_header_repairs
      - no_file_moves_or_deletes
      - v0_probe_preserved
      - v0_reports_preserved
    promotion_gate:
      v0_v1_1_comparison_reviewed: true
      vocabulary_gap_closed: true
      scope_corrections_human_reviewed: true
      false_positives_classified: true
      default_promotion_authorized: false
      next_required_step: shape_review_plan_or_manifest_review

  - id: source_contract_inventory_v1_1_classifier_gap_review
    path: selfdoc/probes/source_contract_inventory_v1_1_classifier_gap_review.py
    safety_class: REPORT_ONLY
    lifecycle_class: PROMOTION_SUPPORT
    role: compare v1.1 output against draft and detect classifier regressions
    outputs:
      - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_classifier_gap_review.md
      - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_classifier_gap_review.csv
      - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_classifier_gap_review.json

  - id: source_contract_inventory_v1_1_promotion_review
    path: selfdoc/probes/source_contract_inventory_v1_1_promotion_review.py
    safety_class: REPORT_ONLY
    lifecycle_class: PROMOTION_SUPPORT
    role: review v1.1 hotfix output for promotion readiness

  - id: source_contract_inventory_v1_1_promotion_candidate_report
    path: selfdoc/probes/source_contract_inventory_v1_1_promotion_candidate_report.py
    safety_class: REPORT_ONLY
    lifecycle_class: PROMOTION_SUPPORT
    role: apply human scope decisions and document v1.1 candidate status

human_scope_decisions:
{row_text}
"""


def build_pipeline_candidate(root: Path, promo: dict[str, Any], timestamp: str) -> str:
    return f"""# SelfDoc pipeline manifest candidate v1.1
# Generated UTC: {timestamp}
# PLAN_ONLY / REPORT_ONLY candidate.
# This file does not replace selfdoc/pipeline_manifest.yaml.
# It documents the candidate pipeline; it does not run or promote anything.

manifest_kind: selfdoc_pipeline_manifest_candidate
manifest_version: v1_1_candidate
status: {STATUS}
project_root: D:\\code\\ccode
default_promotion_authorized: false

gates:
  - id: probe_stability_before_runner
    status: CLOSED_UNTIL_CONDITIONS_MET
    description: >
      selfdoc/selfdoc_run.py must not be created until v1.1 source-contract
      probe has passed comparison review, role/scope vocabulary is accepted,
      report homes are stable, manifests identify probe order, and at least
      two probes have repeatable outputs.
    conditions:
      v1_1_source_contract_probe_passed_comparison_review: true
      role_scope_vocabulary_accepted: true
      report_homes_stable: true
      manifests_identify_probe_order: candidate_only
      at_least_two_probes_have_repeatable_outputs: true
      runner_creation_authorized: false

pipelines:
  - id: source_contracts_v0_baseline
    status: PROMOTED_BASELINE
    default: true
    safety_class: REPORT_ONLY
    steps:
      - id: source_contract_inventory_probe_v0
        tool: selfdoc/probes/source_contract_inventory_probe.py
        outputs:
          - dottalkpp/docs/generated/reports/source_contracts_inventory.md
          - dottalkpp/docs/generated/reports/source_contracts_inventory.csv
          - dottalkpp/docs/generated/reports/source_contracts_inventory.json

  - id: source_contracts_v1_1_candidate
    status: {STATUS}
    default: false
    safety_class: REPORT_ONLY
    description: >
      Candidate source-contract inventory pipeline using v1.1 vocabulary and
      command-scope classifications. This pipeline is documented for review
      but is not the default and must not drive source repairs automatically.
    steps:
      - id: source_contract_inventory_probe_v1_1
        tool: selfdoc/probes/source_contract_inventory_probe_v1_1.py
        outputs:
          - dottalkpp/docs/generated/reports/source_contracts_inventory_v1_1.md
          - dottalkpp/docs/generated/reports/source_contracts_inventory_v1_1.csv
          - dottalkpp/docs/generated/reports/source_contracts_inventory_v1_1.json
          - dottalkpp/docs/generated/reports/source_contract_inventory_v0_vs_v1_1.md

      - id: source_contract_inventory_v1_1_classifier_gap_review
        tool: selfdoc/probes/source_contract_inventory_v1_1_classifier_gap_review.py
        outputs:
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_classifier_gap_review.md
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_classifier_gap_review.csv
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_classifier_gap_review.json

      - id: source_contract_inventory_v1_1_promotion_review
        tool: selfdoc/probes/source_contract_inventory_v1_1_promotion_review.py
        outputs:
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_review.md
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_review.csv
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_review.json

      - id: source_contract_inventory_v1_1_promotion_candidate_report
        tool: selfdoc/probes/source_contract_inventory_v1_1_promotion_candidate_report.py
        outputs:
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_candidate_report.md
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_candidate_report.csv
          - dottalkpp/docs/generated/reports/source_contract_inventory_v1_1_promotion_candidate_report.json

    non_mutation_guards:
      - no_source_edits
      - no_dbf_writes
      - no_help_data_rebuild
      - no_cmdhelpchk_changes
      - no_source_repairs
      - no_data_root_moves
      - no_file_deletes
      - no_default_promotion

next_recommended_pipeline:
  id: source_contract_shape_review_plan_v0
  status: NOT_BUILT
  safety_class: REPORT_ONLY
  purpose: >
    Use corrected v1.1 classification model to group the remaining 73
    shape-review items without repairing source.
"""


def write_md(path: Path, summary: dict[str, Any]) -> None:
    lines = []
    lines.append("# SelfDoc Manifest/Pipeline Candidate v1.1")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `PLAN_ONLY / REPORT_ONLY`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("source_contract_inventory_probe_v1_1: PROMOTION_CANDIDATE_DOCUMENTED_NOT_DEFAULT")
    lines.append("v1.1 default promotion: NOT AUTHORIZED")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Files written")
    lines.append("")
    for output in summary["outputs"]:
        lines.append(f"- `{output}`")
    lines.append("")
    lines.append("## What changed")
    lines.append("")
    lines.append("This generated candidate manifest pair records v1.1 as a documented promotion candidate while preserving v0 as the promoted baseline/default.")
    lines.append("")
    lines.append("## Candidate status")
    lines.append("")
    lines.append(f"- status: `{summary['status']}`")
    lines.append(f"- promotion candidate report present: `{summary['promotion_candidate_report_present']}`")
    lines.append(f"- candidate rows documented: `{summary['candidate_rows']}`")
    lines.append("")
    lines.append("## Probe Stability Before Runner gate")
    lines.append("")
    lines.append("The tiny runner remains blocked. `selfdoc\\selfdoc_run.py` is not created by this package.")
    lines.append("")
    lines.append("## Next recommended action")
    lines.append("")
    lines.append("Build `source_contract_shape_review_plan_v0` using the corrected v1.1 classification model.")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    now = datetime.now(timezone.utc).isoformat()

    promo = load_json_if_exists(root / PROMO_REPORT_JSON)
    promo_summary = promo.get("summary", {}) if isinstance(promo.get("summary", {}), dict) else {}
    candidate_rows = promo.get("candidate_rows", []) if isinstance(promo.get("candidate_rows", []), list) else []

    (root / "selfdoc").mkdir(parents=True, exist_ok=True)
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    tool_candidate = build_tool_candidate(root, promo, now)
    pipeline_candidate = build_pipeline_candidate(root, promo, now)

    (root / OUT_TOOL_CANDIDATE).write_text(tool_candidate, encoding="utf-8", newline="\n")
    (root / OUT_PIPELINE_CANDIDATE).write_text(pipeline_candidate, encoding="utf-8", newline="\n")

    summary = {
        "generated_at_utc": now,
        "status": STATUS,
        "root": str(root),
        "promotion_candidate_report_present": bool((root / PROMO_REPORT_JSON).is_file()),
        "promotion_report_status": promo_summary.get("status", ""),
        "candidate_rows": len(candidate_rows),
        "outputs": [
            str(OUT_TOOL_CANDIDATE),
            str(OUT_PIPELINE_CANDIDATE),
            str(OUT_MD),
            str(OUT_JSON),
        ],
        "non_mutation_guards": [
            "did_not_overwrite_tool_manifest_yaml",
            "did_not_overwrite_pipeline_manifest_yaml",
            "did_not_create_selfdoc_runner",
            "did_not_promote_v1_1_to_default",
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_move_or_delete_files",
        ],
    }

    (root / OUT_JSON).write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")
    write_md(root / OUT_MD, summary)

    print("SelfDoc manifest/pipeline candidate v1.1 complete.")
    print(f"Project root: {root}")
    print(f"Wrote: {OUT_TOOL_CANDIDATE}")
    print(f"Wrote: {OUT_PIPELINE_CANDIDATE}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print("v1.1 was documented as a candidate, not promoted to default.")
    print("Existing manifests were not overwritten.")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    print("selfdoc_run.py was not created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

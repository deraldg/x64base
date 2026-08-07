#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
PROMOTION_JSON = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.json"
PROMOTION_MD = REPORT_DIR / "source_contract_inventory_v1_1_hotfix_004_promotion_review.md"
INV_JSON = REPORT_DIR / "source_contracts_inventory_v1_1.json"
TUNING_JSON = REPORT_DIR / "source_contract_hotfix_004_validation_lane_tuning.json"

OUT_RECORD_MD = REPORT_DIR / "source_contract_hotfix004_arch_intake_record.md"
OUT_RECORD_JSON = REPORT_DIR / "source_contract_hotfix004_arch_intake_record.json"
OUT_DECISION_MD = REPORT_DIR / "ARCH-DECISION-2026-05-16-source-contract-hotfix004.md"

SUBJECT = "source_contract_inventory_v1_1_hotfix_004_writer_binding"
EXPECTED_VERSION = "v1.1-hotfix_004_writer_binding"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def build_decision_record(summary: dict[str, Any]) -> str:
    return f"""# ARCH-DECISION-2026-05-16

Subject: `{SUBJECT}`

## Decision

```text
Reviewed promotion candidate, not default.
Source repairs prohibited.
Next gate: explicit promotion decision.
```

## Authority classification

```text
lane: SelfDoc / source-contract inventory
authority: reviewed evidence / promotion candidate
default authority: not promoted
runtime/data mutation authority: none
source repair authority: none
```

## Evidence summary

- inventory_probe_version: `{summary['inventory_probe_version']}`
- promotion_review_status: `{summary['promotion_review_status']}`
- Batch 0 confirmed: `{summary['batch0_confirmed']}/9`
- Batch 0 false shape-review reduced by: `{summary['batch0_false_shape_review_reduced_by']}`
- cmd_help.cpp stale evidence / do-not-repair: `{summary['cmd_help_stale_evidence_do_not_repair']}`
- source_repair_recommended: `{summary['source_repair_recommended']}`

## Architectural interpretation

The Batch 0 issue is recorded as a scanner/classifier/capture problem, not damaged source. The nine command files are not source-repair targets. The writer-binding hotfix is reviewed as a promotion candidate, but it is not the default authority until a separate explicit promotion decision is made.

## Locked prohibitions

```text
Do not edit the nine Batch 0 source files.
Do not promote v1.1 hotfix 004 to default automatically.
Do not rebuild HELP DATA as a side effect.
Do not write DBFs from the review path.
Do not modify CMDHELPCHK from this decision.
Do not let generated docs outrank their source/runtime evidence.
```

## Next gate

```text
Explicit promotion decision for v1.1-hotfix_004_writer_binding.
Then feed proven facts into DOCSCAN / DOCCHECK / DOCGEN authority lanes.
```
"""


def build_intake_markdown(summary: dict[str, Any], inputs: list[str]) -> str:
    lines = [
        "# Source Contract Hotfix 004 Architecture Intake Record",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY / ARCH_RECORD_ONLY`",
        "",
        "## Verdict",
        "",
        "```text",
        f"arch intake status: {summary['arch_intake_status']}",
        f"subject: {SUBJECT}",
        f"inventory_probe_version: {summary['inventory_probe_version']}",
        f"promotion_review_status: {summary['promotion_review_status']}",
        "default promotion: NOT AUTHORIZED",
        "source repairs: NOT AUTHORIZED",
        "DBF writes: NOT AUTHORIZED",
        "HELP DATA rebuild: NOT AUTHORIZED",
        "CMDHELPCHK changes: NOT AUTHORIZED",
        "```",
        "",
        "## Recorded authority state",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| `status` | `{md_escape(summary['status_recorded'])}` |",
        f"| `default` | `{md_escape(summary['default_state'])}` |",
        f"| `source repair` | `{md_escape(summary['source_repair_state'])}` |",
        f"| `source_repair_recommended` | `{md_escape(summary['source_repair_recommended'])}` |",
        f"| `Batch 0 false shape-review reduced by` | `{md_escape(summary['batch0_false_shape_review_reduced_by'])}` |",
        f"| `cmd_help.cpp` | `{md_escape(summary['cmd_help_state'])}` |",
        "",
        "## Architectural rule reinforced",
        "",
        "```text",
        "Do not repair source when the defect belongs to the scanner.",
        "SelfDoc tooling may evolve.",
        "DotTalk++ runtime/source/data mutation remains gated.",
        "```",
        "",
        "## Recommended next workflow",
        "",
        "```text",
        "1. Keep source-repair path closed for Batch 0.",
        "2. Record this checkpoint in the documentation authority pipeline.",
        "3. Rebuild the documentation authority dashboard when ready.",
        "4. Return to CMDHELPCHK Phase 2 after this checkpoint is recorded.",
        "```",
        "",
        "## Inputs",
        "",
    ]
    for inp in inputs:
        lines.append(f"- `{md_escape(inp)}`")
    lines += ["", "## Non-mutation confirmation", ""]
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{guard}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = Path(".").resolve()
    (root / REPORT_DIR).mkdir(parents=True, exist_ok=True)

    promotion = read_json(root / PROMOTION_JSON)
    promotion_summary = promotion.get("summary", {}) if isinstance(promotion.get("summary", {}), dict) else {}

    inventory = read_json(root / INV_JSON)
    inventory_summary = inventory.get("summary", {}) if isinstance(inventory.get("summary", {}), dict) else {}

    tuning = read_json(root / TUNING_JSON)
    tuning_summary = tuning.get("summary", {}) if isinstance(tuning.get("summary", {}), dict) else {}

    inventory_probe_version = str(
        safe_get(promotion_summary, "inventory_probe_version")
        or safe_get(inventory_summary, "probe_version")
        or safe_get(tuning_summary, "inventory_probe_version")
    )

    promotion_review_status = str(safe_get(promotion_summary, "promotion_review_status", "UNKNOWN"))
    batch0_confirmed = int(safe_get(promotion_summary, "batch0_confirmed", safe_get(tuning_summary, "batch0_tuned_expected_state_met", 0)) or 0)
    reduced_by = int(safe_get(promotion_summary, "batch0_false_shape_review_reduced_by", 0) or 0)
    cmd_help_ok = bool(safe_get(promotion_summary, "cmd_help_stale_evidence_do_not_repair", safe_get(tuning_summary, "cmd_help_stale_evidence_do_not_repair", False)))
    source_repair_recommended = int(safe_get(promotion_summary, "source_repair_recommended", safe_get(tuning_summary, "source_repair_recommended", 0)) or 0)

    evidence_complete = (
        inventory_probe_version == EXPECTED_VERSION
        and batch0_confirmed == 9
        and reduced_by == 9
        and cmd_help_ok
        and source_repair_recommended == 0
    )

    if evidence_complete and promotion_review_status in {"PROMOTION_CANDIDATE_REVIEW_PASSED_NOT_DEFAULT", "PROMOTION_CANDIDATE_APPROVED_WITH_SCOPE_NOTES"}:
        arch_status = "RECORDED_REVIEWED_PROMOTION_CANDIDATE_NOT_DEFAULT"
        status_recorded = "promotion candidate reviewed"
    elif evidence_complete:
        arch_status = "RECORDED_EVIDENCE_COMPLETE_PROMOTION_REVIEW_STATUS_NEEDS_LABEL_REVIEW"
        status_recorded = "evidence complete; review status label should be checked"
    else:
        arch_status = "HOLD_EVIDENCE_INCOMPLETE"
        status_recorded = "hold; evidence incomplete"

    summary = {
        "generated_at_utc": now(),
        "status": "ARCH_RECORD_GENERATED",
        "arch_intake_status": arch_status,
        "subject": SUBJECT,
        "inventory_probe_version": inventory_probe_version,
        "expected_inventory_probe_version": EXPECTED_VERSION,
        "promotion_review_status": promotion_review_status,
        "status_recorded": status_recorded,
        "default_state": "not promoted",
        "source_repair_state": "not authorized",
        "source_repair_recommended": source_repair_recommended,
        "batch0_confirmed": batch0_confirmed,
        "batch0_false_shape_review_reduced_by": reduced_by,
        "cmd_help_stale_evidence_do_not_repair": cmd_help_ok,
        "cmd_help_state": "STALE_EVIDENCE / DO_NOT_REPAIR" if cmd_help_ok else "review required",
        "decision_record": str(root / OUT_DECISION_MD),
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

    inputs = [
        str(root / PROMOTION_JSON),
        str(root / PROMOTION_MD),
        str(root / INV_JSON),
        str(root / TUNING_JSON),
    ]

    (root / OUT_RECORD_JSON).write_text(json.dumps({"summary": summary, "inputs": inputs}, indent=2), encoding="utf-8")
    (root / OUT_RECORD_MD).write_text(build_intake_markdown(summary, inputs), encoding="utf-8")
    (root / OUT_DECISION_MD).write_text(build_decision_record(summary), encoding="utf-8")

    print("SelfDoc hotfix 004 architecture intake record complete.")
    print(f"Arch intake status: {arch_status}")
    print(f"Inventory probe version: {inventory_probe_version}")
    print(f"Promotion review status: {promotion_review_status}")
    print(f"Batch 0 confirmed: {batch0_confirmed}/9")
    print(f"Batch 0 false shape-review reduced by: {reduced_by}")
    print(f"cmd_help stale evidence / do not repair: {cmd_help_ok}")
    print(f"Source repair recommended: {source_repair_recommended}")
    print(f"Wrote: {OUT_RECORD_MD}")
    print(f"Wrote: {OUT_RECORD_JSON}")
    print(f"Wrote: {OUT_DECISION_MD}")
    print("No DotTalk++ src/include files were edited.")
    print("No DBFs were written.")
    print("HELP DATA was not rebuilt.")
    print("CMDHELPCHK was not modified.")
    print("v1.1 was not promoted to default.")

    return 0 if arch_status != "HOLD_EVIDENCE_INCOMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
REPORT_ONLY: source_contract_inventory_v1_1_promotion_candidate_report.py

Run from:
  D:\code\ccode

Reads v1.1 inventory, promotion review, gap review, and comparison reports.
Writes final v1.1 promotion-candidate report artifacts.
Does not edit source, write DBFs, modify CMDHELPCHK, rebuild HELP DATA, repair headers,
move/delete files, or promote v1.1 to default.
"""

from __future__ import annotations

import argparse, csv, fnmatch, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

STATUS = "PROMOTION_CANDIDATE_APPROVED_WITH_SCOPE_NOTES"

REPORT_DIRS = [
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
]

INVENTORY_CSV = "source_contracts_inventory_v1_1.csv"
INVENTORY_JSON = "source_contracts_inventory_v1_1.json"
PROMO_CSV = "source_contract_inventory_v1_1_promotion_review.csv"
PROMO_JSON = "source_contract_inventory_v1_1_promotion_review.json"
GAP_CSV = "source_contract_inventory_v1_1_classifier_gap_review.csv"
COMPARE_MD = "source_contract_inventory_v0_vs_v1_1.md"

OUT_MD = "source_contract_inventory_v1_1_promotion_candidate_report.md"
OUT_CSV = "source_contract_inventory_v1_1_promotion_candidate_report.csv"
OUT_JSON = "source_contract_inventory_v1_1_promotion_candidate_report.json"

DECISIONS = [
    {
        "pattern": "src/cli/shell.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "HIGH",
        "role": "cli_shell_core",
        "family": "selfdoc.cli_shell_contract",
        "action": "alternate_contract_cli_shell_core",
        "note": "Core DotTalk++ conversation loop: input/output, talk, prompt '.', command polling, dispatch glue.",
    },
    {
        "pattern": "src/cli/shell_commands.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "HIGH",
        "role": "command_registry",
        "family": "selfdoc.command_registry_contract",
        "action": "alternate_contract_registry",
        "note": "Command registry / shell input-cycle infrastructure; not ordinary @dottalk.usage v1 backlog.",
    },
    {
        "pattern": "src/cli/shell_*_utils.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "MEDIUM",
        "role": "cli_shell_helpers",
        "family": "selfdoc.cli_shell_helper_contract",
        "action": "alternate_contract_cli_shell_helper",
        "note": "Shell utility/helper source; not ordinary command usage surface.",
    },
    {
        "pattern": "src/cli/console_utils.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "MEDIUM",
        "role": "console_talk_output_helper",
        "family": "selfdoc.cli_console_io_contract",
        "action": "alternate_contract_console_io",
        "note": "Console / talk-output helper.",
    },
    {
        "pattern": "src/cli/browse/browse_util.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "MEDIUM",
        "role": "browser_helper",
        "family": "selfdoc.command_helper_contract",
        "action": "alternate_contract_helper",
        "note": "Browser helper; not ordinary command usage surface.",
    },
    {
        "pattern": "src/cli/index_utils.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "MEDIUM",
        "role": "index_key_manipulation_helper",
        "family": "selfdoc.index_helper_contract",
        "action": "alternate_contract_index_helper",
        "note": "Index key manipulation helper.",
    },
    {
        "pattern": "src/cli/status_helpers.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "MEDIUM",
        "role": "order_status_helper",
        "family": "selfdoc.order_status_contract",
        "action": "alternate_contract_order_status",
        "note": "Order/status helper.",
    },
    {
        "pattern": "src/cli/cmd_buildlmdb.cpp",
        "decision": "KEEP_COMMAND_USAGE_SURFACE",
        "priority": "HIGH",
        "role": "simple_command_index_materialization",
        "family": "@dottalk.usage v1",
        "action": "accepted_existing_command_contract",
        "note": "Creates LMDB index files defined by the index/CDX command layer.",
        "classifier_decision": "Accept requires_confirmation_for_existing_environment as valid safety/effect field.",
    },
    {
        "pattern": "src/cli/cmd_dothelp.cpp",
        "decision": "APPROVE_COMMAND_FAMILY_HELP_SUBSYSTEM_SURFACE",
        "priority": "HIGH",
        "role": "dothelp_listing_help_command_family",
        "family": "selfdoc.help_subsystem_contract",
        "action": "accepted_existing_command_family_contract",
        "note": "DOTHELP listing/help command family.",
    },
    {
        "pattern": "src/cli/cmd_lmdb.cpp",
        "decision": "KEEP_COMMAND_USAGE_SURFACE_WITH_DESIGN_NOTES",
        "priority": "HIGH",
        "role": "lmdb_index_buffer_inspection_command",
        "family": "@dottalk.usage v1",
        "action": "accepted_existing_command_contract",
        "note": "LMDB index/buffer inspection and manipulation command.",
        "classifier_decision": "Do not blindly accept prose-like fields globally; classify design/file/thin-wrapper notes as notes/design metadata or cleanup-later.",
    },
    {
        "pattern": "src/cli/cmdhelp.cpp",
        "decision": "CONFIRM_FAMILY_LEVEL_ACTIONABLE_BACKLOG",
        "priority": "HIGH",
        "role": "selfdoc_help_builder_command_family_applet",
        "family": "selfdoc.help_subsystem_contract",
        "action": "action_required_add_command_family_usage_contract",
        "note": "Scans usage contracts and builds HELP DBF files; family-level backlog, not simple command repair.",
    },
    {
        "pattern": "src/cli/helpdata_cmdhelp_bridge.cpp",
        "decision": "APPROVE_SCOPE_CORRECTION",
        "priority": "HIGH",
        "role": "cmdhelp_help_metadata_bridge",
        "family": "selfdoc.help_metadata_engine_contract",
        "action": "alternate_contract_help_metadata_engine",
        "note": "CMDHELP / HELP metadata bridge.",
    },
    {
        "pattern": "include/xexpr/function.hpp",
        "decision": "APPROVE_EXPRESSION_SYSTEM_SURFACE",
        "priority": "MEDIUM",
        "role": "expression_function_system_api",
        "family": "selfdoc.function_contract_or_api_contract",
        "action": "alternate_contract_function_api",
        "note": "Expression/function system API with function-system lane.",
    },
]

def read_csv_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def read_summary(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("summary", {})
    except Exception as e:
        return {"read_error": f"{type(e).__name__}: {e}"}

def md_escape(x) -> str:
    return str(x).replace("|", "\\|").replace("\n", " ")

def report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d
    for rel in REPORT_DIRS:
        d = root / rel
        if (d / INVENTORY_CSV).is_file():
            return d
    raise SystemExit("Could not find v1.1 inventory reports under dottalkpp\\docs\\generated\\reports")

def matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path.replace("\\", "/"), pattern)

def decision_for(path: str):
    for d in DECISIONS:
        if matches(path, d["pattern"]):
            return d
    return None

def collect_rows(inv: dict, promo: dict, gap: dict) -> list[dict]:
    wanted = set()
    for d in DECISIONS:
        for source in (inv, promo, gap):
            for p in source:
                if matches(p, d["pattern"]):
                    wanted.add(p)
        if "*" not in d["pattern"] and "?" not in d["pattern"]:
            wanted.add(d["pattern"])

    rows = []
    for p in sorted(wanted, key=str.lower):
        d = decision_for(p)
        if not d:
            continue
        i = inv.get(p, {})
        pr = promo.get(p, {})
        g = gap.get(p, {})
        effect = "CONFIRMS_CURRENT_CLASSIFIER" if (
            i.get("recommended_family", "") == d["family"] and i.get("action_class", "") == d["action"]
        ) else "APPROVED_REFINED_ROLE"
        rows.append({
            "path": p,
            "decision": d["decision"],
            "priority": d["priority"],
            "approved_role": d["role"],
            "approved_family": d["family"],
            "approved_action": d["action"],
            "inventory_role": i.get("command_scope_role", ""),
            "inventory_family": i.get("recommended_family", ""),
            "inventory_action": i.get("action_class", ""),
            "promotion_review_class": pr.get("review_class", ""),
            "gap_class": g.get("gap_class", ""),
            "status": STATUS,
            "promotion_effect": effect,
            "note": d["note"],
            "classifier_decision": d.get("classifier_decision", ""),
        })

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    rows.sort(key=lambda r: (order.get(r["priority"], 9), r["path"].lower()))
    return rows

def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "path", "decision", "priority", "approved_role", "approved_family", "approved_action",
        "inventory_role", "inventory_family", "inventory_action", "promotion_review_class",
        "gap_class", "status", "promotion_effect", "note", "classifier_decision",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def write_md(path: Path, csv_path: Path, json_path: Path, summary: dict, rows: list[dict], notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Inventory v1.1 Promotion Candidate Report")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("v1.1 hotfix direction: WORKING")
    lines.append("vocabulary gap: CLOSED")
    lines.append("scope correction: HUMAN REVIEW APPLIED")
    lines.append(f"promotion status: {STATUS}")
    lines.append("default promotion: NOT AUTHORIZED")
    lines.append("source repairs: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report applies the human scope-review decisions to the v1.1 source-contract inventory promotion review. It documents v1.1 as a promotion candidate with refined roles. It does not promote v1.1 to default, edit source, write DBFs, modify CMDHELPCHK, rebuild HELP DATA, or repair headers.")
    lines.append("")
    lines.append("Inputs read:")
    lines.append("")
    for note in notes:
        lines.append(f"- `{md_escape(note)}`")
    lines.append("")
    lines.append("Outputs written:")
    lines.append("")
    lines.append(f"- `{path}`")
    lines.append(f"- `{csv_path}`")
    lines.append(f"- `{json_path}`")
    lines.append("")
    lines.append("## Key inventory counts")
    lines.append("")
    for k, v in summary["source_inventory_summary"].items():
        lines.append(f"- {k}: `{md_escape(v)}`")
    lines.append("")
    lines.append("## Promotion candidate gate")
    lines.append("")
    lines.append("| Gate | Value |")
    lines.append("|---|---|")
    for k, v in summary["promotion_candidate_gate"].items():
        lines.append(f"| `{md_escape(k)}` | `{md_escape(v)}` |")
    lines.append("")
    lines.append("## Human decision counts")
    lines.append("")
    lines.append("| Decision | Count |")
    lines.append("|---|---:|")
    for k, v in summary["human_decision_counts"].items():
        lines.append(f"| `{md_escape(k)}` | {v} |")
    lines.append("")
    lines.append("## Approved family counts")
    lines.append("")
    lines.append("| Family | Count |")
    lines.append("|---|---:|")
    for k, v in summary["approved_family_counts"].items():
        lines.append(f"| `{md_escape(k)}` | {v} |")
    lines.append("")
    lines.append("## Candidate rows")
    lines.append("")
    lines.append("| Path | Priority | Decision | Approved role | Approved family | Approved action | Current action | Promotion effect | Note |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| `{md_escape(r['path'])}` | `{md_escape(r['priority'])}` | `{md_escape(r['decision'])}` | "
            f"`{md_escape(r['approved_role'])}` | `{md_escape(r['approved_family'])}` | `{md_escape(r['approved_action'])}` | "
            f"`{md_escape(r['inventory_action'])}` | `{md_escape(r['promotion_effect'])}` | {md_escape(r['note'])} |"
        )
    lines.append("")
    lines.append("## Classifier decisions carried forward")
    lines.append("")
    classifier_rows = [r for r in rows if r.get("classifier_decision")]
    if classifier_rows:
        lines.append("| Path | Decision |")
        lines.append("|---|---|")
        for r in classifier_rows:
            lines.append(f"| `{md_escape(r['path'])}` | {md_escape(r['classifier_decision'])} |")
    else:
        lines.append("No classifier-decision notes were recorded.")
    lines.append("")
    lines.append("## Promotion implication")
    lines.append("")
    lines.append("This report supports moving v1.1 from `HOLD_REVIEW_REQUIRED` to `PROMOTION_CANDIDATE_APPROVED_WITH_SCOPE_NOTES`. It still does not make v1.1 the default probe. The next safe step is a manifest/pipeline candidate update or shape-review plan, not source repair.")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for g in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(g)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--report-dir", default=None)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    rd = report_dir(root, args.report_dir)

    inv_rows = {r.get("path", ""): r for r in read_csv_rows(rd / INVENTORY_CSV)}
    promo_rows = {r.get("path", ""): r for r in read_csv_rows(rd / PROMO_CSV)}
    gap_rows = {r.get("path", ""): r for r in read_csv_rows(rd / GAP_CSV)}

    rows = collect_rows(inv_rows, promo_rows, gap_rows)

    inv_summary = read_summary(rd / INVENTORY_JSON)
    decision_counts = Counter(r["decision"] for r in rows)
    family_counts = Counter(r["approved_family"] for r in rows)
    role_counts = Counter(r["approved_role"] for r in rows)
    priority_counts = Counter(r["priority"] for r in rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "report_dir": str(rd),
        "candidate_rows": len(rows),
        "human_decision_counts": dict(decision_counts.most_common()),
        "approved_family_counts": dict(family_counts.most_common()),
        "approved_role_counts": dict(role_counts.most_common()),
        "priority_counts": dict(priority_counts.most_common()),
        "source_inventory_summary": {
            "total_records": inv_summary.get("total_records", ""),
            "files_with_contracts": inv_summary.get("files_with_contracts", ""),
            "files_missing_contracts": inv_summary.get("files_missing_contracts", ""),
            "accepted_existing_command_contracts": inv_summary.get("accepted_existing_command_contracts", ""),
            "existing_command_contracts_needing_shape_review": inv_summary.get("existing_command_contracts_needing_shape_review", ""),
            "actionable_missing_command_help_usage_contracts": inv_summary.get("actionable_missing_command_help_usage_contracts", ""),
            "actionable_family_command_usage_contracts": inv_summary.get("actionable_family_command_usage_contracts", ""),
            "registry_contract_candidates": inv_summary.get("registry_contract_candidates", ""),
            "remaining_distinct_unrecognized_fields": inv_summary.get("remaining_distinct_unrecognized_fields", ""),
        },
        "promotion_candidate_gate": {
            "human_scope_review_applied": True,
            "vocabulary_gap_closed": True,
            "scope_corrections_approved": True,
            "source_repairs_authorized": False,
            "dbf_writes_authorized": False,
            "cmdhelpchk_changes_authorized": False,
            "v1_1_default_promotion_authorized": False,
            "next_status": "PROMOTION_CANDIDATE_DOCUMENTED_NOT_DEFAULT",
        },
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
            "did_not_promote_v1_1_to_default",
            "did_not_move_or_delete_files",
        ],
    }

    out_md = rd / OUT_MD
    out_csv = rd / OUT_CSV
    out_json = rd / OUT_JSON

    notes = [
        f"read v1.1 inventory CSV: {rd / INVENTORY_CSV}",
        f"read v1.1 inventory JSON: {rd / INVENTORY_JSON}" if (rd / INVENTORY_JSON).is_file() else f"v1.1 inventory JSON missing: {rd / INVENTORY_JSON}",
        f"read promotion review CSV: {rd / PROMO_CSV}" if (rd / PROMO_CSV).is_file() else f"promotion review CSV missing: {rd / PROMO_CSV}",
        f"read promotion review JSON: {rd / PROMO_JSON}" if (rd / PROMO_JSON).is_file() else f"promotion review JSON missing: {rd / PROMO_JSON}",
        f"read classifier gap review CSV: {rd / GAP_CSV}" if (rd / GAP_CSV).is_file() else f"classifier gap review CSV missing: {rd / GAP_CSV}",
        f"comparison report present: {rd / COMPARE_MD}" if (rd / COMPARE_MD).is_file() else f"comparison report missing: {rd / COMPARE_MD}",
    ]

    write_csv(out_csv, rows)
    out_json.write_text(json.dumps({"summary": summary, "candidate_rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    write_md(out_md, out_csv, out_json, summary, rows, notes)

    print("SelfDoc source contract inventory v1.1 promotion candidate report complete.")
    print(f"Read report directory: {rd}")
    print(f"Candidate rows: {len(rows)}")
    print(f"Promotion status: {STATUS}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    print("v1.1 was not promoted to default.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

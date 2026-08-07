#!/usr/bin/env python3
"""
REPORT_ONLY gap review for source_contract_inventory_probe_v1_1.

Run from:
  D:\code\ccode

Reads:
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
  dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.json
  dottalkpp\docs\generated\reports\source_contract_classifier_update_draft_v1_1.csv
  dottalkpp\docs\generated\reports\source_contract_extension_vocabulary_v1_1.csv

Writes:
  dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_classifier_gap_review.md
  dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_classifier_gap_review.csv
  dottalkpp\docs\generated\reports\source_contract_inventory_v1_1_classifier_gap_review.json

Safety:
  REPORT_ONLY. No source edits. No DBF writes. No CMDHELPCHK changes.
  No HELP DATA rebuild. No repairs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

V11_CSV = "source_contracts_inventory_v1_1.csv"
V11_JSON = "source_contracts_inventory_v1_1.json"
DRAFT_CSV = "source_contract_classifier_update_draft_v1_1.csv"
VOCAB_CSV = "source_contract_extension_vocabulary_v1_1.csv"

OUT_MD = "source_contract_inventory_v1_1_classifier_gap_review.md"
OUT_CSV = "source_contract_inventory_v1_1_classifier_gap_review.csv"
OUT_JSON = "source_contract_inventory_v1_1_classifier_gap_review.json"


def b(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"true", "1", "yes", "y"}


def parts(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if not s:
        return []
    sep = ";" if ";" in s else ","
    return [x.strip() for x in s.split(sep) if x.strip()]


def nf(s: str) -> str:
    return s.strip().lower().replace(" ", "_")


def find_reports(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d
    for rel in REPORT_DIRS:
        d = root / rel
        if (d / V11_CSV).is_file() and (d / DRAFT_CSV).is_file():
            return d
    raise SystemExit("Could not find v1.1 inventory and draft reports under dottalkpp\\docs\\generated\\reports")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_v11_summary(report_dir: Path) -> dict[str, Any]:
    path = report_dir / V11_JSON
    if not path.is_file():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")).get("summary", {}))
    except Exception as exc:
        return {"read_error": str(exc)}


def md_escape(v: object) -> str:
    return str(v).replace("|", "\\|").replace("\n", " ")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "path", "lane", "recommended_family",
        "draft_action", "v1_1_action", "gap_class",
        "draft_accepted", "v1_1_accepted",
        "draft_shape_review", "v1_1_shape_review",
        "draft_unrecognized", "v1_1_unrecognized",
        "should_have_accepted_fields", "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            out = {}
            for k in fields:
                v = row.get(k, "")
                if isinstance(v, list):
                    v = "; ".join(str(x) for x in v)
                out[k] = v
            w.writerow(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--report-dir", default=None)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    report_dir = find_reports(root, args.report_dir)

    v11_path = report_dir / V11_CSV
    draft_path = report_dir / DRAFT_CSV
    vocab_path = report_dir / VOCAB_CSV
    v11_summary = read_v11_summary(report_dir)

    v11 = {r.get("path", ""): r for r in read_csv(v11_path)}
    draft = {r.get("path", ""): r for r in read_csv(draft_path)}

    vocab_rec: dict[str, str] = {}
    vocab_canon: dict[str, str] = {}
    if vocab_path.is_file():
        for r in read_csv(vocab_path):
            field = nf(r.get("field", ""))
            rec = r.get("recommendation", "").strip()
            canon = nf(r.get("canonical_field", "")) or field
            if field:
                vocab_rec[field] = rec
                vocab_canon[field] = canon
                if rec == "ACCEPT_ALIAS":
                    vocab_rec[canon] = "ACCEPTED_CANONICAL_FROM_ALIAS"
                    vocab_canon[canon] = canon

    paths = sorted(set(v11) | set(draft), key=str.lower)
    gaps: list[dict[str, Any]] = []

    for path in paths:
        vr = v11.get(path, {})
        dr = draft.get(path, {})

        v_action = vr.get("action_class", "")
        d_action = dr.get("draft_action", "")

        v_accepted = v_action == "accepted_existing_command_contract"
        d_accepted = b(dr.get("accepted_by_v1_1", False))
        v_shape = b(vr.get("is_shape_review_candidate", False))
        d_shape = b(dr.get("needs_shape_review", False))

        v_unrec = [nf(x) for x in parts(vr.get("unrecognized_fields", ""))]
        d_unrec = [nf(x) for x in parts(dr.get("unrecognized_after_v1_1", ""))]

        should_accept = []
        for f in v_unrec:
            if vocab_rec.get(f) in {"ACCEPT_EXTENSION", "ACCEPT_ALIAS", "ACCEPTED_CANONICAL_FROM_ALIAS"}:
                should_accept.append(f)

        notes: list[str] = []
        if not dr:
            gap = "new_in_v1_1_only"
            notes.append("path present in v1.1 output but not draft output")
        elif not vr:
            gap = "missing_from_v1_1_output"
            notes.append("path present in draft output but not v1.1 output")
        elif d_accepted and not v_accepted:
            if should_accept:
                gap = "accepted_to_shape_review_due_to_vocab_gap"
                notes.append("draft accepted but v1.1 implementation rejected; accepted vocabulary still unrecognized")
            elif b(vr.get("malformed", False)):
                gap = "accepted_to_shape_review_due_to_malformed"
                notes.append("draft accepted but v1.1 implementation reports malformed")
            elif parts(vr.get("missing_required_fields", "")):
                gap = "accepted_to_shape_review_due_to_required_field"
                notes.append("draft accepted but v1.1 implementation reports missing required field")
            else:
                gap = "accepted_to_shape_review_other"
                notes.append("draft accepted but v1.1 implementation changed action")
        elif d_shape and v_accepted:
            gap = "shape_review_to_accepted"
            notes.append("v1.1 implementation accepted an item draft marked for shape review")
        elif d_action != v_action:
            gap = "action_class_changed"
            notes.append("action class changed between draft and implementation")
        elif should_accept:
            gap = "latent_vocab_gap"
            notes.append("action unchanged but accepted vocabulary still appears unrecognized")
        elif set(v_unrec) - set(d_unrec):
            gap = "new_unrecognized_fields"
            notes.append("v1.1 implementation has additional unrecognized fields versus draft")
        else:
            gap = "no_gap"

        gaps.append({
            "path": path,
            "lane": vr.get("lane", dr.get("lane", "")),
            "recommended_family": vr.get("recommended_family", dr.get("recommended_family", "")),
            "draft_action": d_action,
            "v1_1_action": v_action,
            "gap_class": gap,
            "draft_accepted": d_accepted,
            "v1_1_accepted": v_accepted,
            "draft_shape_review": d_shape,
            "v1_1_shape_review": v_shape,
            "draft_unrecognized": d_unrec,
            "v1_1_unrecognized": v_unrec,
            "should_have_accepted_fields": sorted(set(should_accept)),
            "notes": notes,
        })

    gap_counts = Counter(g["gap_class"] for g in gaps)
    transitions = Counter((g["draft_action"], g["v1_1_action"]) for g in gaps)

    draft_accepted = sum(1 for r in draft.values() if b(r.get("accepted_by_v1_1", False)))
    v11_accepted = sum(1 for r in v11.values() if r.get("action_class", "") == "accepted_existing_command_contract")
    draft_shape = sum(1 for r in draft.values() if b(r.get("needs_shape_review", False)))
    v11_shape = sum(1 for r in v11.values() if b(r.get("is_shape_review_candidate", False)))
    vocab_gap_paths = sum(1 for g in gaps if g["should_have_accepted_fields"])

    v_unrec_counts = Counter()
    accepted_gap_fields = Counter()
    for g in gaps:
        for f in g["v1_1_unrecognized"]:
            if f:
                v_unrec_counts[f] += 1
        for f in g["should_have_accepted_fields"]:
            accepted_gap_fields[f] += 1

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report_dir": str(report_dir),
        "records_compared": len(gaps),
        "draft_accepted_existing_command_contracts": draft_accepted,
        "v1_1_accepted_existing_command_contracts": v11_accepted,
        "accepted_drop": draft_accepted - v11_accepted,
        "draft_shape_review_items": draft_shape,
        "v1_1_shape_review_items": v11_shape,
        "shape_review_increase": v11_shape - draft_shape,
        "v1_1_actionable_missing_command_help_usage_contracts": v11_summary.get("actionable_missing_command_help_usage_contracts", ""),
        "v1_1_remaining_distinct_unrecognized_fields": v11_summary.get("remaining_distinct_unrecognized_fields", ""),
        "paths_with_vocab_acceptance_gap": vocab_gap_paths,
        "gap_class_counts": dict(gap_counts.most_common()),
        "action_transition_counts": {f"{a} -> {b}": c for (a, b), c in transitions.most_common()},
        "accepted_gap_field_counts": dict(accepted_gap_fields.most_common()),
        "v1_1_unrecognized_field_counts": dict(v_unrec_counts.most_common()),
    }

    out_md = report_dir / OUT_MD
    out_csv = report_dir / OUT_CSV
    out_json = report_dir / OUT_JSON

    write_csv(out_csv, gaps)
    out_json.write_text(json.dumps({"summary": summary, "gaps": gaps}, indent=2, ensure_ascii=False), encoding="utf-8")

    regressions = [g for g in gaps if g["gap_class"] != "no_gap"]

    lines = []
    lines.append("# Source Contract Inventory v1.1 Classifier Gap Review")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("Safety class: `REPORT_ONLY`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This report compares the v1.1 inventory implementation against the v1.1 draft classifier output. It identifies classifier gaps only. It does not edit source, write DBFs, modify CMDHELPCHK, rebuild HELP DATA, or repair headers.")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("source_contract_inventory_probe_v1_1: GENERATED SUCCESSFULLY")
    lines.append("promotion status: HOLD / REVIEW REQUIRED")
    lines.append("mutation safety: GREEN")
    lines.append("classifier accuracy: NOT READY TO PROMOTE")
    lines.append("```")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for key in [
        "records_compared",
        "draft_accepted_existing_command_contracts",
        "v1_1_accepted_existing_command_contracts",
        "accepted_drop",
        "draft_shape_review_items",
        "v1_1_shape_review_items",
        "shape_review_increase",
        "v1_1_actionable_missing_command_help_usage_contracts",
        "v1_1_remaining_distinct_unrecognized_fields",
        "paths_with_vocab_acceptance_gap",
    ]:
        lines.append(f"- {key}: `{summary[key]}`")
    lines.append("")
    lines.append("## Gap class counts")
    lines.append("")
    lines.append("| Gap class | Count |")
    lines.append("|---|---:|")
    for k, c in gap_counts.most_common():
        lines.append(f"| `{md_escape(k)}` | {c} |")
    lines.append("")
    lines.append("## Action transition counts")
    lines.append("")
    lines.append("| Draft action | v1.1 action | Count |")
    lines.append("|---|---|---:|")
    for (da, va), c in transitions.most_common(30):
        lines.append(f"| `{md_escape(da)}` | `{md_escape(va)}` | {c} |")
    lines.append("")
    lines.append("## Fields that should have been accepted but were still unrecognized")
    lines.append("")
    if accepted_gap_fields:
        lines.append("| Field | Count |")
        lines.append("|---|---:|")
        for f, c in accepted_gap_fields.most_common(100):
            lines.append(f"| `{md_escape(f)}` | {c} |")
    else:
        lines.append("No accepted-vocabulary fields appeared as unrecognized in v1.1 output.")
    lines.append("")
    lines.append("## Top v1.1 unrecognized fields")
    lines.append("")
    if v_unrec_counts:
        lines.append("| Field | Count |")
        lines.append("|---|---:|")
        for f, c in v_unrec_counts.most_common(100):
            lines.append(f"| `{md_escape(f)}` | {c} |")
    else:
        lines.append("No v1.1 unrecognized fields found.")
    lines.append("")
    lines.append("## Regression candidates")
    lines.append("")
    if regressions:
        lines.append("| Path | Gap class | Draft action | v1.1 action | Should-have-accepted fields | v1.1 unrecognized |")
        lines.append("|---|---|---|---|---|---|")
        for g in regressions[:250]:
            lines.append(
                f"| `{md_escape(g['path'])}` | `{md_escape(g['gap_class'])}` | "
                f"`{md_escape(g['draft_action'])}` | `{md_escape(g['v1_1_action'])}` | "
                f"{md_escape(', '.join(g['should_have_accepted_fields']))} | "
                f"{md_escape(', '.join(g['v1_1_unrecognized']))} |"
            )
    else:
        lines.append("No regression candidates found.")
    lines.append("")
    lines.append("## Recommended next action")
    lines.append("")
    lines.append("Do not promote v1.1 yet. Do not repair source headers yet. Review the accepted-vocabulary gap fields first, then patch only the v1.1 classifier vocabulary/normalization logic in a new report-only candidate probe or hotfix.")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    lines.append("- No source files edited.")
    lines.append("- No DBFs written.")
    lines.append("- No HELP DATA rebuilt.")
    lines.append("- No CMDHELPCHK implementation or configuration modified.")
    lines.append("- No source contract headers repaired.")
    lines.append("- This review writes markdown, CSV, and JSON only.")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("SelfDoc source contract inventory v1.1 classifier gap review complete.")
    print(f"Read report directory: {report_dir}")
    print(f"Records compared: {len(gaps)}")
    print(f"Draft accepted existing command contracts: {draft_accepted}")
    print(f"v1.1 accepted existing command contracts: {v11_accepted}")
    print(f"Draft shape-review items: {draft_shape}")
    print(f"v1.1 shape-review items: {v11_shape}")
    print(f"Paths with accepted-vocabulary gap: {vocab_gap_paths}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No repairs were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

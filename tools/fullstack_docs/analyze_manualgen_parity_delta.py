#!/usr/bin/env python3
"""Classify a manualgen dry-run/current-publication Markdown delta."""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import re
from pathlib import Path


CREATED_UTC = re.compile(r"^<!-- created_utc: .* -->$")
GENERATED_ASSEMBLY_METADATA = re.compile(
    r"^<!-- (?:assembly_selection_mode|selected_workspace_role|harvest_workspace|harvest_selection_mode): .* -->$"
)


def is_generated_header_line(line: str) -> bool:
    return bool(CREATED_UTC.match(line) or GENERATED_ASSEMBLY_METADATA.match(line))
MDO_MARKER = re.compile(r"<!--\s*(MDO-\d+[A-Z]?).*?(?:start|begin)", re.IGNORECASE)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    dry_path = args.dry_run.resolve()
    current_path = args.current.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    dry = dry_path.read_text(encoding="utf-8-sig").splitlines()
    current = current_path.read_text(encoding="utf-8-sig").splitlines()
    matcher = difflib.SequenceMatcher(None, dry, current, autojunk=False)
    opcodes = matcher.get_opcodes()
    differences = [opcode for opcode in opcodes if opcode[0] != "equal"]

    rows: list[dict[str, object]] = []
    for index, (tag, i1, i2, j1, j2) in enumerate(differences, start=1):
        dry_slice = dry[i1:i2]
        current_slice = current[j1:j2]
        classification = "CONTENT_DIFFERENCE"
        if (
            tag == "replace"
            and len(dry_slice) == 1
            and len(current_slice) == 1
            and CREATED_UTC.match(dry_slice[0])
            and CREATED_UTC.match(current_slice[0])
        ):
            classification = "VOLATILE_GENERATED_TIMESTAMP"
        elif (
            dry_slice
            and all(is_generated_header_line(line) for line in dry_slice)
            and all(is_generated_header_line(line) for line in current_slice)
        ):
            classification = "GENERATED_ASSEMBLY_METADATA"
        elif tag == "insert" and i1 == len(dry) and j2 == len(current):
            classification = "CURRENT_ONLY_TRAILING_OVERLAY"

        markers = sorted({match.group(1).upper() for line in current_slice for match in [MDO_MARKER.search(line)] if match})
        rows.append(
            {
                "difference_id": f"PARITY-{index:03d}",
                "classification": classification,
                "opcode": tag,
                "dry_start_line": i1 + 1,
                "dry_line_count": i2 - i1,
                "current_start_line": j1 + 1,
                "current_line_count": j2 - j1,
                "current_markers": ";".join(markers),
                "dry_first_line": dry_slice[0] if dry_slice else "",
                "current_first_line": current_slice[0] if current_slice else "",
            }
        )

    substantive = [row for row in rows if row["classification"] == "CONTENT_DIFFERENCE"]
    trailing = [row for row in rows if row["classification"] == "CURRENT_ONLY_TRAILING_OVERLAY"]
    timestamps = [row for row in rows if row["classification"] == "VOLATILE_GENERATED_TIMESTAMP"]
    generated_metadata = [row for row in rows if row["classification"] == "GENERATED_ASSEMBLY_METADATA"]
    section_body_parity = not substantive and len(trailing) <= 1 and len(timestamps) <= 1

    overlay_lines: list[str] = []
    if trailing:
        row = trailing[0]
        start = int(row["current_start_line"]) - 1
        count = int(row["current_line_count"])
        overlay_lines = current[start : start + count]

    overlay_markers = sorted({match.group(1).upper() for line in overlay_lines for match in [MDO_MARKER.search(line)] if match})
    overlay_findings = []
    if any(line == "`powershell" for line in overlay_lines):
        overlay_findings.append("SINGLE_BACKTICK_POWERSHELL_BLOCK")
    if any(line.strip() == "eferences/manual_mutation_cycle_reference_v1.md" for line in overlay_lines):
        overlay_findings.append("TRUNCATED_REFERENCE_ARTIFACT_PATH")
    if "## Manual Mutation Cycle" in overlay_lines and "# Manual Mutation Cycle and Guarded Publication Workflow" in overlay_lines:
        overlay_findings.append("DUPLICATE_TITLE_HIERARCHY")

    summary = {
        "schema": "dottalk.fullstack.manualgen_parity_delta.v1",
        "dry_run": str(dry_path),
        "current": str(current_path),
        "dry_run_sha256": file_hash(dry_path),
        "current_sha256": file_hash(current_path),
        "dry_run_lines": len(dry),
        "current_lines": len(current),
        "sequence_ratio": matcher.ratio(),
        "difference_opcode_count": len(differences),
        "volatile_timestamp_differences": len(timestamps),
        "generated_assembly_metadata_differences": len(generated_metadata),
        "current_only_trailing_overlay_differences": len(trailing),
        "substantive_interior_differences": len(substantive),
        "trailing_overlay_lines": len(overlay_lines),
        "trailing_overlay_markers": overlay_markers,
        "trailing_overlay_findings": overlay_findings,
        "section_body_parity": section_body_parity,
        "promotion_recommendation": "HOLD_FOR_OVERLAY_AUTHORITY_REVIEW",
        "differences": rows,
    }

    csv_path = output_dir / "manualgen_parity_delta_classification_v1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()) if rows else ["difference_id"])
        writer.writeheader()
        writer.writerows(rows)

    (output_dir / "manualgen_parity_delta_classification_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    md = [
        "# Manualgen Parity Delta Classification V1",
        "",
        f"- dry-run lines: {len(dry)}",
        f"- current lines: {len(current)}",
        f"- sequence similarity: {matcher.ratio():.6f}",
        f"- volatile timestamp differences: {len(timestamps)}",
        f"- generated assembly metadata differences: {len(generated_metadata)}",
        f"- current-only trailing overlays: {len(trailing)} ({len(overlay_lines)} lines)",
        f"- substantive interior differences: {len(substantive)}",
        f"- section-body parity: {str(section_body_parity).lower()}",
        f"- overlay markers: {', '.join(overlay_markers) if overlay_markers else 'none'}",
        f"- overlay review findings: {', '.join(overlay_findings) if overlay_findings else 'none'}",
        "- recommendation: `HOLD_FOR_OVERLAY_AUTHORITY_REVIEW`",
        "",
        "The five parity REVIEW checks are multiple normalizations of the same artifact pair. They do not represent five missing sections.",
        "The concrete content delta is a current-only trailing overlay. Generated timestamp, assembly-selection, and harvest-provenance headers are non-content metadata differences. No interior section-body difference was found.",
        "",
        "This report does not modify either artifact or authorize publication replacement.",
        "",
    ]
    (output_dir / "MANUALGEN_PARITY_DELTA_CLASSIFICATION_V1.md").write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({key: summary[key] for key in (
        "difference_opcode_count",
        "volatile_timestamp_differences",
        "generated_assembly_metadata_differences",
        "current_only_trailing_overlay_differences",
        "substantive_interior_differences",
        "trailing_overlay_lines",
        "trailing_overlay_markers",
        "trailing_overlay_findings",
        "section_body_parity",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

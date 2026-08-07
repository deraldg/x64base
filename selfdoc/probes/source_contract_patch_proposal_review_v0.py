#!/usr/bin/env python3
"""
source_contract_patch_proposal_review_v0.py

REPORT_ONLY / REVIEW_ONLY review probe for Batch 0 patch proposal drafts.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0.json
    dottalkpp\docs\generated\patches\source_contract_patch_proposal_draft_v0\*.proposal.json

Writes:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_review_v0.md
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_review_v0.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_review_v0.json

Safety:
    REPORT_ONLY / REVIEW_ONLY
    No source edits.
    No patch files.
    No patch application.
    No repair batch.
    No DBF writes.
    No CMDHELPCHK changes.
    No HELP DATA rebuild.
    No v1.1 default promotion.
    No file moves/deletes.

Purpose:
    Review all Batch 0 proposal drafts.
    Check whether block-comment normalization is acceptable.
    Check whether payload indentation loss matters.
    Separate safe mechanical header-capture fixes from files needing manual review.
    Still do not apply patches.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIRS = (
    Path("dottalkpp") / "docs" / "generated" / "reports",
    Path("docs") / "generated" / "reports",
)

PATCH_DIR = Path("dottalkpp") / "docs" / "generated" / "patches" / "source_contract_patch_proposal_draft_v0"

DRAFT_CSV = "source_contract_patch_proposal_draft_v0.csv"
DRAFT_JSON = "source_contract_patch_proposal_draft_v0.json"

OUT_MD = "source_contract_patch_proposal_review_v0.md"
OUT_CSV = "source_contract_patch_proposal_review_v0.csv"
OUT_JSON = "source_contract_patch_proposal_review_v0.json"

MARKER = "@dottalk.usage v1"
SAFETY_CLASS = "REPORT_ONLY / REVIEW_ONLY"


@dataclass
class ReviewRow:
    path: str
    proposal_status: str
    proposal_md: str
    proposal_json: str
    review_status: str
    review_class: str
    priority: str
    original_header_hash: str = ""
    proposed_header_hash: str = ""
    payload_equivalent: bool = False
    marker_preserved: bool = False
    field_order_preserved: bool = False
    indentation_loss_detected: bool = False
    visual_structure_loss_detected: bool = False
    block_comment_normalization: bool = False
    safe_mechanical_candidate: bool = False
    manual_review_required: bool = False
    patch_authorized: bool = False
    source_edit_authorized: bool = False
    rationale: str = ""
    notes: list[str] = field(default_factory=list)


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


def find_report_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        d = root / explicit
        if not d.is_dir():
            raise SystemExit(f"Report directory not found: {d}")
        return d
    for rel in REPORT_DIRS:
        d = root / rel
        if (d / DRAFT_CSV).is_file():
            return d
    raise SystemExit("Could not find source_contract_patch_proposal_draft_v0.csv under dottalkpp\\docs\\generated\\reports")


def strip_comment_prefix(line: str) -> tuple[str, int]:
    """
    Return content after comment marker and the count of spaces after that marker.
    This is intentionally conservative; it helps detect visual indentation changes.
    """
    raw = line.rstrip("\n\r")
    s = raw.lstrip()
    leading = len(raw) - len(s)

    if s.startswith("/*"):
        after = s[2:]
        spaces = len(after) - len(after.lstrip(" "))
        return after.lstrip(" ").rstrip(), spaces

    if s.endswith("*/") and s.strip() == "*/":
        return "", 0

    if s.startswith("*/"):
        after = s[2:]
        spaces = len(after) - len(after.lstrip(" "))
        return after.lstrip(" ").rstrip(), spaces

    if s.startswith("//"):
        after = s[2:]
        spaces = len(after) - len(after.lstrip(" "))
        return after.lstrip(" ").rstrip(), spaces

    if s.startswith("*"):
        after = s[1:]
        spaces = len(after) - len(after.lstrip(" "))
        return after.lstrip(" ").rstrip(), spaces

    return s.rstrip(), leading


def payload_lines(header: str) -> list[str]:
    lines = []
    for raw in header.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        content, _spaces = strip_comment_prefix(raw)
        content = content.rstrip()
        if not content:
            continue
        if content in {"/*", "*/", "*"}:
            continue
        lines.append(content)
    # Collapse duplicate marker lines but preserve payload order otherwise.
    cleaned = []
    marker_seen = False
    for line in lines:
        if MARKER in line:
            if marker_seen:
                continue
            cleaned.append(MARKER)
            marker_seen = True
        else:
            cleaned.append(line)
    return cleaned


def field_order(lines: list[str]) -> list[str]:
    order = []
    for line in lines:
        m = re.match(r"^([A-Za-z][A-Za-z0-9_ -]{0,60})\s*:", line)
        if m:
            order.append(m.group(1).strip().lower().replace(" ", "_"))
    return order


def indentation_profile(header: str) -> list[int]:
    profile = []
    for raw in header.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        content, spaces = strip_comment_prefix(raw)
        if content:
            profile.append(spaces)
    return profile


def has_visual_structure(header: str) -> bool:
    for raw in header.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        content, spaces = strip_comment_prefix(raw)
        if not content:
            continue
        # Continuation or section-like payload that likely uses visual structure.
        if spaces >= 2:
            return True
        if content.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")):
            return True
        if re.match(r"^[A-Za-z0-9_ -]+:$", content):
            return True
    return False


def hash_text(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def load_proposal(root: Path, row: dict[str, str]) -> dict[str, Any]:
    rel = row.get("proposal_json", "")
    if not rel:
        return {}
    path = root / rel
    return read_json(path)


def review_one(root: Path, row: dict[str, str], proposal_payload: dict[str, Any]) -> ReviewRow:
    path = row.get("path", "")
    proposal = proposal_payload.get("proposal", {}) if isinstance(proposal_payload.get("proposal", {}), dict) else {}
    original = proposal_payload.get("original_header", "")
    proposed = proposal_payload.get("proposed_header", "")

    notes: list[str] = []

    if not original or not proposed:
        return ReviewRow(
            path=path,
            proposal_status=row.get("proposal_status", ""),
            proposal_md=row.get("proposal_md", ""),
            proposal_json=row.get("proposal_json", ""),
            review_status="BLOCKED",
            review_class="MISSING_PROPOSAL_PAYLOAD",
            priority="HIGH",
            manual_review_required=True,
            rationale="Proposal JSON did not include original and proposed header payloads.",
            notes=["proposal payload missing original_header or proposed_header"],
        )

    original_payload = payload_lines(original)
    proposed_payload = payload_lines(proposed)
    original_fields = field_order(original_payload)
    proposed_fields = field_order(proposed_payload)

    payload_equivalent = original_payload == proposed_payload
    marker_preserved = bool(original_payload and proposed_payload and original_payload[0] == MARKER and proposed_payload[0] == MARKER)
    field_order_preserved = original_fields == proposed_fields

    orig_profile = indentation_profile(original)
    prop_profile = indentation_profile(proposed)
    indentation_loss = False
    if orig_profile and prop_profile:
        # The proposal renderer commonly uses one space after "*".
        # If original had varied indentation but proposed becomes uniform, flag it.
        original_distinct = len(set(orig_profile))
        proposed_distinct = len(set(prop_profile))
        if original_distinct > proposed_distinct and max(orig_profile) >= 2:
            indentation_loss = True

    visual_loss = has_visual_structure(original) and indentation_loss
    block_norm = original.strip() != proposed.strip() and proposed.strip().startswith("/*") and proposed.strip().endswith("*/")

    original_hash = proposal.get("computed_header_hash", "") or hash_text(original)
    proposed_hash = hash_text(proposed)

    if not payload_equivalent:
        review_status = "MANUAL_REVIEW_REQUIRED"
        review_class = "PAYLOAD_DIFFERENCE"
        priority = "HIGH"
        safe = False
        manual = True
        rationale = "Original and proposed payload lines differ after stripping comment markers. This is not safe as a mechanical capture fix."
    elif not marker_preserved:
        review_status = "MANUAL_REVIEW_REQUIRED"
        review_class = "MARKER_NOT_PRESERVED"
        priority = "HIGH"
        safe = False
        manual = True
        rationale = "The @dottalk.usage v1 marker was not preserved as the first normalized payload line."
    elif not field_order_preserved:
        review_status = "MANUAL_REVIEW_REQUIRED"
        review_class = "FIELD_ORDER_CHANGED"
        priority = "HIGH"
        safe = False
        manual = True
        rationale = "Field order changed between original and proposed headers."
    elif visual_loss:
        review_status = "MANUAL_REVIEW_REQUIRED"
        review_class = "VISUAL_STRUCTURE_OR_INDENTATION_REVIEW"
        priority = "MEDIUM"
        safe = False
        manual = True
        rationale = "Payload text is preserved, but indentation or visual structure may be flattened. Review before any patch proposal becomes executable."
    elif block_norm:
        review_status = "SAFE_MECHANICAL_CANDIDATE"
        review_class = "BLOCK_COMMENT_NORMALIZATION_PAYLOAD_PRESERVED"
        priority = "LOW"
        safe = True
        manual = False
        rationale = "Payload lines, marker, and field order are preserved. Proposed change is block-comment normalization only."
    else:
        review_status = "NO_TEXT_CHANGE_OR_ALREADY_NORMALIZED"
        review_class = "NO_EFFECTIVE_CHANGE"
        priority = "LOW"
        safe = True
        manual = False
        rationale = "Proposal does not materially change the header after normalization."

    if indentation_loss:
        notes.append("indentation profile appears flattened")
    if visual_loss:
        notes.append("visual structure loss requires review")
    if block_norm:
        notes.append("proposal changes comment style to block-comment form")
    if payload_equivalent:
        notes.append("payload lines preserved")
    else:
        notes.append("payload lines differ")

    return ReviewRow(
        path=path,
        proposal_status=row.get("proposal_status", ""),
        proposal_md=row.get("proposal_md", ""),
        proposal_json=row.get("proposal_json", ""),
        review_status=review_status,
        review_class=review_class,
        priority=priority,
        original_header_hash=original_hash,
        proposed_header_hash=proposed_hash,
        payload_equivalent=payload_equivalent,
        marker_preserved=marker_preserved,
        field_order_preserved=field_order_preserved,
        indentation_loss_detected=indentation_loss,
        visual_structure_loss_detected=visual_loss,
        block_comment_normalization=block_norm,
        safe_mechanical_candidate=safe,
        manual_review_required=manual,
        patch_authorized=False,
        source_edit_authorized=False,
        rationale=rationale,
        notes=notes,
    )


def write_csv_report(path: Path, rows: list[ReviewRow]) -> None:
    fieldnames = [
        "path",
        "proposal_status",
        "proposal_md",
        "proposal_json",
        "review_status",
        "review_class",
        "priority",
        "original_header_hash",
        "proposed_header_hash",
        "payload_equivalent",
        "marker_preserved",
        "field_order_preserved",
        "indentation_loss_detected",
        "visual_structure_loss_detected",
        "block_comment_normalization",
        "safe_mechanical_candidate",
        "manual_review_required",
        "patch_authorized",
        "source_edit_authorized",
        "rationale",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            data = asdict(row)
            for key, value in list(data.items()):
                if isinstance(value, list):
                    data[key] = "; ".join(str(v) for v in value)
            writer.writerow(data)


def write_json_report(path: Path, summary: dict[str, Any], rows: list[ReviewRow]) -> None:
    path.write_text(
        json.dumps({"summary": summary, "review_rows": [asdict(row) for row in rows]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[ReviewRow], load_notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Patch Proposal Review v0")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{SAFETY_CLASS}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("patch proposal review: GENERATED")
    lines.append("patch application: NOT AUTHORIZED")
    lines.append("source edits: NOT AUTHORIZED")
    lines.append("repair batch: NOT CREATED")
    lines.append("DBF writes: NOT AUTHORIZED")
    lines.append("CMDHELPCHK changes: NOT AUTHORIZED")
    lines.append("HELP DATA rebuild: NOT AUTHORIZED")
    lines.append("```")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("This review checks Batch 0 proposal drafts for payload preservation, marker preservation, field-order preservation, block-comment normalization, and indentation/visual-structure risk. It does not apply patches or edit source.")
    lines.append("")
    lines.append("Inputs read:")
    lines.append("")
    for note in load_notes:
        lines.append(f"- `{md_escape(note)}`")
    lines.append("")
    lines.append("Outputs written:")
    lines.append("")
    lines.append(f"- `{path}`")
    lines.append(f"- `{csv_path}`")
    lines.append(f"- `{json_path}`")
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in [
        "proposal_rows_reviewed",
        "safe_mechanical_candidates",
        "manual_review_required",
        "payload_difference_count",
        "visual_structure_or_indentation_review_count",
        "block_comment_normalization_count",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Review class counts")
    lines.append("")
    lines.append("| Review class | Count |")
    lines.append("|---|---:|")
    for review_class, count in summary["review_class_counts"].items():
        lines.append(f"| `{md_escape(review_class)}` | {count} |")
    lines.append("")
    lines.append("## Review rows")
    lines.append("")
    lines.append("| Path | Review status | Review class | Safe mechanical | Manual review | Rationale |")
    lines.append("|---|---|---|---:|---:|---|")
    for row in rows:
        lines.append(
            f"| `{md_escape(row.path)}` | `{md_escape(row.review_status)}` | `{md_escape(row.review_class)}` | "
            f"{row.safe_mechanical_candidate} | {row.manual_review_required} | {md_escape(row.rationale)} |"
        )
    lines.append("")
    lines.append("## Safe mechanical candidates")
    lines.append("")
    safe_rows = [row for row in rows if row.safe_mechanical_candidate and not row.manual_review_required]
    if safe_rows:
        lines.append("| Path | Proposal | Notes |")
        lines.append("|---|---|---|")
        for row in safe_rows:
            lines.append(f"| `{md_escape(row.path)}` | `{md_escape(row.proposal_md)}` | {md_escape('; '.join(row.notes))} |")
    else:
        lines.append("No safe mechanical candidates found.")
    lines.append("")
    lines.append("## Manual review required")
    lines.append("")
    manual_rows = [row for row in rows if row.manual_review_required]
    if manual_rows:
        lines.append("| Path | Review class | Proposal | Notes |")
        lines.append("|---|---|---|---|")
        for row in manual_rows:
            lines.append(f"| `{md_escape(row.path)}` | `{md_escape(row.review_class)}` | `{md_escape(row.proposal_md)}` | {md_escape('; '.join(row.notes))} |")
    else:
        lines.append("No manual-review rows found.")
    lines.append("")
    lines.append("## Planning rules")
    lines.append("")
    lines.append("```text")
    lines.append("This review does not authorize patch application.")
    lines.append("Safe mechanical candidate means proposal may be considered for a future patch bundle.")
    lines.append("Manual review rows must not enter a mechanical patch bundle.")
    lines.append("Do not edit source from this report.")
    lines.append("Do not write DBFs.")
    lines.append("Do not rebuild HELP DATA.")
    lines.append("Do not modify CMDHELPCHK.")
    lines.append("```")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(guard)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review source contract patch proposal draft v0.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)

    draft_rows = read_csv_rows(rd / DRAFT_CSV)
    _draft_json = read_json(rd / DRAFT_JSON)

    review_rows: list[ReviewRow] = []
    for draft in draft_rows:
        payload = load_proposal(root, draft)
        review_rows.append(review_one(root, draft, payload))

    review_rows.sort(key=lambda r: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(r.priority, 9), r.path.lower()))

    class_counts = Counter(row.review_class for row in review_rows)
    status_counts = Counter(row.review_status for row in review_rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_ONLY_GENERATED",
        "report_dir": str(rd),
        "proposal_rows_reviewed": len(review_rows),
        "safe_mechanical_candidates": sum(1 for row in review_rows if row.safe_mechanical_candidate and not row.manual_review_required),
        "manual_review_required": sum(1 for row in review_rows if row.manual_review_required),
        "payload_difference_count": sum(1 for row in review_rows if not row.payload_equivalent),
        "visual_structure_or_indentation_review_count": sum(1 for row in review_rows if row.visual_structure_loss_detected or row.indentation_loss_detected),
        "block_comment_normalization_count": sum(1 for row in review_rows if row.block_comment_normalization),
        "review_class_counts": dict(class_counts.most_common()),
        "review_status_counts": dict(status_counts.most_common()),
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_apply_patches",
            "did_not_create_patch_files",
            "did_not_create_repair_batch",
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

    load_notes = [
        f"read patch proposal draft CSV: {rd / DRAFT_CSV}",
        f"read patch proposal draft JSON: {rd / DRAFT_JSON}" if (rd / DRAFT_JSON).is_file() else f"patch proposal draft JSON missing: {rd / DRAFT_JSON}",
        f"read proposal JSON artifacts under: {PATCH_DIR}",
    ]

    write_csv_report(out_csv, review_rows)
    write_json_report(out_json, summary, review_rows)
    write_md_report(out_md, out_csv, out_json, summary, review_rows, load_notes)

    print("SelfDoc source contract patch proposal review v0 complete.")
    print(f"Read report directory: {rd}")
    print(f"Proposal rows reviewed: {len(review_rows)}")
    print(f"Safe mechanical candidates: {summary['safe_mechanical_candidates']}")
    print(f"Manual review required: {summary['manual_review_required']}")
    print(f"Payload differences: {summary['payload_difference_count']}")
    print(f"Visual/indentation review count: {summary['visual_structure_or_indentation_review_count']}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print("No source files were edited.")
    print("No patches were applied.")
    print("No patch files were created.")
    print("No repair batch was created.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

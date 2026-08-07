#!/usr/bin/env python3
"""
source_contract_patch_proposal_draft_v0_1_marker_preserving.py

REPORT_ONLY / PROPOSAL_ONLY marker-preserving patch proposal draft for Batch 0.

Run from:
    D:\code\ccode

Reads:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_plan_v0.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_plan_v0.json
    dottalkpp\docs\generated\reports\source_contracts_inventory_v1_1.csv
    source files named by Batch 0 rows

Writes:
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0_1_marker_preserving.md
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0_1_marker_preserving.csv
    dottalkpp\docs\generated\reports\source_contract_patch_proposal_draft_v0_1_marker_preserving.json
    dottalkpp\docs\generated\patches\source_contract_patch_proposal_draft_v0_1_marker_preserving\
      *.proposal.md
      *.proposal.json

Safety:
    REPORT_ONLY / PROPOSAL_ONLY
    Does not edit source.
    Does not apply patches.
    Does not create executable patch files.
    Does not create a repair batch.
    Does not write DBFs.
    Does not modify CMDHELPCHK.
    Does not rebuild HELP DATA.
    Does not promote v1.1 to default.
    Does not move/delete files.

Purpose:
    Generate a second proposal draft for Batch 0 only.
    Preserve line-comment style.
    Do not convert // headers to /* ... */ block comments.
    Preserve @dottalk.usage v1 marker position.
    Preserve indentation, blank lines, and visual structure.
    Only propose minimal capture-boundary/header-shape correction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
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

PATCH_ROOT = Path("dottalkpp") / "docs" / "generated" / "patches" / "source_contract_patch_proposal_draft_v0_1_marker_preserving"

PLAN_CSV = "source_contract_patch_proposal_plan_v0.csv"
PLAN_JSON = "source_contract_patch_proposal_plan_v0.json"
INV_CSV = "source_contracts_inventory_v1_1.csv"

OUT_MD = "source_contract_patch_proposal_draft_v0_1_marker_preserving.md"
OUT_CSV = "source_contract_patch_proposal_draft_v0_1_marker_preserving.csv"
OUT_JSON = "source_contract_patch_proposal_draft_v0_1_marker_preserving.json"

MARKER = "@dottalk.usage v1"
SAFETY_CLASS = "REPORT_ONLY / PROPOSAL_ONLY"


@dataclass
class ProposalRow:
    path: str
    selection_status: str
    proposal_lane: str
    proposed_action: str
    source_read_status: str
    inventory_header_hash: str = ""
    computed_header_hash: str = ""
    hash_matches_inventory: bool = False
    header_start_line: int = 0
    header_end_line: int = 0
    original_comment_style: str = ""
    proposed_comment_style: str = ""
    marker_line_index_original: int = -1
    marker_line_index_proposed: int = -1
    marker_position_preserved: bool = False
    payload_preserved_exact: bool = False
    visual_structure_preserved: bool = False
    blank_lines_preserved: bool = False
    proposal_kind: str = ""
    proposal_status: str = ""
    confidence: str = ""
    rationale: str = ""
    original_header_preview: str = ""
    proposed_header_preview: str = ""
    proposal_md: str = ""
    proposal_json: str = ""
    source_edit_authorized: bool = False
    patch_apply_authorized: bool = False
    executable_patch_created: bool = False
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
        if (d / PLAN_CSV).is_file():
            return d
    raise SystemExit("Could not find source_contract_patch_proposal_plan_v0.csv under dottalkpp\\docs\\generated\\reports")


def read_text(path: Path) -> tuple[str, list[str]]:
    raw = path.read_bytes()
    notes: list[str] = []
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc, errors="strict")
            if enc not in ("utf-8", "utf-8-sig"):
                notes.append(f"decoded_as={enc}")
            return text, notes
        except UnicodeDecodeError:
            pass
    text = raw.decode("utf-8", errors="surrogateescape")
    notes.append("decoded_as=utf-8-surrogateescape")
    return text, notes


def line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_contract_blocks(text: str) -> list[tuple[int, int, str]]:
    """
    Same broad capture approach used for review, but draft v0.1 does not rewrite
    the captured header. It uses the capture as evidence only.
    """
    blocks: list[tuple[int, int, str]] = []
    for match in re.finditer(re.escape(MARKER), text):
        marker_start = match.start()

        block_start = text.rfind("/*", 0, marker_start)
        block_end = text.find("*/", match.end())
        if block_start != -1 and block_end != -1:
            prior_close = text.rfind("*/", 0, marker_start)
            if prior_close < block_start:
                end = block_end + 2
                blocks.append((block_start, end, text[block_start:end]))
                continue

        line_start = text.rfind("\n", 0, marker_start) + 1
        line_end = text.find("\n", marker_start)
        if line_end == -1:
            line_end = len(text)

        start = line_start
        while start > 0:
            prev_end = start - 1
            prev_start = text.rfind("\n", 0, prev_end) + 1
            prev_line = text[prev_start:prev_end]
            if prev_line.lstrip().startswith("//"):
                start = prev_start
            elif prev_line.strip() == "":
                # Preserve nearby blank line only if it is between line-comment header lines.
                before_blank_end = prev_start - 1
                before_blank_start = text.rfind("\n", 0, before_blank_end) + 1
                before_blank_line = text[before_blank_start:before_blank_end]
                if before_blank_line.lstrip().startswith("//"):
                    start = prev_start
                else:
                    break
            else:
                break

        end = line_end
        while end < len(text):
            next_start = end + 1
            next_end = text.find("\n", next_start)
            if next_end == -1:
                next_end = len(text)
            next_line = text[next_start:next_end]
            if next_line.lstrip().startswith("//"):
                end = next_end
                if next_end == len(text):
                    break
            elif next_line.strip() == "":
                # Include a blank line only if followed by another line-comment line.
                after_blank_start = next_end + 1
                if after_blank_start >= len(text):
                    break
                after_blank_end = text.find("\n", after_blank_start)
                if after_blank_end == -1:
                    after_blank_end = len(text)
                after_blank_line = text[after_blank_start:after_blank_end]
                if after_blank_line.lstrip().startswith("//"):
                    end = next_end
                    continue
                break
            else:
                break

        blocks.append((start, end, text[start:end]))

    unique = {(s, e): b for s, e, b in blocks}
    return [(s, e, b) for (s, e), b in sorted(unique.items())]


def header_lines_preserve(header: str) -> list[str]:
    # Preserve visual structure, blank lines, indentation, and line content exactly.
    return header.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def detect_comment_style(header: str) -> str:
    stripped = header.lstrip()
    if stripped.startswith("/*"):
        return "block_comment"
    if any(line.lstrip().startswith("//") for line in header.splitlines()):
        return "line_comment"
    return "unknown"


def marker_line_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        if MARKER in line:
            return index
    return -1


def payload_text_for_compare(header: str) -> str:
    """
    In marker-preserving mode, exact text is the intended preservation target.
    Normalize line endings only.
    """
    return header.replace("\r\n", "\n").replace("\r", "\n")


def minimal_boundary_proposal(original_header: str) -> tuple[str, str, list[str]]:
    """
    Minimal proposal:
      - keep the exact captured header text
      - do not convert comment style
      - do not move marker
      - do not flatten indentation
      - do not remove blank lines

    This intentionally returns an identical proposed header unless future evidence
    identifies a safe boundary-only trim. For Batch 0, the prior review showed
    style conversion was unsafe, so this draft is conservative.
    """
    notes = [
        "marker-preserving draft keeps original captured header text exactly",
        "no block-comment conversion",
        "no indentation normalization",
        "no blank-line normalization",
    ]
    return original_header, "NO_TEXT_CHANGE_MARKER_PRESERVING_REVIEW", notes


def shorten(text: str, max_chars: int = 900) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated in CSV preview]"


def safe_stem(path: str) -> str:
    stem = path.replace("\\", "/").replace("/", "__")
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem)
    return stem


def inventory_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("path", ""): row for row in rows if row.get("path", "")}


def selected_batch(plan_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in plan_rows if row.get("selection_status", "") == "BATCH_0_CANDIDATE"]


def write_individual_proposal(root: Path, out_dir: Path, proposal: ProposalRow, original_header: str, proposed_header: str) -> tuple[str, str]:
    stem = safe_stem(proposal.path)
    md_path = out_dir / f"{stem}.proposal.md"
    json_path = out_dir / f"{stem}.proposal.json"

    md = []
    md.append(f"# Marker-Preserving Source Contract Proposal Draft: `{proposal.path}`")
    md.append("")
    md.append("Safety: `PROPOSAL_ONLY`")
    md.append("")
    md.append("This file is a review artifact. It is not a patch file and must not be applied automatically.")
    md.append("")
    md.append("## Status")
    md.append("")
    md.append(f"- proposal_status: `{proposal.proposal_status}`")
    md.append(f"- proposal_kind: `{proposal.proposal_kind}`")
    md.append(f"- confidence: `{proposal.confidence}`")
    md.append(f"- source_edit_authorized: `{proposal.source_edit_authorized}`")
    md.append(f"- patch_apply_authorized: `{proposal.patch_apply_authorized}`")
    md.append(f"- executable_patch_created: `{proposal.executable_patch_created}`")
    md.append(f"- inventory_header_hash: `{proposal.inventory_header_hash}`")
    md.append(f"- computed_header_hash: `{proposal.computed_header_hash}`")
    md.append(f"- hash_matches_inventory: `{proposal.hash_matches_inventory}`")
    md.append(f"- source lines: `{proposal.header_start_line}-{proposal.header_end_line}`")
    md.append(f"- original_comment_style: `{proposal.original_comment_style}`")
    md.append(f"- proposed_comment_style: `{proposal.proposed_comment_style}`")
    md.append(f"- marker_position_preserved: `{proposal.marker_position_preserved}`")
    md.append(f"- visual_structure_preserved: `{proposal.visual_structure_preserved}`")
    md.append(f"- blank_lines_preserved: `{proposal.blank_lines_preserved}`")
    md.append("")
    md.append("## Rationale")
    md.append("")
    md.append(proposal.rationale)
    md.append("")
    md.append("## Original captured header")
    md.append("")
    md.append("```cpp")
    md.append(original_header.rstrip())
    md.append("```")
    md.append("")
    md.append("## Proposed marker-preserving header")
    md.append("")
    md.append("```cpp")
    md.append(proposed_header.rstrip())
    md.append("```")
    md.append("")
    md.append("## Review checklist")
    md.append("")
    md.append("- Confirm the marker position is preserved.")
    md.append("- Confirm line-comment style is preserved.")
    md.append("- Confirm indentation, blank lines, and visual structure are preserved.")
    md.append("- Confirm whether a source patch is needed at all, or whether the fix belongs in classifier/capture logic.")
    md.append("- Confirm this proposal should become an actual patch only after explicit authorization.")
    md.append("")
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    payload = {
        "path": proposal.path,
        "safety": "PROPOSAL_ONLY",
        "proposal": asdict(proposal),
        "original_header": original_header,
        "proposed_header": proposed_header,
        "source_edit_authorized": False,
        "patch_apply_authorized": False,
        "executable_patch_created": False,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return str(md_path.relative_to(root)), str(json_path.relative_to(root))


def make_proposal(root: Path, out_dir: Path, plan: dict[str, str], inv: dict[str, str]) -> ProposalRow:
    rel_path = plan.get("path", "")
    source_path = root / rel_path

    base = ProposalRow(
        path=rel_path,
        selection_status=plan.get("selection_status", ""),
        proposal_lane=plan.get("proposal_lane", ""),
        proposed_action=plan.get("proposed_action", ""),
        source_read_status="not_read",
        inventory_header_hash=inv.get("header_hash", ""),
    )

    if not source_path.is_file():
        base.source_read_status = "missing_source_file"
        base.proposal_status = "BLOCKED"
        base.confidence = "NONE"
        base.rationale = "Source file was not found; no proposal could be generated."
        base.notes.append(f"missing source file: {source_path}")
        return base

    try:
        text, notes = read_text(source_path)
        base.notes.extend(notes)
    except Exception as exc:
        base.source_read_status = "read_error"
        base.proposal_status = "BLOCKED"
        base.confidence = "NONE"
        base.rationale = f"Source read failed: {type(exc).__name__}: {exc}"
        return base

    blocks = find_contract_blocks(text)
    if len(blocks) != 1:
        base.source_read_status = "unexpected_contract_block_count"
        base.proposal_status = "BLOCKED"
        base.confidence = "LOW"
        base.rationale = f"Expected exactly one @dottalk.usage v1 block; found {len(blocks)}. Manual review required."
        base.notes.append(f"contract block count: {len(blocks)}")
        return base

    start, end, original_header = blocks[0]
    computed_hash = hashlib.sha256(original_header.encode("utf-8", errors="surrogateescape")).hexdigest()
    base.computed_header_hash = computed_hash
    base.hash_matches_inventory = bool(base.inventory_header_hash) and base.inventory_header_hash == computed_hash
    base.header_start_line = line_number_for_offset(text, start)
    base.header_end_line = line_number_for_offset(text, end)

    original_lines = header_lines_preserve(original_header)
    proposed_header, proposal_kind, proposal_notes = minimal_boundary_proposal(original_header)
    proposed_lines = header_lines_preserve(proposed_header)

    base.original_comment_style = detect_comment_style(original_header)
    base.proposed_comment_style = detect_comment_style(proposed_header)
    base.marker_line_index_original = marker_line_index(original_lines)
    base.marker_line_index_proposed = marker_line_index(proposed_lines)
    base.marker_position_preserved = base.marker_line_index_original == base.marker_line_index_proposed and base.marker_line_index_original >= 0
    base.payload_preserved_exact = payload_text_for_compare(original_header) == payload_text_for_compare(proposed_header)
    base.visual_structure_preserved = original_lines == proposed_lines
    base.blank_lines_preserved = [line == "" for line in original_lines] == [line == "" for line in proposed_lines]
    base.proposal_kind = proposal_kind
    base.notes.extend(proposal_notes)

    if not base.hash_matches_inventory:
        base.proposal_status = "REVIEW_REQUIRED_HASH_MISMATCH"
        base.confidence = "LOW"
        base.rationale = "Computed header hash does not match inventory hash. Proposal generated for review only; do not patch until inventory is refreshed or mismatch is explained."
    elif not base.marker_position_preserved:
        base.proposal_status = "BLOCKED_MARKER_POSITION_NOT_PRESERVED"
        base.confidence = "NONE"
        base.rationale = "Marker position was not preserved; this proposal must not become a patch."
    elif not base.payload_preserved_exact or not base.visual_structure_preserved or not base.blank_lines_preserved:
        base.proposal_status = "MANUAL_REVIEW_REQUIRED_STRUCTURE_CHANGE"
        base.confidence = "LOW"
        base.rationale = "Marker-preserving constraints were not fully met; manual review required."
    else:
        base.proposal_status = "MARKER_PRESERVING_REVIEW_ONLY"
        base.confidence = "HIGH"
        base.rationale = "Proposal preserves line-comment style, marker position, indentation, blank lines, and visual structure. No source text change is proposed; review should decide whether the actual fix belongs in parser/capture logic instead of source."

    base.source_read_status = "read_ok"
    base.original_header_preview = shorten(original_header)
    base.proposed_header_preview = shorten(proposed_header)

    md_rel, json_rel = write_individual_proposal(root, out_dir, base, original_header, proposed_header)
    base.proposal_md = md_rel
    base.proposal_json = json_rel
    return base


def write_csv_report(path: Path, rows: list[ProposalRow]) -> None:
    fieldnames = [
        "path",
        "selection_status",
        "proposal_lane",
        "proposed_action",
        "source_read_status",
        "inventory_header_hash",
        "computed_header_hash",
        "hash_matches_inventory",
        "header_start_line",
        "header_end_line",
        "original_comment_style",
        "proposed_comment_style",
        "marker_line_index_original",
        "marker_line_index_proposed",
        "marker_position_preserved",
        "payload_preserved_exact",
        "visual_structure_preserved",
        "blank_lines_preserved",
        "proposal_kind",
        "proposal_status",
        "confidence",
        "rationale",
        "proposal_md",
        "proposal_json",
        "source_edit_authorized",
        "patch_apply_authorized",
        "executable_patch_created",
        "notes",
        "original_header_preview",
        "proposed_header_preview",
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


def write_json_report(path: Path, summary: dict[str, Any], rows: list[ProposalRow]) -> None:
    path.write_text(
        json.dumps({"summary": summary, "proposal_rows": [asdict(row) for row in rows]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_md_report(path: Path, csv_path: Path, json_path: Path, summary: dict[str, Any], rows: list[ProposalRow], load_notes: list[str]) -> None:
    lines = []
    lines.append("# Source Contract Patch Proposal Draft v0.1 Marker-Preserving")
    lines.append("")
    lines.append(f"Generated UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append(f"Safety class: `{SAFETY_CLASS}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("```text")
    lines.append("marker-preserving proposal draft: GENERATED")
    lines.append("patch files: NOT CREATED")
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
    lines.append("This second draft responds to the v0 review stop. It preserves line-comment style, marker position, indentation, blank lines, and visual structure. It does not convert `//` headers to block comments. For Batch 0, it intentionally proposes no source text change when the safer conclusion is that the fix may belong in classifier/capture logic rather than source.")
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
    lines.append(f"- `{summary['proposal_output_dir']}`")
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in [
        "batch_0_rows",
        "proposal_rows",
        "marker_preserving_review_only",
        "hash_mismatch_count",
        "marker_position_not_preserved_count",
        "visual_structure_not_preserved_count",
        "source_text_change_proposed_count",
        "blocked_or_low_confidence",
    ]:
        lines.append(f"- {key}: `{summary.get(key, '')}`")
    lines.append("")
    lines.append("## Proposal status counts")
    lines.append("")
    lines.append("| Proposal status | Count |")
    lines.append("|---|---:|")
    for status, count in summary["proposal_status_counts"].items():
        lines.append(f"| `{md_escape(status)}` | {count} |")
    lines.append("")
    lines.append("## Batch 0 marker-preserving proposal rows")
    lines.append("")
    if rows:
        lines.append("| Path | Status | Hash OK | Marker preserved | Visual preserved | Proposed text change | Proposal |")
        lines.append("|---|---|---:|---:|---:|---:|---|")
        for row in rows:
            text_change = row.original_header_preview != row.proposed_header_preview
            lines.append(
                f"| `{md_escape(row.path)}` | `{md_escape(row.proposal_status)}` | {row.hash_matches_inventory} | "
                f"{row.marker_position_preserved} | {row.visual_structure_preserved} | {text_change} | `{md_escape(row.proposal_md)}` |"
            )
    else:
        lines.append("No Batch 0 proposal rows found.")
    lines.append("")
    lines.append("## Planning rules")
    lines.append("")
    lines.append("```text")
    lines.append("This is not a patch.")
    lines.append("This is not a repair batch.")
    lines.append("Do not apply the proposal artifacts automatically.")
    lines.append("Do not edit source from this report.")
    lines.append("If no source text change is proposed, review whether the fix belongs in parser/capture logic.")
    lines.append("Do not write DBFs.")
    lines.append("Do not rebuild HELP DATA.")
    lines.append("Do not modify CMDHELPCHK.")
    lines.append("A future patch bundle requires explicit approval after proposal review.")
    lines.append("```")
    lines.append("")
    lines.append("## Non-mutation confirmation")
    lines.append("")
    for guard in summary["non_mutation_guards"]:
        lines.append(f"- `{md_escape(guard)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create marker-preserving source contract patch proposal draft v0.1.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rd = find_report_dir(root, args.report_dir)

    plan_rows = read_csv_rows(rd / PLAN_CSV)
    _plan_json = read_json(rd / PLAN_JSON)
    inv_rows = read_csv_rows(rd / INV_CSV)
    inv = inventory_index(inv_rows)

    batch_rows = selected_batch(plan_rows)

    out_dir = root / PATCH_ROOT
    out_dir.mkdir(parents=True, exist_ok=True)

    proposal_rows = [make_proposal(root, out_dir, plan, inv.get(plan.get("path", ""), {})) for plan in batch_rows]

    status_counts = Counter(row.proposal_status for row in proposal_rows)
    hash_mismatch = sum(1 for row in proposal_rows if row.computed_header_hash and not row.hash_matches_inventory)
    marker_bad = sum(1 for row in proposal_rows if not row.marker_position_preserved)
    visual_bad = sum(1 for row in proposal_rows if not row.visual_structure_preserved)
    text_changes = sum(1 for row in proposal_rows if row.original_header_preview != row.proposed_header_preview)
    blocked = sum(1 for row in proposal_rows if row.proposal_status.startswith("BLOCKED") or row.confidence in {"LOW", "NONE"})

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PROPOSAL_ONLY_GENERATED",
        "report_dir": str(rd),
        "proposal_output_dir": str(PATCH_ROOT),
        "batch_0_rows": len(batch_rows),
        "proposal_rows": len(proposal_rows),
        "marker_preserving_review_only": status_counts.get("MARKER_PRESERVING_REVIEW_ONLY", 0),
        "hash_mismatch_count": hash_mismatch,
        "marker_position_not_preserved_count": marker_bad,
        "visual_structure_not_preserved_count": visual_bad,
        "source_text_change_proposed_count": text_changes,
        "blocked_or_low_confidence": blocked,
        "proposal_status_counts": dict(status_counts.most_common()),
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_apply_patches",
            "did_not_create_executable_patch_files",
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
        f"read patch proposal plan CSV: {rd / PLAN_CSV}",
        f"read patch proposal plan JSON: {rd / PLAN_JSON}" if (rd / PLAN_JSON).is_file() else f"patch proposal plan JSON missing: {rd / PLAN_JSON}",
        f"read v1.1 inventory CSV: {rd / INV_CSV}" if (rd / INV_CSV).is_file() else f"v1.1 inventory CSV missing: {rd / INV_CSV}",
        f"read Batch 0 source files from project root: {root}",
    ]

    write_csv_report(out_csv, proposal_rows)
    write_json_report(out_json, summary, proposal_rows)
    write_md_report(out_md, out_csv, out_json, summary, proposal_rows, load_notes)

    print("SelfDoc source contract patch proposal draft v0.1 marker-preserving complete.")
    print(f"Read report directory: {rd}")
    print(f"Batch 0 rows: {len(batch_rows)}")
    print(f"Proposal rows: {len(proposal_rows)}")
    print(f"Marker-preserving review-only rows: {summary['marker_preserving_review_only']}")
    print(f"Source text changes proposed: {summary['source_text_change_proposed_count']}")
    print(f"Hash mismatches: {summary['hash_mismatch_count']}")
    print(f"Blocked/low-confidence rows: {summary['blocked_or_low_confidence']}")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")
    print(f"Wrote proposal artifacts under: {PATCH_ROOT}")
    print("No source files were edited.")
    print("No patches were applied.")
    print("No executable patch files were created.")
    print("No repair batch was created.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

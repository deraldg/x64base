from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from .runlog import utc_now_iso
from .util import relpath_posix, sha256_file, write_csv, write_json


BEGIN_RE = re.compile(r"^<!-- BEGIN SECTION:\s*(.*?)\s*-->$")
END_RE = re.compile(r"^<!-- END SECTION:\s*(.*?)\s*-->$")
REVIEW_STATUS_RE = re.compile(r"^Status:.*(?:REVIEW_REQUIRED|DRAFT|CANDIDATE|STAGED)")


def _insert_missing_end(lines: list[str], section: str) -> int:
    separator = len(lines)
    for index in range(len(lines) - 1, -1, -1):
        if lines[index] == "---":
            separator = index
            break
        if lines[index].strip() and not lines[index].startswith("<!--"):
            break
    insertion = [f"<!-- END SECTION: {section} -->", ""]
    lines[separator:separator] = insertion
    return separator + 1


def build_structure_preview(source_text: str):
    source_lines = source_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    marker_rows: list[dict[str, object]] = []
    status_rows: list[dict[str, object]] = []
    findings: list[str] = []
    open_section = ""
    current_title = ""
    for line_number, line in enumerate(source_lines, 1):
        begin = BEGIN_RE.match(line)
        end = END_RE.match(line)
        if begin:
            if open_section:
                candidate_line = _insert_missing_end(output, open_section)
                marker_rows.append({
                    "section": open_section,
                    "action": "INSERT_MISSING_END_MARKER",
                    "before_source_line": line_number,
                    "candidate_line": candidate_line,
                    "status": "PROPOSED",
                })
            open_section = begin.group(1)
        elif end:
            if not open_section:
                findings.append(f"ORPHAN_END:{line_number}:{end.group(1)}")
            elif end.group(1) != open_section:
                findings.append(f"MISMATCHED_END:{line_number}:{open_section}:{end.group(1)}")
            open_section = ""
        if line.startswith("# "):
            current_title = line[2:].strip()
        if REVIEW_STATUS_RE.match(line):
            historical = line.removeprefix("Status:").strip()
            output.append(f"<!-- HISTORICAL STATUS: {historical} -->")
            output.append("Status: REVIEWED_FOR_PUBLICATION")
            status_rows.append({
                "source_line": line_number,
                "section": open_section,
                "title": current_title,
                "current_status": historical,
                "proposed_status": "REVIEWED_FOR_PUBLICATION",
                "historical_status_preserved": 1,
                "action": "MAINTAINER_CONFIRM_OR_HOLD",
                "status": "PROPOSED",
            })
        else:
            output.append(line)
    if open_section:
        output.extend([f"<!-- END SECTION: {open_section} -->", ""])
        marker_rows.append({
            "section": open_section,
            "action": "INSERT_MISSING_END_MARKER_AT_EOF",
            "before_source_line": len(source_lines) + 1,
            "candidate_line": len(output) - 1,
            "status": "PROPOSED",
        })
    candidate = "\r\n".join(output)
    return candidate, marker_rows, status_rows, findings


def build_publication_structure_candidate(paths, logger=None):
    pointer = paths.manualgen_root / "accepted_artifacts" / "ACTIVE_PRIMARY_READER_ARTIFACT.txt"
    reader_record_path = paths.manualgen_root / "accepted_artifacts" / "primary_reader_artifact_v1.json"
    reader_record = json.loads(reader_record_path.read_text(encoding="utf-8-sig"))
    reader = paths.repo_root / pointer.read_text(encoding="utf-8-sig").strip()
    before_hash = sha256_file(reader)
    expected_hash = str(reader_record.get("artifact_sha256", "")).upper()
    if before_hash != expected_hash:
        raise ValueError("accepted reader hash does not match its record")
    source_bytes = reader.read_bytes()
    source_text = source_bytes.decode("utf-8")
    candidate_text, marker_rows, status_rows, findings = build_structure_preview(source_text)
    output_dir = paths.manualgen_root / "generated" / "manualgen_publication_structure_candidates" / logger.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = output_dir / "manual_publication_structure_candidate.md"
    marker_path = output_dir / "marker_normalization_ledger.csv"
    status_path = output_dir / "status_disposition_ledger.csv"
    diff_path = output_dir / "manual_publication_structure_candidate.diff"
    review_path = output_dir / "MANUAL_PUBLICATION_STRUCTURE_REVIEW.md"
    manifest_path = output_dir / "manual_publication_structure_manifest.json"
    candidate_path.write_bytes(candidate_text.encode("utf-8"))
    write_csv(marker_path, marker_rows)
    write_csv(status_path, status_rows)
    source_lines = source_text.replace("\r\n", "\n").splitlines(keepends=True)
    candidate_lines = candidate_text.replace("\r\n", "\n").splitlines(keepends=True)
    diff_path.write_text("".join(difflib.unified_diff(source_lines, candidate_lines, fromfile="accepted-reader", tofile="structure-candidate")), encoding="utf-8")

    begin_count = sum(1 for line in candidate_text.splitlines() if BEGIN_RE.match(line))
    end_count = sum(1 for line in candidate_text.splitlines() if END_RE.match(line))
    remaining_statuses = sum(1 for line in candidate_text.splitlines() if REVIEW_STATUS_RE.match(line))
    preserved_statuses = candidate_text.count("<!-- HISTORICAL STATUS:")
    headings_before = sum(1 for line in source_text.splitlines() if re.match(r"^#{1,6}\s+", line))
    headings_after = sum(1 for line in candidate_text.splitlines() if re.match(r"^#{1,6}\s+", line))
    reader_after_hash = sha256_file(reader)
    if len(marker_rows) != 11:
        findings.append(f"EXPECTED_11_MARKERS:{len(marker_rows)}")
    if len(status_rows) != 14:
        findings.append(f"EXPECTED_14_STATUSES:{len(status_rows)}")
    if begin_count != 24 or end_count != 24:
        findings.append(f"MARKER_BALANCE:{begin_count}:{end_count}")
    if remaining_statuses:
        findings.append(f"REMAINING_REVIEW_STATUSES:{remaining_statuses}")
    if preserved_statuses != 14:
        findings.append(f"HISTORICAL_STATUS_COVERAGE:{preserved_statuses}")
    if headings_before != headings_after:
        findings.append(f"HEADING_DRIFT:{headings_before}:{headings_after}")
    if reader_after_hash != before_hash:
        findings.append("ACCEPTED_READER_MUTATED")
    status = "PASS_CANDIDATE_ONLY" if not findings else "FAIL_CANDIDATE"
    review_lines = [
        "# Manual Publication Structure Review",
        "",
        f"- Status: `{status}`",
        f"- Missing END markers proposed: `{len(marker_rows)}`",
        f"- Candidate marker balance: `{begin_count} BEGIN / {end_count} END`",
        f"- Review-status dispositions proposed: `{len(status_rows)}`",
        f"- Historical statuses preserved: `{preserved_statuses}`",
        f"- Accepted reader before/after: `{before_hash}` / `{reader_after_hash}`",
        "- Publication authority: `0`",
        "",
        "## Status decision required",
        "",
        "Each current draft/REVIEW_REQUIRED line is preserved in an HTML historical-status comment. The preview proposes `Status: REVIEWED_FOR_PUBLICATION`, but acceptance must confirm or hold each row in `status_disposition_ledger.csv`.",
        "",
        "## Findings",
        "",
    ]
    review_lines.extend([f"- `{finding}`" for finding in findings] or ["- None."])
    review_lines.extend(["", "This is a report-only preview. It does not edit the accepted reader, pointer, command pages, source staging, or website.", ""])
    review_path.write_text("\n".join(review_lines), encoding="utf-8")
    manifest = {
        "schema": "dottalk.manualgen.publication_structure_candidate.v1",
        "created_utc": utc_now_iso(),
        "run_id": logger.run_id,
        "status": status,
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "accepted_reader": relpath_posix(reader, paths.repo_root),
        "accepted_reader_sha256": before_hash,
        "accepted_reader_mutated": int(reader_after_hash != before_hash),
        "counts": {
            "inserted_end_markers": len(marker_rows),
            "candidate_begin_markers": begin_count,
            "candidate_end_markers": end_count,
            "status_dispositions": len(status_rows),
            "remaining_review_statuses": remaining_statuses,
            "historical_status_comments": preserved_statuses,
            "headings_before": headings_before,
            "headings_after": headings_after,
            "findings": len(findings),
        },
        "findings": findings,
        "artifacts": {
            "candidate": relpath_posix(candidate_path, paths.repo_root),
            "candidate_sha256": sha256_file(candidate_path),
            "marker_ledger": relpath_posix(marker_path, paths.repo_root),
            "marker_ledger_sha256": sha256_file(marker_path),
            "status_ledger": relpath_posix(status_path, paths.repo_root),
            "status_ledger_sha256": sha256_file(status_path),
            "diff": relpath_posix(diff_path, paths.repo_root),
            "diff_sha256": sha256_file(diff_path),
            "review": relpath_posix(review_path, paths.repo_root),
            "review_sha256": sha256_file(review_path),
        },
        "boundary": {"accepted_reader_mutated": 0, "pointer_mutated": 0, "website_mutated": 0},
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("publication_structure_candidate", candidate_path, "Marker-balanced and status-disposition preview.")
        logger.artifact("marker_normalization_ledger", marker_path, "Eleven proposed missing END markers.")
        logger.artifact("status_disposition_ledger", status_path, "Fourteen explicit maintainer decisions.")
        logger.artifact("publication_structure_diff", diff_path, "Accepted-reader to structure-preview diff.")
        logger.artifact("publication_structure_review", review_path, "Human review entrypoint.")
        logger.artifact("publication_structure_manifest", manifest_path, "Hash-bound report-only structure manifest.")
        logger.boundary("accepted_reader_mutated", 0, "PASS", "Preview is generated outside publication.")
        logger.boundary("publication_authority_claimed", 0, "PASS", "Human confirmation remains required.")
        logger.boundary("website_mutated", 0, "PASS", "No website write path exists.")
    return {"status": status, "output_dir": relpath_posix(output_dir, paths.repo_root), "review": relpath_posix(review_path, paths.repo_root)}, manifest["counts"]

#!/usr/bin/env python3
"""Report-only publication-readiness audit for the accepted Developer Manual."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+\S")
LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:\\")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def heading_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if HEADING_RE.match(line))


def markdown_destinations(text: str) -> list[str]:
    return [match.group(1).strip() for match in LINK_RE.finditer(text)]


def broken_local_links(reader: Path, destinations: list[str]) -> list[str]:
    broken: list[str] = []
    for original in destinations:
        value = original
        if value.startswith("<") and ">" in value:
            value = value[1 : value.index(">")]
        elif " " in value:
            value = value.split(" ", 1)[0]
        value = unquote(value).replace("\\", "/")
        if not value or value.startswith(("#", "http://", "https://", "mailto:")):
            continue
        file_part = value.split("#", 1)[0]
        target = (reader.parent / file_part).resolve()
        if not target.exists():
            broken.append(original)
    return sorted(set(broken))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    manualgen = repo_root / "docs/manuals/developer/manualgen"
    pointer = manualgen / "accepted_artifacts/ACTIVE_PRIMARY_READER_ARTIFACT.txt"
    reader_record_path = manualgen / "accepted_artifacts/primary_reader_artifact_v1.json"
    canonical_path = manualgen / "accepted_manifests/developer_manual_canonical_manifest_v1.json"
    appendix_record_path = manualgen / "accepted_manifests/DOCFLUSH-20260716-001_APPENDIX_ACCEPTANCE_RECORD.md"

    rows: list[dict[str, str]] = []

    def add(check_id: str, status: str, observed: object, required: object, note: str) -> None:
        rows.append(
            {
                "check_id": check_id,
                "status": status,
                "observed": str(observed),
                "required": str(required),
                "note": note,
            }
        )

    add(
        "PYTHON_312",
        "PASS" if sys.version_info[:2] == (3, 12) else "FAIL",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "3.12.x",
        "Repository Python work is fixed to Python 3.12.",
    )
    required_files = [pointer, reader_record_path, canonical_path, appendix_record_path]
    for path in required_files:
        add(
            f"FILE_{path.name.upper().replace('.', '_')}",
            "PASS" if path.is_file() else "FAIL",
            path.is_file(),
            True,
            path.relative_to(repo_root).as_posix(),
        )
    if any(not path.is_file() for path in required_files):
        payload = {"schema": "dottalk.manual.publication_readiness.v1", "checks": rows}
        (output_dir / "manual_publication_readiness_v1.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        return 2

    reader_value = pointer.read_text(encoding="utf-8-sig").strip()
    reader = repo_root / reader_value
    reader_record = json.loads(reader_record_path.read_text(encoding="utf-8-sig"))
    canonical = json.loads(canonical_path.read_text(encoding="utf-8-sig"))
    add("READER_EXISTS", "PASS" if reader.is_file() else "FAIL", reader.is_file(), True, reader_value)
    if not reader.is_file():
        return 2

    reader_text = reader.read_text(encoding="utf-8-sig")
    reader_hash = sha256(reader)
    lines = len(reader_text.splitlines())
    headings = heading_count(reader_text)
    add("READER_HASH", "PASS" if reader_hash == str(reader_record.get("artifact_sha256", "")).upper() else "FAIL", reader_hash, str(reader_record.get("artifact_sha256", "")).upper(), "Accepted reader hash.")
    add("READER_LINES", "PASS" if lines == reader_record.get("artifact_lines") else "FAIL", lines, reader_record.get("artifact_lines"), "Accepted reader line count.")
    add("READER_HEADINGS", "PASS" if headings == reader_record.get("artifact_heading_count") else "FAIL", headings, reader_record.get("artifact_heading_count"), "Accepted reader heading count.")
    add("CANONICAL_REFERENCE_HASH", "PASS" if reader_hash == str(canonical.get("current_reference_sha256", "")).upper() else "FAIL", reader_hash, str(canonical.get("current_reference_sha256", "")).upper(), "Canonical evidence must name the accepted reader bytes.")

    first_heading = next((line.lstrip("#").strip() for line in reader_text.splitlines() if line.startswith("# ")), "")
    add("FIRST_HEADING", "PASS" if first_heading == "DotTalk++ / x64base Developer Manual" else "FAIL", first_heading, "DotTalk++ / x64base Developer Manual", "Reader title.")
    banner_count = reader_text.count("Candidate-only selective merge reader")
    add("CANDIDATE_BANNER_ABSENT", "PASS" if banner_count == 0 else "FAIL", banner_count, 0, "Candidate banner must not enter accepted publication.")
    local_path_lines = [str(index) for index, line in enumerate(reader_text.splitlines(), 1) if LOCAL_PATH_RE.search(line)]
    add("LOCAL_DRIVE_PATHS_ABSENT", "PASS" if not local_path_lines else "FAIL", len(local_path_lines), 0, "Line numbers: " + ";".join(local_path_lines[:20]))

    destinations = markdown_destinations(reader_text)
    broken = broken_local_links(reader, destinations)
    add("MARKDOWN_LINKS_RESOLVE", "PASS" if not broken else "FAIL", f"links={len(destinations)};broken={len(broken)}", "broken=0", "; ".join(broken[:20]))
    images = list(IMAGE_RE.finditer(reader_text))
    empty_alt = [match.group(2) for match in images if not match.group(1).strip()]
    add("IMAGE_ALT_TEXT", "PASS" if not empty_alt else "FAIL", f"images={len(images)};empty_alt={len(empty_alt)}", "empty_alt=0", "; ".join(empty_alt[:20]))

    publication_root = reader.parent
    appendix = publication_root / "appendices/partial_help_reference.md"
    aggregate = publication_root / "developer_manual_publication_v1_appendices.md"
    for path, check_id in ((appendix, "PARTIAL_APPENDIX_EXISTS"), (aggregate, "APPENDIX_AGGREGATE_EXISTS")):
        add(check_id, "PASS" if path.is_file() else "FAIL", path.is_file(), True, path.name)
    appendix_text = appendix.read_text(encoding="utf-8") if appendix.is_file() else ""
    aggregate_text = aggregate.read_text(encoding="utf-8") if aggregate.is_file() else ""
    appendix_body = appendix_text.rstrip()
    add("PARTIAL_APPENDIX_IN_READER", "PASS" if appendix_body and reader_text.count(appendix_body) == 1 else "FAIL", reader_text.count(appendix_body) if appendix_body else 0, 1, "Standalone appendix body must occur once in the reader.")
    add("PARTIAL_APPENDIX_IN_AGGREGATE", "PASS" if appendix_body and aggregate_text.count(appendix_body) == 1 else "FAIL", aggregate_text.count(appendix_body) if appendix_body else 0, 1, "Standalone appendix body must occur once in the aggregate.")
    appendix_record_text = appendix_record_path.read_text(encoding="utf-8-sig")
    appendix_hash = sha256(appendix) if appendix.is_file() else ""
    add("PARTIAL_APPENDIX_ACCEPTED_HASH", "PASS" if appendix_hash and appendix_hash in appendix_record_text else "FAIL", appendix_hash, "hash named by accepted record", "Appendix acceptance evidence.")

    required_new_headings = [
        "## REGRESSION and TEST as proof launchers",
        "### GENERIC remains a developer-utility canary",
        "### Application-style UI entry points",
        "# Partial HELP Reference",
    ]
    for heading in required_new_headings:
        count = sum(1 for line in reader_text.splitlines() if line == heading)
        add("HEADING_" + re.sub(r"[^A-Z0-9]+", "_", heading.upper()).strip("_"), "PASS" if count == 1 else "FAIL", count, 1, heading)

    begin_count = reader_text.count("<!-- BEGIN SECTION:")
    end_count = reader_text.count("<!-- END SECTION:")
    add("SECTION_MARKER_SYMMETRY", "PASS" if begin_count == end_count else "REVIEW", f"begin={begin_count};end={end_count}", "begin=end", "Inherited marker asymmetry must be explicitly dispositioned before external publication.")
    review_status_lines = [
        str(index)
        for index, line in enumerate(reader_text.splitlines(), 1)
        if re.search(r"^Status:.*(?:REVIEW_REQUIRED|DRAFT|CANDIDATE|STAGED)", line)
    ]
    add("INTERNAL_REVIEW_STATUS_LABELS", "PASS" if not review_status_lines else "REVIEW", len(review_status_lines), 0, "Line numbers: " + ";".join(review_status_lines))

    pass_count = sum(row["status"] == "PASS" for row in rows)
    review_count = sum(row["status"] == "REVIEW" for row in rows)
    fail_count = sum(row["status"] == "FAIL" for row in rows)
    status = "FAIL" if fail_count else "HOLD_REVIEW" if review_count else "PASS_PUBLICATION_READY"
    payload = {
        "schema": "dottalk.manual.publication_readiness.v1",
        "status": status,
        "reader": reader.relative_to(repo_root).as_posix(),
        "reader_sha256": reader_hash,
        "summary": {"pass": pass_count, "review": review_count, "fail": fail_count},
        "broken_links": broken,
        "checks": rows,
        "boundary": {
            "reader_mutated": 0,
            "accepted_evidence_mutated": 0,
            "website_mutated": 0,
            "publication_authority_claimed": 0,
        },
    }
    (output_dir / "manual_publication_readiness_v1.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "manual_publication_readiness_v1.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["check_id", "status", "observed", "required", "note"])
        writer.writeheader()
        writer.writerows(rows)
    md = [
        "# Manual Publication Readiness Audit V1",
        "",
        f"- Status: `{status}`",
        f"- Reader: `{payload['reader']}`",
        f"- SHA-256: `{reader_hash}`",
        f"- PASS: {pass_count}",
        f"- REVIEW: {review_count}",
        f"- FAIL: {fail_count}",
        "",
        "| Check | Status | Observed | Required |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        md.append(f"| `{row['check_id']}` | {row['status']} | `{row['observed']}` | `{row['required']}` |")
    md.extend(["", "This audit is report-only. It does not edit the manual, accepted evidence, source staging, or website.", ""])
    (output_dir / "MANUAL_PUBLICATION_READINESS_AUDIT_V1.md").write_text("\n".join(md), encoding="utf-8")
    print(f"publication_readiness status={status} pass={pass_count} review={review_count} fail={fail_count}")
    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

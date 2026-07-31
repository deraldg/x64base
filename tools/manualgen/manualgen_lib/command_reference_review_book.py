from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .command_reference_candidate import _shift_markdown_headings
from .runlog import utc_now_iso
from .util import read_csv, relpath_posix, sha256_file, write_json


def _hash_status(path: Path, expected: str) -> str:
    actual = sha256_file(path)
    if actual == expected:
        return "EXACT"
    data = path.read_bytes()
    candidates = {
        data.replace(b"\r\n", b"\n"),
        data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"),
    }
    if any(hashlib.sha256(candidate).hexdigest().upper() == expected for candidate in candidates):
        return "NEWLINE_EQUIVALENT"
    return "MISMATCH"


def build_command_reference_review_book(paths, candidate_run: str, logger=None):
    source_dir = paths.manualgen_root / "generated" / "manualgen_command_reference_candidates" / candidate_run
    source_manifest_path = source_dir / "command_reference_candidate_manifest.json"
    if not source_manifest_path.is_file():
        raise ValueError(f"missing candidate manifest: {source_manifest_path}")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8-sig"))
    if source_manifest.get("schema") != "dottalk.manualgen.command_reference_candidate.v1":
        raise ValueError("candidate schema mismatch")
    if source_manifest.get("run_id") != candidate_run or source_manifest.get("status") != "PASS_CANDIDATE_ONLY":
        raise ValueError("candidate identity or status mismatch")
    if source_manifest.get("candidate_only") != 1 or source_manifest.get("publication_authority_claimed") != 0:
        raise ValueError("candidate authority boundary mismatch")
    ledger_path = paths.repo_root / source_manifest["artifacts"]["ledger"]
    if sha256_file(ledger_path) != source_manifest["artifacts"]["ledger_sha256"]:
        raise ValueError("candidate ledger hash mismatch")
    ledger = read_csv(ledger_path)
    expected = int(source_manifest["counts"]["candidate_pages"])
    if len(ledger) != expected:
        raise ValueError(f"candidate ledger coverage mismatch: {len(ledger)}/{expected}")

    verified_pages: list[tuple[dict[str, str], Path, str]] = []
    for row in ledger:
        page = paths.repo_root / row["candidate_path"]
        if not page.is_file():
            raise ValueError(f"candidate page missing: {row.get('slug', '')}")
        hash_status = _hash_status(page, row["candidate_sha256"])
        if hash_status == "MISMATCH":
            raise ValueError(f"candidate page hash mismatch: {row.get('slug', '')}")
        try:
            page.resolve().relative_to(source_dir.resolve())
        except ValueError as exc:
            raise ValueError(f"candidate page escapes source run: {page}") from exc
        verified_pages.append((row, page, hash_status))

    output_dir = paths.manualgen_root / "generated" / "manualgen_command_reference_review_books" / logger.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "COMMAND_REFERENCE_REVIEW_INDEX.md"
    combined_path = output_dir / "COMMAND_REFERENCE_COMBINED_REVIEW.md"
    manifest_path = output_dir / "command_reference_review_book_manifest.json"
    relative_source = f"../../manualgen_command_reference_candidates/{candidate_run}/commands"
    index_lines = [
        "<!-- REVIEW ONLY: no publication authority. -->",
        "# Command Reference Review Index",
        "",
        f"All **{len(verified_pages)}** hash-verified candidate pages are listed below.",
        "",
        "- [Open the single combined review book](COMMAND_REFERENCE_COMBINED_REVIEW.md)",
        "",
        "| # | Command | Topic | Status | Evidence rows |",
        "| ---: | --- | --- | --- | ---: |",
    ]
    combined_lines = [
        "<!-- REVIEW ONLY: no publication authority. -->",
        "# Command Reference — Combined Review Book",
        "",
        f"This file contains all **{len(verified_pages)}** hash-verified candidate pages from `{candidate_run}`.",
        "",
        "[Open the alphabetical page index](COMMAND_REFERENCE_REVIEW_INDEX.md)",
        "",
    ]
    attention = 0
    newline_equivalent_pages: list[str] = []
    for number, (row, page, hash_status) in enumerate(verified_pages, 1):
        if hash_status == "NEWLINE_EQUIVALENT":
            newline_equivalent_pages.append(row["slug"])
        limited = row.get("attention_label") == "1"
        attention += int(limited)
        marker = " ⚠" if limited else ""
        index_lines.append(
            f"| {number} | [{row['label']}]({relative_source}/{row['slug']}.md){marker} | `{row['topic_key']}` | `{row['status']}` | {row['included_help_rows']} |"
        )
        combined_lines.extend(["---", "", _shift_markdown_headings(page.read_text(encoding="utf-8").rstrip()), ""])
    index_lines.extend(["", "⚠ marks partial, pending, or unsupported source status.", ""])
    index_path.write_text("\n".join(index_lines), encoding="utf-8")
    combined_path.write_text("\n".join(combined_lines).rstrip() + "\n", encoding="utf-8")

    pointer = paths.manualgen_root / "accepted_artifacts" / "ACTIVE_PRIMARY_READER_ARTIFACT.txt"
    reader = paths.repo_root / pointer.read_text(encoding="utf-8-sig").strip()
    current_reader_hash = sha256_file(reader)
    bound_reader_hash = source_manifest["bindings"]["accepted_reader_sha256"]
    current_reader_hash_status = _hash_status(reader, bound_reader_hash)
    manifest = {
        "schema": "dottalk.manualgen.command_reference_review_book.v1",
        "created_utc": utc_now_iso(),
        "run_id": logger.run_id,
        "status": "PASS_REVIEW_ONLY",
        "review_only": 1,
        "publication_authority_claimed": 0,
        "source_candidate_run": candidate_run,
        "source_candidate_manifest": relpath_posix(source_manifest_path, paths.repo_root),
        "source_candidate_manifest_sha256": sha256_file(source_manifest_path),
        "bound_reader_sha256": bound_reader_hash,
        "current_reader_sha256": current_reader_hash,
        "current_reader_hash_matches_bound": int(current_reader_hash == bound_reader_hash),
        "current_reader_hash_status": current_reader_hash_status,
        "counts": {
            "verified_pages": len(verified_pages),
            "index_links": len(verified_pages),
            "combined_pages": len(verified_pages),
            "attention_labelled_pages": attention,
            "page_hash_failures": 0,
            "exact_hash_pages": len(verified_pages) - len(newline_equivalent_pages),
            "newline_equivalent_pages": len(newline_equivalent_pages),
        },
        "newline_equivalent_page_slugs": newline_equivalent_pages,
        "artifacts": {
            "index": relpath_posix(index_path, paths.repo_root),
            "index_sha256": sha256_file(index_path),
            "combined": relpath_posix(combined_path, paths.repo_root),
            "combined_sha256": sha256_file(combined_path),
        },
        "boundary": {
            "source_candidate_mutated": 0,
            "accepted_reader_mutated": 0,
            "website_mutated": 0,
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("command_reference_review_index", index_path, "Index linking all hash-verified candidate pages.")
        logger.artifact("command_reference_combined_review", combined_path, "Single-file review book containing all candidate pages.")
        logger.artifact("command_reference_review_book_manifest", manifest_path, "Review-only book manifest.")
        logger.boundary("source_candidate_mutated", 0, "PASS", "Existing hash-bound candidate remains unchanged.")
        logger.boundary("accepted_reader_mutated", 0, "PASS", "Review-book generation does not write the accepted reader.")
        logger.boundary("publication_authority_claimed", 0, "PASS", "Review book has no publication authority.")
    return {
        "status": "PASS_REVIEW_ONLY",
        "output_dir": relpath_posix(output_dir, paths.repo_root),
        "index": relpath_posix(index_path, paths.repo_root),
        "combined": relpath_posix(combined_path, paths.repo_root),
    }, manifest["counts"]

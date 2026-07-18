from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any

from . import __version__
from .paths import ManualgenPaths
from .prose_review import COMMAND_SLUG, PARTIAL_HELP_SLUG, RUNTIME_SLUG
from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_csv, write_json


REVIEW_DECISION = "docs/maintenance/lanes/full_stack_documentation/MANUALGEN_PROSE_REVIEW_DECISION_2026-07-17.md"
APPROVAL_LINE = "Decision: approved for non-published selective merge candidate."
RUNTIME_ANCHOR = "## Smoke tests, shakedowns, regressions, builds, and releases"
COMMAND_SURFACE_ANCHOR = "## Command surface"
COMMAND_ALIAS_ANCHOR = "## Aliases and entry variants"


def _latest_prose_review_dir(paths: ManualgenPaths) -> Path | None:
    root = paths.manualgen_root / "generated" / "manualgen_prose_review_batches"
    candidates: list[Path] = []
    for directory in root.glob("MANRUN-*") if root.exists() else []:
        manifest_path = directory / "manual_prose_review_batch_manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        counts = manifest.get("counts", {})
        if (
            manifest.get("status") == "PASS"
            and counts.get("input_topics") == 8
            and counts.get("candidate_files") == 3
            and manifest.get("canonical_manual_mutated") == 0
        ):
            candidates.append(directory)
    return sorted(candidates, key=lambda path: path.name)[-1] if candidates else None


def _extract_from_heading(text: str, heading: str, end_heading: str | None = None) -> str:
    if text.count(heading) != 1:
        raise ValueError(f"Expected exactly one extraction heading: {heading}")
    start = text.index(heading)
    end = len(text)
    if end_heading is not None:
        if text.count(end_heading) != 1:
            raise ValueError(f"Expected exactly one extraction end heading: {end_heading}")
        end = text.index(end_heading, start)
    return text[start:end].strip()


def _insert_after_h2_section(text: str, anchor: str, fragment: str) -> str:
    if text.count(anchor) != 1:
        raise ValueError(f"Expected exactly one merge anchor: {anchor}")
    anchor_start = text.index(anchor)
    anchor_end = text.find("\n", anchor_start)
    if anchor_end < 0:
        raise ValueError(f"Anchor has no subsection body: {anchor}")
    next_h2 = re.search(r"(?m)^## ", text[anchor_end + 1 :])
    if next_h2 is None:
        raise ValueError(f"Anchor has no following level-two boundary: {anchor}")
    insert_at = anchor_end + 1 + next_h2.start()
    before = text[:insert_at]
    after = text[insert_at:]
    if not before.endswith("\n\n"):
        before = before.rstrip("\n") + "\n\n"
    return before + fragment.rstrip() + "\n\n" + after


def _diff_text(base: str, candidate: str, base_label: str, candidate_label: str) -> str:
    lines = list(
        difflib.unified_diff(
            base.splitlines(),
            candidate.splitlines(),
            fromfile=base_label,
            tofile=candidate_label,
            lineterm="",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def _delta_counts(base: str, candidate: str) -> tuple[int, int]:
    additions = 0
    deletions = 0
    matcher = difflib.SequenceMatcher(a=base.splitlines(), b=candidate.splitlines())
    for opcode, a_start, a_end, b_start, b_end in matcher.get_opcodes():
        if opcode in ("insert", "replace"):
            additions += b_end - b_start
        if opcode in ("delete", "replace"):
            deletions += a_end - a_start
    return additions, deletions


def build_selective_merge_candidate(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    prose_dir = _latest_prose_review_dir(paths)
    empty_counts = {
        "reviewed_topics": 0,
        "section_candidates": 0,
        "appendix_candidates": 0,
        "reader_candidates": 0,
        "diff_files": 0,
        "hash_failures": 1,
        "anchor_failures": 0,
        "section_deletions": 0,
        "canonical_hash_changes": 0,
    }
    if not prose_dir:
        return {"created": 0, "status": "FAIL"}, empty_counts

    prose_manifest_path = prose_dir / "manual_prose_review_batch_manifest.json"
    prose_manifest = json.loads(prose_manifest_path.read_text(encoding="utf-8"))
    decision_path = paths.repo_root / REVIEW_DECISION
    decision_text = decision_path.read_text(encoding="utf-8", errors="replace") if decision_path.exists() else ""
    approval_valid = (
        APPROVAL_LINE in decision_text
        and prose_dir.name in decision_text
        and relpath_posix(prose_manifest_path, paths.repo_root) in decision_text
    )

    artifact_rows = prose_manifest.get("artifacts", {}).get("candidate_files", [])
    prose_files: dict[str, dict[str, Any]] = {}
    hash_failures = 0
    for row in artifact_rows:
        path = paths.repo_root / row.get("relative_path", "")
        actual_sha = sha256_file(path) if path.exists() else ""
        if actual_sha != row.get("sha256", ""):
            hash_failures += 1
        name = row.get("candidate_file", "")
        prose_files[name] = {"path": path, "sha256": actual_sha, "relative_path": row.get("relative_path", "")}

    runtime_name = f"{RUNTIME_SLUG}_PROSE_DELTA_CANDIDATE.md"
    command_name = f"{COMMAND_SLUG}_PROSE_DELTA_CANDIDATE.md"
    appendix_name = f"{PARTIAL_HELP_SLUG}_PROSE_APPENDIX_CANDIDATE.md"
    required_names = {runtime_name, command_name, appendix_name}
    if set(prose_files) != required_names:
        hash_failures += len(required_names.symmetric_difference(prose_files)) or 1

    try:
        runtime_prose = prose_files[runtime_name]["path"].read_text(encoding="utf-8")
        command_prose = prose_files[command_name]["path"].read_text(encoding="utf-8")
        appendix_prose = prose_files[appendix_name]["path"].read_text(encoding="utf-8")
        runtime_fragment = _extract_from_heading(runtime_prose, "## REGRESSION and TEST as proof launchers")
        generic_fragment = _extract_from_heading(command_prose, "### GENERIC remains a developer-utility canary", "## Candidate insertion B")
        ui_fragment = _extract_from_heading(command_prose, "### Application-style UI entry points")
        appendix_body = _extract_from_heading(appendix_prose, "## Reading this appendix")
        appendix_candidate = "# Partial HELP Reference\n\n" + appendix_body + "\n"
        extraction_failures: list[str] = []
    except (KeyError, OSError, ValueError) as exc:
        runtime_fragment = generic_fragment = ui_fragment = appendix_body = appendix_candidate = ""
        extraction_failures = [str(exc)]

    canonical_rows = prose_manifest.get("input", {}).get("canonical_targets", {})
    canonical_before: dict[str, dict[str, str]] = {}
    canonical_text: dict[str, str] = {}
    for slug in (RUNTIME_SLUG, COMMAND_SLUG):
        row = canonical_rows.get(slug, {})
        path = paths.repo_root / row.get("relative_path", "")
        actual_sha = sha256_file(path) if path.exists() else ""
        if actual_sha != row.get("sha256", ""):
            hash_failures += 1
        canonical_before[slug] = {
            "relative_path": row.get("relative_path", ""),
            "recorded_sha256": row.get("sha256", ""),
            "actual_sha256": actual_sha,
        }
        canonical_text[slug] = path.read_text(encoding="utf-8") if path.exists() else ""

    reader_path = paths.manualgen_root / "published" / "developer_manual_publication_v1" / "developer_manual_publication_v1.md"
    reader_text = reader_path.read_text(encoding="utf-8") if reader_path.exists() else ""
    reader_sha = sha256_file(reader_path) if reader_path.exists() else ""
    if not reader_text:
        hash_failures += 1

    anchor_failures: list[str] = []
    try:
        runtime_candidate = _insert_after_h2_section(canonical_text[RUNTIME_SLUG], RUNTIME_ANCHOR, runtime_fragment)
        command_candidate = _insert_after_h2_section(canonical_text[COMMAND_SLUG], COMMAND_SURFACE_ANCHOR, generic_fragment)
        command_candidate = _insert_after_h2_section(command_candidate, COMMAND_ALIAS_ANCHOR, ui_fragment)
        reader_candidate_body = _insert_after_h2_section(reader_text, RUNTIME_ANCHOR, runtime_fragment)
        reader_candidate_body = _insert_after_h2_section(reader_candidate_body, COMMAND_SURFACE_ANCHOR, generic_fragment)
        reader_candidate_body = _insert_after_h2_section(reader_candidate_body, COMMAND_ALIAS_ANCHOR, ui_fragment)
    except ValueError as exc:
        runtime_candidate = command_candidate = reader_candidate_body = ""
        anchor_failures.append(str(exc))

    run_id = logger.run_id if logger else "MANRUN-SELECTIVE-MERGE-CANDIDATE"
    output_dir = paths.manualgen_root / "generated" / "manualgen_selective_merge_candidates" / run_id
    section_dir = output_dir / "sections"
    appendix_dir = output_dir / "appendices"
    diff_dir = output_dir / "diffs"
    section_dir.mkdir(parents=True, exist_ok=True)
    appendix_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    runtime_path = section_dir / f"{RUNTIME_SLUG}.md"
    command_path = section_dir / f"{COMMAND_SLUG}.md"
    appendix_path = appendix_dir / f"{PARTIAL_HELP_SLUG}.md"
    reader_candidate_path = output_dir / "developer_manual_selective_merge_candidate.md"
    # Preserve the canonical section's existing EOF whitespace. The diff and
    # written candidate must describe the same bytes; trimming here made a
    # nominally additive candidate contain hidden trailing-blank-line deletes.
    runtime_path.write_text(runtime_candidate, encoding="utf-8")
    command_path.write_text(command_candidate, encoding="utf-8")
    appendix_path.write_text(appendix_candidate.rstrip() + "\n", encoding="utf-8")
    reader_candidate = (
        "<!-- Candidate-only selective merge reader. Not publication. -->\n"
        f"<!-- Base reader SHA-256: {reader_sha} -->\n"
        f"<!-- Approved prose review: {prose_dir.name} -->\n\n"
        + reader_candidate_body.rstrip()
        + "\n\n---\n\n"
        + appendix_candidate.rstrip()
        + "\n"
    )
    reader_candidate_path.write_text(reader_candidate, encoding="utf-8")

    diff_specs = [
        (RUNTIME_SLUG, canonical_text[RUNTIME_SLUG], runtime_candidate, canonical_before[RUNTIME_SLUG]["relative_path"], relpath_posix(runtime_path, paths.repo_root)),
        (COMMAND_SLUG, canonical_text[COMMAND_SLUG], command_candidate, canonical_before[COMMAND_SLUG]["relative_path"], relpath_posix(command_path, paths.repo_root)),
        ("combined_reader", reader_text, reader_candidate, relpath_posix(reader_path, paths.repo_root), relpath_posix(reader_candidate_path, paths.repo_root)),
    ]
    diff_rows = []
    section_deletions = 0
    for name, base, candidate, base_label, candidate_label in diff_specs:
        path = diff_dir / f"{name}.diff"
        path.write_text(_diff_text(base, candidate, base_label, candidate_label), encoding="utf-8")
        additions, deletions = _delta_counts(base, candidate)
        if name != "combined_reader":
            section_deletions += deletions
        diff_rows.append({
            "target": name,
            "relative_path": relpath_posix(path, paths.repo_root),
            "sha256": sha256_file(path),
            "additions": additions,
            "deletions": deletions,
        })

    merge_rows = [
        {
            "target": RUNTIME_SLUG,
            "target_kind": "copied_section",
            "anchor": RUNTIME_ANCHOR,
            "review_topics": "DOT|REGRESSION;DOT|TEST",
            "base_path": canonical_before[RUNTIME_SLUG]["relative_path"],
            "base_sha256": canonical_before[RUNTIME_SLUG]["actual_sha256"],
            "candidate_path": relpath_posix(runtime_path, paths.repo_root),
            "candidate_sha256": sha256_file(runtime_path),
        },
        {
            "target": COMMAND_SLUG,
            "target_kind": "copied_section",
            "anchor": f"{COMMAND_SURFACE_ANCHOR};{COMMAND_ALIAS_ANCHOR}",
            "review_topics": "DOT|GENERIC;UI|ARCTICTALK;UI|FOXPRO",
            "base_path": canonical_before[COMMAND_SLUG]["relative_path"],
            "base_sha256": canonical_before[COMMAND_SLUG]["actual_sha256"],
            "candidate_path": relpath_posix(command_path, paths.repo_root),
            "candidate_sha256": sha256_file(command_path),
        },
        {
            "target": PARTIAL_HELP_SLUG,
            "target_kind": "candidate_appendix",
            "anchor": "APPEND_TO_CANDIDATE_READER_ONLY",
            "review_topics": "DOT|CANARY;FOX|DO;FOX|RUN",
            "base_path": "",
            "base_sha256": "",
            "candidate_path": relpath_posix(appendix_path, paths.repo_root),
            "candidate_sha256": sha256_file(appendix_path),
        },
    ]
    merge_ledger_path = output_dir / "manual_selective_merge_ledger.csv"
    write_csv(merge_ledger_path, merge_rows)

    canonical_hash_changes = 0
    for slug, row in canonical_before.items():
        path = paths.repo_root / row["relative_path"]
        if not path.exists() or sha256_file(path) != row["actual_sha256"]:
            canonical_hash_changes += 1
    if not reader_path.exists() or sha256_file(reader_path) != reader_sha:
        canonical_hash_changes += 1

    review_path = output_dir / "MANUAL_SELECTIVE_MERGE_CONTEXT_REVIEW.md"
    review_body = [
        "# Manual Selective Merge Context Review",
        "",
        f"- Run: `{run_id}`",
        f"- Approved prose review: `{prose_dir.name}`",
        f"- Base reader SHA-256: `{reader_sha}`",
        "- Candidate only: yes",
        "- Canonical hashes changed: 0" if canonical_hash_changes == 0 else f"- Canonical hashes changed: {canonical_hash_changes}",
        "",
        "## Review surfaces",
        "",
        "| Surface | Additions | Deletions | Review point |",
        "| --- | ---: | ---: | --- |",
    ]
    review_points = {
        RUNTIME_SLUG: "REGRESSION/TEST proof-launcher prose before HELP evidence practice.",
        COMMAND_SLUG: "GENERIC remains canary-level; UI entries remain build-conditioned.",
        "combined_reader": "Full reader context plus candidate-only Partial HELP appendix at the end.",
    }
    for row in diff_rows:
        review_body.append(f"| `{row['target']}` | {row['additions']} | {row['deletions']} | {review_points[row['target']]} |")
    review_body.extend([
        "",
        "## Boundary",
        "",
        "This package does not accept the copied sections or appendix and does not replace the reader. Review the full reader and diffs before opening any canonical merge gate.",
        "",
    ])
    review_path.write_text("\n".join(review_body), encoding="utf-8")

    status = "PASS" if (
        approval_valid
        and not extraction_failures
        and not anchor_failures
        and hash_failures == 0
        and section_deletions == 0
        and canonical_hash_changes == 0
        and len(merge_rows) == 3
        and len(diff_rows) == 3
    ) else "FAIL"
    counts = {
        "reviewed_topics": 8,
        "section_candidates": 2,
        "appendix_candidates": 1,
        "reader_candidates": 1,
        "diff_files": len(diff_rows),
        "hash_failures": hash_failures,
        "anchor_failures": len(anchor_failures),
        "extraction_failures": len(extraction_failures),
        "section_deletions": section_deletions,
        "canonical_hash_changes": canonical_hash_changes,
    }
    manifest_path = output_dir / "manual_selective_merge_candidate_manifest.json"
    manifest = {
        "schema": "dottalk.manualgen.selective_merge_candidate.v1",
        "created_utc": utc_now_iso(),
        "manualgen_version": __version__,
        "run_id": run_id,
        "status": status,
        "candidate_only": 1,
        "canonical_manual_mutated": 0,
        "accepted_appendix_mutated": 0,
        "reader_pointer_mutated": 0,
        "publication_authority_claimed": 0,
        "input": {
            "review_decision": relpath_posix(decision_path, paths.repo_root),
            "review_decision_sha256": sha256_file(decision_path) if decision_path.exists() else "",
            "approval_valid": 1 if approval_valid else 0,
            "prose_review_run_id": prose_dir.name,
            "prose_review_manifest": relpath_posix(prose_manifest_path, paths.repo_root),
            "prose_review_manifest_sha256": sha256_file(prose_manifest_path),
            "prose_candidate_files": artifact_rows,
            "canonical_targets": canonical_before,
            "base_reader": relpath_posix(reader_path, paths.repo_root),
            "base_reader_sha256": reader_sha,
        },
        "counts": counts,
        "findings": {
            "extraction_failures": extraction_failures,
            "anchor_failures": anchor_failures,
        },
        "artifacts": {
            "merge_ledger": relpath_posix(merge_ledger_path, paths.repo_root),
            "merge_ledger_sha256": sha256_file(merge_ledger_path),
            "context_review": relpath_posix(review_path, paths.repo_root),
            "context_review_sha256": sha256_file(review_path),
            "reader_candidate": relpath_posix(reader_candidate_path, paths.repo_root),
            "reader_candidate_sha256": sha256_file(reader_candidate_path),
            "merge_targets": merge_rows,
            "diffs": diff_rows,
        },
    }
    write_json(manifest_path, manifest)

    if logger:
        logger.artifact("manual_selective_merge_manifest", manifest_path, "Hash-bound non-published selective merge manifest.")
        logger.artifact("manual_selective_merge_ledger", merge_ledger_path, "Per-target selective merge lineage.")
        logger.artifact("manual_selective_merge_context_review", review_path, "Human contextual review summary.")
        logger.artifact("developer_manual_selective_merge_candidate", reader_candidate_path, "Full non-published reader candidate.")
        for row in merge_rows:
            logger.artifact(f"merge_target_{row['target']}", paths.repo_root / row["candidate_path"], "Copied selective merge candidate.")
        for row in diff_rows:
            logger.artifact(f"merge_diff_{row['target']}", paths.repo_root / row["relative_path"], "Unified contextual review diff.")
        for boundary in (
            "canonical_manual_mutated",
            "accepted_appendix_mutated",
            "reader_pointer_mutated",
            "publication_authority_claimed",
            "source_help_metadata_mutated",
        ):
            logger.boundary(boundary, 0, "PASS", "Selective merge candidate generation writes only beneath generated/.")

    state = {
        "created": 1,
        "status": status,
        "output_dir": relpath_posix(output_dir, paths.repo_root),
        "manifest": relpath_posix(manifest_path, paths.repo_root),
        "reader_candidate": relpath_posix(reader_candidate_path, paths.repo_root),
    }
    return state, counts

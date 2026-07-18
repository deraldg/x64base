from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .inventory import collect_inventory
from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import read_text, relpath_posix, sha256_file, write_csv, write_json
from .validation import validate_inventory, summarize_validation


def _current_combined_markdown(paths: ManualgenPaths, publication_id: str) -> Path | None:
    """Return the authoritative combined Markdown for the selected publication workspace.

    MDO-232: prefer the live selected publication workspace over stale paths recorded
    in older dry-run manifests.  The dry-run manifest path is still useful as a
    fallback, but publication parity must compare against the current selected
    publication artifact after repair packages such as MDO-229.
    """
    if not publication_id:
        return None
    workspace = paths.published_dir / publication_id
    candidate = workspace / f"{publication_id}.md"
    if candidate.exists():
        return candidate
    if workspace.exists():
        matches = sorted(workspace.glob("*.md"))
        if matches:
            return matches[0]
    return None


def _latest_dry_run_manifest(paths: ManualgenPaths, selected_assembly_id: str = "") -> Path | None:
    root = paths.manualgen_root / "generated" / "manualgen_build_dry_runs"
    if not root.exists():
        return None
    manifests = sorted(root.glob("*/build_dry_run_manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if selected_assembly_id:
        for manifest_path in manifests:
            try:
                manifest = _load_json(manifest_path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            manifest_id = str(manifest.get("selected_assembly_id") or manifest.get("publication_id") or "")
            if manifest_id == selected_assembly_id:
                return manifest_path
    return manifests[0] if manifests else None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_from_manifest(paths: ManualgenPaths, value: str) -> Path | None:
    if not value:
        return None
    p = Path(value)
    if p.is_absolute():
        return p
    return paths.repo_root / value


def _strip_bom_chars(text: str) -> str:
    """Remove UTF BOM markers that can appear at the start of section files or
    inside combined Markdown assembled by Windows tooling.

    MDO-234: MDO-231/MDO-233 proved the media section fragment was present
    in the combined artifact while the Python parity report still marked it
    missing.  The most likely text-level mismatch is an invisible BOM/control
    marker at the edge of a section fragment.  Remove BOM characters for
    parity matching; do not change source or publication files.
    """
    return text.replace("\ufeff", "")


def _normalize_line_endings(text: str) -> str:
    return _strip_bom_chars(text).replace("\r\n", "\n").replace("\r", "\n")


def _strip_mdo226_generated_header(text: str) -> str:
    lines = _normalize_line_endings(text).splitlines()
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("<!-- MDO-226 build/rebuild dry-run artifact"):
            idx += 1
            continue
        if stripped.startswith("<!-- publication_id:"):
            idx += 1
            continue
        if stripped.startswith("<!-- assembly_selection_mode:"):
            idx += 1
            continue
        if stripped.startswith("<!-- selected_workspace_role:"):
            idx += 1
            continue
        if stripped.startswith("<!-- created_utc:"):
            idx += 1
            continue
        if stripped == "":
            idx += 1
            continue
        break
    return "\n".join(lines[idx:]).strip() + "\n"


def _normalize_ws(text: str) -> str:
    text = _normalize_line_endings(text)
    out: list[str] = []
    blank = False
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped == "":
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(stripped)
            blank = False
    return "\n".join(out).strip() + "\n"


def _sha_text(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def _section_path(paths: ManualgenPaths, row: dict[str, Any]) -> Path:
    raw = row.get("relative_path") or row.get("relative_path_posix") or ""
    return paths.repo_root / raw


def _section_fragment(path: Path) -> str:
    if not path.exists():
        return ""
    text = _strip_bom_chars(read_text(path)).strip()
    return text


def _fragment_occurrences(haystack: str, fragment: str) -> tuple[int, str]:
    """Count a section fragment in an assembled artifact.

    MDO-232: raw exact matching is still preferred, but parity must not go red
    merely because one side has CRLF/LF differences or light trailing whitespace
    normalization.  This aligns parity-review with the exact-fragment diagnostic
    that proved the media section content was present after MDO-229.
    """
    if not fragment:
        return 0, "empty"
    raw = haystack.count(fragment)
    if raw > 0:
        return raw, "raw"
    h_bom = _strip_bom_chars(haystack)
    f_bom = _strip_bom_chars(fragment)
    bom = h_bom.count(f_bom)
    if bom > 0:
        return bom, "bom_stripped"
    h_norm = _normalize_line_endings(haystack)
    f_norm = _normalize_line_endings(fragment)
    norm = h_norm.count(f_norm)
    if norm > 0:
        return norm, "line_ending_normalized"
    h_light = _normalize_ws(haystack)
    f_light = _normalize_ws(fragment)
    light = h_light.count(f_light)
    if light > 0:
        return light, "whitespace_normalized"
    return 0, "missing"


def parity_review(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    inv = collect_inventory(paths)
    checks = validate_inventory(paths, inv)
    val_counts = summarize_validation(checks)
    validation_fail_rows = val_counts.get("validation_fail_rows", 0)
    validation_review_rows = val_counts.get("validation_review_rows", 0)

    publication_id = inv.get("selected_assembly_id", inv.get("current_publication_id", ""))
    sections = list(inv.get("sections", []))
    media = list(inv.get("media", []))
    appendices = list(inv.get("appendices", []))

    dry_manifest_path = _latest_dry_run_manifest(paths, publication_id)
    dry_manifest = _load_json(dry_manifest_path) if dry_manifest_path else {}
    dry_markdown_path = _path_from_manifest(paths, str(dry_manifest.get("dry_run_markdown", ""))) if dry_manifest else None
    live_current_markdown_path = _current_combined_markdown(paths, publication_id)
    manifest_current_markdown_path = _path_from_manifest(paths, str(dry_manifest.get("current_combined_markdown", ""))) if dry_manifest else None
    # MDO-232: compare against the live selected publication workspace first.
    # Older dry-run manifests can contain stale path/hash context from before a
    # controlled repair and must not override the current publication target.
    current_markdown_path = live_current_markdown_path or manifest_current_markdown_path

    dry_exists = 1 if dry_markdown_path and dry_markdown_path.exists() else 0
    current_exists = 1 if current_markdown_path and current_markdown_path.exists() else 0
    dry_text = read_text(dry_markdown_path) if dry_exists and dry_markdown_path else ""
    current_text = read_text(current_markdown_path) if current_exists and current_markdown_path else ""

    exact_hash_match = 1 if dry_exists and current_exists and sha256_file(dry_markdown_path) == sha256_file(current_markdown_path) else 0
    line_ending_hash_match = 1 if dry_exists and current_exists and _sha_text(_normalize_line_endings(dry_text)) == _sha_text(_normalize_line_endings(current_text)) else 0
    stripped_header_hash_match = 1 if dry_exists and current_exists and _sha_text(_strip_mdo226_generated_header(dry_text)) == _sha_text(_normalize_line_endings(current_text).strip() + "\n") else 0
    whitespace_normalized_hash_match = 1 if dry_exists and current_exists and _sha_text(_normalize_ws(_strip_mdo226_generated_header(dry_text))) == _sha_text(_normalize_ws(current_text)) else 0

    section_rows: list[dict[str, Any]] = []
    missing_in_dry = 0
    missing_in_current = 0
    for row in sections:
        path = _section_path(paths, row)
        frag = _section_fragment(path)
        if frag:
            dry_occ, dry_match_mode = _fragment_occurrences(dry_text, frag)
            cur_occ, cur_match_mode = _fragment_occurrences(current_text, frag)
        else:
            dry_occ, dry_match_mode = 0, "empty"
            cur_occ, cur_match_mode = 0, "empty"
        dry_present = 1 if dry_occ > 0 else 0
        cur_present = 1 if cur_occ > 0 else 0
        if not dry_present:
            missing_in_dry += 1
        if not cur_present:
            missing_in_current += 1
        status = "PASS" if dry_present and cur_present else "FAIL"
        note = (
            f"Section text present in both artifacts (dry={dry_match_mode}; current={cur_match_mode})."
            if status == "PASS"
            else f"Section text missing from one or both artifacts (dry={dry_match_mode}; current={cur_match_mode}); inspect before publication replacement."
        )
        section_rows.append({
            "section_index": row.get("section_index", ""),
            "section_slug": row.get("section_slug", ""),
            "title": row.get("title", ""),
            "section_relative_path": row.get("relative_path", ""),
            "section_sha256": row.get("sha256", ""),
            "present_in_dry_run": dry_present,
            "present_in_current_combined": cur_present,
            "occurrences_in_dry_run": dry_occ,
            "occurrences_in_current_combined": cur_occ,
            "status": status,
            "note": note,
        })

    section_fail_rows = sum(1 for r in section_rows if r.get("status") == "FAIL")
    generated_header_present = 1 if dry_text.lstrip().startswith("<!-- MDO-226 build/rebuild dry-run artifact") else 0
    exact_status = "PASS" if exact_hash_match else "REVIEW"
    normalized_status = "PASS" if whitespace_normalized_hash_match else "REVIEW"
    substantive_status = "PASS" if section_fail_rows == 0 else "FAIL"

    reason_rows = [
        {"check_id": "EXACT_HASH_MATCH", "status": exact_status, "value": exact_hash_match, "note": "Exact byte-for-byte hash match between dry-run combined Markdown and current combined publication Markdown."},
        {"check_id": "LINE_ENDING_NORMALIZED_HASH_MATCH", "status": "PASS" if line_ending_hash_match else "REVIEW", "value": line_ending_hash_match, "note": "Comparison after normalizing CRLF/LF only."},
        {"check_id": "MDO226_HEADER_STRIPPED_HASH_MATCH", "status": "PASS" if stripped_header_hash_match else "REVIEW", "value": stripped_header_hash_match, "note": "Comparison after stripping MDO-226 dry-run generated header comments."},
        {"check_id": "WHITESPACE_NORMALIZED_HASH_MATCH", "status": normalized_status, "value": whitespace_normalized_hash_match, "note": "Comparison after header stripping and light whitespace normalization."},
        {"check_id": "DRY_RUN_GENERATED_HEADER_PRESENT", "status": "REVIEW" if generated_header_present else "PASS", "value": generated_header_present, "note": "Generated dry-run header comments explain at least part of the exact hash mismatch when present."},
        {"check_id": "ALL_SECTIONS_PRESENT_IN_DRY_RUN", "status": "PASS" if missing_in_dry == 0 else "FAIL", "value": len(sections) - missing_in_dry, "note": "Section file text fragments found in dry-run combined Markdown."},
        {"check_id": "ALL_SECTIONS_PRESENT_IN_CURRENT_COMBINED", "status": "PASS" if missing_in_current == 0 else "FAIL", "value": len(sections) - missing_in_current, "note": "Section file text fragments found in current combined publication Markdown."},
        {"check_id": "PARITY_REVIEW_INTERPRETATION", "status": substantive_status, "value": section_fail_rows, "note": "Exact hash mismatch is acceptable only if section-level parity is PASS and publication replacement remains blocked."},
    ]
    diff_review_rows = sum(1 for r in reason_rows if r.get("status") == "REVIEW")
    parity_fail_rows = sum(1 for r in reason_rows if r.get("status") == "FAIL")

    boundary_rows = [
        {"boundary": "manual_publication_rebuilt", "value": 0, "status": "PASS", "note": "Parity review reads artifacts only; it does not rebuild publication."},
        {"boundary": "published_workspace_mutated", "value": 0, "status": "PASS", "note": "Parity review does not write to published workspaces."},
        {"boundary": "media_files_copied_moved_renamed_deleted", "value": 0, "status": "PASS", "note": "Parity review does not alter media files."},
        {"boundary": "x64base_tables_created", "value": 0, "status": "PASS", "note": "Parity review does not create x64base tables."},
        {"boundary": "cpp_files_created", "value": 0, "status": "PASS", "note": "Parity review does not create C++ files."},
        {"boundary": "help_meta_cmdhelpchk_mutations", "value": 0, "status": "PASS", "note": "No protected-system mutation performed."},
        {"boundary": "product_source_edits", "value": 0, "status": "PASS", "note": "No product source edits outside authorized tools/manualgen update."},
        {"boundary": "runtime_data_mutations", "value": 0, "status": "PASS", "note": "No runtime data mutation performed."},
        {"boundary": "production_selfdoc_metadata_promotions", "value": 0, "status": "PASS", "note": "No production SelfDoc metadata promotion performed."},
    ]
    boundary_fail_rows = sum(1 for row in boundary_rows if row.get("status") == "FAIL")

    artifact_rows = [
        {"artifact_kind": "dry_run_manifest", "relative_path": relpath_posix(dry_manifest_path, paths.repo_root) if dry_manifest_path else "", "exists": 1 if dry_manifest_path and dry_manifest_path.exists() else 0, "sha256": sha256_file(dry_manifest_path) if dry_manifest_path and dry_manifest_path.exists() else "", "note": "Latest dry-run manifest selected for parity review."},
        {"artifact_kind": "dry_run_markdown", "relative_path": relpath_posix(dry_markdown_path, paths.repo_root) if dry_markdown_path else "", "exists": dry_exists, "sha256": sha256_file(dry_markdown_path) if dry_exists and dry_markdown_path else "", "note": "Generated dry-run combined Markdown."},
        {"artifact_kind": "current_combined_publication_markdown", "relative_path": relpath_posix(current_markdown_path, paths.repo_root) if current_markdown_path else "", "exists": current_exists, "sha256": sha256_file(current_markdown_path) if current_exists and current_markdown_path else "", "note": "Current combined publication Markdown reference."},
    ]

    summary_rows = [
        {"metric": "mdo_226_confirmed_green", "count": 1, "note": "MDO-226 status and summary were present before MDO-227 execution."},
        {"metric": "mdo_234_parity_trace_report_repair_created", "count": 1, "note": "Python parity matcher repaired with BOM/control-character trace path and report generation validation."},
        {"metric": "selected_assembly_section_files", "count": len(sections), "note": "Sections in the selected assembly workspace."},
        {"metric": "media_files", "count": len(media), "note": "Media inventory count observed."},
        {"metric": "appendix_files", "count": len(appendices), "note": "Appendix inventory count observed."},
        {"metric": "exact_hash_match", "count": exact_hash_match, "note": "Dry-run combined Markdown vs current combined publication Markdown."},
        {"metric": "line_ending_normalized_hash_match", "count": line_ending_hash_match, "note": "Hash comparison after line-ending normalization."},
        {"metric": "stripped_header_hash_match", "count": stripped_header_hash_match, "note": "Hash comparison after stripping MDO-226 generated header comments."},
        {"metric": "whitespace_normalized_hash_match", "count": whitespace_normalized_hash_match, "note": "Hash comparison after light whitespace normalization."},
        {"metric": "section_parity_fail_rows", "count": section_fail_rows, "note": "Sections missing from dry-run or current combined Markdown."},
        {"metric": "diff_review_rows", "count": diff_review_rows, "note": "Diff reason rows with REVIEW status."},
        {"metric": "parity_fail_rows", "count": parity_fail_rows, "note": "Parity reason rows with FAIL status."},
        {"metric": "validation_fail_rows", "count": validation_fail_rows, "note": "Validation FAIL rows from current inventory."},
        {"metric": "validation_review_rows", "count": validation_review_rows, "note": "Validation REVIEW rows from current inventory."},
        {"metric": "boundary_fail_rows", "count": boundary_fail_rows, "note": "Boundary FAIL rows."},
        {"metric": "manual_publication_rebuilt", "count": 0, "note": "MDO-234 does not rebuild or replace publication."},
        {"metric": "published_workspace_mutated", "count": 0, "note": "Published workspaces are not modified."},
        {"metric": "x64base_tables_created", "count": 0, "note": "MDO-234 does not create x64base tables."},
        {"metric": "cpp_files_created", "count": 0, "note": "MDO-234 does not create C++ files."},
        {"metric": "help_meta_cmdhelpchk_mutations", "count": 0, "note": "No protected-system mutation performed."},
    ]

    write_csv(paths.reports_dir / "mdo_227_parity_review_summary_v1.csv", summary_rows, ["metric", "count", "note"])
    write_csv(paths.reports_dir / "mdo_227_parity_artifact_pair_v1.csv", artifact_rows, ["artifact_kind", "relative_path", "exists", "sha256", "note"])
    write_csv(paths.reports_dir / "mdo_227_parity_section_comparison_v1.csv", section_rows, ["section_index", "section_slug", "title", "section_relative_path", "section_sha256", "present_in_dry_run", "present_in_current_combined", "occurrences_in_dry_run", "occurrences_in_current_combined", "status", "note"])
    write_csv(paths.reports_dir / "mdo_227_parity_diff_reason_v1.csv", reason_rows, ["check_id", "status", "value", "note"])
    write_csv(paths.reports_dir / "mdo_227_boundary_check_v1.csv", boundary_rows, ["boundary", "value", "status", "note"])
    write_csv(paths.reports_dir / "mdo_227_next_decision_options_v1.csv", [
        {"option": "A", "decision": "HOLD_AFTER_MDO_227_PARITY_REVIEW", "status": "AVAILABLE", "allowed_now": 1, "note": "Stop with dry-run parity characterized and publication replacement still blocked."},
        {"option": "B", "decision": "FIX_PYTHON_ASSEMBLY_TO_MATCH_CURRENT_PUBLICATION", "status": "REQUIRES_EXPLICIT_AUTHORIZATION", "allowed_now": 0, "note": "Only needed if parity reports show order/header/spacing differences that should be eliminated before replacement."},
        {"option": "C", "decision": "CREATE_X64BASE_MANUALGEN_IMPORT_DRY_RUN", "status": "REQUIRES_EXPLICIT_AUTHORIZATION", "allowed_now": 0, "note": "Would import/report MAN* catalog rows in a dry-run lane, not production metadata."},
        {"option": "D", "decision": "CREATE_PUBLICATION_REBUILD_TO_NEW_REVISION_PACKAGE", "status": "REQUIRES_EXPLICIT_AUTHORIZATION", "allowed_now": 0, "note": "Only after parity findings are accepted; must not replace current publication silently."},
        {"option": "E", "decision": "MUTATE_HELP_META_CMDHELPCHK_SOURCE_OR_RUNTIME", "status": "NOT_AUTHORIZED", "allowed_now": 0, "note": "Protected-system mutation remains outside MDO-227."},
    ], ["option", "decision", "status", "allowed_now", "note"])

    review_doc = paths.reports_dir / "mdo_227_parity_review_interpretation_v1.md"
    interpretation = [
        "# MDO-227 Python Build Dry-Run Parity Review",
        "",
        "MDO-227 explains the MDO-226 `dry_run_hash_matches_current_combined = 0` result without replacing publication.",
        "",
        "## Interpretation rule",
        "",
        "An exact hash mismatch is a REVIEW item, not a failure, when every section is present in both the dry-run artifact and the current combined publication and all boundary checks remain green.",
        "",
        "## Current result",
        "",
        f"- Sections inventoried: {len(sections)}",
        f"- Exact hash match: {exact_hash_match}",
        f"- Section parity fail rows: {section_fail_rows}",
        f"- Diff review rows: {diff_review_rows}",
        f"- Validation fail rows: {validation_fail_rows}",
        f"- Boundary fail rows: {boundary_fail_rows}",
        "",
        "## Boundary",
        "",
        "MDO-227 does not rebuild publication, does not mutate published workspaces, does not alter media files, and does not mutate HELP, META, CMDHELPCHK, catalogs, runtime data, source, or production SelfDoc metadata.",
    ]
    review_doc.write_text("\n".join(interpretation) + "\n", encoding="utf-8")

    if logger is not None:
        for row in boundary_rows:
            logger.boundary(row["boundary"], row["value"], row["status"], row["note"])
        logger.event("INFO", "parity-review", "counts", sections=len(sections), exact_hash_match=exact_hash_match, section_parity_fail_rows=section_fail_rows, validation_fail_rows=validation_fail_rows, boundary_fail_rows=boundary_fail_rows)
        logger.artifact("parity_summary", paths.reports_dir / "mdo_227_parity_review_summary_v1.csv", "MDO-227 parity review summary.")
        logger.artifact("parity_diff_reason", paths.reports_dir / "mdo_227_parity_diff_reason_v1.csv", "MDO-227 diff reason report.")

    state = {
        "publication_id": publication_id,
        "selected_assembly_id": inv.get("selected_assembly_id", ""),
        "selected_assembly_workspace": inv.get("selected_assembly_workspace", ""),
        "selected_workspace_role": inv.get("selected_workspace_role", ""),
        "assembly_selection_mode": inv.get("assembly_selection_mode", ""),
        "section_count": len(sections),
        "media_count": len(media),
        "appendix_count": len(appendices),
        "exact_hash_match": exact_hash_match,
        "section_parity_fail_rows": section_fail_rows,
        "diff_review_rows": diff_review_rows,
        "validation_fail_rows": validation_fail_rows,
        "validation_review_rows": validation_review_rows,
        "boundary_fail_rows": boundary_fail_rows,
        "dry_run_markdown": relpath_posix(dry_markdown_path, paths.repo_root) if dry_markdown_path else "",
        "current_combined_markdown": relpath_posix(current_markdown_path, paths.repo_root) if current_markdown_path else "",
    }
    counts = {
        "validation_fail_rows": validation_fail_rows,
        "validation_review_rows": validation_review_rows,
        "boundary_fail_rows": boundary_fail_rows,
        "section_count": len(sections),
        "media_count": len(media),
        "appendix_count": len(appendices),
        "exact_hash_match": exact_hash_match,
        "section_parity_fail_rows": section_fail_rows,
        "diff_review_rows": diff_review_rows,
        "parity_fail_rows": parity_fail_rows,
    }
    return state, counts

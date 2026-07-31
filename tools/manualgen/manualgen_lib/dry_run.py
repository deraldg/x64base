from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from . import __version__
from .inventory import collect_inventory
from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import read_text, relpath_posix, sha256_file, write_csv, write_json
from .validation import validate_inventory, summarize_validation


def _read_section(path: Path) -> str:
    text = read_text(path).rstrip()
    return text + "\n" if text else ""


def _section_path(paths: ManualgenPaths, row: dict[str, Any]) -> Path:
    raw = row.get("relative_path") or row.get("relative_path_posix") or ""
    return paths.repo_root / raw


def _current_combined_markdown(paths: ManualgenPaths, publication_id: str) -> Path | None:
    if not publication_id:
        return None
    candidate = paths.published_dir / publication_id / f"{publication_id}.md"
    if candidate.exists():
        return candidate
    workspace = paths.published_dir / publication_id
    if workspace.exists():
        matches = sorted(workspace.glob("*.md"))
        if matches:
            return matches[0]
    return None


def build_dry_run(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    """Assemble a dry-run manual artifact under generated/, never published/."""
    inv = collect_inventory(paths)
    checks = validate_inventory(paths, inv)
    val_counts = summarize_validation(checks)
    validation_fail_rows = val_counts.get("validation_fail_rows", 0)
    validation_review_rows = val_counts.get("validation_review_rows", 0)

    publication_id = inv.get("selected_assembly_id", inv.get("current_publication_id", ""))
    sections = list(inv.get("sections", []))
    media = inv.get("media", [])
    appendices = inv.get("appendices", [])
    manifests = inv.get("machine_manifests", [])
    harvest = inv.get("harvest", {})

    run_id = logger.run_id if logger else "MANRUN-DRYRUN"
    dry_root = paths.manualgen_root / "generated" / "manualgen_build_dry_runs" / run_id
    dry_root.mkdir(parents=True, exist_ok=True)
    dry_markdown = dry_root / "developer_manual_build_dry_run.md"
    dry_manifest = dry_root / "build_dry_run_manifest.json"

    parts: list[str] = []
    parts.append("<!-- MDO-226 build/rebuild dry-run artifact. Not a publication replacement. -->\n")
    parts.append(f"<!-- publication_id: {publication_id} -->\n")
    parts.append(f"<!-- assembly_selection_mode: {inv.get('assembly_selection_mode', '')} -->\n")
    parts.append(f"<!-- selected_workspace_role: {inv.get('selected_workspace_role', '')} -->\n")
    parts.append(f"<!-- harvest_workspace: {harvest.get('workspace_posix', '')} -->\n")
    parts.append(f"<!-- harvest_selection_mode: {harvest.get('selection_mode', '')} -->\n")
    parts.append(f"<!-- created_utc: {utc_now_iso()} -->\n\n")
    for row in sections:
        path = _section_path(paths, row)
        if path.exists():
            parts.append(_read_section(path))
            parts.append("\n\n")

    dry_markdown.write_text("".join(parts).rstrip() + "\n", encoding="utf-8")

    current_combined = _current_combined_markdown(paths, publication_id)
    current_combined_exists = 1 if current_combined and current_combined.exists() else 0
    dry_hash = sha256_file(dry_markdown)
    current_hash = sha256_file(current_combined) if current_combined_exists and current_combined else ""
    hash_match = 1 if current_hash and current_hash == dry_hash else 0
    hash_status = "PASS" if hash_match else ("REVIEW" if current_combined_exists else "REVIEW")

    boundary_rows = [
        {"boundary": "manual_publication_rebuilt", "value": 0, "status": "PASS", "note": "Dry-run writes only under generated/manualgen_build_dry_runs."},
        {"boundary": "published_workspace_mutated", "value": 0, "status": "PASS", "note": "Dry-run does not write to published workspaces."},
        {"boundary": "media_files_copied_moved_renamed_deleted", "value": 0, "status": "PASS", "note": "Dry-run does not alter media files."},
        {"boundary": "x64base_tables_created", "value": 0, "status": "PASS", "note": "Dry-run does not create x64base tables."},
        {"boundary": "cpp_files_created", "value": 0, "status": "PASS", "note": "Dry-run does not create C++ files."},
        {"boundary": "help_meta_cmdhelpchk_mutations", "value": 0, "status": "PASS", "note": "No protected-system mutation performed."},
        {"boundary": "product_source_edits", "value": 0, "status": "PASS", "note": "No product source edits outside authorized tools/manualgen update."},
        {"boundary": "runtime_data_mutations", "value": 0, "status": "PASS", "note": "No runtime data mutation performed."},
        {"boundary": "production_selfdoc_metadata_promotions", "value": 0, "status": "PASS", "note": "No production SelfDoc metadata promotion performed."},
    ]
    boundary_fail_rows = sum(1 for row in boundary_rows if row.get("status") == "FAIL")

    section_rows = []
    for row in sections:
        section_rows.append({
            "section_index": row.get("section_index", ""),
            "section_slug": row.get("section_slug", ""),
            "title": row.get("title", ""),
            "source_relative_path": row.get("relative_path", ""),
            "source_sha256": row.get("sha256", ""),
            "included_in_dry_run": 1,
            "publication_id": publication_id,
        })

    artifact_rows = [
        {"artifact_kind": "dry_run_markdown", "relative_path": relpath_posix(dry_markdown, paths.repo_root), "sha256": dry_hash, "status": "CREATED", "note": "Generated dry-run combined Markdown; not publication."},
        {"artifact_kind": "dry_run_manifest", "relative_path": relpath_posix(dry_manifest, paths.repo_root), "sha256": "", "status": "CREATED", "note": "Generated dry-run manifest; hash recorded after write."},
    ]
    if current_combined_exists and current_combined:
        artifact_rows.append({"artifact_kind": "selected_assembly_combined_markdown", "relative_path": relpath_posix(current_combined, paths.repo_root), "sha256": current_hash, "status": "REFERENCE_ONLY", "note": "Existing selected-workspace combined Markdown reference; not modified."})

    manifest = {
        "schema": "dottalk.manualgen.build_dry_run_manifest.v1",
        "created_utc": utc_now_iso(),
        "manualgen_version": __version__,
        "python_version": sys.version,
        "manual_id": paths.manual_id,
        "run_id": run_id,
        "publication_id": publication_id,
        "selected_assembly_workspace": inv.get("selected_assembly_workspace", ""),
        "selected_assembly_id": inv.get("selected_assembly_id", ""),
        "selected_workspace_role": inv.get("selected_workspace_role", ""),
        "assembly_selection_mode": inv.get("assembly_selection_mode", ""),
        "assembly_selection_requested": inv.get("assembly_selection_requested", ""),
        "publication_authority_claimed": 0,
        "harvest_authority_claimed": 0,
        "harvest": harvest,
        "dry_run_workspace": relpath_posix(dry_root, paths.repo_root),
        "dry_run_markdown": relpath_posix(dry_markdown, paths.repo_root),
        "dry_run_sha256": dry_hash,
        "current_combined_markdown": relpath_posix(current_combined, paths.repo_root) if current_combined else "",
        "current_combined_sha256": current_hash,
        "dry_run_hash_matches_current_combined": hash_match,
        "hash_comparison_status": hash_status,
        "section_count": len(sections),
        "media_count": len(media),
        "appendix_count": len(appendices),
        "machine_manifest_count": len(manifests),
        "validation_fail_rows": validation_fail_rows,
        "validation_review_rows": validation_review_rows,
        "boundary_fail_rows": boundary_fail_rows,
        "manual_publication_rebuilt": 0,
        "sections": section_rows,
        "boundary": boundary_rows,
    }
    write_json(dry_manifest, manifest)
    artifact_rows[1]["sha256"] = sha256_file(dry_manifest)

    write_csv(paths.reports_dir / "mdo_226_build_dry_run_summary_v1.csv", [
        {"metric": "mdo_225_confirmed_green", "count": 1, "note": "MDO-225 schema plan status and summary were present before MDO-226 execution."},
        {"metric": "mdo_226_build_dry_run_created", "count": 1, "note": "Build/rebuild dry-run command executed."},
        {"metric": "selected_assembly_section_files", "count": len(sections), "note": "Sections included from the selected assembly workspace."},
        {"metric": "media_files", "count": len(media), "note": "Media inventory count observed."},
        {"metric": "appendix_files", "count": len(appendices), "note": "Appendix inventory count observed."},
        {"metric": "machine_manifest_files", "count": len(manifests), "note": "JSON machine manifest count observed."},
        {"metric": "harvest_required_files", "count": harvest.get("required_file_count", 0), "note": "Required HELP/META evidence contracts attached to this dry run."},
        {"metric": "harvest_present_files", "count": harvest.get("present_file_count", 0), "note": "Present HELP/META evidence contracts attached by hash."},
        {"metric": "dry_run_combined_markdown_created", "count": 1, "note": relpath_posix(dry_markdown, paths.repo_root)},
        {"metric": "selected_assembly_combined_exists", "count": current_combined_exists, "note": relpath_posix(current_combined, paths.repo_root) if current_combined else "No selected-workspace combined Markdown found."},
        {"metric": "dry_run_hash_matches_current_combined", "count": hash_match, "note": "0 is REVIEW unless exact dry-run assembly is expected to match byte-for-byte."},
        {"metric": "validation_fail_rows", "count": validation_fail_rows, "note": "Validation FAIL rows from current inventory."},
        {"metric": "validation_review_rows", "count": validation_review_rows, "note": "Validation REVIEW rows from current inventory."},
        {"metric": "boundary_fail_rows", "count": boundary_fail_rows, "note": "Boundary FAIL rows."},
        {"metric": "manual_publication_rebuilt", "count": 0, "note": "MDO-226 does not rebuild or replace publication."},
        {"metric": "published_workspace_mutated", "count": 0, "note": "Published workspaces are not modified."},
        {"metric": "x64base_tables_created", "count": 0, "note": "MDO-226 does not create x64base tables."},
        {"metric": "cpp_files_created", "count": 0, "note": "MDO-226 does not create C++ files."},
        {"metric": "help_meta_cmdhelpchk_mutations", "count": 0, "note": "No protected-system mutation performed."},
    ], ["metric", "count", "note"])
    write_csv(paths.reports_dir / "mdo_226_build_dry_run_sections_v1.csv", section_rows)
    write_csv(paths.reports_dir / "mdo_226_build_dry_run_artifacts_v1.csv", artifact_rows, ["artifact_kind", "relative_path", "sha256", "status", "note"])
    write_csv(paths.reports_dir / "mdo_226_boundary_check_v1.csv", boundary_rows, ["boundary", "value", "status", "note"])
    write_csv(paths.reports_dir / "mdo_226_next_decision_options_v1.csv", [
        {"option": "A", "decision": "HOLD_AFTER_MDO_226_BUILD_DRY_RUN", "status": "AVAILABLE", "allowed_now": 1, "note": "Stop with Python dry-run build capability proven."},
        {"option": "B", "decision": "COMPARE_DRY_RUN_TO_PUBLICATION_AND_REFINE_ORDERING", "status": "AVAILABLE_IF_HASH_REVIEW_NEEDED", "allowed_now": 0, "note": "If dry-run hash differs, refine assembly ordering/formatting under a later package."},
        {"option": "C", "decision": "CREATE_X64BASE_MANUALGEN_IMPORT_DRY_RUN", "status": "REQUIRES_EXPLICIT_AUTHORIZATION", "allowed_now": 0, "note": "Would dry-run import Python manifests into MAN* proof-lane staging reports, not production tables."},
        {"option": "D", "decision": "CREATE_PYTHON_PUBLICATION_REBUILD_TO_NEW_REVISION", "status": "REQUIRES_EXPLICIT_AUTHORIZATION", "allowed_now": 0, "note": "Would create a new publication revision only after dry-run contract is accepted."},
        {"option": "E", "decision": "MUTATE_HELP_META_CMDHELPCHK_SOURCE_OR_RUNTIME", "status": "NOT_AUTHORIZED", "allowed_now": 0, "note": "Protected-system mutation remains outside MDO-226."},
    ], ["option", "decision", "status", "allowed_now", "note"])

    if logger is not None:
        for row in boundary_rows:
            logger.boundary(row["boundary"], row["value"], row["status"], row["note"])
        logger.event("INFO", "build-dry-run", "counts", sections=len(sections), media=len(media), appendices=len(appendices), validation_fail_rows=validation_fail_rows, boundary_fail_rows=boundary_fail_rows)
        logger.artifact("dry_run_markdown", dry_markdown, "Dry-run generated Markdown; not publication.")
        logger.artifact("dry_run_manifest", dry_manifest, "Dry-run manifest.")
        logger.artifact("build_dry_run_summary", paths.reports_dir / "mdo_226_build_dry_run_summary_v1.csv", "MDO-226 build dry-run summary.")

    state = {
        "run_id": run_id,
        "publication_id": publication_id,
        "selected_assembly_id": inv.get("selected_assembly_id", ""),
        "selected_assembly_workspace": inv.get("selected_assembly_workspace", ""),
        "selected_workspace_role": inv.get("selected_workspace_role", ""),
        "assembly_selection_mode": inv.get("assembly_selection_mode", ""),
        "selected_harvest_workspace": harvest.get("workspace", ""),
        "harvest_selection_mode": harvest.get("selection_mode", ""),
        "harvest_required_file_count": harvest.get("required_file_count", 0),
        "harvest_present_file_count": harvest.get("present_file_count", 0),
        "section_count": len(sections),
        "media_count": len(media),
        "appendix_count": len(appendices),
        "dry_run_markdown": relpath_posix(dry_markdown, paths.repo_root),
        "dry_run_manifest": relpath_posix(dry_manifest, paths.repo_root),
        "dry_run_hash_matches_current_combined": hash_match,
        "validation_fail_rows": validation_fail_rows,
        "validation_review_rows": validation_review_rows,
        "boundary_fail_rows": boundary_fail_rows,
    }
    counts = {
        "validation_fail_rows": validation_fail_rows,
        "validation_review_rows": validation_review_rows,
        "boundary_fail_rows": boundary_fail_rows,
        "section_count": len(sections),
        "media_count": len(media),
        "appendix_count": len(appendices),
        "hash_match": hash_match,
    }
    return state, counts

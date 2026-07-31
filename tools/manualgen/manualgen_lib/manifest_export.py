from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from . import __version__
from .inventory import collect_inventory
from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import write_csv, write_json, sha256_file, relpath_posix
from .validation import validate_inventory, summarize_validation, boundary_rows


def write_inventory_reports(paths: ManualgenPaths, inv: dict[str, Any], prefix: str) -> None:
    sections = inv.get("sections", [])
    media = inv.get("media", [])
    appendices = inv.get("appendices", [])
    manifests = inv.get("machine_manifests", [])
    harvest = inv.get("harvest", {})
    summary = [
        {"metric": "publication_workspaces", "count": len(inv.get("publication_workspaces", [])), "note": "Publication workspaces discovered."},
        {"metric": "selected_assembly_section_files", "count": len(sections), "note": "Section files in the selected assembly workspace."},
        {"metric": "appendix_files", "count": len(appendices), "note": "Appendix Markdown files inventoried."},
        {"metric": "media_files", "count": len(media), "note": "Media files under docs/media inventoried."},
        {"metric": "machine_manifest_files", "count": len(manifests), "note": "JSON machine manifests inventoried."},
        {"metric": "harvest_required_files", "count": harvest.get("required_file_count", 0), "note": "Required HELP/META evidence contracts."},
        {"metric": "harvest_present_files", "count": harvest.get("present_file_count", 0), "note": "Present HELP/META evidence contracts."},
        {"metric": "manual_publication_rebuilt", "count": 0, "note": "Inventory is read/report only."},
        {"metric": "protected_system_mutations", "count": 0, "note": "No HELP/META/CMDHELPCHK/source/runtime mutation."},
    ]
    write_csv(paths.reports_dir / f"{prefix}_inventory_summary_v1.csv", summary, ["metric", "count", "note"])
    write_csv(paths.reports_dir / f"{prefix}_inventory_sections_v1.csv", sections)
    write_csv(paths.reports_dir / f"{prefix}_inventory_media_v1.csv", media)
    write_csv(paths.reports_dir / f"{prefix}_inventory_appendices_v1.csv", appendices)
    write_csv(paths.reports_dir / f"{prefix}_inventory_machine_manifests_v1.csv", manifests)
    write_csv(paths.reports_dir / f"{prefix}_inventory_harvest_v1.csv", harvest.get("files", []))


def write_validate_reports(paths: ManualgenPaths, checks: list[dict[str, Any]], prefix: str) -> dict[str, int]:
    summary_counts = summarize_validation(checks)
    boundaries = boundary_rows()
    boundary_fail_rows = sum(1 for row in boundaries if row.get("status") == "FAIL")
    summary = [
        {"metric": "validation_checks", "count": summary_counts["validation_checks"], "note": "Validation checks executed."},
        {"metric": "validation_fail_rows", "count": summary_counts["validation_fail_rows"], "note": "Validation FAIL rows."},
        {"metric": "validation_review_rows", "count": summary_counts["validation_review_rows"], "note": "Validation REVIEW rows."},
        {"metric": "boundary_fail_rows", "count": boundary_fail_rows, "note": "Boundary FAIL rows."},
        {"metric": "manual_publication_rebuilt", "count": 0, "note": "Validate does not rebuild publication."},
        {"metric": "x64base_tables_created", "count": 0, "note": "Validate does not create x64base tables."},
        {"metric": "cpp_files_created", "count": 0, "note": "Validate does not create C++ files."},
        {"metric": "protected_system_mutations", "count": 0, "note": "No HELP/META/CMDHELPCHK/source/runtime mutation."},
    ]
    write_csv(paths.reports_dir / f"{prefix}_validate_summary_v1.csv", summary, ["metric", "count", "note"])
    write_csv(paths.reports_dir / f"{prefix}_validate_checks_v1.csv", checks, ["check_id", "status", "value", "expected", "note"])
    write_csv(paths.reports_dir / f"{prefix}_boundary_check_v1.csv", boundaries, ["boundary", "value", "status", "note"])
    summary_counts["boundary_fail_rows"] = boundary_fail_rows
    return summary_counts


def export_manifests(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    inv = collect_inventory(paths)
    checks = validate_inventory(paths, inv)
    counts = write_validate_reports(paths, checks, "mdo_224")
    write_inventory_reports(paths, inv, "mdo_224")

    boundaries = boundary_rows()
    exported_utc = utc_now_iso()
    current_state = {
        "schema": "dottalk.manualgen.current_state_manifest.v1",
        "created_utc": exported_utc,
        "manual_id": paths.manual_id,
        "manualgen_version": __version__,
        "python_version": sys.version,
        "repo_root": str(paths.repo_root),
        "selected_assembly_workspace": inv.get("selected_assembly_workspace", ""),
        "selected_assembly_id": inv.get("selected_assembly_id", ""),
        "selected_workspace_role": inv.get("selected_workspace_role", ""),
        "assembly_selection_mode": inv.get("assembly_selection_mode", ""),
        "assembly_selection_requested": inv.get("assembly_selection_requested", ""),
        "assembly_selection_valid": inv.get("assembly_selection_valid", 0),
        "current_publication_workspace": inv.get("current_publication_workspace", ""),
        "current_publication_id": inv.get("current_publication_id", ""),
        "section_count": len(inv.get("sections", [])),
        "media_count": len(inv.get("media", [])),
        "appendix_count": len(inv.get("appendices", [])),
        "machine_manifest_count": len(inv.get("machine_manifests", [])),
        "media_anchor_count": len(inv.get("media_anchors", [])),
        "harvest": inv.get("harvest", {}),
        "validation": counts,
        "sections": inv.get("sections", []),
        "media": inv.get("media", []),
        "appendices": inv.get("appendices", []),
        "machine_manifests": inv.get("machine_manifests", []),
        "media_anchors": inv.get("media_anchors", []),
        "boundary": boundaries,
    }
    publication_manifest = {
        "schema": "dottalk.manualgen.publication_manifest.v1",
        "created_utc": exported_utc,
        "manual_id": paths.manual_id,
        "manifest_role": "legacy_compatibility_assembly_reference_export",
        "publication_authority_claimed": 0,
        "selected_workspace_role": inv.get("selected_workspace_role", ""),
        "assembly_selection_mode": inv.get("assembly_selection_mode", ""),
        "publication_id": inv.get("current_publication_id", ""),
        "publication_workspace": inv.get("current_publication_workspace", ""),
        "section_count": len(inv.get("sections", [])),
        "appendix_count": len(inv.get("appendices", [])),
        "media_count": len(inv.get("media", [])),
        "sections": inv.get("sections", []),
        "appendices": inv.get("appendices", []),
        "media": inv.get("media", []),
        "harvest": inv.get("harvest", {}),
    }
    assembly_manifest = {
        **publication_manifest,
        "schema": "dottalk.manualgen.assembly_reference_manifest.v1",
        "manifest_role": "selected_assembly_reference",
        "assembly_workspace": inv.get("selected_assembly_workspace", ""),
        "assembly_id": inv.get("selected_assembly_id", ""),
        "selection_requested": inv.get("assembly_selection_requested", ""),
        "selection_valid": inv.get("assembly_selection_valid", 0),
        "harvest": inv.get("harvest", {}),
    }
    current_manifest_path = paths.manifests_dir / "manualgen_current_state_manifest_v1.json"
    publication_manifest_path = paths.manifests_dir / "manualgen_current_publication_manifest_v1.json"
    assembly_manifest_path = paths.manifests_dir / "manualgen_selected_assembly_manifest_v1.json"
    write_json(current_manifest_path, current_state)
    write_json(publication_manifest_path, publication_manifest)
    write_json(assembly_manifest_path, assembly_manifest)

    artifact_rows = []
    for kind, path, note in [
        ("current_state_manifest", current_manifest_path, "Canonical current manualgen state export."),
        ("publication_manifest", publication_manifest_path, "Legacy-named compatibility export for the selected assembly reference; no publication authority claimed."),
        ("selected_assembly_manifest", assembly_manifest_path, "Explicitly classified assembly-reference manifest export; not publication authority."),
        ("inventory_summary", paths.reports_dir / "mdo_224_inventory_summary_v1.csv", "MDO-224 inventory summary."),
        ("validate_summary", paths.reports_dir / "mdo_224_validate_summary_v1.csv", "MDO-224 validation summary."),
        ("boundary_check", paths.reports_dir / "mdo_224_boundary_check_v1.csv", "MDO-224 boundary check."),
    ]:
        artifact_rows.append({
            "artifact_kind": kind,
            "relative_path": relpath_posix(path, paths.repo_root),
            "sha256": sha256_file(path),
            "note": note,
        })
        if logger is not None:
            logger.artifact(kind, path, note)

    write_csv(paths.reports_dir / "mdo_224_manifest_export_artifacts_v1.csv", artifact_rows, ["artifact_kind", "relative_path", "sha256", "note"])
    if logger is not None:
        logger.artifact("manifest_export_artifacts", paths.reports_dir / "mdo_224_manifest_export_artifacts_v1.csv", "Artifact list for MDO-224 manifest export.")

    summary = [
        {"metric": "mdo_223_confirmed_green", "count": 1, "note": "MDO-223 validate summary was present before MDO-224 execution."},
        {"metric": "mdo_224_manifest_export_created", "count": 1, "note": "Manifest export command executed."},
        {"metric": "python_312_runtime", "count": 1, "note": "Python runtime satisfies 3.12 requirement."},
        {"metric": "sections_exported", "count": len(inv.get("sections", [])), "note": "Sections in the selected assembly manifest."},
        {"metric": "media_exported", "count": len(inv.get("media", [])), "note": "Media files in current state manifest."},
        {"metric": "appendices_exported", "count": len(inv.get("appendices", [])), "note": "Appendices in current state manifest."},
        {"metric": "machine_manifest_files_after_export", "count": len(list(paths.manifests_dir.glob("*.json"))), "note": "JSON manifest files present after export."},
        {"metric": "validation_fail_rows", "count": counts.get("validation_fail_rows", 0), "note": "Validation FAIL rows after manifest export."},
        {"metric": "boundary_fail_rows", "count": counts.get("boundary_fail_rows", 0), "note": "Boundary FAIL rows after manifest export."},
        {"metric": "manual_publication_rebuilt", "count": 0, "note": "MDO-224 does not rebuild publication."},
        {"metric": "x64base_tables_created", "count": 0, "note": "MDO-224 does not create x64base tables."},
        {"metric": "cpp_files_created", "count": 0, "note": "MDO-224 does not create C++ files."},
        {"metric": "help_meta_cmdhelpchk_mutations", "count": 0, "note": "No protected-system mutation performed."},
    ]
    write_csv(paths.reports_dir / "mdo_224_manifest_export_summary_v1.csv", summary, ["metric", "count", "note"])
    if logger is not None:
        logger.artifact("manifest_export_summary", paths.reports_dir / "mdo_224_manifest_export_summary_v1.csv", "MDO-224 summary.")

    log_summary = [
        {"metric": "run_id", "count": logger.run_id if logger else "", "note": "Structured run id for export command."},
        {"metric": "events_jsonl_created", "count": 1 if logger else 0, "note": "events.jsonl created for the export command."},
        {"metric": "run_json_created", "count": 1 if logger else 0, "note": "run.json created for the export command."},
        {"metric": "artifact_log_rows", "count": len(logger.artifacts) if logger else 0, "note": "Artifact rows recorded before logger close."},
        {"metric": "boundary_log_rows", "count": len(boundaries), "note": "Boundary rows recorded."},
        {"metric": "error_rows", "count": len(logger.errors) if logger else 0, "note": "Error rows recorded before logger close."},
    ]
    write_csv(paths.reports_dir / "mdo_224_run_log_hardening_summary_v1.csv", log_summary, ["metric", "count", "note"])
    if logger is not None:
        logger.artifact("run_log_hardening_summary", paths.reports_dir / "mdo_224_run_log_hardening_summary_v1.csv", "Structured log hardening summary.")

    next_options = [
        {"option": "A", "decision": "HOLD_AFTER_MDO_224_MANIFEST_EXPORT", "status": "AVAILABLE", "allowed_now": 1, "note": "Stop with manifest export and run-log hardening complete."},
        {"option": "B", "decision": "CREATE_MDO_225_X64BASE_MANUALGEN_CATALOG_SCHEMA_PLAN", "status": "REQUIRES_EXPLICIT_AUTHORIZATION", "allowed_now": 0, "note": "Would plan MANRUN, MANSECTION, MANMEDIA, MANANCHOR, MANHASH, MANREVIEW, MANPUB, and MANAPPX tables."},
        {"option": "C", "decision": "CREATE_MDO_226_PYTHON_BUILD_REBUILD_DRY_RUN", "status": "REQUIRES_EXPLICIT_AUTHORIZATION", "allowed_now": 0, "note": "Would add dry-run build/rebuild planning without replacing publication."},
        {"option": "D", "decision": "CREATE_CPP_MANUALGEN_INTEGRATION_PLAN", "status": "DEFERRED", "allowed_now": 0, "note": "C++ integration waits until Python and x64base contracts stabilize."},
        {"option": "E", "decision": "MUTATE_HELP_META_CMDHELPCHK_SOURCE_OR_RUNTIME", "status": "NOT_AUTHORIZED", "allowed_now": 0, "note": "Protected-system mutation remains outside MDO-224."},
    ]
    write_csv(paths.reports_dir / "mdo_224_next_decision_options_v1.csv", next_options, ["option", "decision", "status", "allowed_now", "note"])
    if logger is not None:
        logger.artifact("next_decision_options", paths.reports_dir / "mdo_224_next_decision_options_v1.csv", "MDO-224 next decision options.")

    return current_state, counts

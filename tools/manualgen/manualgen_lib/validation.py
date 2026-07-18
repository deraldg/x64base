from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .paths import ManualgenPaths


def validate_inventory(paths: ManualgenPaths, inv: dict[str, Any]) -> list[dict[str, Any]]:
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    sections = inv.get("sections", [])
    media = inv.get("media", [])
    appendices = inv.get("appendices", [])
    manifests = inv.get("machine_manifests", [])
    anchors = inv.get("media_anchors", [])
    selected = inv.get("selected_assembly_id", inv.get("current_publication_id", ""))
    selection_mode = inv.get("assembly_selection_mode", "")
    selection_valid = int(inv.get("assembly_selection_valid", 0))
    selection_role = inv.get("selected_workspace_role", "")
    section_count = len(sections)
    harvest = inv.get("harvest", {})

    checks: list[dict[str, Any]] = []

    def add(check_id: str, status: str, value: Any, expected: str, note: str) -> None:
        checks.append({"check_id": check_id, "status": status, "value": value, "expected": expected, "note": note})

    add("PYTHON_312", "PASS" if sys.version_info >= (3, 12) else "FAIL", py_version, ">= 3.12", "Manualgen requires Python 3.12 or newer.")
    add("REPO_ROOT_EXISTS", "PASS" if paths.repo_root.exists() else "FAIL", str(paths.repo_root), "exists", "Repository root visible.")
    add("MANUALGEN_ROOT_EXISTS", "PASS" if paths.manualgen_root.exists() else "FAIL", str(paths.manualgen_root), "exists", "Manualgen documentation root visible.")
    add("MANIFEST_DIR_EXISTS", "PASS" if paths.manifests_dir.exists() else "FAIL", str(paths.manifests_dir), "exists", "Machine manifest directory visible.")
    add("MEDIA_ROOT_EXISTS", "PASS" if paths.media_root.exists() else "FAIL", str(paths.media_root), "exists", "docs/media is the current media staging root.")
    add("ASSEMBLY_WORKSPACE_SELECTED", "PASS" if selected else "FAIL", selected or "", "found", "Workspace selected for inventory/assembly; this does not establish publication authority.")
    add("ASSEMBLY_SELECTION_VALID", "PASS" if selection_valid else "FAIL", selection_valid, "1", "Explicit selection must resolve to a discovered publication workspace.")
    add("ASSEMBLY_SELECTION_EXPLICIT", "PASS" if selection_mode == "explicit" else "REVIEW", selection_mode, "explicit", "Legacy default selection remains compatible but must not be presented as authority.")
    add("ASSEMBLY_WORKSPACE_ROLE", "PASS" if selection_role != "unclassified_publication_workspace" else "REVIEW", selection_role, "classified role", "Role distinguishes primary-reader and supporting assembly workspaces.")
    add("CURRENT_PUBLICATION_WORKSPACE", "PASS" if selected else "FAIL", selected or "", "found", "Backward-compatible alias for the selected assembly workspace.")
    expected_sections = "25 after MDO-220 media-section revision, or 24 for original publication"
    add("CURRENT_PUBLICATION_SECTION_COUNT", "PASS" if section_count in (24, 25) else "FAIL", section_count, expected_sections, "Current publication section count.")
    add("APPENDIX_FILE_COUNT", "PASS" if len(appendices) >= 3 else "REVIEW", len(appendices), ">= 3 after MDO-215", "Appendices visible in publication lanes.")
    add("MDO_219_MEDIA_ANCHOR_MANIFEST", "PASS" if paths.mdo219_anchor_manifest.exists() else "FAIL", str(paths.mdo219_anchor_manifest), "exists", "Media anchor manifest from MDO-219.")
    add("MEDIA_ANCHOR_ROW_COUNT", "PASS" if len(anchors) == 9 else "FAIL", len(anchors), "9 after MDO-219", "MDO-219 accepted 9 media anchors.")
    add("MEDIA_FILE_COUNT", "PASS" if len(media) >= 9 else "FAIL", len(media), ">= 9", "Media files visible under docs/media.")
    anchor_hashes = {row.get("sha256", "").upper() for row in anchors if row.get("sha256")}
    media_hashes = {row.get("sha256", "").upper() for row in media if row.get("sha256")}
    mismatch_count = len(anchor_hashes - media_hashes) if anchor_hashes else 0
    add("MEDIA_HASH_MISMATCHES", "PASS" if mismatch_count == 0 else "FAIL", mismatch_count, "0", "Media file hashes should match MDO-219 anchor manifest when present.")
    add("MACHINE_MANIFEST_COUNT", "PASS" if len(manifests) >= 2 else "FAIL", len(manifests), ">= 2", "MDO-222 machine manifests plus later manifest exports.")
    add("HARVEST_WORKSPACE_SELECTED", "PASS" if harvest.get("workspace") else "FAIL", harvest.get("workspace", ""), "found", "HELP/META evidence workspace selected without copying or promotion.")
    add("HARVEST_SELECTION_VALID", "PASS" if harvest.get("selection_valid") else "FAIL", harvest.get("selection_valid", 0), "1", "Explicit harvest selection must resolve to an existing directory.")
    add("HARVEST_SELECTION_EXPLICIT", "PASS" if harvest.get("selection_mode") == "explicit" else "REVIEW", harvest.get("selection_mode", ""), "explicit", "Evidence-bearing runs must name their HELP/META harvest workspace.")
    add("HARVEST_REQUIRED_FILES", "PASS" if harvest.get("present_file_count") == harvest.get("required_file_count") else "FAIL", harvest.get("present_file_count", 0), str(harvest.get("required_file_count", 0)), "All required HELP/META CSV contracts must be present.")
    add("HARVEST_CSV_READABLE", "PASS" if harvest.get("readable_file_count") == harvest.get("required_file_count") else "FAIL", harvest.get("readable_file_count", 0), str(harvest.get("required_file_count", 0)), "Every required harvest file must have a readable CSV header.")
    file_rows = {row.get("file_name"): row for row in harvest.get("files", [])}
    for name in ("HELP_COMMANDS.csv", "HELP_HELP_LINE.csv", "META_SYSCMD.csv"):
        count = file_rows.get(name, {}).get("row_count", -1)
        add(f"HARVEST_NONEMPTY_{name.removesuffix('.csv')}", "PASS" if count > 0 else "FAIL", count, "> 0", "Core harvested evidence must not be empty.")
    return checks


def summarize_validation(checks: list[dict[str, Any]]) -> dict[str, int]:
    fail_rows = sum(1 for row in checks if row.get("status") == "FAIL")
    review_rows = sum(1 for row in checks if row.get("status") == "REVIEW")
    return {
        "validation_checks": len(checks),
        "validation_fail_rows": fail_rows,
        "validation_review_rows": review_rows,
    }


def boundary_rows() -> list[dict[str, Any]]:
    return [
        {"boundary": "manual_publication_rebuilt", "value": 0, "status": "PASS", "note": "MDO-224 does not rebuild publication."},
        {"boundary": "media_files_copied_moved_renamed_deleted", "value": 0, "status": "PASS", "note": "MDO-224 does not alter media files."},
        {"boundary": "x64base_tables_created", "value": 0, "status": "PASS", "note": "MDO-224 does not create x64base tables."},
        {"boundary": "cpp_files_created", "value": 0, "status": "PASS", "note": "MDO-224 does not create C++ files."},
        {"boundary": "help_meta_cmdhelpchk_mutations", "value": 0, "status": "PASS", "note": "No protected-system mutation performed."},
        {"boundary": "product_source_edits", "value": 0, "status": "PASS", "note": "No product source edits outside authorized tools/manualgen update."},
        {"boundary": "runtime_data_mutations", "value": 0, "status": "PASS", "note": "No runtime data mutation performed."},
        {"boundary": "production_selfdoc_metadata_promotions", "value": 0, "status": "PASS", "note": "No production SelfDoc metadata promotion performed."},
    ]

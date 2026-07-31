from __future__ import annotations

from pathlib import Path
from typing import Any

from .harvest import inventory_harvest
from .paths import ManualgenPaths
from .util import first_heading, read_text, relpath, relpath_posix, sha256_file, count_headings, count_words, read_csv

MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tif", ".tiff"}


def discover_publication_workspaces(paths: ManualgenPaths) -> list[Path]:
    if not paths.published_dir.exists():
        return []
    return sorted([p for p in paths.published_dir.iterdir() if p.is_dir() and p.name.startswith("developer_manual_publication_v1")])


def _resolve_requested_workspace(paths: ManualgenPaths, requested: str) -> Path:
    raw = Path(requested)
    if raw.is_absolute():
        return raw.resolve()
    if len(raw.parts) == 1:
        return (paths.published_dir / raw).resolve()
    return (paths.repo_root / raw).resolve()


def select_assembly_workspace(paths: ManualgenPaths, workspaces: list[Path]) -> tuple[Path | None, str, bool]:
    """Select a workspace for inventory/assembly without claiming promotion."""
    if paths.publication_workspace:
        requested = _resolve_requested_workspace(paths, paths.publication_workspace)
        discovered = {workspace.resolve() for workspace in workspaces}
        if requested in discovered:
            return requested, "explicit", True
        return None, "explicit_invalid", False

    preferred = paths.published_dir / "developer_manual_publication_v1_media_section_v1"
    if preferred.exists():
        return preferred, "legacy_default", True
    fallback = paths.published_dir / "developer_manual_publication_v1"
    if fallback.exists():
        return fallback, "legacy_fallback", True
    return (workspaces[-1], "legacy_last_discovered", True) if workspaces else (None, "none", False)


def select_current_publication(paths: ManualgenPaths, workspaces: list[Path]) -> Path | None:
    """Backward-compatible path-only wrapper for older callers."""
    selected, _, _ = select_assembly_workspace(paths, workspaces)
    return selected


def workspace_role(paths: ManualgenPaths, workspace: Path | None) -> str:
    if workspace is None:
        return "unresolved"
    if workspace.name == "developer_manual_publication_v1":
        return "primary_reader_workspace"
    role_index = paths.published_dir / "README.md"
    if role_index.exists():
        role_text = read_text(role_index)
        if workspace.name + "/" in role_text and "Supporting publication workspaces" in role_text:
            return "supporting_assembly_reference"
    return "unclassified_publication_workspace"


def section_slug(path: Path, section_root: Path) -> str:
    rel = path.relative_to(section_root).with_suffix("")
    return "/".join(rel.parts)


def inventory_sections(paths: ManualgenPaths, publication: Path | None) -> list[dict[str, Any]]:
    if publication is None:
        return []
    section_root = publication / "sections"
    if not section_root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for idx, path in enumerate(sorted(section_root.rglob("*.md")), start=1):
        text = read_text(path)
        rows.append({
            "section_index": idx,
            "section_slug": section_slug(path, section_root),
            "title": first_heading(text),
            "publication_id": publication.name,
            "relative_path": relpath(path, paths.repo_root),
            "relative_path_posix": relpath_posix(path, paths.repo_root),
            "sha256": sha256_file(path),
            "line_count": len(text.splitlines()),
            "heading_count": count_headings(text),
            "word_estimate": count_words(text),
        })
    return rows


def inventory_media(paths: ManualgenPaths) -> list[dict[str, Any]]:
    if not paths.media_root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for idx, path in enumerate(sorted(p for p in paths.media_root.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS), start=1):
        rows.append({
            "media_index": idx,
            "file_name": path.name,
            "relative_path": relpath(path, paths.repo_root),
            "relative_path_posix": relpath_posix(path, paths.repo_root),
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return rows


def inventory_appendices(paths: ManualgenPaths) -> list[dict[str, Any]]:
    if not paths.published_dir.exists():
        return []
    files = sorted(paths.published_dir.rglob("appendices/*.md"))
    rows: list[dict[str, Any]] = []
    for idx, path in enumerate(files, start=1):
        text = read_text(path)
        rows.append({
            "appendix_index": idx,
            "appendix_slug": path.stem,
            "title": first_heading(text),
            "relative_path": relpath(path, paths.repo_root),
            "relative_path_posix": relpath_posix(path, paths.repo_root),
            "sha256": sha256_file(path),
            "line_count": len(text.splitlines()),
            "word_estimate": count_words(text),
        })
    return rows


def inventory_machine_manifests(paths: ManualgenPaths) -> list[dict[str, Any]]:
    if not paths.manifests_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for idx, path in enumerate(sorted(paths.manifests_dir.glob("*.json")), start=1):
        rows.append({
            "manifest_index": idx,
            "file_name": path.name,
            "relative_path": relpath(path, paths.repo_root),
            "relative_path_posix": relpath_posix(path, paths.repo_root),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    return rows


def read_media_anchor_manifest(paths: ManualgenPaths) -> list[dict[str, str]]:
    return read_csv(paths.mdo219_anchor_manifest)


def collect_inventory(paths: ManualgenPaths) -> dict[str, Any]:
    workspaces = discover_publication_workspaces(paths)
    selected, selection_mode, selection_valid = select_assembly_workspace(paths, workspaces)
    selected_role = workspace_role(paths, selected)
    sections = inventory_sections(paths, selected)
    media = inventory_media(paths)
    appendices = inventory_appendices(paths)
    manifests = inventory_machine_manifests(paths)
    anchors = read_media_anchor_manifest(paths)
    harvest = inventory_harvest(paths)
    return {
        "manual_id": paths.manual_id,
        "repo_root": str(paths.repo_root),
        "publication_workspaces": [relpath(w, paths.repo_root) for w in workspaces],
        "selected_assembly_workspace": relpath(selected, paths.repo_root) if selected else "",
        "selected_assembly_id": selected.name if selected else "",
        "selected_workspace_role": selected_role,
        "assembly_selection_mode": selection_mode,
        "assembly_selection_requested": paths.publication_workspace or "",
        "assembly_selection_valid": 1 if selection_valid else 0,
        # Backward-compatible aliases. They describe selection, not authority.
        "current_publication_workspace": relpath(selected, paths.repo_root) if selected else "",
        "current_publication_id": selected.name if selected else "",
        "sections": sections,
        "media": media,
        "appendices": appendices,
        "machine_manifests": manifests,
        "media_anchors": anchors,
        "harvest": harvest,
    }

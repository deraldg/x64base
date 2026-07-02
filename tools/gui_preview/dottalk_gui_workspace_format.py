"""Workspace graph/status formatting shared by the Python GUI preview."""

from __future__ import annotations

from dottalk_gui_backend import PythonArea, PythonIndexInfo, PythonRelationInfo


def visible_area_id(area_id: int) -> str:
    return "none" if area_id == 0 else str(area_id - 1)


def format_workspace_graph_text(areas: list[PythonArea],
                                active_area_id: int,
                                title: str,
                                no_open_areas_text: str,
                                indexes: list[PythonIndexInfo] | None = None,
                                relations: list[PythonRelationInfo] | None = None) -> str:
    indexes = indexes or []
    relations = relations or []
    lines = [
        title,
        "",
        f"Areas: {len(areas)}",
        f"Active area: {visible_area_id(active_area_id)}",
        "",
    ]

    if not areas:
        lines.append(no_open_areas_text)
    else:
        lines.append("Areas")
        for area in areas:
            snapshot = area.snapshot
            fields = list(snapshot.get("fields", []))
            marker = "*" if area.area_id == active_area_id else " "
            lines.extend([
                f"{marker} {visible_area_id(area.area_id)}  {area.display_name}",
                f"    table: {area.path}",
                f"    records: {snapshot.get('record_count', 0)}",
                f"    fields: {len(fields)}",
            ])

    lines.append("")
    lines.append("Indexes")
    if not indexes:
        lines.append("  none")
    else:
        for index in indexes:
            active = " yes" if index.active else ""
            tag = f" TAG {index.tag}" if index.tag else ""
            container = f" {index.container}" if index.container else ""
            lines.append(
                f"  {visible_area_id(index.area_id)} {index.area_name} {index.kind}{active}"
                f"{tag} {index.direction} [{index.backend}]{container}"
            )

    lines.append("")
    lines.append("Relations")
    if not relations:
        lines.append("  none")
    else:
        for relation in relations:
            key = f" ON {relation.parent_key}" if relation.parent_key else ""
            matches = f" ({relation.match_count} matches)" if relation.match_count else ""
            lines.append(f"  {relation.parent} -> {relation.child}{key}{matches}")

    lines.extend([
        "",
        "Browsers/lists: workspace graph service pending",
        "ERSATZ presets: runtime output available; visual presets pending",
        "DTSchema load/save: bootstrap menu active; graph service pending",
    ])
    return "\n".join(lines)

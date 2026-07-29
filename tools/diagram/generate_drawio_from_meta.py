#!/usr/bin/env python3
"""
generate_drawio_from_meta.py

M1.1 DotTalk++ metadata-to-draw.io generator.

Reads a pipe-delimited metadata seed and emits a diagrams.net .drawio file.

Design rules:
- The seed owns the architecture facts.
- The generator owns parsing, validation, layout, and XML emission.
- The generator must not hardcode DotTalk++ relationships such as "LIST uses QuerySpec".
"""

from __future__ import annotations

import html
import os
import sys
import textwrap
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


ALLOWED_NODE_TYPES = {
    "command",
    "contract",
    "boundary",
    "runtime_service",
    "source_file",
    "table",
    "field",
    "index_container",
    "index_tag",
    "relation",
    "workspace",
    "metadata_table",
    "help_topic",
}

ALLOWED_STATUS = {
    "implemented",
    "planned",
    "boundary",
    "deprecated",
    "superseded",
    "experimental",
    "unknown",
}

ALLOWED_PROOF = {
    "runtime-confirmed",
    "source-confirmed",
    "script-confirmed",
    "help-confirmed",
    "session-confirmed",
    "design-intent",
    "historical",
    "speculative",
    "unknown",
}

ALLOWED_RELATIONS = {
    "uses",
    "renders_through",
    "reports_through",
    "iterates_through",
    "owns",
    "delegates_to",
    "attaches",
    "activates",
    "must_not_depend_on",
    "may_adapt_to",
    "defines",
    "contains",
    "indexes",
    "relates_to",
    "supersedes",
    "deprecated_by",
}


@dataclass
class Node:
    node_id: str
    label: str
    node_type: str
    subsystem: str
    status: str
    proof: str
    notes: str


@dataclass
class Edge:
    edge_id: str
    from_node: str
    to_node: str
    relation: str
    status: str
    proof: str
    notes: str


@dataclass
class View:
    view_id: str
    label: str
    include_node_types: List[str]
    include_relations: List[str]
    layout: str
    notes: str


@dataclass
class Graph:
    format_info: Dict[str, str]
    nodes: Dict[str, Node]
    edges: Dict[str, Edge]
    views: Dict[str, View]


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def split_pipe(line: str) -> List[str]:
    # V0 deliberately does not support escaping. A pipe is a delimiter.
    return [part.strip() for part in line.rstrip("\n").split("|")]


def read_seed(path: str) -> Graph:
    section = None
    headers: Dict[str, List[str]] = {}
    format_info: Dict[str, str] = {}
    nodes: Dict[str, Node] = {}
    edges: Dict[str, Edge] = {}
    views: Dict[str, View] = {}

    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip().upper()
                if section not in {"FORMAT", "NODES", "EDGES", "VIEWS"}:
                    die(f"{path}:{lineno}: unknown section [{section}]")
                continue
            if section is None:
                die(f"{path}:{lineno}: row outside a section")

            parts = split_pipe(raw)

            if section == "FORMAT":
                if len(parts) != 2:
                    die(f"{path}:{lineno}: FORMAT row must be KEY|VALUE")
                format_info[parts[0]] = parts[1]
                continue

            if section not in headers:
                headers[section] = parts
                continue

            header = headers[section]
            if len(parts) != len(header):
                die(
                    f"{path}:{lineno}: expected {len(header)} fields in [{section}], "
                    f"got {len(parts)}. V0 does not allow embedded pipe characters."
                )
            row = dict(zip(header, parts))

            if section == "NODES":
                node = Node(
                    node_id=row["NODE_ID"],
                    label=row["LABEL"],
                    node_type=row["NODE_TYPE"],
                    subsystem=row["SUBSYSTEM"],
                    status=row["STATUS"],
                    proof=row["PROOF"],
                    notes=row["NOTES"],
                )
                if node.node_id in nodes:
                    die(f"{path}:{lineno}: duplicate NODE_ID {node.node_id}")
                nodes[node.node_id] = node

            elif section == "EDGES":
                edge = Edge(
                    edge_id=row["EDGE_ID"],
                    from_node=row["FROM_NODE"],
                    to_node=row["TO_NODE"],
                    relation=row["RELATION"],
                    status=row["STATUS"],
                    proof=row["PROOF"],
                    notes=row["NOTES"],
                )
                if edge.edge_id in edges:
                    die(f"{path}:{lineno}: duplicate EDGE_ID {edge.edge_id}")
                edges[edge.edge_id] = edge

            elif section == "VIEWS":
                view = View(
                    view_id=row["VIEW_ID"],
                    label=row["LABEL"],
                    include_node_types=[x.strip() for x in row["INCLUDE_NODE_TYPES"].split(",") if x.strip()],
                    include_relations=[x.strip() for x in row["INCLUDE_RELATIONS"].split(",") if x.strip()],
                    layout=row["LAYOUT"],
                    notes=row["NOTES"],
                )
                if view.view_id in views:
                    die(f"{path}:{lineno}: duplicate VIEW_ID {view.view_id}")
                views[view.view_id] = view

    graph = Graph(format_info=format_info, nodes=nodes, edges=edges, views=views)
    validate_graph(graph)
    return graph


def validate_graph(graph: Graph) -> None:
    if graph.format_info.get("VERSION") != "1":
        die("Only FORMAT VERSION|1 is supported")

    for n in graph.nodes.values():
        if not n.node_id:
            die("empty NODE_ID")
        if n.node_type not in ALLOWED_NODE_TYPES:
            die(f"{n.node_id}: unknown NODE_TYPE {n.node_type}")
        if n.status not in ALLOWED_STATUS:
            die(f"{n.node_id}: unknown STATUS {n.status}")
        if n.proof not in ALLOWED_PROOF:
            die(f"{n.node_id}: unknown PROOF {n.proof}")

    for e in graph.edges.values():
        if e.from_node not in graph.nodes:
            die(f"{e.edge_id}: FROM_NODE {e.from_node} not found")
        if e.to_node not in graph.nodes:
            die(f"{e.edge_id}: TO_NODE {e.to_node} not found")
        if e.relation not in ALLOWED_RELATIONS:
            die(f"{e.edge_id}: unknown RELATION {e.relation}")
        if e.status not in ALLOWED_STATUS:
            die(f"{e.edge_id}: unknown STATUS {e.status}")
        if e.proof not in ALLOWED_PROOF:
            die(f"{e.edge_id}: unknown PROOF {e.proof}")

    for v in graph.views.values():
        for t in v.include_node_types:
            if t not in ALLOWED_NODE_TYPES:
                die(f"{v.view_id}: unknown included node type {t}")
        for r in v.include_relations:
            if r not in ALLOWED_RELATIONS:
                die(f"{v.view_id}: unknown included relation {r}")


def select_view(graph: Graph, view_id: str) -> Tuple[View, Dict[str, Node], Dict[str, Edge]]:
    if view_id not in graph.views:
        die(f"view not found: {view_id}")
    view = graph.views[view_id]

    selected_nodes = {
        nid: node
        for nid, node in graph.nodes.items()
        if node.node_type in view.include_node_types
    }

    selected_edges = {}
    for eid, edge in graph.edges.items():
        if edge.relation not in view.include_relations:
            continue
        if edge.from_node not in selected_nodes or edge.to_node not in selected_nodes:
            continue
        selected_edges[eid] = edge

    connected_ids = set()
    for edge in selected_edges.values():
        connected_ids.add(edge.from_node)
        connected_ids.add(edge.to_node)

    # Keep selected nodes that are connected, plus any boundary note nodes.
    selected_nodes = {
        nid: node
        for nid, node in selected_nodes.items()
        if nid in connected_ids or node.node_type == "boundary"
    }

    return view, selected_nodes, selected_edges


def wrap_label(label: str, max_width: int = 24) -> str:
    lines = []
    for raw in label.split("/"):
        raw = raw.strip()
        if not raw:
            continue
        lines.extend(textwrap.wrap(raw, width=max_width) or [raw])
    return "\n".join(lines)


def node_display_label(node: Node) -> str:
    # M1.1 cleanup: keep boxes readable. The proof remains in metadata.
    label = wrap_label(node.label, 26)
    if node.node_type == "contract":
        return f"{label}\n[{node.node_type}]"
    if node.node_type == "boundary":
        return f"{label}\n[{node.status}]"
    return f"{label}\n[{node.node_type}]"


def node_style(node: Node) -> str:
    base = "rounded=1;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;strokeWidth=2;"
    if node.node_type == "command":
        return base + "fillColor=#dae8fc;strokeColor=#6c8ebf;"
    if node.node_type == "contract":
        return base + "fillColor=#d5e8d4;strokeColor=#82b366;"
    if node.node_type == "boundary":
        return base + "fillColor=#fff2cc;strokeColor=#d6b656;dashed=1;"
    return base + "fillColor=#f5f5f5;strokeColor=#666666;"


def edge_style(edge: Edge) -> str:
    base = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=11;endArrow=block;endFill=1;"
    if edge.relation == "must_not_depend_on" or edge.status == "boundary":
        return base + "dashed=1;strokeColor=#b85450;fontColor=#b85450;"
    if edge.status == "planned" or edge.proof in {"design-intent", "speculative"}:
        return base + "dashed=1;strokeColor=#666666;fontColor=#666666;"
    return base + "strokeColor=#000000;fontColor=#000000;"


def relation_label(edge: Edge) -> str:
    # M1.1 cleanup: relation only. Status/proof stay in metadata.
    return edge.relation


def layout_three_column_contracts(nodes: Dict[str, Node]) -> Dict[str, Tuple[int, int, int, int]]:
    # Wider columns and taller rows than M1.
    x_by_type = {
        "command": 80,
        "contract": 560,
        "boundary": 1040,
        "runtime_service": 1040,
    }
    width_by_type = {
        "command": 260,
        "contract": 300,
        "boundary": 300,
        "runtime_service": 280,
    }
    height_by_type = {
        "command": 80,
        "contract": 80,
        "boundary": 80,
        "runtime_service": 70,
    }

    order = {
        "command": 0,
        "contract": 1,
        "boundary": 2,
        "runtime_service": 3,
    }

    columns: Dict[str, List[Node]] = {"command": [], "contract": [], "boundary": [], "runtime_service": []}
    for node in nodes.values():
        columns.setdefault(node.node_type, []).append(node)

    # Stable, human-friendly order for this first lane. This is not relationship knowledge;
    # it is display ordering by ID/name within type.
    preferred = [
        "CMD_LIST",
        "CMD_SMARTLIST",
        "CMD_SIMPLE_BROWSER",
        "CMD_SMART_BROWSER",
        "CMD_WORKSPACE",
        "CMD_SETINDEX",
        "CMD_SETORDER",
        "SMARTLIST_QUERY_CONTRACT",
        "SMARTLIST_OUTPUT_CONTRACT",
        "LIST_MESSAGING_CONTRACT",
        "ORDER_ITERATION_CONTRACT",
        "RELATION_BROWSER_CONTRACT",
        "WORKSPACE_SESSION_CONTRACT",
        "BOUNDARY_SB_NOT_WORKSPACE",
    ]
    preferred_index = {node_id: i for i, node_id in enumerate(preferred)}

    positions: Dict[str, Tuple[int, int, int, int]] = {}
    for node_type, col_nodes in columns.items():
        col_nodes.sort(key=lambda n: preferred_index.get(n.node_id, 1000))
        x = x_by_type.get(node_type, 80)
        w = width_by_type.get(node_type, 260)

        # Give boundary lane more vertical separation from main horizontal traffic.
        y0 = 110 if node_type != "boundary" else 110
        step = 130 if node_type != "boundary" else 160

        for i, node in enumerate(col_nodes):
            h = height_by_type.get(node_type, 70)
            y = y0 + i * step
            positions[node.node_id] = (x, y, w, h)

    return positions


def make_mxfile(page_name: str) -> Tuple[ET.Element, ET.Element]:
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "",
            "agent": "DotTalk++ metadata diagram generator M1.1",
            "version": "24.7.17",
            "type": "device",
        },
    )
    # diagrams.net requires a page id, but a random UUID made identical source
    # regenerate as a dirty file. Keep the id stable for a named metadata view.
    diagram_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"dottalkpp:diagram:{page_name}"))
    diagram = ET.SubElement(mxfile, "diagram", {"id": diagram_id, "name": page_name})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1600",
            "dy": "1000",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1600",
            "pageHeight": "1000",
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    return mxfile, root


def add_vertex(root: ET.Element, cell_id: str, value: str, style: str, x: int, y: int, w: int, h: int) -> None:
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": cell_id,
            "value": html.escape(value).replace("\n", "<br>"),
            "style": style,
            "vertex": "1",
            "parent": "1",
        },
    )
    ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})


def add_edge(root: ET.Element, cell_id: str, edge: Edge, source_id: str, target_id: str, source_pos, target_pos) -> None:
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": cell_id,
            "value": html.escape(relation_label(edge)),
            "style": edge_style(edge),
            "edge": "1",
            "parent": "1",
            "source": source_id,
            "target": target_id,
        },
    )
    geom = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    sx, sy, sw, sh = source_pos
    tx, ty, tw, th = target_pos

    # For boundary edges, route outside the main contract column to reduce visual crossing.
    if edge.relation == "must_not_depend_on":
        arr = ET.SubElement(geom, "Array", {"as": "points"})
        mid_x = max(sx + sw, tx + tw) + 60
        ET.SubElement(arr, "mxPoint", {"x": str(mid_x), "y": str(sy + sh // 2)})
        ET.SubElement(arr, "mxPoint", {"x": str(mid_x), "y": str(ty + th // 2)})


def add_text_note(root: ET.Element, cell_id: str, text: str, x: int, y: int, w: int, h: int) -> None:
    style = "rounded=1;whiteSpace=wrap;html=1;fontSize=12;fillColor=#f5f5f5;strokeColor=#666666;"
    add_vertex(root, cell_id, text, style, x, y, w, h)


def add_title(root: ET.Element, text: str) -> None:
    style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=20;fontStyle=1;"
    add_vertex(root, "title", text, style, 400, 30, 520, 40)


def emit_drawio(graph: Graph, view_id: str, output_path: str) -> Tuple[int, int]:
    view, nodes, edges = select_view(graph, view_id)
    if view.layout != "three_column_contracts":
        die(f"unsupported layout: {view.layout}")

    positions = layout_three_column_contracts(nodes)
    mxfile, root = make_mxfile(view.label)

    add_title(root, view.label)

    id_map: Dict[str, str] = {}
    for node_id, node in nodes.items():
        cid = "n_" + node_id
        id_map[node_id] = cid
        x, y, w, h = positions[node_id]
        add_vertex(root, cid, node_display_label(node), node_style(node), x, y, w, h)

    # M1.1: Draw ordinary edges first, boundary edges last so the intent is visible.
    sorted_edges = sorted(edges.values(), key=lambda e: 1 if e.relation == "must_not_depend_on" else 0)
    for edge in sorted_edges:
        add_edge(
            root,
            "e_" + edge.edge_id,
            edge,
            id_map[edge.from_node],
            id_map[edge.to_node],
            positions[edge.from_node],
            positions[edge.to_node],
        )

    add_text_note(
        root,
        "legend",
        "Legend\nSolid = implemented / confirmed\nDashed = planned or boundary\nLabels come from metadata relations\nProof/status remain in seed",
        1040,
        720,
        310,
        100,
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    tree = ET.ElementTree(mxfile)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return len(nodes), len(edges)


def main(argv: List[str]) -> int:
    if len(argv) != 4:
        print(
            "usage: python generate_drawio_from_meta.py "
            "<seed.meta> <VIEW_ID> <output.drawio>",
            file=sys.stderr,
        )
        return 2

    seed_path, view_id, output_path = argv[1], argv[2], argv[3]
    graph = read_seed(seed_path)
    node_count, edge_count = emit_drawio(graph, view_id, output_path)
    print(f"Wrote {output_path}")
    print(f"Nodes: {node_count}")
    print(f"Edges: {edge_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

#!/usr/bin/env python3
"""Generate the durable SQLite <-> x64base Cascade teaching contract.

SQLite remains the executable relational authority.  The x64base side consists
of one X64 DBF projection per table, materialized teaching snapshots for views,
and this generator's sidecar metadata for relational features DBF cannot store.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
# System-bundle layout (owner ruling 2026-08-10): everything Cascade lives under
# dottalkpp/data/systems/cascade_erp/ -- sqlite/ (sealed package, moved intact
# with its checksums.sha256), dbf/ (43 mirrors), meta/ (generated JSON
# sidecars), indexes/, lmdb/, schema/ (.dtschema), scripts/. Old locations
# dottalkpp/data/cascade_precision_erp and dottalkpp/data/dbf/cascade_erp are
# retired; all files were untracked, so the move is invisible to git history.
SYSTEM_ROOT = REPO_ROOT / "dottalkpp" / "data" / "systems" / "cascade_erp"
DEFAULT_PACKAGE = SYSTEM_ROOT / "sqlite"
DEFAULT_SQLITE = DEFAULT_PACKAGE / "cascade_precision_mfg_erp.sqlite"
DEFAULT_OUTPUT = DEFAULT_PACKAGE / "x64base_mirror"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def quoted_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def rows_as_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    names = [column[0] for column in cursor.description or ()]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def x64_projection(
    column: dict[str, Any], max_text: int, observed_types: list[str]
) -> dict[str, Any]:
    declared = str(column.get("type") or "").upper()
    if "INT" in declared:
        physical = {"type": "N", "width": 20, "decimals": 0}
    elif any(token in declared for token in ("REAL", "FLOA", "DOUB", "NUM", "DEC")):
        physical = {"type": "N", "width": 20, "decimals": 6}
    elif "BLOB" in declared:
        physical = {"type": "unsupported", "width": None, "decimals": None}
    elif not declared and observed_types == ["integer"]:
        physical = {"type": "N", "width": 20, "decimals": 0}
    elif not declared and set(observed_types).issubset({"integer", "real"}):
        physical = {"type": "N", "width": 20, "decimals": 6}
    else:
        physical = {"type": "C", "width": max(1, min(254, max_text)), "decimals": 0}
    return {
        "logical_name": column["name"],
        "sqlite_declared_type": column.get("type") or "",
        "sqlite_not_null": bool(column.get("notnull")),
        "sqlite_default": column.get("dflt_value"),
        "sqlite_primary_key_ordinal": int(column.get("pk") or 0),
        "sqlite_observed_storage_types": observed_types,
        "planned_x64_type": physical,
        "physical_build_authority": "AUTODBF X64 runtime inference from sealed CSV",
    }


def object_metadata(conn: sqlite3.Connection, name: str, kind: str, sql: str) -> dict[str, Any]:
    ident = quoted_identifier(name)
    columns = rows_as_dicts(conn.execute(f"PRAGMA table_xinfo({ident})"))
    count = int(conn.execute(f"SELECT count(*) FROM {ident}").fetchone()[0])
    projections = []
    for column in columns:
        field = quoted_identifier(str(column["name"]))
        max_text = int(
            conn.execute(
                f"SELECT coalesce(max(length(CAST({field} AS TEXT))), 0) FROM {ident}"
            ).fetchone()[0]
        )
        observed_types = [
            str(row[0])
            for row in conn.execute(
                f"SELECT DISTINCT typeof({field}) FROM {ident} "
                f"WHERE {field} IS NOT NULL ORDER BY 1"
            ).fetchall()
        ]
        projections.append(x64_projection(column, max_text, observed_types))

    indexes: list[dict[str, Any]] = []
    foreign_keys: list[dict[str, Any]] = []
    if kind == "table":
        for index in rows_as_dicts(conn.execute(f"PRAGMA index_list({ident})")):
            index_name = quoted_identifier(str(index["name"]))
            index["columns"] = rows_as_dicts(conn.execute(f"PRAGMA index_xinfo({index_name})"))
            indexes.append(index)
        foreign_keys = rows_as_dicts(conn.execute(f"PRAGMA foreign_key_list({ident})"))

    return {
        "name": name,
        "sqlite_kind": kind,
        "sqlite_sql": sql,
        "row_count": count,
        "columns": columns,
        "indexes": indexes,
        "foreign_keys": foreign_keys,
        "x64base": {
            "physical_name": f"CASCADE_{name}",
            "object_kind": "table" if kind == "table" else "materialized_view_snapshot",
            "fields": projections,
            "native_constraints": [],
            "relational_semantics": "dual_schema_contract.json sidecar",
        },
    }


def export_view(conn: sqlite3.Connection, name: str, destination: Path) -> None:
    cursor = conn.execute(f"SELECT * FROM {quoted_identifier(name)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([column[0] for column in cursor.description or ()])
        for row in cursor:
            writer.writerow(["" if value is None else value for value in row])


def schema_document(obj: dict[str, Any]) -> dict[str, Any]:
    field_by_name = {field["name"]: field for field in obj["columns"]}
    fields = []
    for projection in obj["x64base"]["fields"]:
        physical = projection["planned_x64_type"]
        if physical["type"] == "unsupported":
            raise ValueError(
                f"{obj['name']}.{projection['logical_name']} uses unsupported BLOB storage"
            )
        field: dict[str, Any] = {
            "name": projection["logical_name"],
            "type": physical["type"],
            "required": bool(projection["sqlite_not_null"] or projection["sqlite_primary_key_ordinal"]),
        }
        if physical["type"] in {"C", "N"}:
            field["length"] = physical["width"]
        if physical["type"] == "N":
            field["decimals"] = physical["decimals"]
        fields.append(field)

    indexes = []
    for index in obj["indexes"]:
        order = [
            column["name"]
            for column in index["columns"]
            if int(column.get("key") or 0) == 1 and column.get("name")
        ]
        if order:
            indexes.append(
                {
                    "name": index["name"],
                    "engine": "CNX",
                    "order": order,
                    "unique": bool(index.get("unique")),
                }
            )

    relations = []
    grouped: dict[int, list[dict[str, Any]]] = {}
    for edge in obj["foreign_keys"]:
        grouped.setdefault(int(edge["id"]), []).append(edge)
    for relation_id, edges in sorted(grouped.items()):
        edges.sort(key=lambda edge: int(edge["seq"]))
        nullable = any(not bool(field_by_name[edge["from"]].get("notnull")) for edge in edges)
        relations.append(
            {
                "name": f"fk_{obj['name']}_{relation_id}",
                "parent_table": edges[0]["table"],
                "child_table": obj["name"],
                "cardinality": "N:1",
                "enforce": "SOFT",
                "nullable_fk": "ALLOW" if nullable else "DISALLOW",
                "cascade": {
                    "delete": edges[0]["on_delete"] if edges[0]["on_delete"] != "NO ACTION" else "NONE",
                    "update": edges[0]["on_update"] if edges[0]["on_update"] != "NO ACTION" else "NONE",
                },
                "on": [
                    {"parent": edge["to"], "child": edge["from"]}
                    for edge in edges
                ],
            }
        )

    return {
        "version": "1.0",
        "name": obj["x64base"]["physical_name"],
        "table": obj["x64base"]["physical_name"],
        "encoding": "UTF-8",
        "date_policy": "ISO",
        "null_policy": "EMPTY_AS_NULL",
        "logical_policy": "ZERO_ONE",
        "fields": fields,
        "indexes": indexes,
        "relations": relations,
        "x-cascade": {
            "sqlite_object": obj["name"],
            "sqlite_kind": obj["sqlite_kind"],
            "sqlite_sql": obj["sqlite_sql"],
            "constraint_enforcement": "sidecar_only_on_x64base",
        },
    }


def generate(sqlite_path: Path, output_dir: Path) -> dict[str, Any]:
    before_hash = sha256(sqlite_path)
    uri = sqlite_path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        schema_rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_schema "
            "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"
        ).fetchall()
        objects = [object_metadata(conn, name, kind, sql or "") for kind, name, sql in schema_rows]

        output_dir.mkdir(parents=True, exist_ok=True)
        views_dir = output_dir / "views"
        schemas_dir = output_dir / "schemas"
        for obj in objects:
            if obj["sqlite_kind"] == "view":
                export_view(conn, obj["name"], views_dir / f"{obj['name']}.csv")
            schemas_dir.mkdir(parents=True, exist_ok=True)
            (schemas_dir / f"{obj['name']}.schema.json").write_text(
                json.dumps(schema_document(obj), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    finally:
        conn.close()

    after_hash = sha256(sqlite_path)
    if before_hash != after_hash:
        raise RuntimeError("canonical SQLite carrier changed during read-only generation")

    tables = [obj for obj in objects if obj["sqlite_kind"] == "table"]
    views = [obj for obj in objects if obj["sqlite_kind"] == "view"]
    foreign_key_edges = sum(len(obj["foreign_keys"]) for obj in tables)
    contract = {
        "contract": "cascade_dual_carrier_schema_v1",
        "authority": {
            "sqlite_path": str(sqlite_path.resolve()),
            "sqlite_sha256_before": before_hash,
            "sqlite_sha256_after": after_hash,
            "sqlite_version": sqlite3.sqlite_version,
            "open_mode": "read_only",
        },
        "counts": {
            "tables": len(tables),
            "views": len(views),
            "rows_in_tables": sum(obj["row_count"] for obj in tables),
            "foreign_key_field_edges": foreign_key_edges,
            "x64base_physical_tables_planned": len(objects),
        },
        "parity_policy": {
            "tables": "one namespaced X64 DBF projection per SQLite table",
            "views": "one labeled materialized X64 DBF teaching snapshot per SQLite view",
            "x64base_physical_root": "dottalkpp/data/systems/cascade_erp/dbf",
            "constraints_defaults_indexes_and_view_sql": "preserved exactly in this sidecar; not claimed as native DBF enforcement",
            "data_build": "DDL CREATE DBF X64 from explicit schemas, then IMPORT sealed table CSVs and generated read-only view CSVs",
            "truth_rule": "complete logical mirror does not imply identical native database capabilities",
        },
        "objects": objects,
    }

    contract_path = output_dir / "dual_schema_contract.json"
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    dts_lines = [
        "* Generated by tools/cascade_erp/generate_dual_schema_contract.py",
        "* SQLite is authoritative; CASCADE_v_* DBFs are materialized teaching snapshots.",
        "* Explicit DDL prevents value inference from changing TEXT identifiers into numerics.",
        "SET TALK ON",
        "ECHO CASCADE MIRROR BEGIN",
    ]
    for obj in objects:
        source = (
            f"systems/cascade_erp/sqlite/data/{obj['name']}.csv"
            if obj["sqlite_kind"] == "table"
            else f"systems/cascade_erp/sqlite/x64base_mirror/views/{obj['name']}.csv"
        )
        target = obj["x64base"]["physical_name"]
        schema = f"systems/cascade_erp/sqlite/x64base_mirror/schemas/{obj['name']}.schema.json"
        output_dbf = (
            SYSTEM_ROOT / "dbf" / f"{target}.dbf"
        ).as_posix()
        dts_lines.extend(
            [
                f"ECHO CASCADE MIRROR BUILD {obj['sqlite_kind']} {obj['name']} AS {target} EXPECT_ROWS {obj['row_count']} EXPECT_FIELDS {len(obj['columns'])}",
                f"DDL VALIDATE {schema} USING schemas/schema_json_v1.schema.json",
                f"DDL CREATE DBF X64 {output_dbf} FROM {schema} OVERWRITE EMIT SIDECARS",
                f"USE {output_dbf}",
                f"IMPORT {source}",
                "COUNT",
                "FIELDS",
            ]
        )
    dts_lines.append("ECHO CASCADE MIRROR END")
    (output_dir / "build_x64base_mirror.dts").write_text("\n".join(dts_lines) + "\n", encoding="utf-8")

    report = [
        "# Cascade Dual-Carrier Schema Parity Report",
        "",
        "Status: explicit schema contract generated. Current physical runtime status, when available, is recorded in `runtime_status_latest.json`.",
        "",
        f"- SQLite tables: {len(tables)}",
        f"- SQLite views: {len(views)}",
        f"- SQLite table rows: {sum(obj['row_count'] for obj in tables)}",
        f"- SQLite foreign-key field edges: {foreign_key_edges}",
        f"- Planned x64base DBFs: {len(objects)} ({len(tables)} table mirrors + {len(views)} materialized view snapshots)",
        f"- Canonical carrier SHA-256 unchanged: {before_hash == after_hash}",
        "",
        "Relational constraints, defaults, indexes, and view SQL are complete in",
        "`dual_schema_contract.json`. They are sidecar semantics until an x64base",
        "runtime gate proves equivalent enforcement; DBF does not receive credit for",
        "SQLite features it cannot natively enforce.",
        "",
        "The earlier AUTODBF experiment was rejected for schema parity because value",
        "inference converted declared SQLite TEXT identifiers (including account codes",
        "and ZIP codes) to numeric fields and a NULL-only integer FK to character.",
        "",
        "Run `build_x64base_mirror.dts` through the current DotTalk++ runtime, preserve",
        "the transcript, and compare every emitted COUNT/FIELDS result before marking",
        "the physical mirror runtime-observed.",
    ]
    (output_dir / "PARITY_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    contract = generate(args.sqlite, args.output_dir)
    print(json.dumps(contract["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

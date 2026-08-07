from __future__ import annotations
import json
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session

# Map xbase-ish type letters to SQL column DDL (SQLite flavored, generic enough for others)
TYPE_MAP = {
    "C": "TEXT",
    "N": "INTEGER",  # NOTE: decimals>0 could be REAL; simple heuristic below
    "D": "TEXT",     # store YYYYMMDD as TEXT
    "L": "INTEGER"   # 0/1
}

def _column_sql(fld: Dict[str, Any]) -> str:
    t = fld.get("type", "C")
    name = fld["name"]
    if t == "N" and fld.get("decimals", 0) > 0:
        coltype = "REAL"
    else:
        coltype = TYPE_MAP.get(t, "TEXT")
    mods = []
    if fld.get("pk"): mods.append("PRIMARY KEY")
    if fld.get("unique"): mods.append("UNIQUE")
    if not fld.get("nullable", True): mods.append("NOT NULL")
    if "default" in fld:
        dv = fld["default"]
        if isinstance(dv, bool): dv = 1 if dv else 0
        mods.append(f"DEFAULT {json.dumps(dv)}")
    return f'"{name}" {coltype} {" ".join(mods)}'.strip()

def apply_schema(session: Session, schema: Dict[str, Any]) -> None:
    for tbl, spec in schema.get("tables", {}).items():
        fields = spec.get("fields", [])
        col_sql = ", ".join(_column_sql(f) for f in fields if f["name"] != "id")  # we'll create id separately to control PK
        has_id = any(f.get("pk") and f["name"]=="id" for f in fields)
        if has_id:
            create = f'CREATE TABLE IF NOT EXISTS "{tbl}" ("id" INTEGER PRIMARY KEY AUTOINCREMENT, {col_sql})'
        else:
            create = f'CREATE TABLE IF NOT EXISTS "{tbl}" ({col_sql})'
        session.execute(text(create))
        # uniques
        if spec.get("unique"):
            uq_cols = spec["unique"]
            for cols in uq_cols:
                uqname = f'uq_{"_".join(cols)}'
                try:
                    session.execute(text(f'CREATE UNIQUE INDEX "{uqname}" ON "{tbl}" ({", ".join(cols)})'))
                except Exception:
                    pass
    session.commit()

def import_fixtures(session: Session, fixtures: Dict[str, List[Dict[str, Any]]]) -> None:
    for tbl, rows in fixtures.items():
        if not rows: continue
        cols = sorted(set().union(*[r.keys() for r in rows]))
        qmarks = ", ".join(f":{c}" for c in cols)
        collist = ", ".join(f'"{c}"' for c in cols)
        ins = text(f'INSERT OR REPLACE INTO "{tbl}" ({collist}) VALUES ({qmarks})')
        for r in rows:
            cooked = {k: (1 if isinstance(v, bool) and v else 0 if isinstance(v, bool) else v) for k,v in r.items()}
            session.execute(ins, cooked)
    session.commit()

def export_table(session: Session, table: str) -> list[dict]:
    res = session.execute(text(f'SELECT * FROM "{table}"')).mappings().all()
    return [dict(r) for r in res]

# ---------- Extended exports with XBase-like metadata ----------
def _today_ymd() -> str:
    import datetime as _dt
    d = _dt.date.today()
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"

def _estimate_cpr_from_schema(table: str, schema: dict | None) -> int | None:
    """Estimate characters-per-record (cpr) using XBase-style field lengths if schema is provided."""
    if not schema or "tables" not in schema: 
        return None
    spec = schema["tables"].get(table)
    if not spec: 
        return None
    total = 1  # deletion flag
    for f in spec.get("fields", []):
        total += int(f.get("length", 0))
    return total

def export_table_with_meta(session: Session, table: str, 
                           schema: dict | None = None, 
                           settings: dict | None = None,
                           dottalk_client=None,
                           prefer_backend_header: bool = False) -> dict:
    """Export rows + schema + header-like metadata (version, last_updated, cpr) + settings.deleted_on."""
    rows = export_table(session, table)
    # Derive "fields" from schema if available; otherwise, infer from first row
    if schema and "tables" in schema and table in schema["tables"]:
        fields = schema["tables"][table].get("fields", [])
    else:
        fields = [{"name": k, "type": "C", "length": 0, "decimals": 0} for k in (rows[0].keys() if rows else [])]
    cpr = _estimate_cpr_from_schema(table, schema)
    # default header (local estimate)
    header = {
        "version": 3,
        "last_updated": _today_ymd(),
        "num_of_recs": len(rows),
        "cpr": cpr,
    }

    # optionally fetch authoritative DBF header from backend
    if prefer_backend_header and dottalk_client is not None and getattr(dottalk_client, "is_configured")():
        try:
            hdr = dottalk_client.get_header(table)
            if isinstance(hdr, dict) and all(k in hdr for k in ("version","last_updated","num_of_recs","cpr")):
                header = hdr
        except Exception:
            pass
    out = {
        "dialect": "xbase-ish-json",
        "table": table,
        "header": header,
        "fields": fields,
        "settings": {
            "deleted_on": bool(settings.get("deleted_on", True)) if settings else True
        },
        "rows": rows,
    }
    return out

def export_database_with_meta(session: Session, 
                              schema: dict | None = None, 
                              settings: dict | None = None) -> dict:
    """Export all tables listed in 'schema' or all visible tables in DB with per-table packets plus a catalog."""
    # Determine tables
    tables = []
    if schema and "tables" in schema:
        tables = list(schema["tables"].keys())
    else:
        # Try to introspect SQLite / generic: use sqlite_master if available; otherwise, fall back to standard tables
        try:
            res = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
            tables = [r[0] for r in res.fetchall()]
        except Exception:
            pass
    catalog = {}
    payload = {}
    for t in tables:
        packet = export_table_with_meta(session, t, schema=schema, settings=settings)
        payload[t] = packet
        catalog[t] = {
            "rows": len(packet["rows"]),
            "cpr": packet["header"]["cpr"],
        }
    return {
        "dialect": "xbase-ish-json",
        "exported": _today_ymd(),
        "catalog": catalog,
        "tables": payload,
        "settings": {
            "deleted_on": bool(settings.get("deleted_on", True)) if settings else True
        }
    }


def fetch_backend_schema_and_fixtures(client, fallback_schema: dict | None = None, fallback_fixtures: dict | None = None):
    """Best-effort: get schema/fixtures from backend; fall back to provided locals."""
    schema = client.get_schema() if client and client.is_configured() else None
    if schema is None:
        schema = fallback_schema
    fixtures = client.get_fixtures() if client and client.is_configured() else None
    if fixtures is None:
        fixtures = fallback_fixtures
    return schema, fixtures

from __future__ import annotations
import json, datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

def sql_ident(name: str) -> str:
    if not name or not name.replace("_", "").isalnum() or name[0].isdigit():
        raise ValueError(f"invalid SQL identifier: {name!r}")
    return f'"{name}"'

def today_ymd() -> str:
    d = datetime.date.today()
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"

def estimate_cpr(table: str, schema: dict | None) -> int | None:
    if not schema or "tables" not in schema: return None
    spec = schema["tables"].get(table)
    if not spec: return None
    total = 1  # deletion flag byte
    for f in spec.get("fields", []):
        total += int(f.get("length", 0))
    return total

def header_for_table(session: Session, table: str, schema: dict | None) -> dict:
    # count rows
    try:
        n = session.execute(text(f"SELECT COUNT(*) FROM {sql_ident(table)}")).scalar_one()
    except Exception:
        n = 0
    return {
        "version": 3,
        "last_updated": today_ymd(),
        "num_of_recs": int(n),
        "cpr": estimate_cpr(table, schema)
    }

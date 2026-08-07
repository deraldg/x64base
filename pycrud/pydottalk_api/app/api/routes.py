from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query, Body, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict
from app.core.config import SCHEMA_PATH, FIXTURES_PATH

router = APIRouter()

def sql_ident(name: str) -> str:
    if not name or not name.replace("_", "").isalnum() or name[0].isdigit():
        raise HTTPException(400, f"invalid SQL identifier: {name!r}")
    return f'"{name}"'

def require_columns(data: Dict[str, Any]) -> None:
    if not data:
        raise HTTPException(400, "data must include at least one column")
    for name in data:
        sql_ident(name)

# Pydantic models
class ReplaceModel(BaseModel):
    table: str
    id: int
    data: Dict[str, Any]

class AppendModel(BaseModel):
    table: str
    data: Dict[str, Any]

def session_dep(request: Request) -> Session:
    return request.state.db

# Sessions are logical here; we use a single shared factory from main
def get_schema_dict(path: str) -> dict | None:
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def get_fixtures_dict(path: str) -> dict | None:
    try:
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

@router.get("/status")
def status():
    return {"ok": True}

@router.get("/xbase/schema")
def xbase_schema(schema_path: str | None = Query(default=None)):
    s = get_schema_dict(schema_path or SCHEMA_PATH)
    if s is None:
        raise HTTPException(404, "schema not found")
    return s

@router.get("/xbase/fixtures")
def xbase_fixtures(fixtures_path: str | None = Query(default=None)):
    f = get_fixtures_dict(fixtures_path or FIXTURES_PATH)
    if f is None:
        raise HTTPException(404, "fixtures not found")
    return f

@router.get("/xbase/header")
def xbase_header(
    table: str,
    schema_path: str | None = Query(default=None),
    session: Session = Depends(session_dep),
):
    from app.utils.xbase_meta import header_for_table
    s = get_schema_dict(schema_path or SCHEMA_PATH)
    return header_for_table(session, table, s)

@router.post("/session/open")
def session_open():
    # Logical session id stub
    return {"session_id": "local-sqlite"}

@router.post("/session/close")
def session_close(session_id: str = Body(..., embed=True)):
    return {"closed": session_id}

@router.get("/list")
def list_rows(table: str, limit: int = 100, order: str = "id", session: Session = Depends(session_dep)):
    table_sql = sql_ident(table)
    order_sql = sql_ident(order)
    try:
        rows = session.execute(text(f"SELECT * FROM {table_sql} ORDER BY {order_sql} LIMIT :lim"), {"lim": limit}).mappings().all()
        return {"rows": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/display")
def display_row(table: str, id: int, session: Session = Depends(session_dep)):
    table_sql = sql_ident(table)
    try:
        r = session.execute(text(f"SELECT * FROM {table_sql} WHERE id=:id"), {"id": id}).mappings().first()
        if not r:
            raise HTTPException(404, "not found")
        return {"row": dict(r)}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/seek")
def seek_rows(table: str, field: str, value: str, limit: int = 50, session: Session = Depends(session_dep)):
    table_sql = sql_ident(table)
    field_sql = sql_ident(field)
    try:
        sql = text(f"SELECT * FROM {table_sql} WHERE {field_sql} = :v LIMIT :lim")
        rows = session.execute(sql, {"v": value, "lim": limit}).mappings().all()
        return {"rows": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/replace")
def replace_row(payload: ReplaceModel, session: Session = Depends(session_dep)):
    table_sql = sql_ident(payload.table)
    require_columns(payload.data)
    sets = ", ".join([f"{sql_ident(k)}=:{k}" for k in payload.data.keys()])
    params = dict(payload.data); params["id"] = payload.id
    try:
        session.execute(text(f"UPDATE {table_sql} SET {sets} WHERE id=:id"), params)
        session.commit()
        return {"ok": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(400, str(e))

@router.post("/append")
def append_row(payload: AppendModel, session: Session = Depends(session_dep)):
    table_sql = sql_ident(payload.table)
    require_columns(payload.data)
    cols = ", ".join([sql_ident(k) for k in payload.data.keys()])
    vals = ", ".join([f':{k}' for k in payload.data.keys()])
    try:
        session.execute(text(f"INSERT INTO {table_sql} ({cols}) VALUES ({vals})"), payload.data)
        session.commit()
        rowid = session.execute(text("SELECT last_insert_rowid()")).scalar_one()
        return {"ok": True, "id": int(rowid)}
    except Exception as e:
        session.rollback()
        raise HTTPException(400, str(e))

@router.post("/delete")
def delete_row(table: str = Body(...), id: int = Body(...), session: Session = Depends(session_dep)):
    table_sql = sql_ident(table)
    try:
        session.execute(text(f"DELETE FROM {table_sql} WHERE id=:id"), {"id": id})
        session.commit()
        return {"ok": True}
    except Exception as e:
        session.rollback()
        raise HTTPException(400, str(e))

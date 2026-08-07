# pydottalk_api -- Minimal FastAPI backend for DotTalk++ & pycrud

A lightweight REST API that fronts your local SQLite (or any SQLAlchemy URL)
and exposes XBase-flavored endpoints used by **pycrud** plus generic CRUD routes
for the future Java/Spring UI.

## Endpoints

- `GET  /status` -> `{"ok": true}`
- `GET  /xbase/schema` -> loads `../pycrud/data/xbase_schema.json` if present
- `GET  /xbase/fixtures` -> loads `../pycrud/data/xbase_fixtures.json` if present
- `GET  /xbase/header?table=students` -> estimates DBF-style header from schema+rowcount
- `POST /session/open` -> returns a session id (logical; not required by sqlite)
- `POST /session/close`
- `GET  /list?table=students&limit=50&order=id` -> rows
- `GET  /display?table=students&id=1` -> one row
- `GET  /seek?table=students&field=last_name&value=Grimwood` -> matching rows
- `POST /replace` `{table, id, data}` -> upsert-like replace of fields
- `POST /append` `{table, data}` -> add row
- `POST /delete` `{table, id}` -> delete row

> Backing store is configured via env `DB_URL` (default: sqlite:///../pycrud/data/demo.sqlite).

Dynamic table and column names are accepted only as simple SQL identifiers:
letters, numbers, and underscores, with a non-numeric first character. Values
are bound parameters. This keeps the API flexible for pycrud while avoiding raw
identifier injection in generated SQL.

## Quick start

```pwsh
cd ccode/pycrud/pydottalk_api
.\setup.ps1         # create .venv and install deps
.\run.ps1           # uvicorn app.main:app --reload
```

Then set **pycrud** (DotTalk++ -> Settings) to: `http://127.0.0.1:8000`

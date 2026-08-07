# pycrud -- Simple Python CRUD Interface (DotTalk++ Companion)

A small, VS Code--ready GUI to view and edit relational data across SQLite/MySQL/SQL Server.
Designed as an **independent project living inside `ccode/`** with a **future hook to DotTalk++**.

## Highlights
- DB-agnostic via SQLAlchemy (SQLite by default; MySQL & SQL Server optional).
- Sample schema **Teachers / Students / Courses / Enrollments** with seed data.
- GUI (Tkinter) with **menu bar**, **auto-sized grids/forms**, and a **SQL console**.
- Open/preview **.txt / .csv**; import CSV as a new table.
- **Formulas**: compute a new column for a table from an expression (safe AST).
- **Relational ops** (join/project/select) powered by SQL or pandas.
- **Hook stub** for later DotTalk++ integration (`hook/dottalkpp_hook.py`).

## Quick Start (Windows / VS Code)
1. Open VS Code at `ccode/pycrud`.
2. Run the *Tasks* menu: **Setup venv & Install** (creates `.venv`).
3. Press **F5** to launch the app (configured in `.vscode/launch.json`).

> Default DB is `data/demo.sqlite`. You can switch to other engines from **File -> Connect...**.

## Optional Drivers
- MySQL: `pip install pymysql`
- SQL Server: `pip install pyodbc` (and install ODBC Driver 18+ for SQL Server)

## Connection URLs (SQLAlchemy)
- SQLite file: `sqlite:///data/demo.sqlite`
- MySQL: `mysql+pymysql://user:pass@localhost:3306/school`
- SQL Server (ODBC): `mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=school;Trusted_Connection=yes;TrustServerCertificate=yes`

## Project Layout
```
pycrud/
  main.py
  db/
    engine.py        # engine/session & connect dialog
    models.py        # ORM models (Teacher/Student/Course/Enrollment)
    sample_data.py   # seed demo data
  ui/
    app.py           # main window, menus, list + form views
    help_text.md     # in-app help
  utils/
    formulas.py      # safe expression evaluator
    relational.py    # join/project/select helpers
  hook/
    dottalkpp_hook.py  # future DotTalk++ FastAPI hook (stub now)
  sql/
    schema_sqlite.sql
    schema_mysql.sql
    schema_mssql.sql
  data/
    demo.sqlite      # created on first run if missing
  .vscode/
    launch.json
    tasks.json
  requirements.txt
  setup.ps1
```

## DotTalk++ Hook (stub)
Configure later via **DotTalk++ -> Settings...**. The hook is shaped around your
FastAPI contract (session/list/display/seek/replace/etc.).



## JSON (XBase-style)
- `data/xbase_schema.json` defines field names/types/lengths/decimals like XBase.
- `data/xbase_fixtures.json` holds starter rows. Use File -> Import from JSON... to apply.
- Use File -> Export current table to JSON... to dump a table.


### XBase-style Meta Exports
- **Export current table to XBase JSON (with meta)...** includes header-like fields (`version`, `last_updated`, `num_of_recs`, `cpr`) and `settings.deleted_on`.
- **Export ALL tables to XBase JSON package...** emits a multi-table catalog with per-table packets.
- Defaults use `data/xbase_schema.json` to estimate CPR and `data/xbase_settings.json` for `deleted_on`.


### DotTalk++ Backend Integration (alpha)
- **Settings**: DotTalk++ -> Settings lets you set the backend URL and prefer backend header metadata.
- **Fetch schema & fixtures**: pulls from `/xbase/schema` and `/xbase/fixtures` if available, saves/imports locally.
- **Exports**: when preference is ON and backend is reachable, header metadata is fetched from `/xbase/header?table=...`.

## Local Assessment

Assessment date: 2026-07-06.

Classification: independent application with a DotTalk++ integration path.

This project is not part of the DotTalk++ runtime. It is a separate Python GUI
application for database browsing, editing, SQL experimentation, relational
operations, and JSON interchange. The DotTalk++ relationship is intentionally a
hook: pycrud can run on its own against `sqlite:///data/demo.sqlite`, MySQL, or
SQL Server through SQLAlchemy, and it can optionally talk to a future local
DotTalk++/pydottalk backend through HTTP.

What it can do now:

- Launch a Tkinter desktop CRUD app from `main.py`.
- Create and seed a small school schema: teachers, students, courses, and
  enrollments.
- Connect to SQLAlchemy database URLs, with SQLite as the default.
- View, create, edit, and delete rows through forms.
- Open text/CSV files and import CSV files as new SQL tables.
- Run ad hoc SQL in a built-in SQL console.
- Compute a new column from a restricted safe expression evaluator.
- Run simple relational join, project, and select operations using pandas.
- Import schema/fixture JSON and export plain JSON.
- Export XBase-flavored JSON packets with header, field, settings, and row
  metadata.
- Store XBase-ish schema/settings/fixtures in `data/*.json`.
- Optionally ping/fetch schema and fixtures from a backend URL stored in
  `DOT_TALK_URL` or set through the UI.

Intended role:

pycrud appears to have been intended as a teaching and prototyping surface for
relational CRUD concepts that could later bridge to DotTalk++/xBase structures.
It gives a conventional SQL/GUI workflow first, then adds XBase JSON metadata
and a backend hook so the same tables can be compared with or exported toward
DotTalk++ concepts.

Backend contract:

The nested `pydottalk_api` folder is a local FastAPI backend for pycrud and
DotTalk++ experiments. It defaults to `pycrud/data/demo.sqlite` plus the local
XBase schema/fixture JSON files. CRUD routes accept dynamic table and column
names, but only simple identifiers are allowed: letters, numbers, and
underscores, with a non-numeric first character. Use `run-pycrud.ps1` from the
repo root to launch the API and GUI together.

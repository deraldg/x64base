from __future__ import annotations
import os
import csv
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from sqlalchemy import select, text, inspect
from sqlalchemy.orm import Session

from db.engine import EngineBundle, DEFAULT_URL, connect_dialog
from db.models import Base, Teacher, Student, Course, Enrollment
from utils.formulas import eval_expr
from utils import relational as rel
from utils.xbase_json import (
    apply_schema, import_fixtures, export_table,
    export_table_with_meta, export_database_with_meta,
    fetch_backend_schema_and_fixtures
)
from hook.dottalkpp_hook import DotTalkClient

PYCRUD_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PYCRUD_ROOT.parent
TOOLS_ROOT = REPO_ROOT / "tools"
if TOOLS_ROOT.exists() and str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
try:
    from version_info import title_with_version
except Exception:  # pragma: no cover - startup fallback
    def title_with_version(name: str, root: Path | None = None, fallback_version: str = "0.6") -> str:
        return name

TABLES = {
    "teachers": Teacher,
    "students": Student,
    "courses": Course,
    "enrollments": Enrollment,
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._base_title = title_with_version("pycrud - DotTalk++ Companion", REPO_ROOT)
        self.title(self._base_title)
        self.geometry("1000x600")
        self.minsize(800, 480)

        # State
        self.bundle = EngineBundle(DEFAULT_URL)
        self.bundle.create_all_and_seed()
        self.session: Session = self.bundle.session()
        self.current_table = "students"
        self.dottalk = DotTalkClient()
        self._prefer_backend_header = True  # default

        # Menus
        self._build_menus()

        # Toolbar
        bar = tk.Frame(self, bd=1, relief="groove")
        bar.pack(side="top", fill="x")
        tk.Button(bar, text="New", command=self.on_new).pack(side="left", padx=4, pady=2)
        tk.Button(bar, text="Edit", command=self.on_edit).pack(side="left", padx=4, pady=2)
        tk.Button(bar, text="Delete", command=self.on_delete).pack(side="left", padx=4, pady=2)
        tk.Button(bar, text="SQL Console", command=self.open_sql_console).pack(side="left", padx=4, pady=2)

        # Grid
        self.tree = ttk.Treeview(self, show="headings")
        self.tree.pack(side="top", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.on_edit())

        # Status bar
        self.status = tk.StringVar(value=f"Connected: {self.bundle.url}")
        sb = tk.Label(self, textvariable=self.status, anchor="w", bd=1, relief="sunken")
        sb.pack(side="bottom", fill="x")

        # Basic style + fonts
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self._dark_mode = False
        default_font = ("Segoe UI", 10)
        self.option_add("*Font", default_font)

        # Track child windows for easy closing
        self._child_windows = []

        self.refresh()

    def _window_title(self, title: str) -> str:
        return f"{title} - {self._base_title}"

    # ---------------- Menus ----------------
    def _build_menus(self):
        m = tk.Menu(self)
        self.config(menu=m)

        m_file = tk.Menu(m, tearoff=False)
        m.add_cascade(label="File", menu=m_file)
        m_file.add_command(label="Connect…", command=self.on_connect)
        m_file.add_separator()
        m_file.add_command(label="Open Text/CSV…", command=self.open_text_csv)
        m_file.add_command(label="Import from JSON…", command=self.import_from_json)
        m_file.add_command(label="Export current table to JSON…", command=self.export_current_table_json)
        m_file.add_command(label="Export current table to XBase JSON (with meta)…", command=self.export_current_table_with_meta)
        m_file.add_command(label="Export ALL tables to XBase JSON package…", command=self.export_all_tables_with_meta)
        m_file.add_separator()
        m_file.add_command(label="Close Child Windows", command=self.close_children)
        m_file.add_separator()
        m_file.add_command(label="Exit", command=self.destroy)

        m_view = tk.Menu(m, tearoff=False)
        m.add_cascade(label="View", menu=m_view)
        for name in ("teachers","students","courses","enrollments"):
            m_view.add_radiobutton(label=name, command=lambda n=name: self.set_table(n))
        m_view.add_separator()
        size_menu = tk.Menu(m_view, tearoff=False)
        size_menu.add_command(label="Windowed", command=self.set_windowed)
        size_menu.add_command(label="Fullscreen", command=self.set_fullscreen)
        m_view.add_cascade(label="Window Size", menu=size_menu)
        m_view.add_checkbutton(label="Dark Mode", command=self.toggle_dark)

        m_edit = tk.Menu(m, tearoff=False)
        m.add_cascade(label="Edit", menu=m_edit)
        m_edit.add_command(label="New", command=self.on_new, accelerator="Enter")
        m_edit.add_command(label="Edit", command=self.on_edit)
        m_edit.add_command(label="Delete", command=self.on_delete)

        m_tools = tk.Menu(m, tearoff=False)
        m.add_cascade(label="Tools", menu=m_tools)
        m_tools.add_command(label="SQL Console", command=self.open_sql_console)
        m_tools.add_command(label="Compute Column…", command=self.compute_column_dialog)

        m_rel = tk.Menu(m, tearoff=False)
        m.add_cascade(label="Relational", menu=m_rel)
        m_rel.add_command(label="Join…", command=self.join_dialog)
        m_rel.add_command(label="Project…", command=self.project_dialog)
        m_rel.add_command(label="Select…", command=self.select_dialog)

        m_dt = tk.Menu(m, tearoff=False)
        m.add_cascade(label="DotTalk++", menu=m_dt)
        m_dt.add_command(label="Settings…", command=self.dottalk_settings)
        m_dt.add_command(label="Ping", command=self.dottalk_ping)
        m_dt.add_command(label="Fetch schema & fixtures from backend", command=self.fetch_schema_fixtures_backend)

        m_help = tk.Menu(m, tearoff=False)
        m.add_cascade(label="Help", menu=m_help)
        m_help.add_command(label="About", command=self.show_help)

    # ---------------- Actions ----------------
    def set_table(self, name: str):
        self.current_table = name
        self.refresh()

    def refresh(self):
        Model = TABLES[self.current_table]
        insp = inspect(Model)
        cols = [c.key for c in insp.columns]
        rows = self.session.execute(select(Model)).scalars().all()
        values = [[getattr(r, c) for c in cols] for r in rows]
        # Rebuild columns
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=self._measure_col_width(c, [str(getattr(r, c)) for r in rows]))
        for row in values:
            self.tree.insert("", "end", values=row)

        self.status.set(f"Connected: {self.bundle.url} | Table: {self.current_table} | {len(values)} rows")

    def _measure_col_width(self, header: str, samples, min_w=60, max_w=320):
        try:
            lengths = [len(s) for s in samples if s is not None]
            avg = sum(lengths) / max(1, len(lengths))
        except Exception:
            avg = len(header)
        w = int(max(len(header) * 9, avg * 9)) + 24
        return max(min_w, min(max_w, w))

    def _selected_row_pk(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0])["values"]
        return int(vals[0])  # assume first col is PK id

    def on_new(self):
        self._open_form(mode="new")

    def on_edit(self):
        pk = self._selected_row_pk()
        if pk is None:
            messagebox.showinfo("Edit", "Select a row first.")
            return
        self._open_form(mode="edit", pk=pk)

    def on_delete(self):
        pk = self._selected_row_pk()
        if pk is None:
            messagebox.showinfo("Delete", "Select a row first.")
            return
        Model = TABLES[self.current_table]
        obj = self.session.get(Model, pk)
        if not obj:
            return
        if messagebox.askyesno("Confirm", f"Delete {Model.__name__} #{pk}?"):
            self.session.delete(obj)
            self.session.commit()
            self.refresh()

    def _open_form(self, mode: str, pk: int | None = None):
        Model = TABLES[self.current_table]
        insp = inspect(Model)
        cols = [c for c in insp.columns]

        dlg = tk.Toplevel(self)
        dlg.title(self._window_title(f"{mode.title()} {Model.__name__}"))
        dlg.grab_set()
        self._register_child(dlg)

        entries = {}
        row = 0
        obj = None
        if mode == "edit":
            obj = self.session.get(Model, pk)
        for c in cols:
            if c.primary_key and mode == "new":
                continue
            tk.Label(dlg, text=c.key).grid(row=row, column=0, sticky="e", padx=6, pady=4)
            var = tk.StringVar()
            if obj is not None:
                val = getattr(obj, c.key)
                var.set("" if val is None else str(val))
            ent = tk.Entry(dlg, textvariable=var, width=40)
            ent.grid(row=row, column=1, sticky="we", padx=6, pady=4)
            entries[c.key] = (c, var)
            row += 1

        dlg.columnconfigure(1, weight=1)
        btns = tk.Frame(dlg)
        btns.grid(row=row, column=0, columnspan=2, pady=8)

        def save():
            nonlocal obj
            if obj is None:
                obj = Model()
            for name, (col, var) in entries.items():
                if col.primary_key:
                    continue
                raw = var.get().strip()
                if raw == "":
                    setattr(obj, name, None)
                else:
                    python_t = getattr(col.type, "python_type", str)
                    try:
                        if python_t is bool:
                            val = raw.lower() in ("1","t","true","y","yes")
                        else:
                            val = python_t(raw)
                    except Exception:
                        val = raw
                    setattr(obj, name, val)
            self.session.add(obj)
            self.session.commit()
            dlg.destroy()
            self.refresh()

        tk.Button(btns, text="Save", command=save).pack(side="left", padx=5)
        tk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=5)

    def on_connect(self):
        new_url = connect_dialog(self, self.bundle.url)
        if not new_url:
            return
        try:
            self.session.close()
        except Exception:
            pass
        self.bundle = EngineBundle(new_url)
        self.bundle.create_all_and_seed()
        self.session = self.bundle.session()
        self.status.set(f"Connected: {self.bundle.url}")
        self.refresh()

    def open_text_csv(self):
        path = filedialog.askopenfilename(title="Open Text/CSV", filetypes=[("Text/CSV", "*.txt *.csv"), ("All", "*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read(200_000)
        win = tk.Toplevel(self)
        win.title(self._window_title(os.path.basename(path)))
        win.geometry("800x600")
        self._register_child(win)

        txtw = tk.Text(win, wrap="none")
        txtw.insert("1.0", data)
        txtw.pack(fill="both", expand=True)
        if path.lower().endswith(".csv"):
            def import_csv():
                self._import_csv_to_table(path)
            tk.Button(win, text="Import as new table…", command=import_csv).pack(side="bottom")

    def _import_csv_to_table(self, path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            messagebox.showerror("CSV", "No data found.")
            return
        headers = [h.strip() or f"col{i+1}" for i, h in enumerate(rows[0])]
        tbl = os.path.splitext(os.path.basename(path))[0]
        # Create table
        cols_sql = ", ".join(f'"{h}" TEXT' for h in headers)
        self.session.execute(text(f'CREATE TABLE IF NOT EXISTS "{tbl}" (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols_sql})'))
        col_names = ", ".join([f'"{h}"' for h in headers])
        placeholders = ", ".join([f":{h}" for h in headers])
        ins_sql = text(f'INSERT INTO "{tbl}" ({col_names}) VALUES ({placeholders})')
        for r in rows[1:]:
            rec = {headers[i]: r[i] if i < len(r) else None for i in range(len(headers))}
            self.session.execute(ins_sql, rec)
        self.session.commit()
        messagebox.showinfo("CSV", f"Imported {len(rows)-1} rows into '{tbl}'.")

    # ---- SQL Console ----
    def open_sql_console(self):
        win = tk.Toplevel(self)
        win.title(self._window_title("SQL Console"))
        win.geometry("900x600")
        self._register_child(win)

        txtw = tk.Text(win, wrap="word")
        txtw.pack(fill="both", expand=True)
        out = ttk.Treeview(win, show="headings")
        out.pack(fill="both", expand=True)
        btn = tk.Frame(win)
        btn.pack(fill="x")

        def run():
            q = txtw.get("1.0", "end").strip()
            if not q:
                return
            try:
                res = self.session.execute(text(q))
                if res.returns_rows:
                    rows = res.fetchall()
                    cols = res.keys()
                    out.delete(*out.get_children())
                    out["columns"] = cols
                    for c in cols:
                        out.heading(c, text=c)
                        out.column(c, width=120)
                    for row in rows:
                        out.insert("", "end", values=list(row))
                else:
                    self.session.commit()
                    messagebox.showinfo("SQL", f"{res.rowcount} row(s) affected.")
            except Exception as e:
                messagebox.showerror("SQL Error", str(e))

        tk.Button(btn, text="Run (Ctrl+Enter)", command=run).pack(side="left", padx=6, pady=4)
        txtw.bind("<Control-Return>", lambda e: (run(), "break"))

    # ---- Formulas ----
    def compute_column_dialog(self):
        Model = TABLES[self.current_table]
        tbl = Model.__tablename__
        dlg = tk.Toplevel(self)
        dlg.title(self._window_title("Compute Column..."))
        dlg.grab_set()
        self._register_child(dlg)

        tk.Label(dlg, text=f"Table: {tbl}").pack(anchor="w", padx=8, pady=4)
        tk.Label(dlg, text="New column name:").pack(anchor="w", padx=8)
        name_var = tk.StringVar()
        tk.Entry(dlg, textvariable=name_var).pack(fill="x", padx=8)
        tk.Label(dlg, text="Expression (use column names, e.g., len(last_name)+gpa):").pack(anchor="w", padx=8, pady=4)
        expr = tk.Text(dlg, height=5)
        expr.pack(fill="both", expand=True, padx=8, pady=4)

        def run():
            colname = name_var.get().strip()
            if not colname:
                messagebox.showerror("Compute", "Provide a column name.")
                return
            e = expr.get("1.0", "end").strip()
            if not e:
                messagebox.showerror("Compute", "Provide an expression.")
                return
            try:
                self.session.execute(text(f'ALTER TABLE {tbl} ADD COLUMN "{colname}" TEXT'))
            except Exception as ex:
                if "duplicate" not in str(ex).lower():
                    messagebox.showerror("Compute", str(ex))
                    return
            rows = self.session.execute(text(f"SELECT * FROM {tbl}")).mappings().all()
            for r in rows:
                val = eval_expr(e, dict(r))
                self.session.execute(text(f'UPDATE {tbl} SET "{colname}" = :v WHERE id = :id'), {"v": str(val), "id": r["id"]})
            self.session.commit()
            dlg.destroy()
            self.refresh()

        tk.Button(dlg, text="Compute", command=run).pack(pady=6)

    # ---- Relational ----
    def join_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title(self._window_title("Join..."))
        dlg.grab_set()
        self._register_child(dlg)

        tk.Label(dlg, text="Left table:").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        tk.Label(dlg, text="Right table:").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        tk.Label(dlg, text="Left key:").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        tk.Label(dlg, text="Right key:").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        left = tk.StringVar(value="students")
        right = tk.StringVar(value="enrollments")
        left_key = tk.StringVar(value="id")
        right_key = tk.StringVar(value="student_id")
        how = tk.StringVar(value="inner")

        tables = list(TABLES.keys())
        ttk.Combobox(dlg, textvariable=left, values=tables, state="readonly").grid(row=0, column=1, sticky="we", padx=6, pady=4)
        ttk.Combobox(dlg, textvariable=right, values=tables, state="readonly").grid(row=1, column=1, sticky="we", padx=6, pady=4)
        tk.Entry(dlg, textvariable=left_key).grid(row=2, column=1, sticky="we", padx=6, pady=4)
        tk.Entry(dlg, textvariable=right_key).grid(row=3, column=1, sticky="we", padx=6, pady=4)
        ttk.Combobox(dlg, textvariable=how, values=["inner", "left", "right", "outer"], state="readonly").grid(row=4, column=1, sticky="we", padx=6, pady=4)
        dlg.columnconfigure(1, weight=1)

        def run():
            df = rel.join(self.session, left.get(), right.get(), left_key.get(), right_key.get(), how=how.get())
            self._show_df(df, title=f"{how.get()} join {left.get()} ⋈ {right.get()}")
            dlg.destroy()

        tk.Button(dlg, text="Run", command=run).grid(row=5, column=0, columnspan=2, pady=8)

    def project_dialog(self):
        Model = TABLES[self.current_table]
        cols = [c.key for c in inspect(Model).columns]
        dlg = tk.Toplevel(self)
        dlg.title(self._window_title("Project..."))
        dlg.grab_set()
        self._register_child(dlg)

        tk.Label(dlg, text=f"Columns (comma-separated, available: {', '.join(cols)})").pack(anchor="w", padx=8, pady=4)
        var = tk.StringVar(value=", ".join(cols[:3]))
        tk.Entry(dlg, textvariable=var).pack(fill="x", padx=8, pady=4)

        def run():
            df = rel.read_table_df(self.session, Model.__tablename__)
            sel = [c.strip() for c in var.get().split(",") if c.strip()]
            self._show_df(rel.project(df, sel), title=f"project {Model.__tablename__}[{', '.join(sel)}]")
            dlg.destroy()

        tk.Button(dlg, text="Run", command=run).pack(pady=6)

    def select_dialog(self):
        Model = TABLES[self.current_table]
        dlg = tk.Toplevel(self)
        dlg.title(self._window_title("Select..."))
        dlg.grab_set()
        self._register_child(dlg)

        tk.Label(dlg, text="pandas/SQL-ish filter (e.g., gpa >= 3.5 and active == 1)").pack(anchor="w", padx=8, pady=4)
        var = tk.StringVar(value="gpa >= 3.5")
        tk.Entry(dlg, textvariable=var).pack(fill="x", padx=8, pady=4)

        def run():
            df = rel.read_table_df(self.session, Model.__tablename__)
            self._show_df(rel.select(df, var.get()), title=f"select {Model.__tablename__} WHERE {var.get()}")
            dlg.destroy()

        tk.Button(dlg, text="Run", command=run).pack(pady=6)

    def _show_df(self, df, title="Result"):
        win = tk.Toplevel(self)
        win.title(self._window_title(title))
        win.geometry("900x500")
        self._register_child(win)

        tv = ttk.Treeview(win, show="headings")
        tv.pack(fill="both", expand=True)
        cols = list(df.columns)
        tv["columns"] = cols
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=120)
        for _, row in df.iterrows():
            tv.insert("", "end", values=[row[c] for c in cols])

    # ---- DotTalk++ ----
    def dottalk_settings(self):
        cur = self.dottalk.base_url or ""
        dlg = tk.Toplevel(self)
        dlg.title(self._window_title("DotTalk++ Settings"))
        dlg.grab_set()
        self._register_child(dlg)

        tk.Label(dlg, text="Backend base URL:").grid(row=0, column=0, sticky="e", padx=8, pady=6)
        url_var = tk.StringVar(value=cur)
        tk.Entry(dlg, textvariable=url_var, width=60).grid(row=0, column=1, sticky="we", padx=8, pady=6)

        pref_var = tk.BooleanVar(value=getattr(self, "_prefer_backend_header", True))
        tk.Checkbutton(dlg, text="Prefer backend header metadata in exports", variable=pref_var).grid(row=1, column=1, sticky="w", padx=8)
        dlg.columnconfigure(1, weight=1)

        def ok():
            os.environ["DOT_TALK_URL"] = url_var.get().strip()
            self.dottalk = DotTalkClient(url_var.get().strip())
            self._prefer_backend_header = bool(pref_var.get())
            dlg.destroy()
            messagebox.showinfo("DotTalk++", "Settings saved.")

        def cancel():
            dlg.destroy()

        btns = tk.Frame(dlg)
        btns.grid(row=2, column=0, columnspan=2, pady=8)
        tk.Button(btns, text="OK", command=ok).pack(side="left", padx=6)
        tk.Button(btns, text="Cancel", command=cancel).pack(side="left", padx=6)

    def dottalk_ping(self):
        messagebox.showinfo("DotTalk++", f"Status: {self.dottalk.status()}")

    def fetch_schema_fixtures_backend(self):
        schema_local, _ = self._load_schema_and_settings()
        schema, fixtures = fetch_backend_schema_and_fixtures(self.dottalk, fallback_schema=schema_local, fallback_fixtures=None)
        if schema:
            path = os.path.join(os.path.dirname(__file__), "..", "data", "xbase_schema.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2)
        if fixtures:
            import_fixtures(self.session, fixtures)
        self.session.commit()
        self.refresh()
        messagebox.showinfo("DotTalk++", "Fetched schema/fixtures from backend (where available).")

    # ---- JSON Import/Export ----
    def import_from_json(self):
        path = filedialog.askopenfilename(title="Import JSON (schema or fixtures)", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "tables" in data:  # schema
                apply_schema(self.session, data)
                messagebox.showinfo("JSON", "Schema applied.")
            else:  # fixtures
                import_fixtures(self.session, data)
                messagebox.showinfo("JSON", "Fixtures imported.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("JSON Import", str(e))

    def export_current_table_json(self):
        Model = TABLES[self.current_table]
        tbl = Model.__tablename__
        rows = export_table(self.session, tbl)
        path = filedialog.asksaveasfilename(title="Export JSON", defaultextension=".json", initialfile=f"{tbl}.json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
        messagebox.showinfo("Export", f"Exported {len(rows)} row(s) to {os.path.basename(path)}.")

    def _load_schema_and_settings(self):
        # Try to load schema/settings from data dir if present
        try:
            with open(os.path.join(os.path.dirname(__file__), "..", "data", "xbase_schema.json"), "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception:
            schema = None
        try:
            with open(os.path.join(os.path.dirname(__file__), "..", "data", "xbase_settings.json"), "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = None
        return schema, settings

    def export_current_table_with_meta(self):
        Model = TABLES[self.current_table]
        tbl = Model.__tablename__
        schema, settings = self._load_schema_and_settings()
        packet = export_table_with_meta(
            self.session,
            tbl,
            schema=schema,
            settings=settings,
            dottalk_client=self.dottalk,
            prefer_backend_header=getattr(self, "_prefer_backend_header", True)
        )
        path = filedialog.asksaveasfilename(
            title="Export XBase JSON (with meta)",
            defaultextension=".json",
            initialfile=f"{tbl}_xbase.json",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(packet, f, indent=2)
        messagebox.showinfo("Export", f"Exported {tbl} with meta to {os.path.basename(path)}.")

    def export_all_tables_with_meta(self):
        schema, settings = self._load_schema_and_settings()
        payload = export_database_with_meta(self.session, schema=schema, settings=settings)
        path = filedialog.asksaveasfilename(
            title="Export ALL (XBase JSON package)",
            defaultextension=".json",
            initialfile="database_xbase_package.json",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        messagebox.showinfo("Export", f"Exported XBase JSON package to {os.path.basename(path)}.")

    # ---------------- Window / Theme helpers ----------------
    def toggle_dark(self):
        self._dark_mode = not self._dark_mode
        self._apply_palette()

    def _apply_palette(self):
        if self._dark_mode:
            bg = "#1e1e1e"
            fg = "#e0e0e0"
            acc = "#3a3a3a"
        else:
            bg = self.cget("bg")
            fg = "#000000"
            acc = "#efefef"
        self.configure(bg=bg)
        try:
            self.style.configure(".", background=bg, foreground=fg, fieldbackground=bg)
            self.style.configure("Treeview", background=bg, fieldbackground=bg, foreground=fg)
            self.style.configure("TFrame", background=bg, foreground=fg)
            self.style.configure("TLabel", background=bg, foreground=fg)
            self.style.configure("TButton", background=bg, foreground=fg)
            self.style.map("TButton", background=[("active", acc)])
        except Exception:
            pass

    def _register_child(self, win: tk.Toplevel):
        self._child_windows.append(win)

        def on_close():
            if win in self._child_windows:
                self._child_windows.remove(win)
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

    def close_children(self):
        for w in list(self._child_windows):
            try:
                w.destroy()
            except Exception:
                pass
        self._child_windows.clear()

    def set_windowed(self):
        self.state("normal")
        self.attributes("-fullscreen", False)
        self.geometry("1000x600")

    def set_fullscreen(self):
        try:
            self.attributes("-fullscreen", True)
        except Exception:
            self.state("zoomed")

    # ---- Help ----
    def show_help(self):
        win = tk.Toplevel(self)
        win.title(self._window_title("About"))
        win.geometry("800x600")
        self._register_child(win)
        txt = tk.Text(win, wrap="word")
        txt.pack(fill="both", expand=True)
        txt.insert(
            "1.0",
            "pycrud — DotTalk++ Companion\n\n"
            "• File: connect, open text/CSV, import/export JSON, XBase meta exports\n"
            "• Edit: CRUD via forms; double-click a row to edit\n"
            "• Tools: SQL Console, Compute Column\n"
            "• Relational: join, project, select (pandas-based)\n"
            "• DotTalk++: set backend URL, ping, fetch schema/fixtures\n"
            "• View: table switcher, dark mode, fullscreen\n"
        )
        txt.configure(state="disabled")

def run():
    app = App()
    app.mainloop()
